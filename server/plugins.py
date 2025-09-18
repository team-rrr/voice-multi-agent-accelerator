from semantic_kernel.functions.kernel_function_decorator import kernel_function

class CaregiverPlugin:
    """A plugin containing functions for caregiver appointment preparation."""

    @kernel_function(
        description="Gets a baseline checklist for a cardiology appointment.",
        name="InfoAgent"
    )
    def get_cardiology_checklist(self) -> str:
        """Provides a static, friendly checklist for a cardiology visit."""
        return """To prepare for the cardiology appointment, bring:
- Recent medical records
- A complete list of current medications (including supplements)
- A log of symptoms
- Family history of heart conditions
- A list of questions for the doctor
Helpful Links:
- Printable Medication Form: https://www.ahrq.gov/sites/default/files/wysiwyg/health-literacy/my-medicines-list.pdf
- Question Builder Tool: https://www.ahrq.gov/questions/question-builder/online.html"""

    @kernel_function(
        description="Gets the patient's recent clinical context from their record.",
        name="PatientContextAgent"
    )
    def get_patient_context(self) -> str:
        """Retrieves mock patient data for the demo."""
        return "The patient's recent diagnoses include hypertension and atrial fibrillation. Their last EKG was performed two months ago and showed mild arrhythmia."

    @kernel_function(
        description="Merges a checklist and patient context into a final, actionable response and offers to send it.",
        name="ActionAgent"
    )
    def create_final_checklist(self, checklist: str, context: str) -> str:
        """Combines information and prepares the final output for the user."""
        final_response = f"""I've created a checklist for the appointment based on this information:
{checklist}

I've also noted the following from the patient's recent record:
{context}

Would you like me to send this checklist to your phone or email?"""
        return final_response