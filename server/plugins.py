from semantic_kernel.functions.kernel_function_decorator import kernel_function
from pydantic import BaseModel
from typing import List, Dict, Optional
import json

# Enhanced structured response models for agent functions
class InfoAgentResponse(BaseModel):
    summary: str  # Brief intro/context summary
    checklist_items: List[str]  # Organized preparation items
    links: List[Dict[str, str]] = []  # Helpful resources with name/url
    follow_up_question: Optional[str] = None  # Single follow-up question
    appointment_type: Optional[str] = None
    priority_level: str = "medium"  # high/medium/low for urgency

class PatientContextResponse(BaseModel):
    summary: str  # Summary of patient's relevant medical context
    medical_context: Dict[str, str]  # Structured medical information
    relevant_conditions: List[str] = []
    current_medications: List[str] = []
    follow_up_question: Optional[str] = None  # Single clarifying question
    confidence_level: str = "medium"  # high/medium/low for data completeness

class ActionAgentResponse(BaseModel):
    summary: str  # Final summary/recommendation
    questions_to_ask: List[str] = []  # Questions for the doctor
    follow_up_actions: List[str] = []  # Actions user should take
    priority_items: List[str] = []  # Most important items to focus on
    follow_up_question: Optional[str] = None  # Single question for user
    next_steps: List[str] = []  # Clear next steps for user

