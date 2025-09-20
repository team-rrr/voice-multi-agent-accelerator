# Solution B Migration Strategy: Azure AI Foundry Agent Mode

## Overview

This document outlines the complete migration strategy to eliminate the Voice Live API race condition by deploying the multi-agent orchestration system to Azure AI Foundry. This approach replaces the dual-AI architecture with a single, centralized agent system.

## Migration Objectives

### Primary Goal
Eliminate the race condition where Voice Live API's default AI competes with our custom orchestrator by deploying all intelligence to Azure AI Foundry.

### Success Criteria
- Zero "conversation already has an active response" errors
- Single AI response per user input
- Reliable speech synthesis and card delivery
- Maintained conversation state and multi-turn capabilities
- Preserved professional logging and debugging capabilities

## Current vs Target Architecture

### Current Architecture (Local Orchestration)
```
User Voice → Voice Live API → Local FastAPI Server
                ↓
            Multi-Agent Orchestrator (local)
                ├── InfoAgent
                ├── PatientContextAgent  
                ├── ActionAgent
                └── Response Formation
                ↓
            Voice Live API (TTS) → User
            
PROBLEM: Voice Live's default AI also responds simultaneously
```

### Target Architecture (Azure AI Foundry Agent Mode)
```
User Voice → Voice Live API (connected to agent_id)
                ↓
            Azure AI Foundry Agent System
                ├── OrchestratorAgent (main)
                ├── InfoAgent
                ├── PatientContextAgent
                ├── ActionAgent
                └── Response Formation
                ↓
            Voice Live API (TTS) → User
            
SOLUTION: Single AI system, no race condition
```

## Pre-Migration Analysis

### Code Assets to Migrate

1. **Orchestrator Logic** (`orchestrator.py`)
   - Intent classification system
   - Conversation state management
   - Agent coordination logic
   - Response formation and card generation

2. **Agent Implementations** (`plugins.py`)
   - InfoAgent: Symptom and medical history extraction
   - PatientContextAgent: Appointment relevance analysis
   - ActionAgent: Checklist generation logic

3. **Supporting Systems**
   - Professional logging configuration
   - Conversation state tracking
   - Dynamic card generation logic
   - Multi-turn conversation handling

### Dependencies to Address

- **Semantic Kernel**: Verify Azure AI Foundry compatibility with current SK version
- **Pydantic Models**: Convert to Azure AI Foundry schema format
- **Environment Variables**: Migrate to Azure AI Foundry configuration
- **Conversation State**: Implement in Azure agent context

## Migration Strategy: 3-Phase Approach

## Phase 1: Azure AI Foundry Setup & Agent Development

### Step 1.1: Environment Preparation

**Azure Resources Required:**
- Azure AI Foundry workspace
- Azure AI project 
- Connected Azure OpenAI service
- Agent deployment endpoints

**Setup Commands:**
```bash
# Create AI Foundry workspace (if not exists)
az ml workspace create --name voice-agents-workspace --resource-group $RG_NAME

# Create AI project
az ml project create --name voice-multi-agent-project --workspace voice-agents-workspace

# Connect OpenAI service
az ml connection create --name openai-connection --type azure_open_ai \
  --target $AZURE_OPENAI_ENDPOINT --auth-mode key
```

### Step 1.2: Agent Development Strategy

**Agent Conversion Priority:**
1. **InfoAgent** → Azure AI agent (independent, no dependencies)
2. **PatientContextAgent** → Azure AI agent (depends on InfoAgent output)
3. **ActionAgent** → Azure AI agent (depends on both previous agents)  
4. **OrchestratorAgent** → Main Azure AI agent (coordinates all others)

### Step 1.3: Agent Implementation Approach

**Convert Semantic Kernel Functions to Azure AI Agents:**

```python
# Current: Semantic Kernel function
@kernel_function(name="InfoAgent", description="Gathers patient symptoms")
def info_agent(self, user_query: str) -> str:
    # Implementation logic

# Target: Azure AI Foundry agent configuration
{
  "name": "InfoAgent",
  "description": "Gathers patient symptoms and medical history",
  "instructions": "You are a medical information gathering agent...",
  "model": "gpt-4o-mini",
  "functions": [...],
  "file_ids": [...]
}
```

## Phase 2: Agent Deployment & Testing

### Step 2.1: Individual Agent Deployment

**InfoAgent Deployment:**
```bash
# Deploy InfoAgent with system prompt from docs/agent-prompts/InfoAgent.md
az ml agent create --name InfoAgent --file agents/info-agent.yaml
```

**Agent Configuration Template:**
```yaml
# agents/info-agent.yaml
name: InfoAgent
description: Gathers patient symptoms and medical history
instructions: |
  You are a specialized medical information gathering agent focused on healthcare appointment preparation.
  
  Your role is to extract and analyze:
  - Current symptoms and their characteristics
  - Medical history and previous diagnoses
  - Current medications and treatments
  - Lifestyle factors relevant to the appointment
  
  Always maintain a professional, empathetic tone while gathering comprehensive information.
model: gpt-4o-mini
temperature: 0.3
functions:
  - type: "function"
    function:
      name: "extract_symptoms"
      description: "Extract symptom information from user input"
      parameters:
        type: "object"
        properties:
          user_input:
            type: "string"
            description: "Raw user query about their symptoms"
```

