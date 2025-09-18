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
    
    # Step 2: Call PatientContextAgent to get patient data
    context_function = kernel.get_function("CaregiverPlugin", "PatientContextAgent")
    context_result = await kernel.invoke(context_function)
    context = str(context_result)
    
    # Step 3: Call ActionAgent to merge information into final response
    action_function = kernel.get_function("CaregiverPlugin", "ActionAgent")
    arguments = KernelArguments(checklist=checklist, context=context)
    result = await kernel.invoke(action_function, arguments)

    # For the demo, we'll manually create the card payload.
    # A more advanced version would have the ActionAgent return structured JSON.
    card_payload = {
        "title": "Cardiology Appointment Checklist",
        "items": [
            "Recent medical records",
            "Medication list (including supplements)",
            "Symptom log",
            "Family history",
            "Questions for the doctor"
        ],
        "context": "Recent diagnoses include hypertension and atrial fibrillation.",
        "links": [
            "https://www.ahrq.gov/sites/default/files/wysiwyg/health-literacy/my-medicines-list.pdf",
            "https://www.ahrq.gov/questions/question-builder/online.html"
        ]
    }

    return ChecklistResponse(spoken=str(result), card=card_payload)