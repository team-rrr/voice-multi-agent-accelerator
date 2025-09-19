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

class ConversationState:
    """Tracks the state of appointment preparation conversations."""
    def __init__(self):
        self.phase = "idle"  # idle, gathering_info, information_complete, card_ready
        self.appointment_type = None
        self.gathered_info = []
        self.completion_signals = 0  # Count of completion indicators
        
    def is_gathering_info(self) -> bool:
        return self.phase == "gathering_info"
        
    def is_complete(self) -> bool:
        return self.phase == "information_complete"
        
    def mark_info_gathering_started(self, appointment_type: str = None):
        self.phase = "gathering_info"
        if appointment_type:
            self.appointment_type = appointment_type
            
    def add_completion_signal(self):
        self.completion_signals += 1
        if self.completion_signals >= 1:  # One strong signal is enough
            self.phase = "information_complete"
            
    def mark_card_generated(self):
        self.phase = "card_ready"
        
    def reset(self):
        self.phase = "idle"
        self.appointment_type = None
        self.gathered_info = []
        self.completion_signals = 0

# Session-based conversation states
session_states = {}

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

def detect_conversation_completion(query: str, conversation_state: ConversationState) -> bool:
    """Detect if user is signaling completion of information gathering."""
    query_lower = query.lower().strip()
    
    # Strong completion signals
    completion_phrases = [
        "that's all", "that's it", "i'm ready", "i'm done", "no more questions",
        "nothing else", "that covers it", "i think that's everything",
        "sounds good", "perfect", "great", "excellent", "wonderful",
        "thank you", "thanks", "appreciate it"
    ]
    
    # Confirmation responses that suggest they're satisfied
    confirmation_phrases = [
        "yes", "sure", "ok", "okay", "alright", "sounds right",
        "that works", "that's correct", "exactly"
    ]
    
    # Check for strong completion signals
    if any(phrase in query_lower for phrase in completion_phrases):
        return True
        
    # Check for confirmations when already gathering info
    if conversation_state.is_gathering_info():
        if any(phrase in query_lower for phrase in confirmation_phrases) and len(query_lower) < 20:
            return True
            
    return False

