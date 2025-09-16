param location string
param keyVaultName string
param tags object
@secure()
param aiServicesKey string
@secure()
param acsConnectionString string
@secure()
param openAIKey string = '' // Optional: if supplied, will be stored as secret

var sanitizedKeyVaultName = take(toLower(replace(replace(replace(replace(keyVaultName, '--', '-'), '_', '-'), '[^a-zA-Z0-9-]', ''), '-$', '')), 24)

resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: sanitizedKeyVaultName
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    accessPolicies: []
    enableRbacAuthorization: true
    enableSoftDelete: true
    enablePurgeProtection: true
    publicNetworkAccess: 'Enabled'
  }
}


resource aiServicesKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'AZURE-VOICE-LIVE-API-KEY'
  properties: {
    value: aiServicesKey
  }
}

resource acsConnectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: keyVault
  name: 'ACS-CONNECTION-STRING'
  properties: {
    value: acsConnectionString
  }
}

// Conditional OpenAI key secret creation when key provided
resource openAIKeySecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(openAIKey)) {
  parent: keyVault
  name: 'AZURE-OPENAI-API-KEY'
  properties: {
    value: openAIKey
  }
}

var keyVaultDnsSuffix = environment().suffixes.keyvaultDns

output aiServicesKeySecretUri string = 'https://${keyVault.name}${keyVaultDnsSuffix}/secrets/${aiServicesKeySecret.name}'
output acsConnectionStringUri string = 'https://${keyVault.name}${keyVaultDnsSuffix}/secrets/${acsConnectionStringSecret.name}'
output keyVaultId string = keyVault.id
output keyVaultName string = keyVault.name
// NOTE: Not outputting secret URI to avoid exposing potential secret metadata; fetch at runtime by name via managed identity.
output openAIKeySecretUri string = ''
