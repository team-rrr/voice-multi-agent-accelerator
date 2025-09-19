import os
from semantic_kernel.functions.kernel_function_decorator import kernel_function

AGENT_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "agent_prompts")

def load_agent_prompt(agent_name):
    path = os.path.join(AGENT_PROMPTS_DIR, f"{agent_name}.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

class CardiologyAgent:
    """Specialized agent for cardiology appointment preparation."""

    @kernel_function(
        description="Extracts symptoms from user query for cardiology context.",
        name="extract_symptoms"
    )
    def extract_symptoms(self, query: str) -> str:
        prompt = load_agent_prompt("CardiologyAgent_extract_symptoms")
        return prompt.format(query=query)

    @kernel_function(
        description="Recommends tests based on context and symptoms.",
        name="recommend_tests"
    )
    def recommend_tests(self, context: str) -> str:
        prompt = load_agent_prompt("CardiologyAgent_recommend_tests")
        return prompt.format(context=context)
