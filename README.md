# Voice Multi-Agent Accelerator

Enterprise-grade voice interaction system with Azure AI Foundry multi-agent orchestration for healthcare appointment preparation. Features real-time voice processing, direct agent integration, and elimination of race conditions through cloud-native architecture.

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

Enterprise voice interaction system with comprehensive Azure AI Foundry integration:

**Core Capabilities:**
- Azure AI Foundry Agent Mode with cloud-native multi-agent orchestration
- Healthcare Caregiver Assistant powered by specialized Azure AI agents
- Real-time voice processing through Azure Voice Live API with direct agent connections
- Professional FastAPI WebSocket backend with enhanced error handling
- Structured appointment preparation checklist generation
- Dual interaction modes supporting both voice and text input
- Production-ready deployment on Azure Container Apps

**Technical Excellence:**
- Race condition elimination through direct Azure AI Foundry agent connections
- Professional conversation flow logging and monitoring
- Secure authentication using Azure DefaultAzureCredential
- Comprehensive session management and error recovery
- Premium neural voice synthesis (en-US-Ava:DragonHDLatestNeural)
- Voice-first interface design with enhanced conversation display
- Real-time user speech transcription and structured response formatting

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

### Local Development Setup

**Environment Configuration:**
```bash
# Navigate to server directory
cd server

# Create environment configuration from template
cp .env.example .env

# Configure Azure credentials in .env file
# See .env.example for detailed setup instructions
```

**Dependency Installation:**
```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# or: source .venv/bin/activate  # Linux/macOS

# Install application dependencies
pip install -e .
```

**Application Startup:**
```bash
# Start Azure AI Foundry Agent Mode server
python app_voice_live_agent_mode.py

# Server will be available at http://localhost:8000
# Voice interface accessible at http://localhost:8000/static/voice_test.html
```

**Authentication Setup:**
```bash
# Option 1: Azure CLI authentication (recommended)
az login

# Option 2: Configure API key in .env file
# Set AZURE_VOICE_LIVE_API_KEY in .env
```

### Testing Multi-Agent Voice Interaction

