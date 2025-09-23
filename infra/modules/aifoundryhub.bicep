/*
  Azure AI Foundry Hub Module

  This module creates an Azure AI Foundry Hub workspace configured for multi-agent systems.
  The hub provides the foundation for deploying and orchestrating AI agents that work together
  to accomplish complex tasks like healthcare appointment preparation.

  Key Features:
  - Secure Azure AI Foundry Hub with managed identity integration
  - Storage account for AI artifacts and model storage
  - Key Vault integration for secure secret management
  - Application Insights for monitoring and telemetry
  - Configured for multi-agent orchestration scenarios

  Security Considerations:
  - Uses managed identity for secure service-to-service authentication
  - Public network access can be controlled via parameter
  - All secrets stored in Azure Key Vault
  - RBAC-based access control
*/

param location string
param environmentName string
param uniqueSuffix string
param tags object = {}

@description('Resource ID of the user-assigned managed identity for secure authentication')
param identityId string

@description('Resource ID of the Key Vault for secret management')
param keyVaultId string

@description('Resource ID of Application Insights for monitoring')
param appInsightsId string

@description('Whether to allow public network access to the AI Foundry Hub')
param publicNetworkAccess string = 'Enabled'

// Generate unique names for Azure AI Foundry resources
var sanitizedEnvName = toLower(replace(replace(replace(replace(environmentName, ' ', '-'), '--', '-'), '[^a-zA-Z0-9-]', ''), '_', '-'))
var aiFoundryHubName = take('aihub-${sanitizedEnvName}-${uniqueSuffix}', 64)
var storageAccountName = take('staihub${replace(sanitizedEnvName, '-', '')}${uniqueSuffix}', 24)

// Create storage account for AI Foundry Hub (required for AI artifacts)
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  tags: tags
  sku: {
    name: 'Standard_LRS' // Locally redundant storage for cost efficiency
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true  // Required for AI Foundry Hub integration
    encryption: {
      services: {
        blob: {
          enabled: true
          keyType: 'Account'
        }
        file: {
          enabled: true
          keyType: 'Account'
        }
      }
      keySource: 'Microsoft.Storage'
    }
    minimumTlsVersion: 'TLS1_2'
    networkAcls: {
      defaultAction: 'Allow' // Allow access for AI Foundry Hub
    }
    publicNetworkAccess: publicNetworkAccess
    supportsHttpsTrafficOnly: true
  }
}

// Create Azure AI Foundry Hub workspace
resource aiFoundryHub 'Microsoft.MachineLearningServices/workspaces@2024-10-01' = {
  name: aiFoundryHubName
  location: location
  tags: union(tags, {
    'ai-foundry-type': 'hub'
    'multi-agent-system': 'voice-healthcare'
  })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identityId}': {}
    }
  }
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
  kind: 'Hub' // Specify this is an AI Foundry Hub
  properties: {
    description: 'Azure AI Foundry Hub for Voice Multi-Agent Healthcare System'
    friendlyName: 'Voice Multi-Agent AI Hub'
    
    // Required associated services
    storageAccount: storageAccount.id
    keyVault: keyVaultId
    applicationInsights: appInsightsId
    
    // Security and access configuration
    publicNetworkAccess: publicNetworkAccess
    hbiWorkspace: false  // Not a high business impact workspace for this scenario
    
    // AI Foundry Hub specific configuration
    hubResourceId: null // This IS the hub, so null reference
    v1LegacyMode: false // Use modern v2 APIs
    
    // Primary identity for the workspace
    primaryUserAssignedIdentity: identityId
  }
}

// Output values for use by other modules
@description('The resource ID of the Azure AI Foundry Hub')
output aiFoundryHubId string = aiFoundryHub.id

@description('The name of the Azure AI Foundry Hub')
output aiFoundryHubName string = aiFoundryHub.name

@description('The endpoint URL for the Azure AI Foundry Hub')
output aiFoundryHubEndpoint string = 'https://${aiFoundryHub.name}.api.azureml.ms'

@description('The resource ID of the storage account created for the AI Foundry Hub')
output storageAccountId string = storageAccount.id

@description('The name of the storage account created for the AI Foundry Hub') 
output storageAccountName string = storageAccount.name

@description('The workspace ID (GUID) for the Azure AI Foundry Hub')
output workspaceId string = aiFoundryHub.properties.workspaceId
