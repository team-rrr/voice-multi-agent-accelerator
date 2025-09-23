# Provision a| 6 | `resource not found: ... tagged with 'azd-service-name: backend'` | Container App tagged with `azd-service-name: app` but `azure.yaml` service name is `backend` | Updated tag to `backend` in `containerapp.bicep` and reprovisioned |
| 7 | Container App image is placeholder | Initial scaffold used sample image | Plan to replace with built ACR image (`backend:latest`) |
| 8 | `MANIFEST_UNKNOWN: manifest tagged by "latest" is not found` | Container App trying to pull non-existent image tag | Updated Bicep template to use existing image with specific tag |
| 9 | Network connectivity issues (`ConnectionResetError`) | Azure CLI/ACR build network connectivity problems | Retry commands, use existing images from registry |
| 10 | Dockerfile references wrong Python file | Dockerfile CMD pointed to `app_voice_live:app` instead of `app_voice_live_agent_mode:app` | Updated Dockerfile CMD entry point |
| 11 | Bicep secrets configuration error | Secrets property outside configuration object in container app Bicep | Fixed indentation and structure of secrets in Bicep template | Deployment Troubleshooting Guide

This document captures the real issues encountered and the steps taken to achieve a successful `azd provision` and `azd deploy backend` for this accelerator.

## Summary of Issues Encountered

| # | Symptom / Error | Root Cause | Resolution |
|---|-----------------|-----------|-----------|
| 1 | `AuthorizationFailed` / inability to create role assignments | Insufficient RBAC permissions (no roleAssignment write) | Manually created required role assignments + added template toggle to skip |
| 2 | `RoleAssignmentExists` | Template attempted to recreate roles already added manually | Introduced `createRoleAssignments` & `createAcrPullAssignment` flags (set to `false`) |
| 3 | Missing ACR in early attempt | Partial / failed deployment left infra incomplete | Manually created ACR + ensured template module compiles cleanly |
| 4 | Bicep compile error (registry name length) | Generated ACR name could be < 5 chars | Introduced deterministic fallback prefix ensuring length >= 5 |
| 5 | Invalid use of `assert()` in Bicep | `assert` not a Bicep function | Removed invalid variable & simplified name logic |
| 6 | `resource not found: ... tagged with 'azd-service-name: backend'` | Container App tagged with `azd-service-name: app` but `azure.yaml` service name is `backend` | Updated tag to `backend` in `containerapp.bicep` and reprovisioned |
| 7 | Container App image is placeholder | Initial scaffold used sample image | Plan to replace with built ACR image (`backend:dev`) |

---

## 1. Role Assignment Permission Errors

**Symptom:**

```text
AuthorizationFailed: The client '...' with object id '...' does not have authorization to perform action 'Microsoft.Authorization/roleAssignments/write'
```

**Root Cause:** Account lacked permission to create RBAC assignments (e.g. not Owner / User Access Administrator).

**Resolution:** Manually assign roles to the User Assigned Managed Identity (UAMI), then disable automatic RBAC creation in templates.

### Manual Role Assignment Commands

```pwsh
# Variables (replace placeholders)
$subId = (az account show --query id -o tsv)
$rg = 'rg-dev-6uvq7'                          # Resource group
$miName = '<user-assigned-identity-name>'      # From deployment output
$principalId = az identity show -g $rg -n $miName --query principalId -o tsv

# Cognitive Services User
az role assignment create --assignee-object-id $principalId --assignee-principal-type ServicePrincipal --role "Cognitive Services User" --scope \
  /subscriptions/$subId/resourceGroups/$rg/providers/Microsoft.CognitiveServices/accounts/<ai-services-account-name>

# Key Vault Secrets User
az role assignment create --assignee-object-id $principalId --assignee-principal-type ServicePrincipal --role "Key Vault Secrets User" --scope \
  /subscriptions/$subId/resourceGroups/$rg/providers/Microsoft.KeyVault/vaults/<key-vault-name>

# AcrPull
az role assignment create --assignee-object-id $principalId --assignee-principal-type ServicePrincipal --role AcrPull --scope \
  /subscriptions/$subId/resourceGroups/$rg/providers/Microsoft.ContainerRegistry/registries/<acr-name>
```

