const data = JSON.parse(document.getElementById('site-data').textContent);
const projects = [...data.projectsC, ...data.projectsPython];
const grid = document.getElementById('projectGrid');
const count = document.getElementById('projectCount');
const search = document.getElementById('search');
const trackFilter = document.getElementById('trackFilter');
const dialog = document.getElementById('codeDialog');
const dialogTitle = document.getElementById('dialogTitle');
const dialogMeta = document.getElementById('dialogMeta');
const dialogCode = document.getElementById('dialogCode');

document.getElementById('closeDialog').addEventListener('click', () => dialog.close());

function esc(s='') { return String(s).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch])); }
function projectText(p){ return `${p.track} ${p.number} ${p.title} ${p.folder} ${p.file} ${p.language}`.toLowerCase(); }
function pillClass(track){ return track.startsWith('Python') ? 'pill python' : 'pill'; }
function renderProjects(){
  const q = search.value.trim().toLowerCase();
  const track = trackFilter.value;
  const shown = projects.filter(p => (track === 'all' || p.track === track) && (!q || projectText(p).includes(q)));
  count.textContent = `${shown.length} of ${projects.length} examples shown`;
  grid.innerHTML = shown.map((p, idx) => `
    <article class="card project">
      <div class="pillRow"><span class="${pillClass(p.track)}">${esc(p.track)}</span>${p.number ? `<span class="pill">${esc(p.number)}</span>` : ''}<span class="pill">${esc(p.language)}</span></div>
      <h3>${esc(p.title)}</h3>
      <p><code>${esc(p.folder)}</code></p>
      ${p.file ? `<p>Main file: <strong>${esc(p.file)}</strong></p>` : ''}
      <div class="actions">
        <a class="primary" href="${esc(p.docsUrl)}">Official docs</a>
        <a href="${esc(p.sourceUrl)}">Source</a>
        ${p.code ? `<button data-code-index="${projects.indexOf(p)}">Preview code</button>` : ''}
      </div>
    </article>`).join('');
}

grid.addEventListener('click', e => {
  const btn = e.target.closest('[data-code-index]');
  if (!btn) return;
  const p = projects[Number(btn.dataset.codeIndex)];
  dialogTitle.textContent = p.title;
  dialogMeta.textContent = `${p.track} · ${p.folder}/${p.file}`;
  dialogCode.textContent = p.code || 'No preview available.';
  dialog.showModal();
});

function renderList(id, items, max = 999){
  const el = document.getElementById(id);
  el.innerHTML = items.slice(0,max).map(item => `
    <div class="listItem">
      <a href="${esc(item.sourceUrl)}">${esc(item.name || item.title || item.file)}</a>
      <small>${esc(item.track || item.size || '')}${item.track && item.size ? ' · ' + esc(item.size) : ''}</small>
    </div>`).join('');
}

search.addEventListener('input', renderProjects);
trackFilter.addEventListener('change', renderProjects);
renderProjects();
renderList('libraries', data.libraries);
renderList('pdfs', data.pdfs);
