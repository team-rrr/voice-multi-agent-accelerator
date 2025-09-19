# MedOrchestrator

*Azure Sample accelerator for Microsoft Hackathon 2025 - Real-time voice interaction system with complete multi-agent orchestration.*

## Table of Contents

- [Project Overview](#project-overview)
- [Healthcare Multi-Agent System](#healthcare-multi-agent-system)
- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [Repository Structure](#repository-structure)
- [Core Components](#core-components)
- [Voice Processing Pipeline](#voice-processing-pipeline)
- [Multi-Agent Architecture](#multi-agent-architecture---fully-implemented)
- [Security & Configuration](#security--configuration)
- [Development Workflow](#development-workflow)
- [Project Status](#project-status)
- [Deployment](#deploying-infrastructure-azure-developer-cli)
- [Troubleshooting](#rbac-troubleshooting)
- [Monitoring & Debugging](#monitoring--debugging)

## Project Overview

A **real-time voice interaction system** featuring:

- **Multi-Agent Orchestration** with Semantic Kernel integration
- **Healthcare Caregiver Assistant** with specialized agents (InfoAgent, PatientContextAgent, ActionAgent)
- **Azure Voice Live API** integration for real-time speech processing
- **FastAPI WebSocket** backend with professional web interface
- **Structured Response System** with appointment preparation checklists
- **Dual Mode Support** - Voice and Text interaction
- **Cloud-native deployment** on Azure Container Apps

## Healthcare Multi-Agent System

**Complete Multi-Agent System Implementation:**

- **InfoAgent**: Gathers patient symptoms and medical history
- **PatientContextAgent**: Analyzes patient context and appointment relevance
- **ActionAgent**: Generates personalized appointment preparation checklists
- **Orchestration**: Sequential agent execution with context passing
- **Voice Integration**: Full voice-to-orchestration-to-speech pipeline

## Architecture Overview

### Multi-Agent Voice Pipeline

```text
User Voice Input (Caregiver Query)
    ↓ WebSocket (PCM Audio)
FastAPI Server (app_voice_live.py)
    ↓ Voice Live Handler + Orchestration Callback
Azure Voice Live API ────────┐
    ├── Speech-to-Text       │
    └── Text-to-Speech       │
                             │
Multi-Agent Orchestration    │
    ├── InfoAgent            │
    ├── PatientContextAgent  │
    ├── ActionAgent          │
    └── Structured Response  │
    ↓                        │
Audio Synthesis ─────────────┘
    ↓ WebSocket (Binary Audio)
Web Client (Professional UI + Card Display)
```

## Agent Orchestration Flow

1. **InfoAgent** → Analyzes user query for symptoms and medical context
2. **PatientContextAgent** → Determines appointment relevance and patient needs
3. **ActionAgent** → Generates personalized preparation checklists
4. **Response Formation** → Combines spoken response + structured card data
5. **Voice Synthesis** → Converts to natural speech for audio playback

## Quick Start

### Local Development

```bash
# 1. Setup environment
cp .env.template .env
# Edit .env with your Azure credentials
cd server

# 2. Install dependencies
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 3. Run server (Updated command)
python -m uvicorn app_voice_live:app --host 0.0.0.0 --port 8000 --reload

# 4. Open client
# Navigate to: http://localhost:8000/static/voice_test.html
```

### Testing Multi-Agent Voice Interaction

1. **Connect**: Click "Connect" button
2. **Voice Mode**: Select "Voice Mode" (default)
3. **Start Speaking**: Click "Start Speaking"
4. **Caregiver Query**: Say *"I have chest pain and need to prepare for my appointment with Doctor Smith"*
5. **Hear Response**: Listen to complete orchestrated response with appointment guidance
6. **View Checklist**: See structured appointment preparation checklist in the card display

### Sample Interactions

**Voice Input**: *"I'm experiencing shortness of breath and have an appointment tomorrow"*

**AI Response**: Comprehensive spoken guidance + structured checklist including:

- **Symptom Documentation**: When symptoms started, severity, triggers
- **Medical History**: Previous conditions, current medications, allergies
- **Lifestyle Factors**: Relevant habits, stress levels, recent changes
- **Questions for Doctor**: Prepared questions specific to your condition

## Repository Structure

```text
voice-multi-agent-accelerator/
├── server/                    # FastAPI backend
│   ├── app_voice_live.py     # Main server with WebSocket endpoints
│   ├── voice_live_handler.py # Azure Voice Live API handler
│   ├── orchestrator.py       # Multi-agent orchestration engine
│   ├── plugins.py           # Semantic Kernel agents (InfoAgent, PatientContextAgent, ActionAgent)
│   ├── static/               # Web client files
│   │   ├── voice_test.html   # Professional multi-agent UI with card display
│   │   └── audio-processor.js # AudioWorklet processor
│   ├── .env.template         # Environment variables template
│   └── requirements.txt      # Python dependencies
├── infra/                    # Azure infrastructure
│   ├── main.bicep           # Main Bicep template
│   ├── main.parameters.json # Deployment parameters
│   └── modules/             # Bicep modules
├── docs/                     # Documentation
│   └── agent-prompts/        # Agent system prompts
│       ├── InfoAgent.md      # Symptom gathering agent
│       ├── PatientContextAgent.md # Context analysis agent
│       ├── ActionAgent.md    # Checklist generation agent
│       └── OrchestratorAgent.md # Orchestration logic
└── azure.yaml               # Azure Developer CLI config
```

## Core Components

### Multi-Agent Orchestration (`orchestrator.py`)

- **Semantic Kernel Integration**: Microsoft's AI orchestration framework
- **Sequential Agent Execution**: InfoAgent → PatientContextAgent → ActionAgent
- **Context-Aware Processing**: User query analysis and context passing
- **Structured Response Generation**: Spoken response + card data payload
- **Healthcare-Focused Logic**: Specialized for appointment preparation

### Healthcare Agents (`plugins.py`)

- **InfoAgent**: Extracts symptoms, medical history, lifestyle factors from user input
- **PatientContextAgent**: Analyzes appointment relevance and patient preparation needs
- **ActionAgent**: Generates personalized appointment preparation checklists
- **Kernel Functions**: Decorated with `@kernel_function` for Semantic Kernel integration

### Voice Live Handler (`voice_live_handler.py`)

- **Azure Voice Live API** WebSocket client
- **Real-time audio streaming** (PCM binary data)
- **Premium neural voice**: en-US-Ava:DragonHDLatestNeural
- **Orchestration Integration**: Calls multi-agent system on transcription
- **Session management** and error handling

### FastAPI Server (`app_voice_live.py`)

- **WebSocket endpoint**: `/ws/voice` for real-time communication with orchestration
- **HTTP API endpoint**: `/api/query` for direct multi-agent queries
- **Orchestration Callback**: Passes `run_orchestration` function to voice handler
- **Static file serving**: Professional multi-agent web client
- **Health monitoring**: `/health` endpoint

### Professional Web Client (`voice_test.html` + `audio-processor.js`)

- **Dual Mode Interface**: Voice Mode and Text Mode with clean button layout
- **Card Display System**: Structured appointment preparation checklists
- **Enhanced Conversation Formatting**: Proper bullet points, bold text, structured responses
- **AudioWorklet** for smooth audio playback
- **Real-time Multi-Agent Responses**: Visual and audio feedback
- **Professional UI Design**: Fluent UI inspired styling with responsive layout

## Voice Processing Pipeline

### Audio Flow

1. **Browser** → Microphone capture (getUserMedia)
2. **WebSocket** → PCM audio streaming to server
3. **Voice Live API** → Real-time Speech-to-Text
4. **Multi-Agent Orchestration** → Healthcare-focused response generation
5. **Neural TTS** → Ava voice synthesis
6. **WebSocket** → Binary audio streaming to client
7. **AudioWorklet** → Smooth audio playback

### Audio Technical Details

- **Format**: PCM 16kHz, 16-bit, mono
- **Streaming**: Binary WebSocket messages
- **Playback**: AudioWorklet with ring buffer
- **Latency**: ~200-500ms end-to-end
- **Voice**: Premium neural voice (Ava)

### Multi-Agent Integration Details

#### Orchestration Flow

1. **Voice Input** → Azure Speech-to-Text transcription
2. **Transcription** → Triggers `on_final_transcription` callback
3. **Orchestration** → Sequential agent execution (Info → Context → Action)
4. **Response Formation** → Combines spoken response + structured card data
5. **TTS Synthesis** → Converts orchestrated response to audio
6. **Audio Streaming** → Real-time playback with visual card display

#### Technical Stack

- **Semantic Kernel v1.37.0**: Microsoft's AI orchestration framework
- **FastAPI + WebSockets**: Real-time bidirectional communication
- **Pydantic Models**: Structured API responses (`ChecklistResponse`)
- **Professional UI**: Fluent Design inspired interface with responsive layout
- **Context Management**: Agent-to-agent context passing with `KernelArguments`

## Multi-Agent Architecture - FULLY IMPLEMENTED

### Current Implementation: Healthcare Caregiver Assistant

**Complete Semantic Kernel Integration:**

```python
# orchestrator.py - Multi-agent orchestration with Semantic Kernel
@kernel_function(name="InfoAgent", description="Gathers patient symptoms and medical history")
def info_agent(self, user_query: str) -> str:
    # Extracts symptoms, medical history, lifestyle factors

@kernel_function(name="PatientContextAgent", description="Analyzes patient context")
def patient_context_agent(self, user_query: str, info_analysis: str) -> str:
    # Determines appointment relevance and preparation needs

@kernel_function(name="ActionAgent", description="Generates appointment checklist")
def action_agent(self, user_query: str, context_analysis: str) -> str:
    # Creates personalized appointment preparation tasks

# Sequential execution with context passing
info_result = await kernel.invoke("InfoAgent", KernelArguments(user_query=query))
context_result = await kernel.invoke("PatientContextAgent", KernelArguments(
    user_query=query, info_analysis=info_result.value))
action_result = await kernel.invoke("ActionAgent", KernelArguments(
    user_query=query, context_analysis=context_result.value))
```

**Voice Integration Pipeline:**

```python
# voice_live_handler.py - Voice-to-orchestration integration
async def on_final_transcription(self, user_query: str):
    if self.orchestration_callback:
        response = await self.orchestration_callback(user_query)
        # Returns ChecklistResponse with spoken_response and card_data
```

**Structured Response Model:**

```python
# Pydantic model for consistent API responses
class ChecklistResponse(BaseModel):
    spoken_response: str      # Natural language for TTS
    card_data: dict          # Structured data for UI cards
```

### Agent Specialization

Each agent has dedicated system prompts and specialized functions:

- **InfoAgent**: Medical symptom extraction and history gathering
- **PatientContextAgent**: Appointment relevance analysis and patient needs assessment
- **ActionAgent**: Personalized preparation checklist generation with specific tasks

### Conversation Context & Memory

```python
# Context-aware agent execution
kernel_args = KernelArguments(
    user_query=user_input,
    info_analysis=previous_agent_output,
    context_analysis=context_agent_output
)
# Each agent builds upon previous agent insights
```

## Security & Configuration

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

- `.env` excluded from git (in `.gitignore`)
- Managed Identity for Azure resources
- Key Vault for secret management
- RBAC permissions with least privilege
- Secure credential handling in production

## Development Workflow

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

## Project Status

### Core Foundation - IMPLEMENTED

- Azure Voice Live API integration
- Real-time audio streaming
- Azure deployment infrastructure
- Security best practices

### Multi-Agent Framework - IMPLEMENTED

- **Semantic Kernel integration** with Microsoft's AI orchestration framework
- **Healthcare agent system** (InfoAgent, PatientContextAgent, ActionAgent)
- **Sequential agent execution** with context passing between agents
- **Voice-to-orchestration pipeline** with callback integration
- **Structured response system** with spoken + card data
- **Professional UI** with card display and conversation formatting

### Specialized Healthcare Agents - IMPLEMENTED

- **InfoAgent**: Symptom and medical history extraction
- **PatientContextAgent**: Appointment relevance analysis
- **ActionAgent**: Personalized preparation checklist generation
- **Orchestration Engine**: Coordinates all agents with context awareness

### System Verification Checklist

1. **Run the local server** - `python -m uvicorn app_voice_live:app --host 0.0.0.0 --port 8000 --reload`
2. **Connect with a voice client** - Professional web interface with Voice/Text modes
3. **Speak the full caregiver query** - Real-time voice input with transcription
4. **Hear the complete, orchestrated response spoken back** - Multi-agent orchestrated responses with TTS

### Future Enhancements (Optional)

- Additional healthcare specializations (mental health, chronic conditions)
- Integration with healthcare APIs (EHR, appointment systems)
- Multi-language support for diverse patient populations
- Advanced conversation memory and patient history tracking

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

## Monitoring & Debugging

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
