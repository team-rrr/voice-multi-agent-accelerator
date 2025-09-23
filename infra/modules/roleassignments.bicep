param identityPrincipalId string
param aiServicesId string
param keyVaultName string
param aiFoundryHubId string = ''

resource aiServicesResource 'Microsoft.CognitiveServices/accounts@2023-05-01' existing = {
  name: last(split(aiServicesId, '/'))
}

resource aiServicesRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiServicesId, identityPrincipalId, 'Cognitive Services User')
  scope: aiServicesResource
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
    principalId: identityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Removed generic Reader role (aiAccess) to avoid duplicate / unnecessary assignments once manual access granted.


resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' existing = {
  name: keyVaultName
}

resource keyVaultRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, identityPrincipalId, 'Key Vault Secrets User')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7')
    principalId: identityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// Azure AI Foundry Hub role assignment (if hub is deployed)
resource aiFoundryHubResource 'Microsoft.MachineLearningServices/workspaces@2024-10-01' existing = if (!empty(aiFoundryHubId)) {
  name: last(split(aiFoundryHubId, '/'))
}

resource aiFoundryHubRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(aiFoundryHubId)) {
  name: guid(aiFoundryHubId, identityPrincipalId, 'AzureML Data Scientist')
  scope: aiFoundryHubResource
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'f6c7c914-8db3-469d-8ca1-694a8f32e121')
    principalId: identityPrincipalId
    principalType: 'ServicePrincipal'
  }
}
