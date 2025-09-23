/*
  Voice Multi-Agent Accelerator - Infrastructure Deployment
  
  This Bicep template deploys the complete Azure infrastructure required for
  the Voice Multi-Agent system using Azure AI Foundry for healthcare scenarios.
  
  Key Resources Deployed:
  - Azure AI Services (for Voice Live API)
  - Azure Communication Services (for call center integration)
  - Container Apps Environment (for hosting the application)
  - Key Vault (for secure secret management)
  - Managed Identity (for secure service authentication)
  - Role-based access control (RBAC) assignments
  
  Architecture:
  Voice Client → Container App → Azure AI Services → Azure AI Foundry Agents
*/

targetScope = 'subscription'

// ===========================================
// Core Parameters
// ===========================================

@minLength(1)
@maxLength(64)
@description('Environment name used to generate unique resource names and enable multi-environment deployments (dev, staging, prod)')
param environmentName string

@minLength(1)
@description('Primary Azure region for deployment. Limited to regions with Azure OpenAI Service availability.')
@allowed([
  'eastus2'      // US East 2 - Primary recommended region
  'swedencentral' // Sweden Central - EU alternative
])
param location string

@description('Whether to create RBAC role assignments automatically. Set to false if roles are managed separately.')
param createRoleAssignments bool = true

// ===========================================
// Global Variables
// ===========================================

// Generate unique suffix for resource names to prevent conflicts
var uniqueSuffix = substring(uniqueString(subscription().id, environmentName), 0, 5)

// Standard tags applied to all resources for governance and cost tracking
var tags = {
  'azd-env-name': environmentName
  project: 'voice-multi-agent-accelerator'
  architecture: 'azure-ai-foundry'
}
var rgName = 'rg-${environmentName}-${uniqueSuffix}'
// TODO: Allow user to select in runtime
var modelName = 'gpt-4o-mini'

resource rg 'Microsoft.Resources/resourceGroups@2023-07-01' = {
  name: rgName
  location: location
  tags: tags
}

// [ User Assigned Identity for App to avoid circular dependency ]
module appIdentity './modules/identity.bicep' = {
  name: 'uami'
  scope: rg
  params: {
    location: location
    environmentName: environmentName
    uniqueSuffix: uniqueSuffix
  }
}

var sanitizedEnvName = toLower(replace(replace(replace(replace(environmentName, ' ', '-'), '--', '-'), '[^a-zA-Z0-9-]', ''), '_', '-'))
var logAnalyticsName = take('log-${sanitizedEnvName}-${uniqueSuffix}', 63)
var appInsightsName = take('insights-${sanitizedEnvName}-${uniqueSuffix}', 63)
module monitoring 'modules/monitoring/monitor.bicep' = {
  name: 'monitor'
  scope: rg
  params: {
    logAnalyticsName: logAnalyticsName
    appInsightsName: appInsightsName
    tags: tags
  }
}
module registry 'modules/containerregistry.bicep' = {
  name: 'registry'
  scope: rg
  params: {
    location: location
    environmentName: environmentName
    uniqueSuffix: uniqueSuffix
    identityName: appIdentity.outputs.name
    tags: tags
    // Reuse createRoleAssignments toggle for ACR pull role as well
    createAcrPullAssignment: createRoleAssignments
  }
}


module aiServices 'modules/aiservices.bicep' = {
  name: 'ai-services-deployment'
  scope: rg
  params: {
    environmentName: environmentName
    uniqueSuffix: uniqueSuffix
    identityId: appIdentity.outputs.identityId
    tags: tags
  }
}

// Azure AI Foundry Hub for multi-agent orchestration
module aiFoundryHub 'modules/aifoundryhub.bicep' = {
  name: 'ai-foundry-hub-deployment'
  scope: rg
  params: {
    location: location
    environmentName: environmentName
    uniqueSuffix: uniqueSuffix
    tags: tags
    identityId: appIdentity.outputs.identityId
    keyVaultId: keyvault.outputs.keyVaultId
    appInsightsId: monitoring.outputs.appInsightsId
  }
}

module acs 'modules/acs.bicep' = {
  name: 'acs-deployment'
  scope: rg
  params: {
    environmentName: environmentName
    uniqueSuffix: uniqueSuffix
    tags: tags
  }
}

