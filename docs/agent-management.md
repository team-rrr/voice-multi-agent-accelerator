# Voice Multi-Agent Accelerator: Agent Management UI & File Structure

## Goal
Imitate AI Foundry's agent management experience by adding CRUD (Create, Read, Update, Delete) pages for agents. Agents can be managed in the UI and used in the conversation page.

---

## Proposed File System Structure

```
c:\Users\pconnelly\source\repos\hack2025\voice-multi-agent-accelerator-curr\
│
├── server\
│   ├── app_voice_live.py
│   ├── orchestrator.py
│   ├── plugins.py
│   ├── voice_live_handler.py
│   ├── agents\                # NEW: Python agent definitions (CRUD backend)
│   │   ├── __init__.py
│   │   ├── agent_model.py     # Agent data model
│   │   ├── agent_store.py     # CRUD logic for agents
│   │   └── ...
│   └── ...
│
├── server\static\
│   ├── audio-processor.js
│   ├── voice_test.html        # Conversation UI
│   ├── agents.html            # NEW: Agent CRUD UI
│   ├── agent_form.html        # NEW: Create/Edit agent UI
│   ├── agents.js              # NEW: Frontend logic for agent CRUD
│   └── ...
│
├── docs\
│   └── agent-management.md    # NEW: This design doc
│
└── ...
```

---

## UI Pages & Features

### 1. Agent List Page (`agents.html`)
- Table of all agents (name, type, description, status)
- Buttons: Create, Edit, Delete
- Search/filter agents

### 2. Agent Form Page (`agent_form.html`)
- Form for creating or editing an agent
- Fields: Name, Type, Description, Parameters, Status
- Save/Cancel buttons

### 3. Conversation Page (`voice_test.html`)
- Select agent(s) to use in conversation
- Agents loaded dynamically from backend

---

## Backend API Endpoints (Python)
- `GET /api/agents`         → List all agents
- `POST /api/agents`        → Create new agent
- `GET /api/agents/{id}`    → Get agent details
- `PUT /api/agents/{id}`    → Update agent
- `DELETE /api/agents/{id}` → Delete agent

---

## Data Model Example (`agent_model.py`)
```python
class Agent:
    def __init__(self, id, name, type, description, parameters, status):
        self.id = id
        self.name = name
        self.type = type
        self.description = description
        self.parameters = parameters
        self.status = status
```

---

## Workflow
1. User manages agents in the CRUD UI (create, edit, delete).
2. Agents are stored in backend (file/db).
3. Conversation page loads available agents for selection/use.
4. Selected agent(s) are used in orchestration logic for conversations.

---

## Next Steps
- Implement backend agent CRUD logic and API endpoints.
- Build agent management UI pages.
- Integrate agent selection into conversation flow.
