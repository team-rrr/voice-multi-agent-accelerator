# Voice Live API Race Condition Troubleshooting Guide

## Overview

This document addresses the race condition issue that occurs when using the Azure Voice Live API with custom multi-agent orchestration. The problem manifests as competing AI responses and "conversation already has an active response" errors.

## Problem Description

### Symptoms
- Error messages: `"conversation already has an active response"`
- Dual AI responses in logs (local orchestrator + Voice Live default AI)
- Inconsistent speech synthesis and response delivery
- Conversation flow interruptions

### Root Cause
The Azure Voice Live API has a built-in conversational AI that responds to user input simultaneously with your custom orchestrator, creating a race condition where both systems attempt to generate responses.

## Detailed Analysis

### What's Happening
1. **User speaks**: Voice Live API transcribes the input
2. **Two AI systems activate simultaneously**:
   - Your local multi-agent orchestrator processes the input
   - Voice Live's default conversational AI also processes the input
3. **Race condition occurs**: Whichever AI responds first "locks" the conversation
4. **Second response fails**: The slower AI gets the "active response" error

### Log Evidence
```
[Timestamp] INFO     | orchestrator        | Orchestrator processing completed - Sending response to Voice Live API
[Timestamp] INFO     | voice_live_handler  | AI said: Sure! What specific areas would you like help with...
```

This shows both your orchestrator completing its work AND the default AI providing its own response.

## Solution Options

### Solution A: Empty Model Approach (Quick Fix)
**Status**: Attempted but caused speech synthesis issues

Modify the Voice Live connection to use an empty model name, forcing fallback to speech-only mode:
```python
# In voice_live_handler.py
"VOICE_LIVE_MODEL": os.getenv("VOICE_LIVE_MODEL", "")  # Empty string
```

**Issues Encountered**:
- Speech synthesis reliability problems
- Potential breaking changes if API behavior changes
- Not a guaranteed long-term solution

### Solution B: Azure AI Foundry Agent Mode (Recommended)
**Status**: Planned for implementation

Deploy the entire orchestration system as Azure AI agents, eliminating the dual-AI architecture entirely.

**Benefits**:
- Eliminates race condition at the source
- Production-ready architecture following Microsoft's intended patterns
- Better performance and reliability
- Centralized agent management and monitoring

## Implementation Strategy for Solution B

### Phase 1: Agent Deployment
1. **Deploy OrchestratorAgent**: Convert orchestrator.py logic to Azure AI agent
2. **Deploy Supporting Agents**: InfoAgent, PatientContextAgent, ActionAgent
3. **Configure Agent Communication**: Set up inter-agent communication flows

### Phase 2: Integration Update
1. **Update Voice Live Connection**: Connect directly to agent_id instead of model
2. **Migrate State Management**: Move conversation state to Azure agent context
3. **Preserve Logging**: Maintain professional logging through Azure AI Foundry

### Phase 3: Testing and Validation
1. **Test Multi-turn Conversations**: Ensure state persistence works correctly
2. **Validate Card Generation**: Confirm dynamic card creation functions
3. **Performance Testing**: Verify response times and reliability

## Current Workarounds

While planning the migration to Solution B:

1. **Monitor Logs**: Use the professional logging system to track race condition occurrences
2. **Graceful Degradation**: Handle "active response" errors gracefully in client code
3. **User Communication**: Inform users of potential response delays

## Success Metrics

The race condition will be considered resolved when:
- [ ] Zero "conversation already has an active response" errors
- [ ] Single AI response per user input
- [ ] Consistent speech synthesis delivery
- [ ] Reliable multi-turn conversation flow
- [ ] Stable card generation and delivery

## Professional Logging for Debugging

The application now includes comprehensive professional logging to help diagnose race condition issues:

### Server-side Logging
```
[HH:MM:SS.mmm] INFO     | orchestrator        | Intent classification completed - Flow: checklist_request
[HH:MM:SS.mmm] INFO     | voice_live_handler  | Speech detection started - Audio start: 1234 ms
[HH:MM:SS.mmm] INFO     | app_voice_live      | User message received - Session: abc123, Type: voice
```

### Client-side Logging
```javascript
[Conversation] User input received: { type: 'voice', content: '...', length: 45 }
[Conversation] Agent response: { spoken_length: 156, has_card: true }
[WebSocket] Message received: { type: 'ai_response', session: 'abc123' }
```

## Next Steps

1. **Research Azure AI Foundry Setup**: Understand agent deployment requirements
2. **Plan Migration Timeline**: Schedule the transition to Solution B
3. **Backup Current Implementation**: Ensure rollback capability during migration
4. **Test in Development Environment**: Validate Solution B before production deployment

## Related Documents

- [Provision and Deployment Troubleshooting](./PROVISION_AND_DEPLOYMENT_TROUBLESHOOTING.md)
- [Architecture Overview](../README.md#architecture)
- [Agent Documentation](./agent-prompts/)

---

**Document Version**: 1.0  
**Last Updated**: September 20, 2025  
**Status**: Race condition identified, Solution B planned for implementation