1. **Connect**: Click "Connect to Assistant" button
2. **Start Speaking**: Click "Start Speaking" to begin voice interaction
3. **Voice Input**: Say *"I have chest pain and need to prepare for my appointment with Doctor Smith"*
4. **View Transcription**: See your speech transcribed in the conversation history
5. **Hear AI Response**: Listen to complete orchestrated response with appointment guidance
6. **View Structured Response**: See properly formatted AI response with headers and bullet points
7. **Review Checklist**: View structured appointment preparation checklist in the card display

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
├── server/                              # Enterprise FastAPI Backend
│   ├── app_voice_live_agent_mode.py    # Main application server with comprehensive Azure AI Foundry integration
│   ├── voice_live_agent_handler_agent_mode.py # Professional agent handler with enhanced error handling
│   ├── logging_config.py               # Production-grade logging and conversation flow tracking
│   ├── static/                         # Professional web client interface
│   │   ├── voice_test.html             # Enhanced multi-agent UI with structured response display
│   │   └── audio-processor.js          # Optimized AudioWorklet processor for real-time audio
│   ├── .env.example                    # Comprehensive environment configuration template
│   ├── README.md                       # Detailed server documentation with setup guides
│   └── pyproject.toml                  # Python project configuration with complete dependencies
├── infra/                              # Azure infrastructure
│   ├── main.bicep                      # Main Bicep template
│   ├── main.parameters.json            # Deployment parameters
│   └── modules/                        # Bicep modules
├── docs/                               # Comprehensive documentation
│   ├── agent-prompts/                  # Agent system prompts for Azure AI Foundry
│   ├── implementation-guides/          # Strategic implementation documentation
│   │   ├── README.md                   # Implementation overview and status
│   │   ├── SOLUTION_B_MIGRATION_STRATEGY.md
│   │   ├── SOLUTION_B_IMPLEMENTATION_PLAN.md
│   │   └── AZURE_AI_FOUNDRY_AGENT_INSTRUCTIONS.md
│   ├── deployment/                     # Infrastructure deployment guides
│   │   ├── AZURE_INFRASTRUCTURE_DEPLOYMENT_GUIDE.md  # Complete azd deployment guide
│   │   └── DEPLOYMENT_STATUS_REPORT.md               # Current deployment status
│   ├── troubleshooting-guides/         # Operational support guides
│   │   ├── README.md                   # Troubleshooting overview
│   │   ├── PROVISION_AND_DEPLOYMENT_TROUBLESHOOTING.md  # Deployment issue resolution
│   │   ├── SOLUTION_B_TESTING_GUIDE.md
│   │   └── VOICE_LIVE_API_RACE_CONDITION.md
│   └── DOCUMENTATION_UPDATE_SUMMARY.md # Summary of all documentation updates
├── obsolete-files/                     # Archived Solution A files
│   ├── app_voice_live.py              # Original server (Semantic Kernel)
│   ├── voice_live_handler.py          # Original handler
│   ├── orchestrator.py                # Local orchestration engine
│   ├── plugins.py                     # Semantic Kernel agents
│   └── voice_live_agent_handler.py    # Original agent handler
└── azure.yaml                         # Azure Developer CLI config
```

## Core Components

### Azure AI Foundry Agent Integration Handler

**File: `voice_live_agent_handler_agent_mode.py`**

**Architecture Design:**
- Direct Azure AI Foundry agent connections using agent_id parameters
- Race condition elimination through single-source AI responses
- Comprehensive WebSocket management for bidirectional communication
- Azure DefaultAzureCredential authentication with API key fallback

**Audio Processing Capabilities:**
- Real-time PCM binary audio streaming at 24kHz sampling rate
- Premium neural voice synthesis using en-US-Ava:DragonHDLatestNeural
- Server-side voice activity detection with configurable thresholds
- Professional audio transcription using Whisper-1 model

**Session Management:**
- Automated session configuration for Azure AI Foundry agent mode
- Professional conversation flow logging and error tracking
- Graceful error handling and connection recovery
- Structured logging for production monitoring and debugging

### Azure AI Foundry Agents (Cloud-Deployed)

- **OrchestratorAgent** (`asst_bvYsNwZvM3jlJVEJ9kRzvc1Z`): Main coordination agent
- **InfoAgent** (`asst_IyzeNFdfP85EOtBFAqCDrsHh`): Extracts symptoms, medical history, lifestyle factors
- **PatientContextAgent** (`asst_h1I4NmJlQwOLKnOJGufsEuvp`): Analyzes appointment relevance and patient preparation needs
- **ActionAgent** (`asst_iFzbrJduLjccC42HVuFlGmYz`): Generates personalized appointment preparation checklists
- **Native Azure Orchestration**: Agent-to-agent communication handled by Azure AI Foundry

### FastAPI Application Server

**File: `app_voice_live_agent_mode.py`**

**WebSocket Endpoints:**
- `/ws/voice` - Primary real-time voice communication with Azure AI Foundry agents
- `/ws/text` - Legacy text-based interaction endpoint for testing

**HTTP API Endpoints:**
- `/api/query` - Direct agent query interface with structured responses
- `/health` - Comprehensive health check with configuration validation
- `/api/agents` - Agent configuration and status debugging interface

**Application Features:**
- Professional FastAPI application with comprehensive metadata
- Enhanced WebSocket message handling with proper error recovery
- Structured session management with unique identifier tracking
- Professional conversation flow logging for production monitoring
- Static file serving for professional web interface

### Professional Web Client (`voice_test.html` + `audio-processor.js`)

- **Voice-First Interface**: Streamlined voice interaction with simplified controls
- **Card Display System**: Structured appointment preparation checklists with enhanced formatting
- **Real-Time Transcription Display**: User speech and AI responses shown in conversation history
- **Enhanced Conversation Formatting**: Professional headers, bullet points, bold text with proper spacing
- **AudioWorklet Processing**: Smooth real-time audio playback with optimized streaming
- **Professional UI Design**: Fluent UI inspired styling with responsive voice-focused layout

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

### Local Testing and Validation

**Application Startup:**

```bash
# Navigate to server directory
cd server

# Start Azure AI Foundry Agent Mode server
python app_voice_live_agent_mode.py
# Server initializes on http://localhost:8000
```

**Health Verification:**

```bash
# Verify server health and configuration
curl http://localhost:8000/health

# Test API query endpoint
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"text": "I need help preparing for my appointment"}'
```

**Voice Interface Testing:**

```bash
# Access professional voice interface
# Navigate to: http://localhost:8000/static/voice_test.html
# Test real-time voice interaction with Azure AI Foundry agents
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

### COMPLETED: Azure AI Foundry Agent Mode Implementation

**Architecture Excellence:**

- Azure AI Foundry Integration: Cloud-native multi-agent orchestration with production-grade reliability
- Race Condition Resolution: Direct agent connections eliminate competing AI responses
- Production Agent Deployment: All healthcare agents operational in Azure AI Foundry with verified agent IDs
- Voice Processing Integration: Real-time Azure Voice Live API with optimized agent mode connections
- Enterprise Logging: Professional conversation flow tracking and structured debugging capabilities

**Code Quality Improvements:**

- Comprehensive documentation with professional-grade comments throughout codebase
- Enhanced error handling and graceful connection recovery mechanisms
- Improved session management with proper cleanup and resource management
- Professional FastAPI application structure with comprehensive endpoint documentation
- Refined Azure AI Foundry agent handler with detailed architecture documentation

