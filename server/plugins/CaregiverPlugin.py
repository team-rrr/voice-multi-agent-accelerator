import os
from semantic_kernel.functions.kernel_function_decorator import kernel_function

AGENT_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "agent_prompts")

def load_agent_prompt(agent_name):
    path = os.path.join(AGENT_PROMPTS_DIR, f"{agent_name}.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

class CaregiverPlugin:
    """A plugin containing functions for caregiver appointment preparation."""

    @kernel_function(
        description="Gets a baseline checklist for a cardiology appointment.",
        name="InfoAgent"
    )
    def get_cardiology_checklist(self) -> str:
        return load_agent_prompt("InfoAgent")

    @kernel_function(
        description="Gets the patient's recent clinical context from their record.",
        name="PatientContextAgent"
    )
    def get_patient_context(self) -> str:
        return load_agent_prompt("PatientContextAgent")

    @kernel_function(
        description="Merges a checklist and patient context into a final, actionable response and offers to send it.",
        name="ActionAgent"
    )
    def create_final_checklist(self, checklist: str, context: str) -> str:
        template = load_agent_prompt("ActionAgent")
        return template.format(checklist=checklist, context=context)
