// Simple markdown editor/viewer
// Requires marked.js (add CDN in manage.html if needed)
function updatePreview() {
  const input = document.getElementById('markdownInput');
  const preview = document.getElementById('markdownPreview');
  if (input && preview) {
    preview.innerHTML = marked.parse(input.value);
  }
}
document.getElementById('markdownInput').addEventListener('input', updatePreview);
// Initial render
updatePreview();

// Save markdown functionality for manage.html
const saveBtn = document.getElementById('saveMarkdownBtn');
function showMessageBar(msg, success=true) {
  const bar = document.getElementById('messageBar');
  if (!bar) return;
  bar.textContent = msg;
  bar.style.display = 'block';
  if (success) {
    bar.style.background = 'linear-gradient(90deg, #f6fef8 80%, #d1fae5 100%)';
    bar.style.color = '#198754';
    bar.style.borderBottom = '1px solid #a7f3d0';
  } else {
    bar.style.background = 'linear-gradient(90deg, #fff1f2 80%, #fecaca 100%)';
    bar.style.color = '#b91c1c';
    bar.style.borderBottom = '1px solid #ef4444';
  }
  bar.style.fontSize = '1rem';
  bar.style.fontWeight = '500';
  bar.style.boxShadow = '0 2px 8px #0001';
  setTimeout(() => { bar.style.display = 'none'; }, 2000);
}

if (saveBtn) {
  saveBtn.onclick = async function() {
    const title = document.getElementById('detailsTitle').textContent;
    const markdown = document.getElementById('markdownInput').value;
    if (!title || !markdown) {
      showMessageBar('Select an agent and enter markdown.', false);
      return;
    }
    // Determine if saving agent or tool prompt
    let res;
    if (title.includes('/')) {
      // Tool prompt: title is Agent/Function
      const [agent, func] = title.split('/');
      res = await fetch(`/api/tool/${agent}/${func}`, {
        method: 'POST',
        headers: {'Content-Type': 'text/plain'},
        body: markdown
      });
    } else {
      // Agent prompt
      res = await fetch(`/api/agent/${title}`, {
        method: 'POST',
        headers: {'Content-Type': 'text/plain'},
        body: markdown
      });
    }
    if (res.ok) {
      showMessageBar('Saved!', true);
    } else {
      showMessageBar('Error saving markdown', false);
    }
  };
}
