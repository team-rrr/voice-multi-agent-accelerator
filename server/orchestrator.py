import os
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_arguments import KernelArguments
from pydantic import BaseModel
import logging

from plugins import CaregiverPlugin

logger = logging.getLogger(__name__)

# Conversation state management
conversation_context = {}

class UserPreferences:
    """User preferences for conversation flow control."""
    def __init__(self):
        self.show_cards_immediately = False
        self.preferred_response_style = "conversational"  # "detailed", "brief", "conversational"
        self.voice_first = True  # Prioritize voice over visual elements

# Define a Pydantic model for our structured response [cite: 483]
class ChecklistResponse(BaseModel):
    spoken: str
    card: dict | None = None

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

def classify_intent(query: str) -> str:
    """Classify user intent to determine agent flow."""
    query_lower = query.lower()
    
    # Keywords for different intents
    checklist_keywords = ["appointment", "prepare", "checklist", "bring", "doctor visit", "visit", "see doctor"]
    patient_keywords = ["my condition", "my diagnosis", "my medication", "my health", "my symptoms", "chest pain", "pain", "symptoms"]
    general_keywords = ["what is", "tell me", "explain", "how", "why", "what kind", "what tests", "tests"]
    
    # Short responses that should be treated as conversational
    short_responses = ["yes", "no", "ok", "sure", "thanks", "that's it", "got it"]
    
    if len(query_lower.strip()) <= 3 or any(response in query_lower for response in short_responses):
        return "conversational"
    elif any(keyword in query_lower for keyword in checklist_keywords):
        return "checklist_request"
    elif any(keyword in query_lower for keyword in patient_keywords):
        return "patient_specific"
    elif any(keyword in query_lower for keyword in general_keywords):
        return "general_question"
    else:
        return "conversational"

def should_show_card(query: str, agent_response: str, preferences: UserPreferences = None) -> bool:
    """Determine if a card should be displayed based on content and user preferences."""
    if preferences is None:
        preferences = UserPreferences()
        
    if not preferences.voice_first:
        return True
        
    # Only show cards for structured content
    has_list_items = any(marker in agent_response for marker in ['-', '•', '1.', '2.'])
    is_checklist_query = any(word in query.lower() for word in ["checklist", "prepare", "bring", "appointment"])
    
    return has_list_items and is_checklist_query

def generate_dynamic_card(checklist: str, context: str, query: str = "") -> dict:
    """Generate card data from agent responses instead of using static data."""
    items = []
    lines = checklist.split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('-') or line.startswith('•'):
            # Remove bullet point and clean up text
            item_text = line[1:].strip()
            if item_text:  # Only add non-empty items
                items.append({
                    "text": item_text,
                    "completed": False
                })
    
    # Determine appointment type from context
    appointment_type = "General"
    if "cardiology" in (query + context).lower():
        appointment_type = "Cardiology"
    elif "dermatology" in (query + context).lower():
        appointment_type = "Dermatology"
    
    return {
        "title": f"{appointment_type} Appointment Preparation",
        "items": items,
        "patientContext": context,
        "appointmentType": appointment_type
    }

async def simple_response_flow(query: str) -> ChecklistResponse:
    """Simple flow for general questions - InfoAgent only."""
    info_function = kernel.get_function("CaregiverPlugin", "InfoAgent")
    arguments = KernelArguments(query=query)
    info_result = await kernel.invoke(info_function, arguments)
    
    return ChecklistResponse(
        spoken=str(info_result),
        card=None
    )

