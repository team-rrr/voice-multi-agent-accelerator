param location string
param environmentName string
param uniqueSuffix string
param tags object
param identityId string
param containerRegistryName string
param aiServicesEndpoint string
param modelDeploymentName string
param aiServicesKeySecretUri string
param acsConnectionStringSecretUri string
param logAnalyticsWorkspaceName string
@description('Azure OpenAI endpoint (optional)')
param openAIEndpoint string = ''
@description('Name of Key Vault secret containing OpenAI API Key (optional).')
param openAISecretName string = 'AZURE-OPENAI-API-KEY'
@description('Key Vault name (without https:// and domain) hosting secrets.')
param keyVaultName string

@description('Azure AI Foundry Hub endpoint for agent orchestration')
param aiFoundryHubEndpoint string = ''

@description('Azure AI Foundry Hub workspace ID for agent deployment')
param aiFoundryWorkspaceId string = ''

@description('Client ID of the user-assigned managed identity')
param identityClientId string

@description('Container image name to deploy')
param imageName string = ''

// Helper to sanitize environmentName for valid container app name
var sanitizedEnvName = toLower(replace(replace(replace(replace(environmentName, ' ', '-'), '--', '-'), '[^a-zA-Z0-9-]', ''), '_', '-'))
var containerAppName = take('ca-${sanitizedEnvName}-${uniqueSuffix}', 32)
var containerEnvName = take('cae-${sanitizedEnvName}-${uniqueSuffix}', 32)

// Base secrets used always
var baseSecrets = [
  {
    name: 'azure-ai-services-key'
    keyVaultUrl: aiServicesKeySecretUri
    identity: identityId
  }
  {
    name: 'acs-connection-string'
    keyVaultUrl: acsConnectionStringSecretUri
    identity: identityId
  }
]

// Optional OpenAI secret injection (points to KV secret; will succeed only if exists)
var openAISecret = empty(openAIEndpoint) ? [] : [
  {
    name: 'azure-openai-api-key'
    keyVaultUrl: 'https://${keyVaultName}${environment().suffixes.keyvaultDns}/secrets/${openAISecretName}'
    identity: identityId
  }
]

// Environment variables
var baseEnv = [
  {
    name: 'AZURE_VOICE_LIVE_API_KEY'
    secretRef: 'azure-ai-services-key'
  }
  {
    name: 'AZURE_VOICE_LIVE_ENDPOINT'
    value: aiServicesEndpoint
  }
  {
    name: 'VOICE_LIVE_MODEL'
    value: modelDeploymentName
  }
  {
    name: 'ACS_CONNECTION_STRING'
    secretRef: 'acs-connection-string'
  }
  {
    name: 'DEBUG_MODE'
    value: 'true'
  }
]

// Azure AI Foundry environment variables
var aiFoundryEnv = empty(aiFoundryHubEndpoint) ? [] : [
  {
    name: 'AZURE_AI_FOUNDRY_ENDPOINT'
    value: aiFoundryHubEndpoint
  }
  {
    name: 'AI_FOUNDRY_PROJECT_NAME'
    value: '${environmentName}-project'
  }
  {
    name: 'AI_FOUNDRY_AGENT_ID'
    value: 'orchestrator-agent'
  }
  {
    name: 'AZURE_AI_FOUNDRY_AGENT_ID'
    value: 'orchestrator-agent'  
  }
  {
    name: 'AZURE_AI_ORCHESTRATOR_AGENT_ID'
    value: 'orchestrator-agent'
  }
  {
    name: 'AZURE_AI_INFO_AGENT_ID'
    value: 'info-agent'
  }
  {
    name: 'AZURE_AI_PATIENT_CONTEXT_AGENT_ID'
    value: 'patient-context-agent'
  }
  {
    name: 'AZURE_AI_ACTION_AGENT_ID'
    value: 'action-agent'
  }
  {
    name: 'VOICE_LIVE_AGENT_ID'
    value: 'orchestrator-agent'
  }
  {
    name: 'AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID'
    value: identityClientId
  }
  {
    name: 'AZURE_AI_FOUNDRY_WORKSPACE_ID'
    value: aiFoundryWorkspaceId
  }
]
var openAIEnv = empty(openAIEndpoint) ? [] : [
  {
    name: 'AZURE_OPENAI_ENDPOINT'
    value: openAIEndpoint
  }
  {
    name: 'AZURE_OPENAI_API_KEY'
    secretRef: 'azure-openai-api-key'
  }
]
var allEnv = concat(baseEnv, openAIEnv, aiFoundryEnv)

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' existing = { name: logAnalyticsWorkspaceName }


// Remove the fetch image module as it causes circular dependency issues

resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: containerEnvName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
  }
}

resource containerApp 'Microsoft.App/containerApps@2024-10-02-preview' = {
  name: containerAppName
  location: location
  tags: union(tags, { 'azd-service-name': 'backend' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${identityId}': {} }
  }
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      registries: [
        {
          server: '${containerRegistryName}.azurecr.io'
          identity: identityId
        }
      ]
      secrets: concat(baseSecrets, openAISecret)
    }
    template: {
      containers: [
        {
          name: 'main'
          image: !empty(imageName) ? imageName : '${containerRegistryName}.azurecr.io/voice-multi-agent-accelerator/backend-dev:azd-deploy-1758111171'
          env: allEnv
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
        }
      ]
      // TODO add memory/cpu scaling
      scale: {
        minReplicas: 1
        maxReplicas: 10
        rules: [
          {
            name: 'http-scaler'
            http: {
              metadata: {
                concurrentRequests: '100'
              }
            }
          }
        ]
      }
    }
  }
}

output containerAppFqdn string = containerApp.properties.configuration.ingress.fqdn
output containerAppId string = containerApp.id
