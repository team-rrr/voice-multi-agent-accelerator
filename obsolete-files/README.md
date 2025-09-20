# Obsolete Files - Solution A Implementation

This directory contains files from the original **Solution A** implementation that were replaced during the migration to **Solution B (Azure AI Foundry Agent Mode)**.

## Why These Files Are Obsolete

The original implementation (Solution A) had a **race condition** between:
- Local multi-agent orchestration (Semantic Kernel)  
- Azure Voice Live API processing

**Solution B** eliminates this race condition by using **Azure AI Foundry native agents** instead of local orchestration.

## Files Moved Here

### **Original Server Implementation**
- `app_voice_live.py` - Original FastAPI server with local orchestration
- `voice_live_handler.py` - Original Voice Live handler with orchestration callback

### **Local Multi-Agent System** 
- `orchestrator.py` - Local multi-agent orchestration engine (Semantic Kernel)
- `plugins.py` - Local agent implementations (InfoAgent, PatientContextAgent, ActionAgent)

### **Experimental Implementation**
- `voice_live_agent_handler.py` - First attempt at Solution B (replaced by agent mode version)

## Current Active Files (Solution B)

The current working implementation uses:
- `app_voice_live_agent_mode.py` - Solution B FastAPI server
- `voice_live_agent_handler_agent_mode.py` - Azure AI Foundry integration
- Azure AI Foundry agents deployed in the cloud

## Migration Date

Files moved to obsolete-files: **September 20, 2025**

## Recovery Instructions

If you need to restore any of these files:

```bash
# Copy file back to server directory
cp obsolete-files/<filename> server/<filename>

# Or move permanently back
mv obsolete-files/<filename> server/<filename>
```

## References

- [Solution B Migration Strategy](../docs/implementation-guides/SOLUTION_B_MIGRATION_STRATEGY.md)
- [Voice Live API Race Condition](../docs/troubleshooting-guides/VOICE_LIVE_API_RACE_CONDITION.md)
- [Solution B Implementation Plan](../docs/implementation-guides/SOLUTION_B_IMPLEMENTATION_PLAN.md)