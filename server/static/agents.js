// Simple frontend logic for agent CRUD (no backend yet)

let agents = [];
let editingAgent = null;
let editingFunction = null;


async function renderAgents() {
  const tbody = document.querySelector('#agentsTable tbody');
  tbody.innerHTML = '';
  const search = document.getElementById('searchInput').value.toLowerCase();
  // Fetch agents from backend
  const res = await fetch('/api/agents');
  agents = await res.json();
  agents.filter(a => a.name.toLowerCase().includes(search)).forEach((agent, idx) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${agent.name}</td>
      <td>${agent.module}</td>
      <td>${agent.functions.map(f => `<div><b>${f.name}</b>: ${f.description} <button onclick="editFunction(${idx}, '${f.name}')">Edit Prompt</button></div>`).join('')}</td>
      <td>-</td>
      <td>
        <button onclick="deleteAgent(${idx})">Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}


function showModal(edit = false, agent = null, func = null) {
  document.getElementById('agentFormModal').style.display = 'block';
  document.getElementById('formTitle').textContent = edit ? `Edit Prompt: ${func ? func : ''}` : 'Create Agent';
  editingAgent = agent;
  editingFunction = func;
}
function closeModal() {
  document.getElementById('agentFormModal').style.display = 'none';
  editingAgent = null;
  editingFunction = null;
  document.getElementById('agentForm').reset();
  document.getElementById('agentMarkdown').value = '';
}


document.getElementById('createAgentBtn').onclick = () => {
  showModal(false);
};
document.getElementById('closeModal').onclick = closeModal;
document.getElementById('cancelBtn').onclick = closeModal;
document.getElementById('searchInput').oninput = renderAgents;

document.getElementById('agentForm').onsubmit = function(e) {
  e.preventDefault();
  const name = document.getElementById('agentName').value;
  const type = document.getElementById('agentType').value;
  const description = document.getElementById('agentDescription').value;
  const parameters = document.getElementById('agentParameters').value;
  const status = document.getElementById('agentStatus').value;
  if (editingId) {
    const agent = agents.find(a => a.id === editingId);
    agent.name = name;
    agent.type = type;
    agent.description = description;
    agent.parameters = parameters;
    agent.status = status;
  } else {
    agents.push({
      id: Date.now(),
      name, type, description, parameters, status
    });
  }
  closeModal();
  renderAgents();
};

window.editFunction = async function(agentIdx, funcName) {
  const agent = agents[agentIdx];
  showModal(true, agent, funcName);
  // Fetch markdown for this agent function
  try {
    const res = await fetch(`/api/agent/${agent.name}_${funcName}`);
    if (res.ok) {
      document.getElementById('agentMarkdown').value = await res.text();
    } else {
      document.getElementById('agentMarkdown').value = '';
    }
  } catch {
    document.getElementById('agentMarkdown').value = '';
  }
};
// Save markdown to backend

document.getElementById('saveMarkdownBtn').onclick = async function() {
  if (!editingAgent || !editingFunction) return alert('Select an agent function to edit');
  const markdown = document.getElementById('agentMarkdown').value;
  const res = await fetch(`/api/agent/${editingAgent.name}_${editingFunction}`, {
    method: 'POST',
    headers: {'Content-Type': 'text/plain'},
    body: markdown
  });
  if (res.ok) {
    alert('Markdown saved!');
  } else {
    alert('Failed to save markdown');
  }
};


window.deleteAgent = function(idx) {
  agents.splice(idx, 1);
  renderAgents();
};


renderAgents();
