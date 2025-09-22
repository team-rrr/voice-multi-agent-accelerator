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

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AI_FOUNDRY_PROJECT_NAME` | Azure AI Foundry project name | `voice-multi-agent-project` |
| `AI_FOUNDRY_AGENT_ID` | Agent ID from Azure AI Foundry | `asst_abc123...` |
| `AZURE_VOICE_LIVE_ENDPOINT` | Voice Live API endpoint | `https://your-resource.cognitiveservices.azure.com` |
| `AZURE_SPEECH_KEY` | Speech service API key | `your-speech-key` |
| `AZURE_SPEECH_REGION` | Speech service region | `eastus2` |
| `ACS_CONNECTION_STRING` | Communication Services connection | `endpoint=https://...` |

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