# Voice Multi-Agent Accelerator: Real-Time Voice AI with Azure Voice Live API

*Azure Sample accelerator for Microsoft Hackathon 2025 - Real-time voice interaction system with multi-agent architecture foundation.*

## 🎯 Project Overview

A **real-time voice interaction system** featuring:

- ✅ **Echo Bot** with premium AI voice (en-US-Ava:DragonHDLatestNeural)
- ✅ **Azure Voice Live API** integration for real-time speech processing  
- ✅ **FastAPI WebSocket** backend with AudioWorklet client
- ✅ **Multi-agent architecture** foundation (ready for expansion)
- ✅ **Cloud-native deployment** on Azure Container Apps

## 🏗️ Architecture Overview

```text
🎙️ User Voice Input
    ↓ WebSocket (PCM Audio)
🌐 FastAPI Server (app_voice_live.py)
    ↓ Voice Live Handler
📡 Azure Voice Live API
    ├── 🎤 Speech-to-Text
    ├── 🧠 GPT-4o-mini (Echo Logic)
    ├── 🔊 Text-to-Speech (Ava Neural Voice)
    └── 📡 Real-time Audio Streaming
    ↓ WebSocket (Binary Audio)
🎧 Web Client (AudioWorklet Playback)
```

## 🚀 Quick Start

### Local Development

```bash
# 1. Setup environment
cd server
cp .env.template .env
# Edit .env with your Azure credentials

# 2. Install dependencies
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 3. Run server
python app_voice_live.py

# 4. Open client
# Navigate to: http://localhost:8000/static/voice_test.html
```

### Test Voice Interaction

1. Click "Connect to Echo Bot"
2. Switch to "Voice Mode"
3. Click "Start Speaking"
4. Say "Hello" → Hear AI respond "Hello" in Ava voice! 🎉

## 📂 Repository Structure

```text
voice-multi-agent-accelerator/
├── server/                    # FastAPI backend
│   ├── app_voice_live.py     # Main server with WebSocket endpoints
│   ├── voice_live_handler.py # Azure Voice Live API handler
│   ├── static/               # Web client files
│   │   ├── voice_test.html   # Voice interaction UI
│   │   └── audio-processor.js # AudioWorklet processor
│   ├── .env.template         # Environment variables template
│   └── requirements.txt      # Python dependencies
├── infra/                    # Azure infrastructure
│   ├── main.bicep           # Main Bicep template
│   ├── main.parameters.json # Deployment parameters
│   └── modules/             # Bicep modules
└── azure.yaml               # Azure Developer CLI config
```

## 🔧 Core Components

### Voice Live Handler (`voice_live_handler.py`)

- **Azure Voice Live API** WebSocket client
- **Real-time audio streaming** (PCM binary data)
- **Premium neural voice**: en-US-Ava:DragonHDLatestNeural
- **Echo bot logic** with GPT-4o-mini integration
- **Session management** and error handling

### FastAPI Server (`app_voice_live.py`)

- **WebSocket endpoint**: `/ws/voice` for real-time communication
- **Static file serving**: Voice interaction web client
- **Health monitoring**: `/health` endpoint
- **CORS enabled** for cross-origin requests

### Web Client (`voice_test.html` + `audio-processor.js`)

- **AudioWorklet** for smooth audio playback
- **WebSocket** binary audio handling
- **Real-time transcription** display
- **Voice controls** and connection management

## 🎙️ Voice Processing Pipeline

### Audio Flow

1. **Browser** → Microphone capture (getUserMedia)
2. **WebSocket** → PCM audio streaming to server
3. **Voice Live API** → Real-time Speech-to-Text
4. **GPT-4o-mini** → Echo response generation
5. **Neural TTS** → Ava voice synthesis
6. **WebSocket** → Binary audio streaming to client
7. **AudioWorklet** → Smooth audio playback

### Audio Technical Details

- **Format**: PCM 16kHz, 16-bit, mono
- **Streaming**: Binary WebSocket messages
- **Playback**: AudioWorklet with ring buffer
- **Latency**: ~200-500ms end-to-end
- **Voice**: Premium neural voice (Ava)

## 🚀 Multi-Agent Architecture (Ready for Expansion)

### Current Implementation: Echo Bot

```python
# Simple echo logic in voice_live_handler.py
async def process_message(self, text: str) -> str:
    return text  # Echo back the spoken text
```

### Future Multi-Agent Expansion

**Agent Router** (Coming Soon):

```python
agents = {
    "weather": WeatherAgent(),
    "calendar": CalendarAgent(),  
    "email": EmailAgent(),
    "general": GeneralAssistantAgent()
}

# Route based on intent classification
agent = await classify_intent(user_message)
response = await agents[agent].process(user_message)
```

**Conversation Context**:

```python
# Maintain conversation history across agents
context = ConversationContext()
context.add_turn(user_message, agent_response, agent_type)
```

## 🔐 Security & Configuration

### Environment Variables

Create `.env` from `.env.template`:

```bash
# Required Azure credentials
AZURE_OPENAI_API_KEY=your_openai_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_SPEECH_KEY=your_speech_key
AZURE_SPEECH_REGION=your_region
```

### Security Best Practices

- ✅ `.env` excluded from git (in `.gitignore`)
- ✅ Managed Identity for Azure resources
- ✅ Key Vault for secret management
- ✅ RBAC permissions with least privilege
- ✅ Secure credential handling in production

## 🛠️ Development Workflow

### Local Testing

```bash
# Run server
python server/app_voice_live.py

# Test endpoints
curl http://localhost:8000/health
# Open: http://localhost:8000/static/voice_test.html
```

### Git Workflow

```bash
# Feature development
git checkout -b feature/new-agent
git add .
git commit -m "feat: Add weather agent"
git push origin feature/new-agent
```

### Docker Testing

```bash
# Build container
docker build -t voice-app server/

# Run locally
docker run -p 8000:8000 --env-file server/.env voice-app
```

## 🔄 Next Steps & Roadmap

### Phase 1: Core Foundation ✅

- [x] Azure Voice Live API integration
- [x] Real-time audio streaming
- [x] Echo bot implementation
- [x] Azure deployment infrastructure
- [x] Security best practices

### Phase 2: Multi-Agent Framework (In Progress)

- [ ] Agent routing system
- [ ] Intent classification
- [ ] Conversation context management
- [ ] Agent registry and discovery

### Phase 3: Specialized Agents (Planned)

- [ ] Calendar management agent
- [ ] Email assistance agent

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

## 📊 Monitoring & Debugging

### Application Insights

- **Real-time metrics**: Response times, error rates
- **Custom telemetry**: Voice session tracking
- **Performance**: Audio streaming latency
- **Debugging**: Detailed error traces

### Log Analysis

```bash
# View Azure logs
azd logs --follow

# Local debugging
python app_voice_live.py --log-level DEBUG
```

## Next Steps

1. Push a custom container image (replace placeholder image in container app module).
2. Add model orchestration logic to FastAPI server.
3. Extend monitoring / dashboards.

## License

MIT