### Disable Role Creation in Future Runs

```pwsh
azd env set createRoleAssignments false
azd env set createAcrPullAssignment false
azd provision
```

---

## 2. RoleAssignmentExists Errors

**Symptom:**

```text
RoleAssignmentExists: The role assignment already exists
```

**Root Cause:** Template attempted to recreate a role already assigned manually.

**Resolution:** Turned off role assignment modules via environment flags.

### Flags

| Env Var | Purpose |
|---------|---------|
| `createRoleAssignments` | Wraps cognitive services + key vault RBAC module |
| `createAcrPullAssignment` | Controls ACR `AcrPull` role assignment |

**Set both to false if roles already exist.**

---

## 3. Missing / Partially Created ACR

**Symptom:** Subsequent template steps assumed ACR existed but it wasn't deployed.

**Root Cause:** Earlier failed provision aborted before reaching registry module.

**Resolution:** A later successful provision created the registry after fixing compilation issues; alternatively could have been created manually:

```pwsh
az acr create -g <rg-name> -n <acr-name> --sku Basic
```

---

## 4. Registry Name Length Validation

**Symptom:** Bicep error: minimum length 5 not enforced.

**Fix:** Enforced fallback prefix + suffix logic:

```bicep
// Simplified logic now guarantees >=5 characters
overrides: var containerRegistryName = take('${fallbackAcrBase}${generatedAcrBase}${uniqueSuffix}', 50)
```

---

## 5. Invalid `assert` Usage in Bicep

**Symptom:** Compilation error: `The name 'assert' does not exist`.

**Resolution:** Removed pseudo-assert variable; relied on safe construction of `containerRegistryName`.

---

## 6. Service Tag Mismatch Prevented Deployment

**Symptom:**

```text
error ... unable to find a resource tagged with 'azd-service-name: backend'
```

**Root Cause:** `containerapp.bicep` used `azd-service-name: app` but `azure.yaml` service key is `backend`.

**Resolution:** Updated resource tag:

```bicep
tags: union(tags, { 'azd-service-name': 'backend' })
```

Then:

```pwsh
azd provision
azd deploy backend
```

---

## 7. Skipping RBAC Creation After Manual Fixes

When RBAC exists, always disable template-driven RBAC to keep deployments idempotent:

```pwsh
azd env set createRoleAssignments false
azd env set createAcrPullAssignment false
```

Verify:

```pwsh
azd env get-values
```

---

## 8. Verifying Tags & Outputs

Check Container App tags:

```pwsh
az resource show -g <rg-name> -n <container-app-name> --resource-type Microsoft.App/containerApps --query tags
```

Expect:

```json
{
  "azd-env-name": "dev",
  "azd-service-name": "backend"
}
```

---

## 9. Replacing Placeholder Container Image (Planned)

Current image: `mcr.microsoft.com/azuredocs/containerapps-helloworld:latest`.

To use your app image:

```pwsh
$acr = (azd env get-values | Select-String AZURE_CONTAINER_REGISTRY_ENDPOINT).ToString().Split('=')[1].Trim('"')
az acr login --name ($acr.Split('.')[0])
docker build -t $acr/backend:dev -f server/Dockerfile ./server
docker push $acr/backend:dev
```

Update in `infra/modules/containerapp.bicep`:

```bicep
image: '${containerRegistryName}.azurecr.io/backend:dev'
```

Then:

```pwsh
azd deploy backend
```

---

## 10. Useful Diagnostic Commands

```pwsh
# What-if to preview infra changes
az deployment sub what-if --location eastus2 --name preview --template-file infra/main.bicep --parameters environmentName=dev createRoleAssignments=false

# List role assignments for identity
az role assignment list --assignee <principal-id> -o table

# Tail Container App logs
az containerapp logs show -g <rg> -n <container-app-name> --follow
```

---

## 11. Checklist For a Clean Re-Deployment

