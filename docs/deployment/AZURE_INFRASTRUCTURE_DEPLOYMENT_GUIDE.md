# Azure Infrastructure Deployment Guide

Complete guide for deploying the Voice Multi-Agent Accelerator infrastructure using Azure Developer CLI (azd).

## 🎯 **Deployment Overview**

This infrastructure deployment creates a complete Azure AI Foundry environment supporting:
- **Azure AI Foundry Hub**: Multi-agent orchestration platform
- **Container Apps**: Serverless hosting for FastAPI application
- **Azure AI Services**: Voice Live API integration
- **Azure OpenAI**: GPT-4o-mini model deployment
- **Supporting Services**: Key Vault, Storage, Container Registry, Monitoring

## 📋 **Prerequisites**

### Required Tools
```powershell
# Install Azure CLI
winget install Microsoft.AzureCLI

# Install Azure Developer CLI
winget install Microsoft.Azd

# Verify installations
az --version
azd version
```

### Authentication
```powershell
# Login to Azure CLI
az login

# Login to Azure Developer CLI
azd auth login
```

### Required Permissions
Your Azure account needs:
- **Subscription Contributor** role
- **User Access Administrator** role (for RBAC assignments)
- Access to **Azure AI services** and **OpenAI services**

## 🚀 **Deployment Steps**

### 1. Clone and Navigate to Repository
```powershell
git clone <repository-url>
cd voice-multi-agent-accelerator
```

### 2. Initialize Azure Developer CLI
```powershell
# Initialize azd environment
azd init

# Set environment variables if needed
azd env set createRoleAssignments true
```

### 3. Deploy Infrastructure
```powershell
# Complete deployment (provision + deploy)
azd up

# Or provision infrastructure only
azd provision

# Or deploy application only (after provision)
azd deploy
```

### 4. Verify Deployment
```powershell
# Check deployment status
azd show

# Get environment values
azd env get-values

# Test health endpoint
curl https://ca-dev-6uvq7.lemondune-86508fd9.eastus2.azurecontainerapps.io/health
```

## 🏗️ **Infrastructure Components**

### Core Resources Created

| Resource Type | Purpose | Naming Convention |
|---------------|---------|-------------------|
| **Resource Group** | Container for all resources | `rg-{env}-{suffix}` |
| **Azure AI Foundry Hub** | Multi-agent orchestration | `aihub-{env}-{suffix}` |
| **Container Apps Environment** | Application hosting | `cae-{env}-{suffix}` |
| **Container App** | FastAPI application | `ca-{env}-{suffix}` |
| **Azure AI Services** | Voice Live API | `aiServices-{env}-{suffix}` |
| **Azure OpenAI** | Language models | `oai-{env}-{suffix}` |
| **Container Registry** | Docker images | `acr{suffix}` |
| **Key Vault** | Secret management | `kvcvoice{suffix}` |
| **Storage Account** | AI Hub storage | `staihub{suffix}` |
| **Managed Identity** | Secure authentication | `{env}-{suffix}-id` |

### Security Configuration

#### Managed Identity Permissions
The deployment creates a User-Assigned Managed Identity with:
- **Cognitive Services User** role on AI Services
- **Key Vault Secrets User** role on Key Vault  
- **AcrPull** role on Container Registry
- **Contributor** role on AI Foundry Hub

#### Key Vault Secrets
Automatically stored secrets:
- `AZURE-AI-SERVICES-KEY`: AI Services API key
- `ACS-CONNECTION-STRING`: Communication Services connection
- `AZURE-OPENAI-API-KEY`: OpenAI API key

## 🔧 **Configuration Options**

### Environment Variables

#### Core Settings
```powershell
# Set environment name
azd env set AZURE_ENV_NAME dev

# Set deployment location
azd env set AZURE_LOCATION eastus2
```

#### RBAC Configuration
```powershell
# Enable automatic role assignments (default: true)
azd env set createRoleAssignments true

# Disable if you want to manage roles manually
azd env set createRoleAssignments false
```

### Deployment Parameters

Available parameters in `infra/main.parameters.json`:
```json
{
  "environmentName": "dev",
  "location": "eastus2",
  "createRoleAssignments": true
}
```

## 🎯 **Azure AI Foundry Configuration**

### AI Foundry Hub Outputs
After successful deployment, these values are available:

```powershell
# Get AI Foundry configuration
azd env get-values | grep AZURE_AI_FOUNDRY

# Expected outputs:
AZURE_AI_FOUNDRY_ENDPOINT="https://aihub-dev-6uvq7.api.azureml.ms"
AZURE_AI_FOUNDRY_HUB_NAME="aihub-dev-6uvq7"  
AZURE_AI_FOUNDRY_WORKSPACE_ID="ceead15b-9209-492e-ab73-069e43269e3d"
```