### Step 2.2: Agent Chain Testing

**Standalone Agent Testing:**
```python
# Test script for individual agent validation
import azure.ai.projects as ai_projects

client = ai_projects.AIProjectClient.from_connection_string(CONNECTION_STRING)

# Test InfoAgent
info_response = client.agents.create_message(
    agent_id="InfoAgent",
    content="I have chest pain and shortness of breath"
)

# Validate response structure and content quality
assert "symptoms" in info_response.content.lower()
assert len(info_response.content) > 50  # Sufficient detail
```

### Step 2.3: Orchestrator Agent Development

**Main Orchestrator Logic:**
```yaml
# agents/orchestrator-agent.yaml
name: VoiceMultiAgentOrchestrator
description: Main orchestrator for healthcare appointment preparation
instructions: |
  You coordinate a team of healthcare agents to provide comprehensive appointment preparation.
  
  Your workflow:
  1. Analyze user input to determine intent
  2. Route to appropriate agent(s) based on query type
  3. Coordinate sequential agent execution when needed
  4. Format final response combining spoken content + structured card data
  
  Agent chain: InfoAgent → PatientContextAgent → ActionAgent → Response Formation
functions:
  - type: "function" 
    function:
      name: "coordinate_agents"
      description: "Coordinate multi-agent workflow"
  - type: "function"
    function:
      name: "format_response"
      description: "Format final response with spoken + card data"
```

## Phase 3: Voice Live Integration & Migration

### Step 3.1: Update Voice Live Handler

**Current Connection (Model-based):**
```python
# voice_live_handler.py - Current approach
url = f"wss://eastus2.api.speech.microsoft.com/cognitiveservices/websocket/v2?model={self.model}"
```

**Target Connection (Agent-based):**
```python
# voice_live_handler.py - Agent mode
url = f"wss://eastus2.api.speech.microsoft.com/cognitiveservices/websocket/v2?agent_id={self.agent_id}"

class VoiceLiveHandler:
    def __init__(self, agent_id: str, api_key: str):
        self.agent_id = agent_id  # Main orchestrator agent ID
        self.api_key = api_key
        # Remove orchestration_callback - no longer needed
```

### Step 3.2: Remove Local Orchestration

**Files to Modify/Remove:**
- **Keep**: `orchestrator.py` (for reference during migration)
- **Modify**: `voice_live_handler.py` (remove orchestration callback)
- **Modify**: `app_voice_live.py` (remove orchestration import and callback)
- **Archive**: `plugins.py` (logic now in Azure agents)

**Updated FastAPI Server:**
```python
# app_voice_live.py - Simplified for agent mode
from voice_live_handler import VoiceLiveHandler

# Remove orchestration callback
handler = VoiceLiveHandler(
    agent_id=os.getenv("AZURE_AI_AGENT_ID"),  # Main orchestrator agent
    api_key=os.getenv("AZURE_SPEECH_KEY")
    # No orchestration_callback parameter
)
```

### Step 3.3: Environment Configuration Update

**New Environment Variables:**
```bash
# Add to .env
AZURE_AI_FOUNDRY_ENDPOINT=https://your-workspace.cognitiveservices.azure.com/
AZURE_AI_PROJECT_ID=your-project-id
AZURE_AI_AGENT_ID=VoiceMultiAgentOrchestrator  # Main orchestrator agent
AZURE_AI_CONNECTION_STRING=your-connection-string

# Keep existing
AZURE_SPEECH_KEY=your-speech-key
AZURE_SPEECH_REGION=your-region

# Remove (no longer needed)
# AZURE_OPENAI_API_KEY - Now handled by AI Foundry
# AZURE_OPENAI_ENDPOINT - Now handled by AI Foundry
# AZURE_OPENAI_DEPLOYMENT - Now handled by AI Foundry
```

## Data Migration & State Preservation

### Conversation State Migration

**Current State Management:**
```python
# orchestrator.py - Local session state
session_states = {}  # In-memory state per session

class ConversationState:
    def __init__(self):
        self.phase = "idle"
        self.previous_queries = []
        self.patient_info = {}
        # ... other state
```

**Azure AI Foundry State Management:**
```python
# Agent context-based state management
{
  "conversation_context": {
    "session_id": "abc123",
    "phase": "gathering_info", 
    "previous_queries": [...],
    "patient_info": {...},
    "completion_signals": 1
  }
}
```

### Professional Logging Preservation

**Maintain Logging Architecture:**
- Keep `logging_config.py` for client-side logging
- Add Azure AI Foundry agent logging integration
- Preserve conversation flow debugging capabilities

