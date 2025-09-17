param location string
param environmentName string
param uniqueSuffix string
param identityName string
param tags object = {}

param adminUserEnabled bool = true
param anonymousPullEnabled bool = false
param dataEndpointEnabled bool = false
param encryption object = {
  status: 'disabled'
}
param networkRuleBypassOptions string = 'AzureServices'
param publicNetworkAccess string = 'Enabled'
param sku object = {
  name: 'Standard'
}
param zoneRedundancy string = 'Disabled'
@description('Create AcrPull role assignment for the provided user-assigned identity (set false if role already assigned manually).')
param createAcrPullAssignment bool = true

// Helper to sanitize environmentName for valid container registry name (alphanumeric only)
var sanitizedEnvName = toLower(replace(replace(replace(replace(replace(environmentName, ' ', ''), '-', ''), '--', ''), '[^a-zA-Z0-9]', ''), '_', ''))
// Guarantee min length by always prefixing with 'acr' and then adding sanitized env + unique suffix
var fallbackAcrBase = 'acrrg' // 5 chars to satisfy minimum length
var generatedAcrBase = empty(sanitizedEnvName) ? 'base' : sanitizedEnvName
// This guarantees minimal length: fallbackAcrBase (4) + at least one char from generatedAcrBase (set to 'base' if empty) + uniqueSuffix (at least 3) => >=8
var containerRegistryName = take('${fallbackAcrBase}${generatedAcrBase}${uniqueSuffix}', 50)

// 2022-02-01-preview needed for anonymousPullEnabled
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2022-02-01-preview' = {
  name: containerRegistryName
  location: location
  tags: tags
  sku: sku
  properties: {
    adminUserEnabled: adminUserEnabled
    anonymousPullEnabled: anonymousPullEnabled
    dataEndpointEnabled: dataEndpointEnabled
    encryption: encryption
    networkRuleBypassOptions: networkRuleBypassOptions
    publicNetworkAccess: publicNetworkAccess
    zoneRedundancy: zoneRedundancy
  }
}

resource appIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = { name: identityName }

// Skip if createAcrPullAssignment = false to avoid RoleAssignmentExists when manually pre-created
resource acrPullRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (createAcrPullAssignment) {
  scope: containerRegistry
  name: guid(subscription().id, containerRegistry.id, appIdentity.id, 'acrPullRole')
  properties: {
    roleDefinitionId:  subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalType: 'ServicePrincipal'
    principalId: appIdentity.properties.principalId
  }
}

output loginServer string = containerRegistry.properties.loginServer
output name string = containerRegistry.name
