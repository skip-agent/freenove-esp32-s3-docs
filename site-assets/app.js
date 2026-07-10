/* ===========================================================================
   TinySkiff ESP32-S3 Lab · landing behaviour
   The landing is course-forward: the hero voyage instrument reflects course
   progress from localStorage (the same store the course pages write), and the
   reference Library below is a searchable browser over every official example,
   with a "Taught in Day N" cross-link on the sketches a course day covers.
   =========================================================================== */

function readJSON(id) {
  const el = document.getElementById(id);
  if (!el) return null;
  try { return JSON.parse(el.textContent); } catch { return null; }
}

const data = readJSON('site-data') || {};
const course = readJSON('landing-course') || {};
const projects = [...(data.projectsC || []), ...(data.projectsPython || [])];

const grid = document.getElementById('projectGrid');
const count = document.getElementById('projectCount');
const search = document.getElementById('search');
const trackFilter = document.getElementById('trackFilter');
const dialog = document.getElementById('codeDialog');
const dialogTitle = document.getElementById('dialogTitle');
const dialogMeta = document.getElementById('dialogMeta');
const dialogCode = document.getElementById('dialogCode');

document.getElementById('closeDialog').addEventListener('click', () => dialog.close());
// backdrop click closes
dialog.addEventListener('click', (e) => { if (e.target === dialog) dialog.close(); });

function esc(s = '') {
  return String(s).replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
}
function projectText(p) { return `${p.track} ${p.number} ${p.title} ${p.folder} ${p.file} ${p.language}`.toLowerCase(); }
function trackShort(track) { return track.startsWith('Python') ? 'MicroPython' : 'C / Arduino'; }

function taughtLink(p) {
  const d = p.taughtInDay;
  if (!d) return '';
  return `<a class="proj-taught" href="./course/${esc(d.slug)}/">Taught in Day ${esc(d.day)} · ${esc(d.title)} →</a>`;
}

function renderProjects() {
  const q = search.value.trim().toLowerCase();
  const track = trackFilter.value;
  const shown = projects.filter(p => (track === 'all' || p.track === track) && (!q || projectText(p).includes(q)));
  count.textContent = `${shown.length} of ${projects.length} examples`;
  grid.innerHTML = shown.map(p => `
    <article class="proj-card">
      <div class="proj-pills">
        <span class="proj-pill ${p.track.startsWith('Python') ? 'is-py' : 'is-c'}">${esc(trackShort(p.track))}</span>
        ${p.number ? `<span class="proj-pill is-num">${esc(p.number)}</span>` : ''}
      </div>
      <h3>${esc(p.title)}</h3>
      <p class="proj-path mono">${esc(p.folder)}</p>
      ${taughtLink(p)}
      <div class="proj-actions">
        <a class="pa-primary" href="${esc(p.docsUrl)}">Official docs →</a>
        <a class="pa-ghost" href="${esc(p.sourceUrl)}">Source</a>
        ${p.code ? `<button class="pa-ghost" data-code-index="${projects.indexOf(p)}">Preview</button>` : ''}
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

function renderList(id, items, max = 999) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = items.slice(0, max).map(item => `
    <div class="res-item">
      <a href="${esc(item.sourceUrl)}">${esc(item.name || item.title || item.file)}</a>
      <small class="mono">${esc(item.track || item.size || '')}${item.track && item.size ? ' · ' + esc(item.size) : ''}</small>
    </div>`).join('');
}

search.addEventListener('input', renderProjects);
trackFilter.addEventListener('change', renderProjects);
renderProjects();
renderList('libraries', data.libraries || []);
renderList('pdfs', data.pdfs || []);

/* --------------------------------------------------------------------------
   Voyage progress instrument — mirrors the course store (localStorage).
   Same keys the course pages write: `tinyskiff.day.N` (with .done) + resume.
   -------------------------------------------------------------------------- */
const store = {
  isDone(day) {
    try { return (JSON.parse(localStorage.getItem(`tinyskiff.day.${day}`)) || {}).done === true; }
    catch { return false; }
  },
  getResume() {
    try { const r = localStorage.getItem('tinyskiff.resume'); return r ? Number(r) : null; }
    catch { return null; }
  },
};

(function reflectVoyage() {
  const total = course.total || 0;
  if (!total) return;
  const days = course.publishedDays || [];
  const slugs = course.slugs || {};
  const doneSet = new Set(days.filter(d => store.isDone(d)));
  const done = doneSet.size;

  const doneCount = document.getElementById('doneCount');
  if (doneCount) doneCount.textContent = String(done);

  // One pip per day of the voyage — filled for days logged, outlined for the
  // next unlogged day. A friendly, meaningful tracker rather than a gauge.
  const voyage = document.getElementById('mapVoyage');
  if (voyage) {
    const resumeDay = store.getResume();
    voyage.textContent = '';
    for (let d = 1; d <= total; d++) {
      const pip = document.createElement('span');
      pip.className = 'pip';
      if (doneSet.has(d)) pip.classList.add('is-done');
      else if (d === resumeDay) pip.classList.add('is-next');
      pip.title = `Day ${d}`;
      voyage.appendChild(pip);
    }
  }

  const resume = store.getResume();
  const resumeLink = document.getElementById('mapResume');
  const firstRun = document.getElementById('firstRun');
  if (resume && slugs[resume]) {
    if (resumeLink) {
      resumeLink.hidden = false;
      resumeLink.href = `./course/${slugs[resume]}/`;
      resumeLink.textContent = `Resume — Day ${resume} →`;
    }
    if (firstRun) firstRun.hidden = true;
  } else if (done > 0 && firstRun) {
    firstRun.textContent = `${done} of ${total} days logged. Pick up any day from the map.`;
  }
})();
