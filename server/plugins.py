from semantic_kernel.functions.kernel_function_decorator import kernel_function

class CaregiverPlugin:
    """A plugin containing functions for caregiver appointment preparation."""

    @kernel_function(
        description="Provides contextual appointment preparation guidance based on user query and appointment type.",
        name="InfoAgent"
    )
    def get_contextual_checklist(self, query: str = "") -> str:
        """Provides dynamic checklist based on the specific query and appointment type."""
        
        # Analyze query for appointment type and context
        query_lower = query.lower() if query else ""
        
        if any(word in query_lower for word in ["cardiology", "heart", "cardiac", "chest pain"]):
            return self._get_cardiology_specific_checklist()
        elif any(word in query_lower for word in ["dermatology", "skin", "mole", "rash"]):
            return self._get_dermatology_checklist()
        elif any(word in query_lower for word in ["general", "primary care", "physical", "checkup"]):
            return self._get_general_checkup_checklist()
        else:
            # Default to adaptive checklist based on query context
            return self._get_adaptive_checklist(query)
    
    def _get_cardiology_specific_checklist(self) -> str:
        """Cardiology appointment specific checklist."""
        return """I'll help you prepare for your cardiology appointment. Here's what to bring:
- Recent EKG results and cardiac test reports
- Blood pressure log (if you monitor at home)
- Complete list of current heart medications
- Family history of cardiovascular conditions
- Any symptoms you've experienced (chest pain, shortness of breath, palpitations)
- Questions about your heart condition or treatment plan

To make this more specific to your situation, can you tell me when your chest pain typically occurs?

Helpful Links:
- Heart Health Tracker: https://www.heart.org/en/health-topics/consumer-healthcare/what-is-cardiovascular-disease/heart-attack-symptoms-in-women
- Medication Form: https://www.ahrq.gov/sites/default/files/wysiwyg/health-literacy/my-medicines-list.pdf"""
    
    def _get_dermatology_checklist(self) -> str:
        """Dermatology appointment specific checklist."""
        return """For your dermatology appointment, bring:
- Photos of skin changes or concerning areas
- List of current skincare products and medications
- Family history of skin conditions or skin cancer
- Record of sun exposure and sunscreen use
- Any symptoms (itching, pain, changes in moles)
- Questions about skin care routine or treatments"""
    
    def _get_general_checkup_checklist(self) -> str:
        """General/Primary care appointment checklist."""
        return """For your general appointment, bring:
- Current list of all medications and supplements
- Record of vital signs if monitoring at home
- Any symptoms or health concerns
- Family medical history updates
- Questions about preventive care or screenings
- Insurance cards and identification"""
    
    def _get_adaptive_checklist(self, query: str) -> str:
        """Adaptive checklist based on query context."""
        return """To prepare for your medical appointment, bring:
- Recent medical records relevant to your concern
- Complete list of current medications (including supplements)
- Log of symptoms related to your visit
- Family history relevant to your condition
- List of questions for the doctor
- Insurance cards and identification
Helpful Links:
- Medication Form: https://www.ahrq.gov/sites/default/files/wysiwyg/health-literacy/my-medicines-list.pdf
- Question Builder: https://www.ahrq.gov/questions/question-builder/online.html"""

    @kernel_function(
        description="Gets the patient's recent clinical context from their record, tailored to the user query.",
        name="PatientContextAgent"
    )
    def get_patient_context(self, user_query: str = "") -> str:
        """Retrieves mock patient data for the demo, contextualized to the query."""
        
        # Base patient data
        base_context = "Recent diagnoses include hypertension and atrial fibrillation. Last EKG performed two months ago showed mild arrhythmia."
        
        query_lower = user_query.lower() if user_query else ""
        
        # Add context based on query type
        if any(word in query_lower for word in ["cardiology", "heart", "cardiac"]):
            return f"{base_context} Patient reports occasional chest discomfort and has been monitoring blood pressure daily. Last cardiologist visit recommended lifestyle modifications."
        elif any(word in query_lower for word in ["medication", "drug", "prescription"]):
            return f"{base_context} Currently taking Lisinopril 10mg daily and Metoprolol 25mg twice daily. Patient reports good medication adherence."
        elif any(word in query_lower for word in ["symptoms", "pain", "discomfort"]):
            return f"{base_context} Patient experiences intermittent palpitations and mild shortness of breath with exertion. Symptoms have been stable over past month."
        else:
            return base_context

    @kernel_function(
        description="Merges a checklist and patient context into a final, actionable response tailored to the user query.",
        name="ActionAgent"
    )
    def create_final_checklist(self, checklist: str, context: str, user_query: str = "") -> str:
        """Combines information and prepares the final output for the user, contextualized to their specific request."""
        
        query_lower = user_query.lower() if user_query else ""
        
        # Create personalized response based on query context
        if any(word in query_lower for word in ["prepare", "preparation", "checklist"]):
            final_response = f"""I've prepared a personalized checklist for your upcoming appointment:

{checklist}

Based on your medical history:
{context}

I recommend prioritizing the items that relate to your current symptoms. Would you like me to send this checklist to your phone or email for easy reference during your appointment?"""
        
        elif any(word in query_lower for word in ["what", "bring", "need"]):
            final_response = f"""Here's what you should bring to your appointment:

{checklist}

Given your medical history:
{context}

Make sure to bring any recent test results or symptom logs. Would you like me to send this information to your phone for easy access?"""
        
        else:
            # Default comprehensive response
            final_response = f"""I've created a comprehensive preparation guide for your appointment:

{checklist}

Your medical background shows:
{context}

This personalized checklist takes into account your specific health conditions. Would you like me to send this checklist to your phone or email?"""
        
        return final_response