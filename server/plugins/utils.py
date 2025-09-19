import os


AGENT_PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "agent_prompts")
AGENTS_DIR = os.path.join(AGENT_PROMPTS_DIR, "agents")
TOOLS_DIR = os.path.join(AGENT_PROMPTS_DIR, "tools")

def list_agent_prompts():
    # List agent markdown files in agents/
    return [f[:-3] for f in os.listdir(AGENTS_DIR) if f.endswith(".md")]

def list_tool_prompts():
    # List all tool prompts as {agent}/{function}
    result = {}
    for agent in os.listdir(TOOLS_DIR):
        agent_dir = os.path.join(TOOLS_DIR, agent)
        if os.path.isdir(agent_dir):
            result[agent] = [f[:-3] for f in os.listdir(agent_dir) if f.endswith(".md")]
    return result

def load_agent_prompt(agent_name):
    path = os.path.join(AGENTS_DIR, f"{agent_name}.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def load_tool_prompt(agent_name, function_name):
    path = os.path.join(TOOLS_DIR, agent_name, f"{function_name}.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""