### Container App Environment Variables
The Container App is configured with:
```bash
AZURE_AI_FOUNDRY_ENDPOINT          # AI Foundry Hub endpoint
AI_FOUNDRY_PROJECT_NAME            # Project name for agents
AZURE_AI_ORCHESTRATOR_AGENT_ID     # Orchestrator agent ID
AZURE_AI_INFO_AGENT_ID            # Info agent ID  
AZURE_AI_PATIENT_CONTEXT_AGENT_ID # Patient context agent ID
AZURE_AI_ACTION_AGENT_ID          # Action agent ID
VOICE_LIVE_AGENT_ID               # Voice Live agent ID
AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID  # Managed identity
```

## 🚨 **Common Issues & Troubleshooting**

### Issue: Container App Image Not Found
```
MANIFEST_UNKNOWN: manifest tagged by "latest" is not found
```

**Solution**: Update container image reference
```powershell
# Use existing working image
az acr repository show-tags --name acrrgdev6uvq7 --repository voice-multi-agent-accelerator/backend-dev

# Update Bicep template to use existing tag
# See troubleshooting guide for details
```

### Issue: RBAC Permission Errors
```
AuthorizationFailed: The client does not have authorization to perform action 'Microsoft.Authorization/roleAssignments/write'
```

**Solution**: Manual role assignment
```powershell
# Disable automatic RBAC
azd env set createRoleAssignments false

# Assign roles manually (see troubleshooting guide)
```

### Issue: Network Connectivity Problems
```
Connection aborted, ConnectionResetError
```

**Solution**: Check network and retry
```powershell
# Check Azure CLI connectivity
az account show

# Retry deployment
azd up --no-prompt
```

## 📊 **Deployment Verification**

### Infrastructure Validation Checklist
- [ ] Resource group created with all resources
- [ ] Azure AI Foundry Hub accessible
- [ ] Container App running and accessible
- [ ] Key Vault secrets populated
- [ ] Managed Identity roles assigned
- [ ] Container Registry contains images

### Application Validation
```powershell
# Test endpoints
$endpoint = (azd env get-values | Select-String "SERVICE_API_ENDPOINTS").ToString().Split('"')[1]

# Test health endpoint
curl "$endpoint/health"

# Test voice interface
# Navigate to: $endpoint/static/voice_test.html
```

## 🔄 **Post-Deployment Steps**

### 1. Configure Azure AI Foundry Agents
```powershell
# Get Azure AI Foundry Hub endpoint
$hubEndpoint = (azd env get-values | Select-String "AZURE_AI_FOUNDRY_ENDPOINT").ToString().Split('"')[1]

# Navigate to Azure AI Foundry Studio
Start-Process $hubEndpoint
```

### 2. Deploy Multi-Agent System
Follow the [Agent Deployment Guide](../implementation-guides/AZURE_AI_FOUNDRY_AGENT_INSTRUCTIONS.md) to:
- Create agents in Azure AI Foundry
- Configure agent prompts
- Test agent orchestration

### 3. Update Environment Variables
```powershell
# Set agent IDs after creating agents
azd env set AZURE_AI_ORCHESTRATOR_AGENT_ID "asst_abc123..."
azd env set AZURE_AI_INFO_AGENT_ID "asst_def456..."
azd env set AZURE_AI_PATIENT_CONTEXT_AGENT_ID "asst_ghi789..."
azd env set AZURE_AI_ACTION_AGENT_ID "asst_jkl012..."

# Redeploy with agent configuration
azd deploy
```

## 📚 **Related Documentation**

- [Provision and Deployment Troubleshooting](../troubleshooting-guides/PROVISION_AND_DEPLOYMENT_TROUBLESHOOTING.md)
- [Azure AI Foundry Agent Instructions](../implementation-guides/AZURE_AI_FOUNDRY_AGENT_INSTRUCTIONS.md)
- [Solution B Testing Guide](../troubleshooting-guides/SOLUTION_B_TESTING_GUIDE.md)

## 🎉 **Success Criteria**

Deployment is successful when:
- ✅ All Azure resources created without errors
- ✅ Container App accessible and responding to health checks
- ✅ Azure AI Foundry Hub operational
- ✅ Managed Identity has required permissions
- ✅ Environment variables properly configured
- ✅ Ready for agent deployment phase

Your infrastructure is now ready to support the Azure AI Foundry multi-agent system!