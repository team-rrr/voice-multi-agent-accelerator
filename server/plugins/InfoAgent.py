import os
from semantic_kernel.functions.kernel_function_decorator import kernel_function

AGENT_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "agent_prompts")

def load_agent_prompt(agent_name):
    path = os.path.join(AGENT_PROMPTS_DIR, f"{agent_name}.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

class InfoAgent:
    @kernel_function(
        description="Gets a baseline checklist for a cardiology appointment.",
        name="InfoAgent"
    )
    def get_checklist(self) -> str:
        return load_agent_prompt("InfoAgent")
