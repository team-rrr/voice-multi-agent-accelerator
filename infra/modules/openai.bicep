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

@secure()
output openAIKey string = openAI.listKeys().key1
output openAIEndpoint string = openAI.properties.endpoint
