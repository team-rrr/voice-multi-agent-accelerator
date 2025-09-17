param location string
param name string
param tags object = {}

@allowed([
  'S0'
])
param skuName string = 'S0'

resource openAI 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: name
  location: location
  kind: 'OpenAI'
  sku: {
    name: skuName
  }
  tags: tags
  properties: {
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      defaultAction: 'Allow'
    }
    disableLocalAuth: false
  }
}

// Deploy gpt-4o-mini model
resource gpt4oMiniDeployment 'Microsoft.CognitiveServices/accounts/deployments@2023-05-01' = {
  parent: openAI
  name: 'gpt-4o-mini'
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4o-mini'
      version: '2024-07-18'
    }
  }
  sku: {
    name: 'Standard'
    capacity: 10
  }
}

@secure()
output openAIKey string = openAI.listKeys().key1
output openAIEndpoint string = openAI.properties.endpoint
