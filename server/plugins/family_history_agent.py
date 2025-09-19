
import os
from semantic_kernel.functions.kernel_function_decorator import kernel_function

AGENT_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "agent_prompts")

def load_agent_prompt(agent_name):
    path = os.path.join(AGENT_PROMPTS_DIR, f"{agent_name}.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

class FamilyHistoryAgent:
    @kernel_function(
        description="Runs the family history dialog flow for physical appointments.",
        name="run"
    )
    def run(self, appointment_reason: str, answers: str = "") -> str:
        if 'physical' not in (appointment_reason or '').lower():
            return ""
        if not answers:
            return self.start_dialog()
        return self.summarize_answers(answers)
    """Agent for collecting family history for physical appointments."""

    @kernel_function(
        description="Checks if the appointment is a physical and should trigger family history dialog.",
        name="should_trigger"
    )
    def should_trigger(self, appointment_reason: str) -> bool:
        return 'physical' in (appointment_reason or '').lower()

    @kernel_function(
        description="Starts the family history dialog by asking three health risk questions.",
        name="start_dialog"
    )
    def start_dialog(self) -> str:
        prompt = load_agent_prompt("FamilyHistoryAgent_start_dialog")
        return prompt

    @kernel_function(
        description="Summarizes the family history answers in a bullet list.",
        name="summarize_answers"
    )
    def summarize_answers(self, answers: str) -> str:
        prompt = load_agent_prompt("FamilyHistoryAgent_summarize_answers")
        return prompt.format(answers=answers)
