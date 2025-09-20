# Solution B Testing Guide: Azure AI Foundry Agent Mode

## Testing Overview

You now have a complete Solution B implementation that eliminates the race condition by using Azure AI Foundry agents instead of local orchestration. Here's how to test and deploy it.

## Phase 3 Testing Steps

### Step 1: Test Solution B Implementation

**Start the new Solution B server:**
```bash
cd server
python app_voice_live_agent_mode.py
```

**Expected output:**
```
INFO: Voice Multi-Agent Assistant - Azure AI Foundry Mode
INFO: VoiceLiveAgentHandler initialized with Azure AI Foundry Agent: asst_bvYsNwZvM3jlJVEJ9kRzvc1Z
INFO: Application startup complete
```

### Step 2: Verify Agent Mode Connection

**Test health endpoint:**
```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "mode": "azure_ai_foundry_agent",
  "race_condition_status": "eliminated_by_agent_mode",
  "orchestrator_agent": "asst_bvYsNwZvM3jlJVEJ9kRzvc1Z",
  "agent_id_configured": true
}
```

### Step 3: Test Voice WebSocket Connection

**Open browser to:** `http://localhost:8000/static/voice_test.html`

**Expected behavior:**
1. ✅ "Voice Multi-Agent Assistant is ready! (Azure AI Foundry Agent Mode - Race condition eliminated)"
2. ✅ Speech detection works
3. ✅ Single AI response per input (no race condition)
4. ✅ Professional logging shows "Azure AI Foundry" processing

### Step 4: Monitor for Race Condition Elimination

**Watch logs for these SUCCESS indicators:**
- ✅ `Voice Live Agent Mode session created`
- ✅ `Azure AI agents will process` (instead of local orchestration)
- ✅ `Azure AI Foundry response completed`
- ❌ NO "conversation already has an active response" errors

**Watch logs for these FAILURE indicators:**
- ❌ "conversation already has an active response" (race condition still exists)
- ❌ Multiple AI responses to single input
- ❌ Connection errors with agent_id

## Comparison Testing

### ⚠️ Note: Solution A Files Moved to `obsolete-files/`

The original Solution A files have been moved to the `obsolete-files/` directory to keep the repository clean:
- `obsolete-files/app_voice_live.py` - Original server with race condition
- `obsolete-files/orchestrator.py` - Local orchestration engine  
- `obsolete-files/plugins.py` - Local agent implementations

### Test Solution B (Agent Mode - Race Condition Eliminated)
```bash  
# Start Solution B server (current implementation)
python app_voice_live_agent_mode.py
```
- **Expected**: Single AI response, no race condition errors, Azure AI Foundry integration

### To Test Original Solution A (For Comparison):
```bash
# Temporarily restore original server if needed
cp obsolete-files/app_voice_live.py server/app_voice_live.py
cp obsolete-files/orchestrator.py server/orchestrator.py  
cp obsolete-files/plugins.py server/plugins.py
python app_voice_live.py
```
- **Expected**: Race condition errors, dual AI responses (this demonstrates why Solution B was needed)

## Environment Validation

### Verify All Required Variables Are Set:
```bash
# Check Azure AI Foundry configuration
echo $AZURE_AI_FOUNDRY_ENDPOINT
echo $AZURE_AI_FOUNDRY_API_KEY  
echo $VOICE_LIVE_AGENT_ID

# Check agent IDs
echo $AZURE_AI_ORCHESTRATOR_AGENT_ID
echo $AZURE_AI_INFO_AGENT_ID
echo $AZURE_AI_PATIENT_CONTEXT_AGENT_ID
echo $AZURE_AI_ACTION_AGENT_ID
```

**All should return values, not empty or "not_configured"**

## Troubleshooting

### Issue: "Agent ID not configured" error
**Fix:** Verify `VOICE_LIVE_AGENT_ID` is set to your orchestrator agent:
```bash
VOICE_LIVE_AGENT_ID="asst_bvYsNwZvM3jlJVEJ9kRzvc1Z"
```

### Issue: Connection failed to Voice Live API
**Fix:** Check agent_id parameter in URL:
- ✅ Correct: `?agent_id=asst_bvYsNwZvM3jlJVEJ9kRzvc1Z`
- ❌ Wrong: `?model=gpt-4o-mini` (this causes race condition)

### Issue: Azure AI Foundry agents not responding
**Fix:** Verify agents are deployed and accessible:
1. Check Azure AI Foundry portal
2. Test individual agents
3. Verify API key permissions

## Production Deployment

### Step 1: Update Azure Container App Environment
```bash
# Set environment variables in Azure Container App
az containerapp update \
  --name your-container-app \
  --resource-group your-rg \
  --set-env-vars \
    AZURE_AI_FOUNDRY_ENDPOINT="https://your-ai-foundry-resource.cognitiveservices.azure.com/" \
    AZURE_AI_FOUNDRY_API_KEY="your-azure-ai-foundry-api-key" \
    VOICE_LIVE_AGENT_ID="asst_bvYsNwZvM3jlJVEJ9kRzvc1Z"
```

### Step 2: Update Startup Command
Change container startup command from:
```bash
# OLD (Solution A)
python app_voice_live.py
```

To:
```bash  
# NEW (Solution B)
python app_voice_live_agent_mode.py
```

## Success Criteria

### ✅ Solution B Successfully Implemented When:
1. **Zero race condition errors** - No "conversation already has an active response"
2. **Single AI response** per user input
3. **Azure AI Foundry logging** appears in console
4. **Voice synthesis works** without conflicts
5. **Professional logging** shows agent mode processing

### ❌ Issues to Address:
1. **Race condition persists** - Check agent_id vs model parameter
2. **No agent response** - Verify Azure AI Foundry agent deployment
3. **Connection errors** - Check API keys and endpoints
4. **Multiple responses** - Confirm not using both systems simultaneously

## Next Steps After Successful Testing

1. **Deploy to production** with Solution B configuration
2. **Monitor for 24-48 hours** to confirm race condition elimination
3. **Remove local orchestration code** (orchestrator.py, plugins.py) if stable
4. **Update documentation** to reflect Azure AI Foundry architecture
5. **Train team** on new agent-based debugging and monitoring

## Rollback Plan (If Needed)

If Solution B has issues, you can restore the original Solution A files:

```bash
# Restore Solution A files from obsolete-files
cp obsolete-files/app_voice_live.py server/app_voice_live.py
cp obsolete-files/orchestrator.py server/orchestrator.py
cp obsolete-files/plugins.py server/plugins.py
cp obsolete-files/voice_live_handler.py server/voice_live_handler.py

# Start original server
python app_voice_live.py

# Restore original environment variables
VOICE_LIVE_MODEL="gpt-4o-mini"  # Instead of VOICE_LIVE_AGENT_ID
```

**Note:** Remember that Solution A has the race condition issue, so this should only be temporary.

This testing guide ensures you can validate that Solution B successfully eliminates the race condition while maintaining all functionality.