### ✅ COMPLETED: Healthcare Agent System

- **OrchestratorAgent** (`asst_bvYsNwZvM3jlJVEJ9kRzvc1Z`) - Main coordination agent
- **InfoAgent** (`asst_IyzeNFdfP85EOtBFAqCDrsHh`) - Symptom and medical history extraction
- **PatientContextAgent** (`asst_h1I4NmJlQwOLKnOJGufsEuvp`) - Appointment relevance analysis  
- **ActionAgent** (`asst_iFzbrJduLjccC42HVuFlGmYz`) - Personalized preparation checklist generation
- **Native Azure Orchestration** - Agent-to-agent coordination handled by Azure AI Foundry

### ✅ COMPLETED: Full Azure Infrastructure Deployment

**Successfully Deployed Resources (September 2025):**
- ✅ **Azure AI Foundry Hub**: `aihub-dev-6uvq7` - Multi-agent orchestration platform
- ✅ **Container Apps Environment**: `cae-dev-6uvq7` - Serverless application hosting  
- ✅ **Container App**: `ca-dev-6uvq7` - FastAPI application running
- ✅ **Azure AI Services**: `aiServices-dev-6uvq7` - Voice Live API integration
- ✅ **Azure OpenAI**: `oai-dev-6uvq7` - GPT-4o-mini model deployed
- ✅ **Container Registry**: `acrrgdev6uvq7` - Docker images stored
- ✅ **Key Vault**: `kvcvoice6uvq7` - Secure secret management
- ✅ **Storage Account**: `staihubdev6uvq7` - AI Hub storage
- ✅ **Managed Identity**: Secure service authentication configured
- ✅ **Monitoring**: Application Insights and Log Analytics operational

**Infrastructure Validation:**
```powershell
# Verify deployment
azd show
# ✅ All resources operational
# ✅ Service endpoints accessible  
# ✅ Environment variables configured
```

**Ready for Agent Configuration:**
The infrastructure is now fully deployed and ready for Azure AI Foundry agent deployment phase.

### System Verification Checklist

**Server Initialization:**
- Execute `python app_voice_live_agent_mode.py` for Azure AI Foundry Agent Mode startup
- Verify health endpoint at `http://localhost:8000/health` shows all configurations as valid

**Voice Interface Validation:**
- Access professional web interface at `http://localhost:8000/static/voice_test.html`
- Confirm successful WebSocket connection and Azure AI Foundry agent initialization

**End-to-End Voice Testing:**
- Initiate voice interaction with healthcare query: "I have chest pain and need to prepare for my appointment"
- Validate real-time voice transcription and multi-agent response coordination
- Confirm audio synthesis and playback through premium neural voice (en-US-Ava:DragonHDLatestNeural)
- Review structured appointment preparation checklist generation

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

### ✅ Successfully Deployed Infrastructure

The infrastructure has been **successfully deployed** using `azd up` with the following components:

**Core Resources Created:**
- **Resource Group**: `rg-dev-6uvq7`
- **Azure AI Foundry Hub**: `aihub-dev-6uvq7` 
- **Container App**: `ca-dev-6uvq7.lemondune-86508fd9.eastus2.azurecontainerapps.io`
- **Azure AI Services**: `aiServices-dev-6uvq7`
- **Container Registry**: `acrrgdev6uvq7.azurecr.io`
- **Key Vault**: `kvcvoice6uvq7`

### Prerequisites for Fresh Deployment:

1. Install Azure CLI (<https://learn.microsoft.com/cli/azure/install-azure-cli>)
2. Install Azure Developer CLI (<https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd>)
3. Login:

```pwsh
az login
azd auth login
```

### Deploy Complete Infrastructure:

```pwsh
# Deploy everything (infrastructure + application)
azd up

# Or provision infrastructure only
azd provision

# Or deploy application only (after provision)
azd deploy
```

### Verify Deployment:

```pwsh
# Check deployment status
azd show

# Get all environment variables
azd env get-values

# Test the deployed application
curl https://ca-dev-6uvq7.lemondune-86508fd9.eastus2.azurecontainerapps.io/health
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

The repository includes comprehensive documentation organized into logical categories for enterprise deployment and maintenance:

### Implementation Guides

Strategic documentation for understanding and implementing Solution B:

- **[Solution B Migration Strategy](./docs/implementation-guides/SOLUTION_B_MIGRATION_STRATEGY.md)** - Complete migration approach and planning
- **[Solution B Implementation Plan](./docs/implementation-guides/SOLUTION_B_IMPLEMENTATION_PLAN.md)** - Step-by-step implementation checklist
- **[Azure AI Foundry Agent Instructions](./docs/implementation-guides/AZURE_AI_FOUNDRY_AGENT_INSTRUCTIONS.md)** - Agent configuration details

### Troubleshooting Guides

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
