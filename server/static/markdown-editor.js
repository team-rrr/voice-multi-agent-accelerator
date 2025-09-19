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
if (saveBtn) {
  saveBtn.onclick = async function() {
    const title = document.getElementById('detailsTitle').textContent;
    const markdown = document.getElementById('markdownInput').value;
    if (!title || !markdown) return alert('Select an agent and enter markdown.');
    // Only save if title matches an agent name
    const res = await fetch(`/api/agent/${title}`, {
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
}
