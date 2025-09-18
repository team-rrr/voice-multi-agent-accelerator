import os
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_arguments import KernelArguments
from pydantic import BaseModel

from plugins import CaregiverPlugin

# Define a Pydantic model for our structured response [cite: 483]
class ChecklistResponse(BaseModel):
    spoken: str
    card: dict

# Initialize the Semantic Kernel
kernel = sk.Kernel()

# Add the Azure OpenAI chat service from the environment variables set on Day 1
# Only initialize if environment variables are set
if all(key in os.environ for key in ["AZURE_OPENAI_DEPLOYMENT", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_KEY"]):
    kernel.add_service(
        AzureChatCompletion(
            service_id="chat-gpt",
            deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_KEY"],
        )
    )
else:
    # Print warning but allow the module to load for testing
    print("Warning: Azure OpenAI environment variables not set. Some functionality may be limited.")

# Import our plugin with the agent functions
kernel.add_plugin(CaregiverPlugin(), "CaregiverPlugin")

# Load the orchestrator prompt you wrote on Day 1
with open("../docs/agent-prompts/OrchestratorAgent.md", "r") as f:
    orchestrator_prompt_template = f.read()

async def run_orchestration(query: str) -> ChecklistResponse:
    """
    Runs the full multi-agent orchestration flow.
    Following the orchestrator pattern: InfoAgent -> PatientContextAgent -> ActionAgent
    """
    # Step 1: Call InfoAgent to get the baseline checklist
    info_function = kernel.get_function("CaregiverPlugin", "InfoAgent")
    checklist_result = await kernel.invoke(info_function)
    checklist = str(checklist_result)
    
    # Step 2: Call PatientContextAgent with user query for context-aware response
    context_function = kernel.get_function("CaregiverPlugin", "PatientContextAgent")
    context_arguments = KernelArguments(user_query=query)
    context_result = await kernel.invoke(context_function, context_arguments)
    context = str(context_result)
    
    # Step 3: Call ActionAgent to create contextual response based on user query
    action_function = kernel.get_function("CaregiverPlugin", "ActionAgent")
    arguments = KernelArguments(checklist=checklist, context=context, user_query=query)
    result = await kernel.invoke(action_function, arguments)

    # Create the card payload matching the UI structure
    card_payload = {
        "title": "Cardiology Appointment Checklist",
        "appointment_details": {
            "doctor": "Doctor mentioned in conversation",
            "reason": "Appointment reason from user input",
            "timing": "As mentioned by user"
        },
        "preparation_items": [
            "Bring current medications list",
            "Document chest pain episodes with dates and severity", 
            "Prepare questions about treatment options",
            "Bring insurance cards and ID",
            "List family history of heart conditions",
            "Recent medical records",
            "Symptom log"
        ],
        "questions_to_ask": [
            "What could be causing my chest pain?",
            "What tests do you recommend?",
            "Are there lifestyle changes I should make?",
            "When should I be concerned about symptoms?",
            "What are my treatment options?"
        ],
        "follow_up_actions": [
            "Schedule any recommended tests",
            "Follow medication instructions", 
            "Monitor symptoms as directed",
            "Keep symptom diary",
            "Follow up as scheduled"
        ]
    }

    return ChecklistResponse(spoken=str(result), card=card_payload)