class CaregiverPlugin:
    """A plugin containing functions for caregiver appointment preparation."""

    @kernel_function(
        description="Provides contextual appointment preparation guidance based on user query and conversation state.",
        name="InfoAgent"
    )
    def get_contextual_checklist(self, query: str = "", conversation_state: str = "{}") -> str:
        """Provides dynamic checklist based on the specific query and conversation state."""
        
        # Parse conversation state to understand context
        try:
            state = json.loads(conversation_state) if conversation_state else {}
        except json.JSONDecodeError:
            state = {}
        
        # Analyze query for appointment type and context
        query_lower = query.lower() if query else ""
        
        # Check if we've already provided a checklist to avoid redundancy
        conversation_history = state.get("conversation_history", [])
        already_provided_checklist = any("checklist" in msg.lower() or "preparation" in msg.lower() 
                                        for msg in conversation_history[-3:])  # Check last 3 messages
        
        if any(word in query_lower for word in ["cardiology", "heart", "cardiac", "chest pain"]):
            response = self._get_cardiology_specific_response(already_provided_checklist)
        elif any(word in query_lower for word in ["dermatology", "skin", "mole", "rash"]):
            response = self._get_dermatology_response(already_provided_checklist)
        elif any(word in query_lower for word in ["general", "primary care", "physical", "checkup"]):
            response = self._get_general_checkup_response(already_provided_checklist)
        else:
            # Default to adaptive checklist based on query context
            response = self._get_adaptive_response(query, already_provided_checklist)
        
        # Return JSON string that can be parsed by orchestrator
        return json.dumps(response.dict())
    
    def _get_cardiology_specific_response(self, already_provided_checklist: bool = False) -> InfoAgentResponse:
        """Cardiology appointment specific response."""
        if already_provided_checklist:
            summary = "Since we've already discussed your cardiology preparation checklist, let me focus on the most important items."
            follow_up = "Is there a specific aspect of your heart health you're most concerned about discussing?"
        else:
            summary = "I'll help you prepare for your cardiology appointment. Here's what to bring:"
            follow_up = "To make this more specific, can you tell me when your chest pain typically occurs?"
        
        return InfoAgentResponse(
            summary=summary,
            checklist_items=[
                "Recent EKG results and cardiac test reports",
                "Blood pressure log (if you monitor at home)",
                "Complete list of current heart medications",
                "Family history of cardiovascular conditions", 
                "Any symptoms you've experienced (chest pain, shortness of breath, palpitations)",
                "Questions about your heart condition or treatment plan"
            ],
            links=[
                {"name": "Heart Health Tracker", "url": "https://www.heart.org/en/health-topics/consumer-healthcare/what-is-cardiovascular-disease/heart-attack-symptoms-in-women"},
                {"name": "Medication Form", "url": "https://www.ahrq.gov/sites/default/files/wysiwyg/health-literacy/my-medicines-list.pdf"}
            ],
            follow_up_question=follow_up,
            appointment_type="Cardiology",
            priority_level="high"
        )
    
    def _get_dermatology_response(self, already_provided_checklist: bool = False) -> InfoAgentResponse:
        """Dermatology appointment specific response."""
        if already_provided_checklist:
            summary = "For your dermatology visit, let me highlight the most crucial items to bring."
            follow_up = "Have you noticed any changes in your skin since we last talked?"
        else:
            summary = "For your dermatology appointment, I'll help you prepare the essential items."
            follow_up = "What specific skin concerns would you like to discuss with your dermatologist?"
        
        return InfoAgentResponse(
            summary=summary,
            checklist_items=[
                "Photos of skin changes or concerning areas",
                "List of current skincare products and medications", 
                "Family history of skin conditions or skin cancer",
                "Record of sun exposure and sunscreen use",
                "Any symptoms (itching, pain, changes in moles)",
                "Questions about skin care routine or treatments"
            ],
            links=[],
            follow_up_question=follow_up,
            appointment_type="Dermatology",
            priority_level="medium"
        )
    
    def _get_general_checkup_response(self, already_provided_checklist: bool = False) -> InfoAgentResponse:
        """General/Primary care appointment response."""
        if already_provided_checklist:
            summary = "For your general checkup, let me remind you of the key preparation items."
            follow_up = "Are there any new symptoms or concerns that have come up since we last discussed?"
        else:
            summary = "For your general appointment, I'll help you prepare all the necessary items."
            follow_up = "Are there any specific health concerns or symptoms you'd like to discuss during your visit?"
        
        return InfoAgentResponse(
            summary=summary,
            checklist_items=[
                "Current list of all medications and supplements",
                "Record of vital signs if monitoring at home", 
                "Any symptoms or health concerns",
                "Family medical history updates",
                "Questions about preventive care or screenings",
                "Insurance cards and identification"
            ],
            links=[],
            follow_up_question=follow_up,
            appointment_type="General",
            priority_level="medium"
        )
    
    def _get_adaptive_response(self, query: str, already_provided_checklist: bool = False) -> InfoAgentResponse:
        """Adaptive response based on query context."""
        if already_provided_checklist:
            summary = "Let me refine your appointment preparation based on what we've discussed."
            follow_up = "Is there anything specific about your upcoming appointment that concerns you?"
        else:
            summary = "To prepare for your medical appointment, I'll help you gather the essential items."
            follow_up = "Can you tell me more about the main reason for your visit?"
        
        return InfoAgentResponse(
            summary=summary,
            checklist_items=[
                "Recent medical records relevant to your concern",
                "Complete list of current medications (including supplements)",
                "Log of symptoms related to your visit", 
                "Family history relevant to your condition",
                "List of questions for the doctor",
                "Insurance cards and identification"
            ],
            links=[
                {"name": "Medication Form", "url": "https://www.ahrq.gov/sites/default/files/wysiwyg/health-literacy/my-medicines-list.pdf"},
                {"name": "Question Builder", "url": "https://www.ahrq.gov/questions/question-builder/online.html"}
            ],
            follow_up_question=follow_up,
            appointment_type="General",
            priority_level="medium"
        )

    @kernel_function(
        description="Gets the patient's recent clinical context from their record, tailored to the user query and conversation state.",
        name="PatientContextAgent"
    )
    def get_patient_context(self, user_query: str = "", conversation_state: str = "{}") -> str:
        """Retrieves mock patient data for the demo, contextualized to the query and conversation history."""
        
        # Parse conversation state to understand context
        try:
            state = json.loads(conversation_state) if conversation_state else {}
        except json.JSONDecodeError:
            state = {}
        
        query_lower = user_query.lower() if user_query else ""
        
        # Check conversation history to avoid repeating information
        conversation_history = state.get("conversation_history", [])
        already_mentioned_conditions = any("hypertension" in msg.lower() or "atrial fibrillation" in msg.lower() 
                                         for msg in conversation_history[-5:])  # Check last 5 messages
        
        # Create structured response based on query type
        if any(word in query_lower for word in ["cardiology", "heart", "cardiac"]):
            if already_mentioned_conditions:
                summary = "Focusing on your heart conditions, your recent symptoms are the key information for your cardiologist."
                follow_up = "Have your symptoms changed since we last discussed them?"
                confidence = "high"
            else:
                summary = "Based on your medical history, you have hypertension and atrial fibrillation. Since you've been experiencing chest discomfort, it's important to discuss your blood pressure readings with your cardiologist."
                follow_up = "How often have you been experiencing the chest discomfort?"
                confidence = "medium"
            
            response = PatientContextResponse(
                summary=summary,
                medical_context={
                    "primary_conditions": "hypertension, atrial fibrillation",
                    "recent_tests": "EKG two months ago showed mild arrhythmia",
                    "current_symptoms": "occasional chest discomfort",
                    "monitoring": "daily blood pressure monitoring"
                },
                relevant_conditions=["hypertension", "atrial fibrillation"],
                current_medications=["Lisinopril 10mg daily", "Metoprolol 25mg twice daily"],
                follow_up_question=follow_up,
                confidence_level=confidence
            )
        elif any(word in query_lower for word in ["medication", "drug", "prescription"]):
            already_mentioned_meds = any("lisinopril" in msg.lower() or "metoprolol" in msg.lower() 
                                       for msg in conversation_history[-3:])
            
            if already_mentioned_meds:
                summary = "Your medication regimen is well-established with good adherence."
                follow_up = "Have you experienced any side effects from your current medications?"
                confidence = "high"
            else:
                summary = "Your current medications include Lisinopril and Metoprolol for your heart conditions. It's great that you've been consistent with taking them."
                follow_up = "Are you taking any other medications or supplements?"
                confidence = "medium"
            
            response = PatientContextResponse(
                summary=summary,
                medical_context={
                    "primary_conditions": "hypertension, atrial fibrillation",
                    "medication_adherence": "good adherence reported",
                    "recent_tests": "EKG two months ago showed mild arrhythmia"
                },
                relevant_conditions=["hypertension", "atrial fibrillation"],
                current_medications=["Lisinopril 10mg daily", "Metoprolol 25mg twice daily"],
                follow_up_question=follow_up,
                confidence_level=confidence
            )
        elif any(word in query_lower for word in ["symptoms", "pain", "discomfort"]):
            already_discussed_symptoms = any("palpitations" in msg.lower() or "shortness of breath" in msg.lower() 
                                           for msg in conversation_history[-3:])
            
            if already_discussed_symptoms:
                summary = "Your symptoms remain stable, which is reassuring for your healthcare team."
                follow_up = "Have you noticed any changes in when these symptoms occur?"
                confidence = "high"
            else:
                summary = "You've been experiencing intermittent palpitations and mild shortness of breath with activity. These symptoms have been stable, which is good information for your doctor."
                follow_up = "When do you typically notice these symptoms most?"
                confidence = "medium"
            
            response = PatientContextResponse(
                summary=summary,
                medical_context={
                    "primary_conditions": "hypertension, atrial fibrillation",
                    "current_symptoms": "intermittent palpitations, mild shortness of breath with exertion",
                    "symptom_stability": "stable over past month"
                },
                relevant_conditions=["hypertension", "atrial fibrillation"],
                current_medications=["Lisinopril 10mg daily", "Metoprolol 25mg twice daily"],
                follow_up_question=follow_up,
                confidence_level=confidence
            )
        else:
            # General context request
            if already_mentioned_conditions:
                summary = "Your established medical conditions and recent test results provide good context for your appointment."
                follow_up = "What specific aspect of your health would you like to focus on today?"
                confidence = "high"
            else:
                summary = "Your medical history shows hypertension and atrial fibrillation, with a recent EKG showing mild arrhythmia."
                follow_up = "Is there a particular health concern you'd like to discuss?"
                confidence = "medium"
            
            response = PatientContextResponse(
                summary=summary,
                medical_context={
                    "primary_conditions": "hypertension, atrial fibrillation",
                    "recent_tests": "EKG two months ago showed mild arrhythmia"
                },
                relevant_conditions=["hypertension", "atrial fibrillation"],
                current_medications=[],
                follow_up_question=follow_up,
                confidence_level=confidence
            )
        
        return json.dumps(response.dict())

    @kernel_function(
        description="Merges a checklist and patient context into a final, actionable response tailored to the user query and conversation state.",
        name="ActionAgent"
    )
    def create_final_checklist(self, checklist: str, context: str, user_query: str = "", conversation_state: str = "{}") -> str:
        """Combines information and prepares the final output for the user, contextualized to their specific request and conversation history."""
        
        query_lower = user_query.lower() if user_query else ""
        
        # Parse conversation state to understand context
        try:
            state = json.loads(conversation_state) if conversation_state else {}
        except json.JSONDecodeError:
            state = {}
        
        # Parse the structured inputs (they should be JSON strings from other agents)
        try:
            checklist_data = json.loads(checklist) if checklist.startswith('{') else {}
            context_data = json.loads(context) if context.startswith('{') else {}
        except json.JSONDecodeError:
            # Fallback for non-JSON input (backward compatibility)
            checklist_data = {}
            context_data = {}
        
        # Check conversation history to avoid redundant offerings
        conversation_history = state.get("conversation_history", [])
        already_offered_to_send = any("send" in msg.lower() and ("phone" in msg.lower() or "email" in msg.lower()) 
                                    for msg in conversation_history[-3:])
        
        # Create structured response based on query context
        if any(word in query_lower for word in ["prepare", "preparation", "checklist"]):
            if already_offered_to_send:
                summary = "I've refined your personalized checklist based on our conversation. Focus on the priority items that relate most to your current health situation."
                follow_up = "Is there anything else you'd like to add to your preparation list?"
            else:
                summary = "I've prepared a personalized checklist for your upcoming appointment. I recommend prioritizing the items that relate to your current symptoms."
                follow_up = "Would you like me to send this checklist to your phone or email for easy reference during your appointment?"
            
            response = ActionAgentResponse(
                summary=summary,
                questions_to_ask=[
                    "Are there any specific concerns you'd like to discuss with your doctor?",
                    "Do you have any recent test results or symptom logs to bring?",
                    "What questions do you want to make sure to ask your healthcare provider?"
                ],
                follow_up_actions=[
                    "Review your current medications list", 
                    "Prepare any questions about your symptoms",
                    "Gather recent medical records"
                ],
                priority_items=checklist_data.get("checklist_items", [])[:3],  # Top 3 items
                follow_up_question=follow_up,
                next_steps=[
                    "Organize your medical documents",
                    "Print or save your preparation checklist",
                    "Schedule time to review your questions before the appointment"
                ]
            )
        elif any(word in query_lower for word in ["what", "bring", "need"]):
            if already_offered_to_send:
                summary = "Here are the essential items to bring, prioritized based on your health conditions."
                follow_up = "Do you have all of these items readily available, or do you need help organizing anything?"
            else:
                summary = "Here's what you should bring to your appointment. Make sure to bring any recent test results or symptom logs."
                follow_up = "Would you like me to send this information to your phone for easy access?"
            
            response = ActionAgentResponse(
                summary=summary,
                questions_to_ask=[
                    "Do you have any recent test results to bring?",
                    "Are there any new symptoms you've noticed?",
                    "What's your biggest concern about this appointment?"
                ],
                follow_up_actions=[
                    "Organize your medical documents",
                    "Update your medication list", 
                    "Prepare your insurance information"
                ],
                priority_items=checklist_data.get("checklist_items", []),
                follow_up_question=follow_up,
                next_steps=[
                    "Gather all documents in one place",
                    "Double-check appointment time and location",
                    "Prepare transportation and arrive early"
                ]
            )
        else:
            # Default comprehensive response
            if already_offered_to_send:
                summary = "Your comprehensive preparation guide is ready, personalized for your specific health conditions and appointment type."
                follow_up = "What's the most important thing you want to accomplish during your appointment?"
            else:
                summary = "I've created a comprehensive preparation guide for your appointment. This personalized checklist takes into account your specific health conditions."
                follow_up = "Would you like me to send this checklist to your phone or email?"
            
            response = ActionAgentResponse(
                summary=summary,
                questions_to_ask=[
                    "Are there any other health concerns you want to discuss?",
                    "Do you need help organizing any of these items?", 
                    "What outcomes are you hoping for from this appointment?"
                ],
                follow_up_actions=[
                    "Schedule any necessary follow-up appointments",
                    "Review your current treatment plan",
                    "Prepare questions for your healthcare provider"
                ],
                priority_items=checklist_data.get("checklist_items", []),
                follow_up_question=follow_up,
                next_steps=[
                    "Complete all preparation items",
                    "Arrive 15 minutes early for check-in", 
                    "Bring a trusted person if needed for support"
                ]
            )
        
        return json.dumps(response.dict())