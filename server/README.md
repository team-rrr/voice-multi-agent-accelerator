# Voice Multi-Agent Accelerator - Server

Enterprise voice-enabled multi-agent system using Azure AI Foundry for healthcare appointment preparation. This implementation eliminates race conditions by connecting directly to Azure AI Foundry agents through the Voice Live API.

## Features

- **Direct Azure AI Foundry Integration**: Connects to pre-configured agents eliminating race conditions
- **Real-time Voice Processing**: WebSocket-based bidirectional audio streaming with user transcription display
- **Voice-First Interface**: Streamlined interface focused on voice interaction
- **Enhanced Conversation Display**: Professional formatting with headers, bullet points, and structured responses
- **Secure Authentication**: Azure DefaultAzureCredential with API key fallback
- **Professional Logging**: Comprehensive conversation flow tracking
- **Healthcare Optimized**: Multi-agent orchestration for appointment preparation

## Architecture

```
Client WebSocket ←→ VoiceLiveAgentHandler ←→ Azure Voice Live API ←→ Azure AI Foundry Agent
```

**Key Benefits:**
- Single source of AI responses (no race conditions)
- Preserves multi-agent orchestration from Azure AI Foundry
- Real-time voice interaction with minimal latency

## Quick Start

### Prerequisites

- Python 3.12 or higher
- Azure subscription with AI services
- Azure CLI installed (`az login` for authentication)

### 1. Environment Setup

```bash
# Copy configuration template
cp .env.example .env

# Edit .env with your Azure resource details
# See .env.example for detailed instructions
```

### 2. Required Azure Resources

1. **Azure AI Foundry Project** with configured agents
2. **Azure AI Services** resource for Voice Live API
3. **Azure Speech Service** resource
4. **Azure Communication Services** resource

### 3. Install Dependencies

```bash
# Using pip
pip install -e .

# Or using uv (recommended)
uv pip install -e .
```

### 4. Run the Server

```bash
python app_voice_live_agent_mode.py
```

Server starts on `http://localhost:8000`

## Configuration

### ✅ Deployed Environment Variables

The infrastructure deployment has configured these environment variables:

| Variable | Value (Deployed) | Purpose |
|----------|------------------|---------|
| `AZURE_AI_FOUNDRY_ENDPOINT` | `https://aihub-dev-6uvq7.api.azureml.ms` | AI Foundry Hub endpoint |
| `AI_FOUNDRY_PROJECT_NAME` | `dev-project` | Azure AI Foundry project name |
| `AZURE_AI_ORCHESTRATOR_AGENT_ID` | `orchestrator-agent` | Orchestrator agent ID |
| `AZURE_AI_INFO_AGENT_ID` | `info-agent` | Info agent ID |
| `AZURE_AI_PATIENT_CONTEXT_AGENT_ID` | `patient-context-agent` | Patient context agent ID |
| `AZURE_AI_ACTION_AGENT_ID` | `action-agent` | Action agent ID |
| `AZURE_VOICE_LIVE_ENDPOINT` | Configured via Key Vault | Voice Live API endpoint |
| `AZURE_USER_ASSIGNED_IDENTITY_CLIENT_ID` | `4dbe675e-e044-4f6a-bc41-8cba2fc9a1b9` | Managed identity client ID |

### Additional Configuration Needed

After infrastructure deployment, you'll need to:

1. **Create actual agents in Azure AI Foundry Studio**
2. **Update agent IDs with real Azure AI Foundry agent IDs** 
3. **Configure agent prompts and instructions**

### Authentication Options

**Option 1 (Recommended): DefaultAzureCredential**
```bash
az login
# No additional configuration needed
```

**Option 2: API Key**
```bash
# Set in .env
AZURE_VOICE_LIVE_API_KEY=your-api-key
```

## API Endpoints

### WebSocket Endpoints

- `/ws/voice` - Primary voice interaction endpoint
- `/ws/text` - Text-only interaction (legacy)

### HTTP Endpoints  

- `/` - API information and status
- `/health` - Health check and configuration status
- `/api/query` - HTTP text query endpoint
- `/api/agents` - Agent configuration debug info

### Static Files

- `/static/voice_test.html` - Voice interaction test interface

## Testing

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Voice Interface
Navigate to `http://localhost:8000/static/voice_test.html`

**Interface Features:**

- Voice-first design with streamlined controls
- Real-time user speech transcription display
- Professional AI response formatting with headers and bullet points
- Structured appointment preparation checklists
- Enhanced conversation history with proper spacing

### 3. API Query

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, I need help with my appointment"}'
```

## Project Structure

```text
server/
├── app_voice_live_agent_mode.py          # Main FastAPI application
├── voice_live_agent_handler_agent_mode.py # Azure AI Foundry handler
├── logging_config.py                      # Professional logging setup
├── static/
│   ├── voice_test.html                   # Voice testing interface
│   └── audio-processor.js                # Client-side audio processing
├── .env.example                          # Configuration template
├── pyproject.toml                        # Python project configuration
└── requirements.txt                      # Dependencies
```

## Development

### Adding New Features

1. **Voice Processing**: Modify `voice_live_agent_handler_agent_mode.py`
2. **API Endpoints**: Add routes to `app_voice_live_agent_mode.py`  
3. **Frontend**: Update `static/voice_test.html` and `audio-processor.js`

### Logging

The system uses professional logging with conversation flow tracking:

```python
from logging_config import ConversationFlowLogger
flow_logger = ConversationFlowLogger(__name__)
flow_logger.conversation_start(session_id, "voice_websocket_agent_mode")
```

## Troubleshooting

### Common Issues

#### AI_FOUNDRY_AGENT_ID not configured

- Ensure environment variables are set in `.env`
- Check Azure AI Foundry project and agent configuration

#### Voice Live API connection failed

- Verify `AZURE_VOICE_LIVE_ENDPOINT` is correct
- Ensure authentication is working (`az login`)
- Check Azure AI Services resource permissions

#### No audio output

- Verify voice configuration in session config
- Check browser microphone permissions
- Test with `/health` endpoint

### Debug Mode

Enable debug logging:

```python
# In logging_config.py
setup_professional_logging(level="DEBUG")
```

## Resources

- [Azure AI Foundry Documentation](https://docs.microsoft.com/azure/ai-foundry/)
- [Voice Live API Reference](https://docs.microsoft.com/azure/ai-services/voice-live/)
- [Azure Communication Services](https://docs.microsoft.com/azure/communication-services/)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with proper documentation
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.