// --- Azure OpenAI (Cognitive Services - kind OpenAI) ---
// Provides model endpoints (o-series/GPT) for multi-agent orchestration.
// Keep name length <= 64.
var openAIName = take('oai-${sanitizedEnvName}-${uniqueSuffix}', 30)
module openAIAccount 'modules/openai.bicep' = {
  name: 'openai'
  scope: rg
  params: {
    location: location
    name: openAIName
    tags: tags
  }
}

// --- AI Foundry Agent Service (Stub) ---
// TODO: Add resource definition when API surface is published/available.
// Expected (illustrative only):
// resource agentService 'Microsoft.AI/agentServices@<api-version>' = {
//   name: 'agent-${environmentName}-${uniqueSuffix}'
//   scope: rg
//   location: location
//   properties: {
//     openAIAccountId: openAI.id
//   }
// }

var keyVaultBaseName = 'kvcvoice'
var sanitizedKeyVaultName = take('${keyVaultBaseName}${uniqueSuffix}', 24)
module keyvault 'modules/keyvault.bicep' = {
  name: 'keyvault-deployment'
  scope: rg
  params: {
    location: location
    keyVaultName: sanitizedKeyVaultName
    tags: tags
    aiServicesKey: aiServices.outputs.aiServicesKey
    acsConnectionString: acs.outputs.acsConnectionString
    openAIKey: openAIAccount.outputs.openAIKey
  }
}

// Add role assignments 
module RoleAssignments 'modules/roleassignments.bicep' = if (createRoleAssignments) {
  scope: rg
  name: 'role-assignments'
  params: {
    identityPrincipalId: appIdentity.outputs.principalId
    aiServicesId: aiServices.outputs.aiServicesId
    keyVaultName: sanitizedKeyVaultName
    aiFoundryHubId: aiFoundryHub.outputs.aiFoundryHubId
  }

}

// Container App dependency array to ensure ordering if role assignments are created
var containerAppDeps = createRoleAssignments ? [RoleAssignments] : []

module containerapp 'modules/containerapp.bicep' = {
  name: 'containerapp-deployment'
  scope: rg
  params: {
    location: location
    environmentName: environmentName
    uniqueSuffix: uniqueSuffix
    tags: tags
    identityId: appIdentity.outputs.identityId
    containerRegistryName: registry.outputs.name
    aiServicesEndpoint: aiServices.outputs.aiServicesEndpoint
    modelDeploymentName: modelName
    aiServicesKeySecretUri: keyvault.outputs.aiServicesKeySecretUri
    acsConnectionStringSecretUri: keyvault.outputs.acsConnectionStringUri
    logAnalyticsWorkspaceName: logAnalyticsName
    openAIEndpoint: openAIAccount.outputs.openAIEndpoint
    keyVaultName: sanitizedKeyVaultName
    aiFoundryHubEndpoint: aiFoundryHub.outputs.aiFoundryHubEndpoint
    aiFoundryWorkspaceId: aiFoundryHub.outputs.workspaceId
    identityClientId: appIdentity.outputs.clientId
    imageName: ''
  }
  dependsOn: containerAppDeps
}


// OUTPUTS will be saved in azd env for later use
output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = rg.name
output AZURE_USER_ASSIGNED_IDENTITY_ID string = appIdentity.outputs.identityId
output AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID string = appIdentity.outputs.clientId

output AZURE_CONTAINER_REGISTRY_ENDPOINT string = registry.outputs.loginServer

// Convenience outputs for OpenAI (optional consumption by app/local tooling)
output AZURE_OPENAI_ENDPOINT string = openAIAccount.outputs.openAIEndpoint

// Azure AI Foundry Hub outputs for agent configuration
output AZURE_AI_FOUNDRY_ENDPOINT string = aiFoundryHub.outputs.aiFoundryHubEndpoint
output AZURE_AI_FOUNDRY_HUB_NAME string = aiFoundryHub.outputs.aiFoundryHubName
output AZURE_AI_FOUNDRY_WORKSPACE_ID string = aiFoundryHub.outputs.workspaceId

output SERVICE_API_ENDPOINTS array = ['${containerapp.outputs.containerAppFqdn}/acs/incomingcall']
