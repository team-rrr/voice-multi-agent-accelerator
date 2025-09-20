# Voice Multi-Agent Accelerator

*Azure Sample accelerator for Microsoft Hackathon 2025 - Real-time voice interaction system with Azure AI Foundry multi-agent orchestration.*

## Table of Contents

- [Project Overview](#project-overview)
- [Healthcare Multi-Agent System](#healthcare-multi-agent-system)
- [Architecture Overview](#architecture-overview)
- [Quick Start](#quick-start)
- [Repository Structure](#repository-structure)
- [Core Components](#core-components)
- [Voice Processing Pipeline](#voice-processing-pipeline)
- [Azure AI Foundry Architecture](#azure-ai-foundry-multi-agent-architecture---fully-implemented)
- [Security & Configuration](#security--configuration)
- [Development Workflow](#development-workflow)
- [Project Status](#project-status)
- [Deployment](#deploying-infrastructure-azure-developer-cli)
- [Documentation & Support](#documentation--support)
- [Monitoring & Debugging](#monitoring--debugging)

## Project Overview

A **real-time voice interaction system** featuring:

- **Azure AI Foundry Agent Mode** - Cloud-native multi-agent orchestration eliminating race conditions
- **Healthcare Caregiver Assistant** with specialized Azure AI agents (InfoAgent, PatientContextAgent, ActionAgent)
- **Azure Voice Live API** integration with direct agent connection for real-time speech processing  
- **FastAPI WebSocket** backend with professional web interface
- **Structured Response System** with appointment preparation checklists
- **Dual Mode Support** - Voice and Text interaction
- **Cloud-native deployment** on Azure Container Apps with Azure AI Foundry integration

## Healthcare Multi-Agent System

**Azure AI Foundry Multi-Agent System (Solution B - COMPLETED):**

- **OrchestratorAgent**: `asst_bvYsNwZvM3jlJVEJ9kRzvc1Z` - Main coordination agent deployed in Azure AI Foundry
- **InfoAgent**: `asst_IyzeNFdfP85EOtBFAqCDrsHh` - Gathers patient symptoms and medical history
- **PatientContextAgent**: `asst_h1I4NmJlQwOLKnOJGufsEuvp` - Analyzes patient context and appointment relevance  
- **ActionAgent**: `asst_iFzbrJduLjccC42HVuFlGmYz` - Generates personalized appointment preparation checklists
- **Race Condition Eliminated**: Direct Azure AI Foundry agent connection prevents competing AI responses
- **Voice Integration**: Direct agent-to-speech pipeline with Azure Voice Live API agent mode

## Architecture Overview

### Azure AI Foundry Agent Mode Pipeline (Solution B)

```text
User Voice Input (Caregiver Query)
    ↓ WebSocket (PCM Audio)
FastAPI Server (app_voice_live_agent_mode.py)
    ↓ Voice Live Agent Handler (Agent Mode)
Azure Voice Live API ────────────────┐
    ├── Speech-to-Text               │
    ├── Direct Agent Connection      │
    └── Text-to-Speech               │
                                     │
Azure AI Foundry Agent System       │
    ├── OrchestratorAgent ───────────┤
    ├── InfoAgent                    │
    ├── PatientContextAgent          │
    ├── ActionAgent                  │
    └── Native Agent Orchestration   │
    ↓                                │
Audio Synthesis ─────────────────────┘
    ↓ WebSocket (Binary Audio)
Web Client (Professional UI + Card Display)
```

## Azure AI Foundry Agent Flow (Solution B)

1. **OrchestratorAgent** → Receives user query and coordinates multi-agent response
2. **InfoAgent** → Analyzes user query for symptoms and medical context (via OrchestratorAgent)
3. **PatientContextAgent** → Determines appointment relevance and patient needs (via OrchestratorAgent)
4. **ActionAgent** → Generates personalized preparation checklists (via OrchestratorAgent)
5. **Native Azure Response** → Azure AI Foundry provides coordinated response
6. **Voice Synthesis** → Direct conversion to natural speech via Voice Live API agent mode

## Quick Start

### Local Development

```bash
# 1. Setup environment
cd server
cp .env.template .env
# Edit .env with your Azure credentials

# 2. Install dependencies
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install .

# 3. Run server (Solution B - Azure AI Foundry Agent Mode)
python app_voice_live_agent_mode.py

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
├── server/                              # FastAPI backend (Solution B)
│   ├── app_voice_live_agent_mode.py    # Main server with Azure AI Foundry integration  
│   ├── voice_live_agent_handler_agent_mode.py # Azure AI Foundry agent handler
│   ├── logging_config.py               # Professional logging configuration
│   ├── static/                         # Web client files
│   │   ├── voice_test.html             # Professional multi-agent UI with card display
│   │   └── audio-processor.js          # AudioWorklet processor
│   ├── .env.template                   # Environment variables template
│   └── pyproject.toml                  # Python dependencies
├── infra/                              # Azure infrastructure
│   ├── main.bicep                      # Main Bicep template
│   ├── main.parameters.json            # Deployment parameters
│   └── modules/                        # Bicep modules
├── docs/                               # Organized documentation
│   ├── agent-prompts/                  # Original agent system prompts
│   ├── implementation-guides/          # Strategic implementation documentation
│   │   ├── SOLUTION_B_MIGRATION_STRATEGY.md
│   │   ├── SOLUTION_B_IMPLEMENTATION_PLAN.md
│   │   └── AZURE_AI_FOUNDRY_AGENT_INSTRUCTIONS.md
│   └── troubleshooting-guides/         # Operational support guides
│       ├── PROVISION_AND_DEPLOYMENT_TROUBLESHOOTING.md
│       ├── SOLUTION_B_TESTING_GUIDE.md
│       └── VOICE_LIVE_API_RACE_CONDITION.md
├── obsolete-files/                     # Archived Solution A files
│   ├── app_voice_live.py              # Original server (Semantic Kernel)
│   ├── voice_live_handler.py          # Original handler
│   ├── orchestrator.py                # Local orchestration engine
│   ├── plugins.py                     # Semantic Kernel agents
│   └── voice_live_agent_handler.py    # Original agent handler
└── azure.yaml                         # Azure Developer CLI config
```

## Core Components

### Azure AI Foundry Agent Integration (`voice_live_agent_handler_agent_mode.py`)

- **Direct Agent Connection**: Uses `agent_id` instead of `model` for Voice Live API
- **Race Condition Elimination**: No competing AI responses between local and cloud agents
- **Real-time audio streaming** (PCM binary data)
- **Premium neural voice**: en-US-Ava:DragonHDLatestNeural
- **Session management** and error handling with professional logging

### Azure AI Foundry Agents (Cloud-Deployed)

- **OrchestratorAgent** (`asst_bvYsNwZvM3jlJVEJ9kRzvc1Z`): Main coordination agent
- **InfoAgent** (`asst_IyzeNFdfP85EOtBFAqCDrsHh`): Extracts symptoms, medical history, lifestyle factors
- **PatientContextAgent** (`asst_h1I4NmJlQwOLKnOJGufsEuvp`): Analyzes appointment relevance and patient preparation needs
- **ActionAgent** (`asst_iFzbrJduLjccC42HVuFlGmYz`): Generates personalized appointment preparation checklists
- **Native Azure Orchestration**: Agent-to-agent communication handled by Azure AI Foundry

### FastAPI Server (`app_voice_live_agent_mode.py`)

- **WebSocket endpoint**: `/ws/voice` for real-time communication with Azure AI Foundry agents
- **HTTP API endpoint**: `/api/query` for direct agent queries
- **Azure AI Foundry Integration**: Direct connection to deployed agents
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

### Azure AI Foundry Integration Details

#### Agent Mode Flow (Solution B)

1. **Voice Input** → Azure Speech-to-Text transcription
2. **Transcription** → Direct connection to Azure AI Foundry OrchestratorAgent
3. **Native Agent Orchestration** → Azure AI Foundry manages agent coordination
4. **Multi-Agent Processing** → Info → Context → Action agents via Azure AI Foundry
5. **Azure Response** → Native Azure AI response generation
6. **Audio Streaming** → Direct TTS synthesis and real-time playback

#### Solution B Technical Implementation

- **Azure AI Foundry**: Cloud-native agent orchestration and management
- **FastAPI + WebSockets**: Real-time bidirectional communication
- **Professional UI**: Fluent Design inspired interface with responsive layout
- **Agent Mode Connection**: Direct `agent_id` connection eliminating race conditions
- **Professional Logging**: Structured logging with conversation flow tracking

## Azure AI Foundry Multi-Agent Architecture - FULLY IMPLEMENTED

### Solution B: Azure AI Foundry Agent Mode ✅ COMPLETED

**Azure AI Foundry Deployed Agents:**

```bash
# Deployed Azure AI Foundry Agents (Production)
OrchestratorAgent: asst_bvYsNwZvM3jlJVEJ9kRzvc1Z
InfoAgent: asst_IyzeNFdfP85EOtBFAqCDrsHh  
PatientContextAgent: asst_h1I4NmJlQwOLKnOJGufsEuvp
ActionAgent: asst_iFzbrJduLjccC42HVuFlGmYz
```

**Voice Live API Integration:**

```python
# voice_live_agent_handler_agent_mode.py - Direct agent connection
def session_config():
    return {
        "type": "session.update", 
        "session": {
            "instructions": "You are connected to an Azure AI Foundry multi-agent system...",
            "turn_detection": {"type": "server_vad"},
            "input_audio_format": "pcm16",
            "output_audio_format": "pcm16",
            "voice": "alloy"
        }
    }

# Direct agent connection eliminates race conditions
agent_id = os.getenv("AZURE_AI_FOUNDRY_AGENT_ID")
# Uses agent_id instead of model parameter
```

**Race Condition Elimination:**

```python
# Solution B: No local orchestration competing with Azure Voice Live API
# Azure AI Foundry agents handle all multi-agent coordination natively
# Single AI response source prevents "conversation already has an active response" errors
```

### Agent Specialization

Each agent has dedicated system prompts and specialized functions:

- **InfoAgent**: Medical symptom extraction and history gathering
- **PatientContextAgent**: Appointment relevance analysis and patient needs assessment  
- **ActionAgent**: Personalized preparation checklist generation with specific tasks

### Azure AI Foundry Agent Context Management

```python
# Azure AI Foundry native agent context handling
# Context is managed automatically by Azure AI Foundry between agents
# OrchestratorAgent coordinates with InfoAgent, PatientContextAgent, ActionAgent
# No manual context passing required - Azure AI Foundry handles agent communication natively

# Direct agent connection
agent_id = os.getenv("AZURE_AI_FOUNDRY_AGENT_ID")  
# Agent coordination handled by Azure AI Foundry platform
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
# Run server (Solution B - Azure AI Foundry Agent Mode)
cd server
python app_voice_live_agent_mode.py

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
# Build container (Solution B)
docker build -t voice-app server/

# Run locally with Azure AI Foundry agents
docker run -p 8000:8000 --env-file server/.env voice-app
```

## Project Status

### ✅ COMPLETED: Solution B - Azure AI Foundry Agent Mode

- **Azure AI Foundry Integration** - Cloud-native multi-agent orchestration
- **Race Condition Eliminated** - Direct agent connection prevents competing AI responses
- **Deployed Production Agents** - All healthcare agents operational in Azure AI Foundry
- **Azure Voice Live API** - Real-time voice processing with agent mode connection
- **Professional logging system** - Structured debugging with conversation flow tracking

### ✅ COMPLETED: Healthcare Agent System

- **OrchestratorAgent** (`asst_bvYsNwZvM3jlJVEJ9kRzvc1Z`) - Main coordination agent
- **InfoAgent** (`asst_IyzeNFdfP85EOtBFAqCDrsHh`) - Symptom and medical history extraction
- **PatientContextAgent** (`asst_h1I4NmJlQwOLKnOJGufsEuvp`) - Appointment relevance analysis  
- **ActionAgent** (`asst_iFzbrJduLjccC42HVuFlGmYz`) - Personalized preparation checklist generation
- **Native Azure Orchestration** - Agent-to-agent coordination handled by Azure AI Foundry

### ✅ COMPLETED: Infrastructure & Deployment

- **Real-time audio streaming** - WebSocket-based PCM audio pipeline
- **Azure deployment infrastructure** - Container Apps with Bicep templates
- **Security best practices** - Managed Identity, Key Vault, RBAC
- **Professional UI** with card display and conversation formatting
- **Repository Organization** - Clean separation of active code, obsolete files, and documentation

### System Verification Checklist

1. **Run the local server** - `python app_voice_live_agent_mode.py` (Solution B)
2. **Connect with a voice client** - Professional web interface at `http://localhost:8000/static/voice_test.html`
3. **Speak the full caregiver query** - Real-time voice input with transcription
4. **Hear the complete Azure AI Foundry response** - Multi-agent responses via Azure AI Foundry with TTS

### ✅ COMPLETED: Azure AI Foundry Migration (Solution B)

**Successfully Implemented:**

- ✅ Deployed all agents to Azure AI Foundry with production agent IDs
- ✅ Migrated InfoAgent, PatientContextAgent, ActionAgent to Azure AI Foundry
- ✅ Updated Voice Live connection to use agent_id instead of model
- ✅ Race condition eliminated - no competing AI responses
- ✅ All functionality preserved with improved reliability

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

## Documentation & Support

The repository includes comprehensive documentation organized into logical categories:

### 📚 [Implementation Guides](./docs/implementation-guides/)

Strategic documentation for understanding and implementing Solution B:

- **[Solution B Migration Strategy](./docs/implementation-guides/SOLUTION_B_MIGRATION_STRATEGY.md)** - Complete migration approach and planning
- **[Solution B Implementation Plan](./docs/implementation-guides/SOLUTION_B_IMPLEMENTATION_PLAN.md)** - Step-by-step implementation checklist
- **[Azure AI Foundry Agent Instructions](./docs/implementation-guides/AZURE_AI_FOUNDRY_AGENT_INSTRUCTIONS.md)** - Agent configuration details

### 🔧 [Troubleshooting Guides](./docs/troubleshooting-guides/)

Operational support for common issues:

- **[Provision and Deployment Issues](./docs/troubleshooting-guides/PROVISION_AND_DEPLOYMENT_TROUBLESHOOTING.md)** - Azure deployment troubleshooting

  - RBAC permission errors (`AuthorizationFailed`, `RoleAssignmentExists`)
  - Container App deployment problems
  - Bicep template compilation issues
  - Manual role assignment procedures

- **[Voice Live API Race Condition](./docs/troubleshooting-guides/VOICE_LIVE_API_RACE_CONDITION.md)** - **Status: ✅ RESOLVED**

  - Problem identification and root cause analysis
  - Professional logging for debugging
  - Solution A vs Solution B comparison
  - Implementation strategy and resolution

- **[Solution B Testing Guide](./docs/troubleshooting-guides/SOLUTION_B_TESTING_GUIDE.md)** - Validation and testing procedures

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

# Local debugging (Solution B)
python app_voice_live_agent_mode.py
```

## Next Steps

1. Push a custom container image (replace placeholder image in container app module).
2. Extend Azure AI Foundry agent capabilities with additional healthcare specializations.
3. Extend monitoring / dashboards for agent performance tracking.

## License

MIT
