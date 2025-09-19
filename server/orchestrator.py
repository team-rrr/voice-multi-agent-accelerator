# Orchestrator for multi-agent voice accelerator
import os
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_arguments import KernelArguments
from pydantic import BaseModel

# from plugins import CaregiverPlugin, list_agents, AGENT_PROMPTS_DIR, load_agent_prompt
from plugins.CaregiverPlugin import CaregiverPlugin
# from plugins.utils import list_agent_prompts, list_tool_prompts
from plugins.CardiologyAgent import CardiologyAgent
from plugins.family_history_agent import FamilyHistoryAgent

class ChecklistResponse(BaseModel):
    spoken: str
    card: dict

kernel = sk.Kernel()

if all(key in os.environ for key in ["AZURE_OPENAI_DEPLOYMENT", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_KEY"]):
    kernel.add_service(
        AzureChatCompletion(
            service_id="chat-gpt",
            deployment_name=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_KEY"]
        )
    )
else:
    print("Warning: Azure OpenAI environment variables not set. Some functionality may be limited.")

kernel.add_plugin(CaregiverPlugin(), "CaregiverPlugin")
kernel.add_plugin(CardiologyAgent(), "CardiologyAgent")
kernel.add_plugin(FamilyHistoryAgent(), "FamilyHistoryAgent")

with open(os.path.join(os.path.dirname(__file__), "agent_prompts", "OrchestratorAgent.md"), "r") as f:
    orchestrator_prompt_template = f.read()

async def run_orchestration(query: str) -> ChecklistResponse:
    """
    Runs the full multi-agent orchestration flow.
    Following the orchestrator pattern: InfoAgent -> PatientContextAgent -> ActionAgent
    """
    info_function = kernel.get_function("CaregiverPlugin", "InfoAgent")
    checklist_result = await kernel.invoke(info_function)
    checklist = str(checklist_result)

    context_function = kernel.get_function("CaregiverPlugin", "PatientContextAgent")
    context_arguments = KernelArguments(user_query=query)
    context_result = await kernel.invoke(context_function, context_arguments)
    context = str(context_result)

    # Extract appointment details from context (simulate for now)
    appointment_reason = query.lower()
    answers = ""  # TODO: manage dialog state for answers if needed

    # FamilyHistoryAgent dialog logic
    family_history_agent = kernel.get_function("FamilyHistoryAgent", "run")
    fh_result = await kernel.invoke(family_history_agent, KernelArguments(appointment_reason=appointment_reason, answers=answers))
    if fh_result:
        # Log invocation for debugging
        print(f"[Orchestrator] Agent: FamilyHistoryAgent, Function: run")
        return ChecklistResponse(spoken=str(fh_result), card={})

    # Step 3: CardiologyAgent - extract symptoms
    extract_symptoms_fn = kernel.get_function("CardiologyAgent", "extract_symptoms")
    symptoms_result = await kernel.invoke(extract_symptoms_fn, KernelArguments(query=query))
    symptoms = str(symptoms_result)

    # Step 4: CardiologyAgent - recommend tests
    recommend_tests_fn = kernel.get_function("CardiologyAgent", "recommend_tests")
    tests_result = await kernel.invoke(recommend_tests_fn, KernelArguments(context=symptoms))
    recommended_tests = str(tests_result)

    # Step 5: ActionAgent (CaregiverPlugin)
    action_function = kernel.get_function("CaregiverPlugin", "ActionAgent")
    arguments = KernelArguments(checklist=checklist, context=context, user_query=query)
    result = await kernel.invoke(action_function, arguments)

    # Card payload now includes recommended tests
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
        ],
        "recommended_tests": recommended_tests
    }

    return ChecklistResponse(spoken=str(result), card=card_payload)