1. `azd env get-values` shows `createRoleAssignments=false` (and `createAcrPullAssignment=false` if used).
2. All required roles already present on UAMI.
3. Container App tagged with correct `azd-service-name`.
4. Bicep compiles (`azd provision` succeeds with no RBAC errors).
5. Image updated & deployable (`azd deploy backend`).

---

## 12. Recent Deployment Issues (September 2025)

### Container App Image Issues

**Symptom:**
```text
MANIFEST_UNKNOWN: manifest tagged by "latest" is not found
```

**Root Cause:** Container App Bicep template references `backend:latest` but actual images have different naming convention.

**Resolution Steps:**

1. **Check existing images in ACR:**
```pwsh
az acr repository list --name acrrgdev6uvq7
az acr repository show-tags --name acrrgdev6uvq7 --repository voice-multi-agent-accelerator/backend-dev
```

2. **Update Bicep template to use existing image:**
```bicep
image: '${containerRegistryName}.azurecr.io/voice-multi-agent-accelerator/backend-dev:azd-deploy-1758111171'
```

### Dockerfile Application Entry Point

**Symptom:** Container fails to start with wrong Python module reference.

**Resolution:** Update Dockerfile CMD:
```dockerfile
CMD ["uvicorn", "app_voice_live_agent_mode:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Bicep Template Structure Issues

**Symptom:** Bicep compilation errors with secrets configuration.

**Resolution:** Ensure proper indentation:
```bicep
configuration: {
  secrets: concat(baseSecrets, openAISecret)
  registries: [...]
}
```

### Network Connectivity Issues

**Symptom:**
```text
Connection aborted, ConnectionResetError(10054)
```

**Workaround:** 
- Retry commands multiple times
- Use existing images instead of building new ones
- Check network firewall settings

---

## 13. Azure AI Foundry Infrastructure

### New Resources Added

The infrastructure now includes Azure AI Foundry Hub:

```bicep
module aiFoundryHub 'modules/aifoundryhub.bicep' = {
  name: 'ai-foundry-hub-deployment'
  // Creates AI Foundry Hub for multi-agent orchestration
}
```

**Key Environment Variables Created:**
- `AZURE_AI_FOUNDRY_ENDPOINT`
- `AZURE_AI_FOUNDRY_HUB_NAME`
- `AZURE_AI_FOUNDRY_WORKSPACE_ID`

### Container App Environment Variables

Updated to include Azure AI Foundry agent configuration:
- `AI_FOUNDRY_PROJECT_NAME`
- `AZURE_AI_ORCHESTRATOR_AGENT_ID`
- `AZURE_AI_INFO_AGENT_ID`
- `AZURE_AI_PATIENT_CONTEXT_AGENT_ID`
- `AZURE_AI_ACTION_AGENT_ID`

---

## 14. Successful Deployment Verification

After successful `azd up`, verify:

```pwsh
# Check all environment values
azd env get-values

# Expected key values:
AZURE_AI_FOUNDRY_ENDPOINT="https://aihub-dev-6uvq7.api.azureml.ms"
AZURE_AI_FOUNDRY_HUB_NAME="aihub-dev-6uvq7"
AZURE_AI_FOUNDRY_WORKSPACE_ID="ceead15b-9209-492e-ab73-069e43269e3d"
SERVICE_BACKEND_IMAGE_NAME="acrrgdev6uvq7.azurecr.io/voice-multi-agent-accelerator/backend-dev:azd-deploy-1758111171"
```

---

## 15. Future Hardening Ideas

- Add health probe & liveness config.
- Separate `createAcrPullAssignment` from general RBAC toggle (currently reused).
- Add CI pipeline for lint + what-if + deploy.
- Parameterize image tag & model selection.

---

## Related Documents

- [Voice Live API Race Condition Troubleshooting](./VOICE_LIVE_API_RACE_CONDITION.md)
- [Architecture Overview](../README.md#architecture)

---

If you encounter a new error not covered here, capture the full message and run a `what-if` to see pending changes before retrying.