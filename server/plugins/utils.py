import os

AGENT_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "agent_prompts")

def load_agent_prompt(agent_name):
    path = os.path.join(AGENT_PROMPTS_DIR, f"{agent_name}.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def list_agents():
    return [f[:-3] for f in os.listdir(AGENT_PROMPTS_DIR) if f.endswith(".md")]
