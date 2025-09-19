// Dynamically load agent menu items from backend

async function fetchAgents() {
  const res = await fetch('/api/agents');
  if (!res.ok) return [];
  return await res.json();
}

async function fetchTools() {
  const res = await fetch('/api/tools');
  if (!res.ok) return {};
  return await res.json();
}

async function populateSidebar() {
  const agentList = document.getElementById('agentList');
  const toolList = document.getElementById('toolList');
  // Agents
  if (agentList) {
    agentList.innerHTML = '';
    const agents = await fetchAgents();
    agents.forEach(agent => {
      const li = document.createElement('li');
      li.className = 'agent-subitem';
      li.innerHTML = `<a href="#" onclick="showDetails('agent', '${agent}')">${agent}</a>`;
      agentList.appendChild(li);
    });
  }
  // Tools (grouped by agent)
  if (toolList) {
    toolList.innerHTML = '';
    const tools = await fetchTools();
    Object.keys(tools).forEach(agent => {
      const agentHeader = document.createElement('li');
      agentHeader.className = 'tool-agent';
      agentHeader.textContent = agent;
      toolList.appendChild(agentHeader);
      tools[agent].forEach(func => {
        const li = document.createElement('li');
        li.className = 'tool-func';
        li.innerHTML = `<a href="#" onclick="showDetails('tool', '${agent}', '${func}')">${func}</a>`;
        toolList.appendChild(li);
      });
    });
  }
}

window.showDetails = async function(type, name, func) {
  if (type === 'agent') {
    const res = await fetch(`/api/agent/${name}`);
    if (res.ok) {
      const md = await res.text();
      document.getElementById('detailsTitle').textContent = name;
      document.getElementById('markdownInput').value = md;
      document.getElementById('markdownPreview').innerHTML = marked.parse(md);
    }
  } else if (type === 'tool') {
    const res = await fetch(`/api/tool/${name}/${func}`);
    if (res.ok) {
      const md = await res.text();
      document.getElementById('detailsTitle').textContent = `${name}/${func}`;
      document.getElementById('markdownInput').value = md;
      document.getElementById('markdownPreview').innerHTML = marked.parse(md);
    }
  }
};

document.addEventListener('DOMContentLoaded', populateSidebar);
