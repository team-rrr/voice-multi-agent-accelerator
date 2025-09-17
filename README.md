# Voice-Orchestrator: Real-Time Multi-Agent Assistant with Azure AI

*Azure Sample accelerator for the Microsoft Hackathon 2025.*

## Deploying Infrastructure (Azure Developer CLI)

Prerequisites:

1. Install Azure CLI (<https://learn.microsoft.com/cli/azure/install-azure-cli>)
2. Install Azure Developer CLI (<https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd>)
3. Login:

```pwsh
az login
azd auth login
```

Provision (creates resource group + core services):

```pwsh
azd up
```

If you only want to (re)provision infra without rebuilding/publishing the container image:

```pwsh
azd provision
```

## Parameters & Environment Flags

The Bicep templates include toggles you can set per environment:

| Env Var | Purpose | Default | When to set false |
|---------|---------|---------|-------------------|
| `createRoleAssignments` | Creates Cognitive Services + Key Vault role assignments for the user-assigned identity | true | You already granted roles manually or lack permission to assign RBAC (avoid RoleAssignmentExists) |
| `createAcrPullAssignment` | Creates `AcrPull` assignment on the Container Registry for the identity | mirrors `createRoleAssignments` | ACR `AcrPull` already granted manually |

Set a value:

```pwsh
azd env set createRoleAssignments false
azd env set createAcrPullAssignment false
```

Show all current values:

```pwsh
azd env get-values
```

## RBAC Troubleshooting

### 1. Missing Permission to Create Role Assignments

Symptoms: Deployment fails with `AuthorizationFailed` or `Client is not authorized to perform action Microsoft.Authorization/roleAssignments/write`.

Workaround:

1. Manually assign needed roles (portal or CLI) to the managed identity:

```pwsh
$subId = (az account show --query id -o tsv)
$rg = '<resource-group-name>'
$miName = '<user-assigned-identity-name>'
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

1. Disable template RBAC creation:

```pwsh
azd env set createRoleAssignments false
azd env set createAcrPullAssignment false
azd provision
```

### 2. RoleAssignmentExists Error
Symptom: `RoleAssignmentExists: The role assignment already exists.`

Cause: Template attempts to create a role that was already manually created in a previous attempt.

Fix:

```pwsh
azd env set createRoleAssignments false
azd env set createAcrPullAssignment false
azd provision
```

### 3. Verifying Identity Permissions

```pwsh
az role assignment list --assignee <principal-id> -o table
```

## Next Steps
1. Push a custom container image (replace placeholder image in container app module).
2. Add model orchestration logic to FastAPI server.
3. Extend monitoring / dashboards.

## License
MIT