**Enhanced Logging for Agent Mode:**
```python
# Enhanced logging for Azure agent calls
flow_logger.agent_processing(session_id, "AzureAIFoundry", "agent_chain_started")
flow_logger.agent_response(session_id, "InfoAgent", response_length, has_card=False)
flow_logger.agent_response(session_id, "OrchestratorAgent", response_length, has_card=True)
```

## Testing & Validation Strategy

### Phase 1 Testing: Agent Functionality

**Individual Agent Tests:**
```python
# Test each agent independently
test_cases = [
    {
        "agent": "InfoAgent",
        "input": "I have chest pain and need to see my cardiologist",
        "expected_output_contains": ["chest pain", "symptoms", "medical history"]
    },
    {
        "agent": "PatientContextAgent", 
        "input": "Cardiology appointment for chest pain",
        "expected_output_contains": ["appointment preparation", "cardiology", "relevant"]
    },
    {
        "agent": "ActionAgent",
        "input": "Need checklist for cardiology appointment",
        "expected_output_contains": ["checklist", "bring", "questions"]
    }
]
```

### Phase 2 Testing: Integration

**Agent Chain Workflow Tests:**
```python
# Test complete agent orchestration
integration_tests = [
    {
        "scenario": "New cardiology appointment",
        "user_input": "I have chest pain and see Dr. Smith tomorrow",
        "expected_flow": ["InfoAgent", "PatientContextAgent", "ActionAgent"],
        "expected_output": {
            "spoken_response": "string with guidance",
            "card_data": {"title": "Cardiology Appointment Preparation", ...}
        }
    }
]
```

### Phase 3 Testing: Voice Integration

**End-to-End Voice Tests:**
1. **Voice Input Processing**: Verify speech-to-text accuracy
2. **Agent Chain Execution**: Confirm proper agent coordination
3. **Response Synthesis**: Validate TTS output quality
4. **Card Delivery**: Test structured data delivery
5. **Multi-turn Conversations**: Verify state persistence

## Risk Mitigation

### Rollback Strategy

**Preparation:**
1. Tag current working version: `git tag v1.0-local-orchestration`
2. Create rollback branch: `git checkout -b rollback-ready`
3. Document current environment configuration
4. Backup current `.env` configuration

**Rollback Procedure (if needed):**
```bash
git checkout rollback-ready
# Restore original voice_live_handler.py with orchestration callback
# Restore original app_voice_live.py with local orchestration
# Restore original .env configuration
```

### Parallel Testing Approach

**Development Strategy:**
1. **Maintain current system** while building Azure agents
2. **Create feature branch** for agent migration: `feature/azure-ai-foundry-migration`
3. **Test agents independently** before integration
4. **A/B testing** between local and Azure orchestration
5. **Gradual cutover** once Azure agents are validated

## Timeline & Milestones

### Week 1: Azure AI Foundry Setup & Agent Development
- **Day 1-2**: Azure AI Foundry workspace and project setup
- **Day 3-4**: Convert InfoAgent to Azure AI agent
- **Day 5-7**: Convert PatientContextAgent and ActionAgent

### Week 2: Orchestrator Development & Testing
- **Day 1-3**: Develop main OrchestratorAgent
- **Day 4-5**: Implement agent chain coordination
- **Day 6-7**: Test complete agent workflow independently

### Week 3: Integration & Voice Live Connection
- **Day 1-2**: Update voice_live_handler.py for agent mode
- **Day 3-4**: Modify FastAPI server and environment configuration
- **Day 5-7**: End-to-end testing and validation

### Week 4: Production Deployment & Monitoring
- **Day 1-2**: Deploy to Azure Container Apps with new configuration
- **Day 3-4**: Monitor performance and resolve any issues
- **Day 5-7**: Documentation update and team training

## Success Metrics & Monitoring

### Technical Metrics
- **Zero race condition errors**: No "conversation already has an active response"
- **Response consistency**: Single AI response per user input
- **Performance**: Response time ≤ current system performance
- **Reliability**: 99%+ successful conversation completions

### Functional Metrics  
- **Multi-turn conversations**: State preserved across conversation turns
- **Card generation**: Dynamic cards generated correctly
- **Voice quality**: TTS synthesis quality maintained
- **Professional logging**: Debug visibility preserved

### Monitoring Setup
```python
# Enhanced monitoring for Azure AI Foundry integration
azure_monitor_config = {
    "agent_performance_tracking": True,
    "conversation_flow_logging": True, 
    "error_rate_alerting": True,
    "response_time_monitoring": True
}
```

## Next Steps

1. **Review and Approve Strategy**: Validate approach with team
2. **Azure AI Foundry Access**: Ensure proper subscriptions and permissions
3. **Development Environment**: Set up dedicated branch for migration work
4. **Agent Development**: Begin with InfoAgent conversion
5. **Testing Framework**: Establish automated testing for agents

This migration strategy provides a comprehensive path to eliminate the race condition while preserving all current functionality and improving the overall architecture for long-term maintainability.

---

**Document Version**: 1.0  
**Last Updated**: September 20, 2025  
**Status**: Migration strategy ready for implementation