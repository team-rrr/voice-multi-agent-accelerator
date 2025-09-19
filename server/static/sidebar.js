// Dynamically load agent menu items from backend
async function fetchAgents() {
  const res = await fetch('/api/agents');
  if (!res.ok) return [];
  return await res.json();
}

async function populateSidebar() {
  const agentList = document.getElementById('agentList');
  const toolList = document.getElementById('toolList');
  if (agentList) {
    agentList.innerHTML = '';
    const agents = await fetchAgents();
    agents.forEach(agent => {
      const li = document.createElement('li');
      li.innerHTML = `<a href="#" onclick="showDetails('agent', '${agent}')">${agent}</a>`;
      agentList.appendChild(li);
    });
  }
  // ...existing code for tools...
}

window.showDetails = async function(type, name) {
  if (type === 'agent') {
    const res = await fetch(`/api/agent/${name}`);
    if (res.ok) {
      const md = await res.text();
      document.getElementById('detailsTitle').textContent = name;
      document.getElementById('markdownInput').value = md;
      document.getElementById('markdownPreview').innerHTML = marked.parse(md);
    }
  }
  // ...existing code for tools...
};

document.addEventListener('DOMContentLoaded', populateSidebar);