async def contextual_flow(query: str) -> ChecklistResponse:
    """Context flow for patient-specific queries - InfoAgent + PatientContextAgent."""
    # Get functions
    info_function = kernel.get_function("CaregiverPlugin", "InfoAgent")
    context_function = kernel.get_function("CaregiverPlugin", "PatientContextAgent")
    
    # Execute InfoAgent and PatientContextAgent with query context
    info_arguments = KernelArguments(query=query)
    info_result = await kernel.invoke(info_function, info_arguments)
    
    context_arguments = KernelArguments(user_query=query)
    context_result = await kernel.invoke(context_function, context_arguments)
    
    # Combine responses
    combined_response = f"{str(info_result)}\n\nBased on your medical history:\n{str(context_result)}"
    
    return ChecklistResponse(
        spoken=combined_response,
        card=None
    )

async def conversational_flow(query: str) -> ChecklistResponse:
    """Conversational flow for general chat."""
    query_lower = query.lower()
    
    # Handle common short responses
    if query_lower in ["yes", "sure", "ok"]:
        response_text = "Great! Is there anything else I can help you prepare for your appointment?"
    elif query_lower in ["no", "that's it", "nothing"]:
        response_text = "Perfect! You're all set. Good luck with your appointment, and feel free to ask if you need any more help!"
    elif "thank" in query_lower:
        response_text = "You're welcome! I'm here whenever you need help preparing for medical appointments."
    else:
        response_text = f"I understand. I'm here to help you prepare for medical appointments. You can ask me about appointment preparation, what to bring to your doctor visit, or questions about your health conditions."
    
    return ChecklistResponse(
        spoken=response_text,
        card=None
    )

async def full_agent_flow(query: str) -> ChecklistResponse:
    """Full 3-agent flow for appointment preparation requests."""
    logger.info("Running full multi-agent orchestration...")
    
    # Step 1: Call InfoAgent to get the contextual checklist
    info_function = kernel.get_function("CaregiverPlugin", "InfoAgent")
    info_arguments = KernelArguments(query=query)
    checklist_result = await kernel.invoke(info_function, info_arguments)
    checklist = str(checklist_result)
    logger.info(f"InfoAgent completed: {checklist[:100]}...")
    
    # Step 2: Call PatientContextAgent with user query for context-aware response
    context_function = kernel.get_function("CaregiverPlugin", "PatientContextAgent")
    context_arguments = KernelArguments(user_query=query)
    context_result = await kernel.invoke(context_function, context_arguments)
    context = str(context_result)
    logger.info(f"PatientContextAgent completed: {context[:100]}...")
    
    # Step 3: Call ActionAgent to create contextual response based on user query
    action_function = kernel.get_function("CaregiverPlugin", "ActionAgent")
    arguments = KernelArguments(checklist=checklist, context=context, user_query=query)
    result = await kernel.invoke(action_function, arguments)
    logger.info(f"ActionAgent completed: {str(result)[:100]}...")

    # Generate dynamic card based on agent outputs
    preferences = UserPreferences()
    card_payload = None
    if should_show_card(query, checklist, preferences):
        card_payload = generate_dynamic_card(checklist, context, query)
        logger.info("Generated dynamic card from agent responses")

    return ChecklistResponse(spoken=str(result), card=card_payload)

async def run_orchestration(query: str, session_id: str = "default") -> ChecklistResponse:
    """
    Enhanced orchestration with intelligent routing based on query intent.
    Routes to appropriate agent flow based on user query classification.
    """
    # Retrieve or initialize conversation context
    if session_id not in conversation_context:
        conversation_context[session_id] = {
            "previous_queries": [],
            "patient_info": {},
            "appointment_type": None
        }
    
    context = conversation_context[session_id]
    context["previous_queries"].append(query)
    
    # Classify the query intent
    intent = classify_intent(query)
    logger.info(f"Classified query intent as: {intent}")
    
    if intent == "checklist_request":
        # Full 3-agent flow for appointment preparation
        return await full_agent_flow(query)
    elif intent == "general_question":
        # Just InfoAgent for general medical questions  
        return await simple_response_flow(query)
    elif intent == "patient_specific":
        # InfoAgent + PatientContextAgent for patient-specific queries
        return await contextual_flow(query)
    else:
        # Fallback to conversational response
        return await conversational_flow(query)