def classify_intent(query: str) -> str:
    """Classify user intent to determine agent flow."""
    query_lower = query.lower().strip()
    
    # Handle very short or incomplete queries
    if len(query_lower) <= 3:
        return "conversational"
    
    # Keywords for different intents - prioritize appointment preparation requests
    checklist_keywords = ["appointment", "prepare", "checklist", "bring", "doctor visit", "visit", "see doctor", "help me prepare", "personalized guidance", "preparation", "guide", "can you help me prepare"]
    patient_keywords = ["my condition", "my diagnosis", "my medication", "my health", "my symptoms"]
    general_keywords = ["what is", "tell me", "explain", "how", "why", "what kind", "what tests", "tests", "what should", "need help"]
    
    # Short responses that should be treated as conversational
    short_responses = ["yes", "no", "ok", "sure", "thanks", "that's it", "got it", "hey", "hello"]
    
    # Handle incomplete sentences or fragments
    incomplete_patterns = ["can you help", "i need help", "hey can"]
    
    # Priority 1: Explicit appointment preparation requests (highest priority)
    if ("appointment" in query_lower and any(word in query_lower for word in ["prepare", "help", "guidance", "ready"])):
        return "checklist_request"
    elif any(keyword in query_lower for keyword in checklist_keywords):
        return "checklist_request"
    elif any(response in query_lower for response in short_responses):
        return "conversational"
    elif any(pattern in query_lower for pattern in incomplete_patterns):
        return "conversational"
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
    """Generate card data from agent responses in the format expected by the frontend."""
    preparation_items = []
    questions_to_ask = []
    
    lines = checklist.split('\n')
    current_section = "preparation"  # Default section
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and headers
        if not line or line.startswith('I\'ll help') or line.startswith('For your') or line.startswith('To make'):
            continue
            
        # Check for section headers
        if 'question' in line.lower() or 'ask' in line.lower():
            current_section = "questions"
            continue
        elif 'bring' in line.lower() or 'preparation' in line.lower():
            current_section = "preparation" 
            continue
            
        # Extract list items
        if line.startswith('-') or line.startswith('•'):
            item_text = line[1:].strip()
            if item_text and not item_text.startswith('http'):  # Skip URLs
                if current_section == "questions":
                    questions_to_ask.append(item_text)
                else:
                    preparation_items.append(item_text)
    
    # Extract appointment details from query
    appointment_details = {}
    query_lower = query.lower()
    
    # Try to extract doctor name
    if 'dr.' in query_lower or 'doctor' in query_lower:
        words = query.split()
        for i, word in enumerate(words):
            if word.lower() in ['dr.', 'doctor'] and i + 1 < len(words):
                appointment_details['doctor'] = f"Dr. {words[i+1].title()}"
                break
    
    # Extract appointment reason from context and query
    if 'cardiology' in (query + context).lower() or 'heart' in query_lower or 'chest pain' in query_lower:
        appointment_details['reason'] = 'Cardiology consultation'
        appointment_type = "Cardiology"
    elif 'dermatology' in (query + context).lower() or 'skin' in query_lower:
        appointment_details['reason'] = 'Dermatology consultation' 
        appointment_type = "Dermatology"
    else:
        appointment_details['reason'] = 'Medical consultation'
        appointment_type = "General"
    
    # Extract timing if mentioned
    if 'next week' in query_lower:
        appointment_details['timing'] = 'Next week'
    elif 'tomorrow' in query_lower:
        appointment_details['timing'] = 'Tomorrow'
    elif 'today' in query_lower:
        appointment_details['timing'] = 'Today'
    
    # Add some default questions if none were found
    if not questions_to_ask:
        if appointment_type == "Cardiology":
            questions_to_ask = [
                "What tests or procedures might be needed?",
                "Are there any lifestyle changes I should make?",
                "How often should I monitor my symptoms?"
            ]
        elif appointment_type == "Dermatology":
            questions_to_ask = [
                "Are there any concerning features I should watch for?",
                "What skincare routine do you recommend?",
                "When should I schedule a follow-up?"
            ]
        else:
            questions_to_ask = [
                "Are there any additional tests needed?", 
                "What follow-up care is recommended?",
                "Are there any warning signs to watch for?"
            ]
    
    return {
        "title": f"{appointment_type} Appointment Preparation",
        "appointment_details": appointment_details,
        "preparation_items": preparation_items,
        "questions_to_ask": questions_to_ask,
        "follow_up_actions": [
            "Schedule any recommended follow-up appointments",
            "Fill any new prescriptions promptly", 
            "Keep a record of visit notes for future reference"
        ]
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

async def full_agent_flow_no_card(query: str, context: dict) -> dict:
    """Full 3-agent flow for appointment preparation - stores data but doesn't generate card yet."""
    logger.info("Running full multi-agent orchestration for information gathering...")
    
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
    patient_context = str(context_result)
    logger.info(f"PatientContextAgent completed: {patient_context[:100]}...")
    
    # Step 3: Call ActionAgent to create contextual response based on user query
    action_function = kernel.get_function("CaregiverPlugin", "ActionAgent")
    arguments = KernelArguments(checklist=checklist, context=patient_context, user_query=query)
    result = await kernel.invoke(action_function, arguments)
    logger.info(f"ActionAgent completed: {str(result)[:100]}...")

    # Return data without generating card
    return {
        "spoken": str(result),
        "checklist": checklist,
        "context": patient_context
    }

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

def enforce_single_question(response_text: str) -> str:
    """Ensure response contains only one question by extracting the first question if multiple exist."""
    if not response_text or '?' not in response_text:
        return response_text
    
    # Split by question marks and find the first complete question
    parts = response_text.split('?')
    if len(parts) <= 2:  # No multiple questions (0 or 1 question)
        return response_text
    
    # Find the first question and include context before it
    first_question_end = response_text.find('?') + 1
    result = response_text[:first_question_end]
    
    # Add a note that we'll ask more questions later
    if len(parts) > 2:  # Multiple questions detected
        result += "\n\nI'll ask you more specific questions once you answer this one."
    
    return result

async def run_orchestration(query: str, session_id: str = "default") -> ChecklistResponse:
    """
    Enhanced orchestration with intelligent routing and conversation state management.
    Routes to appropriate agent flow and manages card generation timing.
    """
    # Initialize session state if needed
    if session_id not in session_states:
        session_states[session_id] = ConversationState()
    
    # Retrieve or initialize conversation context
    if session_id not in conversation_context:
        conversation_context[session_id] = {
            "previous_queries": [],
            "patient_info": {},
            "appointment_type": None,
            "gathered_checklist": None,
            "gathered_context": None
        }
    
    state = session_states[session_id]
    context = conversation_context[session_id]
    context["previous_queries"].append(query)
    
    # Check for conversation completion signals
    is_completion_signal = detect_conversation_completion(query, state)
    
    # If user is signaling completion and we have checklist data, generate the card
    if is_completion_signal and state.is_gathering_info():
        state.mark_card_generated()
        
        # Generate card from stored information
        if context.get("gathered_checklist") and context.get("gathered_context"):
            card_payload = generate_dynamic_card(
                context["gathered_checklist"], 
                context["gathered_context"], 
                query
            )
            
            # Provide completion response with card
            completion_response = "Perfect! I've prepared a comprehensive checklist for your appointment. This should help you be well-prepared and make the most of your time with your doctor."
            return ChecklistResponse(spoken=completion_response, card=card_payload)
        else:
            # Completion signal but no checklist data
            return ChecklistResponse(
                spoken="I understand you're ready! Is there anything specific about your appointment that you'd like help preparing for?",
                card=None
            )
    
    # Classify the query intent
    intent = classify_intent(query)
    logger.info(f"Classified query '{query}' intent as: {intent}")
    
    if intent == "checklist_request":
        # Start information gathering mode (no card yet)
        state.mark_info_gathering_started()
        
        # Get checklist and context info but don't generate card yet
        result = await full_agent_flow_no_card(query, context)
        
        # Store the information for later card generation
        context["gathered_checklist"] = result.get("checklist", "")
        context["gathered_context"] = result.get("context", "")
        
        # Enforce single question rule and add continuation guidance
        spoken_response = enforce_single_question(result["spoken"])
        if "?" in spoken_response:
            spoken_response += "\n\nOnce I have all the information I need, I'll prepare a comprehensive checklist for your appointment."
        
        return ChecklistResponse(spoken=spoken_response, card=None)
        
    elif intent == "general_question":
        # Just InfoAgent for general medical questions  
        result = await simple_response_flow(query)
        result.spoken = enforce_single_question(result.spoken)
        return result
        
    elif intent == "patient_specific":
        # Continue information gathering if in progress
        if state.is_gathering_info():
            result = await contextual_flow(query)
            # Update stored context
            context["gathered_context"] = context.get("gathered_context", "") + f"\nAdditional info: {str(result.spoken)}"
            result.spoken = enforce_single_question(result.spoken)
            return result
        else:
            # Regular patient-specific flow
            result = await contextual_flow(query)
            result.spoken = enforce_single_question(result.spoken)
            return result
    else:
        # Conversational responses - check if it could be completion
        if state.is_gathering_info() and is_completion_signal:
            # Handle completion in conversational context
            state.add_completion_signal()
            
        return await conversational_flow(query)