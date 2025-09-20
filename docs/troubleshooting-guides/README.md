# Troubleshooting Guides

This directory contains practical troubleshooting guides and testing procedures for the Voice Multi-Agent Accelerator using **Solution B (Azure AI Foundry Agent Mode)**.

## 📋 **Available Guides**

### **🔧 Infrastructure & Deployment**
- **[Provision and Deployment Troubleshooting](PROVISION_AND_DEPLOYMENT_TROUBLESHOOTING.md)**
  - Azure infrastructure provisioning issues
  - Role assignment and permission problems
  - Container registry and deployment errors
  - `azd provision` and `azd deploy` troubleshooting

### **🧪 Testing & Validation**
- **[Solution B Testing Guide](SOLUTION_B_TESTING_GUIDE.md)**
  - Step-by-step testing procedures for Azure AI Foundry Agent Mode
  - WebSocket connection validation
  - Voice interaction testing
  - Race condition elimination verification

### **⚠️ Technical Issues**
- **[Voice Live API Race Condition](VOICE_LIVE_API_RACE_CONDITION.md)**
  - Understanding the race condition problem
  - Why Solution A failed and Solution B succeeds
  - Technical diagnosis and resolution steps

## 🎯 **Quick Start Troubleshooting**

### **Common Issues**

1. **Server Won't Start**
   - Check [Testing Guide](SOLUTION_B_TESTING_GUIDE.md#step-1-test-solution-b-implementation)
   - Verify environment variables are set correctly

2. **WebSocket Connection Fails**
   - See [Testing Guide](SOLUTION_B_TESTING_GUIDE.md#step-2-test-websocket-connection)
   - Check Azure AI Foundry configuration

3. **Infrastructure Deployment Fails**
   - Follow [Deployment Troubleshooting](PROVISION_AND_DEPLOYMENT_TROUBLESHOOTING.md)
   - Check Azure permissions and role assignments

4. **Race Condition Errors**
   - Review [Race Condition Guide](VOICE_LIVE_API_RACE_CONDITION.md)
   - Ensure using Solution B implementation

## 🔍 **Getting Help**

1. **Check the specific troubleshooting guide** for your issue type
2. **Review the logs** mentioned in each guide
3. **Verify your configuration** against the examples provided
4. **Test systematically** using the step-by-step procedures

## 📚 **Related Documentation**

For implementation and planning documents, see the [implementation-guides](../implementation-guides/) directory:
- [Solution B Implementation Plan](../implementation-guides/SOLUTION_B_IMPLEMENTATION_PLAN.md)
- [Solution B Migration Strategy](../implementation-guides/SOLUTION_B_MIGRATION_STRATEGY.md)
- [Azure AI Foundry Agent Instructions](../implementation-guides/AZURE_AI_FOUNDRY_AGENT_INSTRUCTIONS.md)