/* SentimentPro — main.js */

/* ── Dark Mode ─────────────────────────────────────────────── */
(function () {
  const saved = localStorage.getItem('sp-theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);
})();

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next    = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('sp-theme', next);
  const btn = document.getElementById('theme-btn');
  if (btn) btn.textContent = next === 'dark' ? '☀️' : '🌙';
}

/* ── Sentiment Analysis ─────────────────────────────────────── */
async function analyze() {
  const ta   = document.getElementById('review-ta');
  const btn  = document.getElementById('analyze-btn');
  const spin = document.getElementById('analyze-spin');
  const area = document.getElementById('result-area');
  const text = ta ? ta.value.trim() : '';
  if (!text) { showToast('Please enter some text to analyze.', 'warning'); return; }

  btn.disabled = true;
  if (spin) { spin.style.display = 'inline-block'; }
  btn.querySelector('.btn-txt').textContent = 'Analyzing…';

  try {
    const res  = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();
    if (data.error) { showToast(data.error, 'danger'); return; }
    renderResult(data);
    if (area) area.style.display = 'block';
  } catch (e) {
    showToast('Server error. Please try again.', 'danger');
  } finally {
    btn.disabled = false;
    if (spin) spin.style.display = 'none';
    btn.querySelector('.btn-txt').textContent = 'Analyze';
  }
}

function renderResult(data) {
  const s    = data.overall_sentiment;
  const conf = data.overall_confidence;
  const EMOJI = { positive: '😊', negative: '😞', neutral: '😐', mixed: '🔀' };
  const LABEL = { positive: 'Positive', negative: 'Negative', neutral: 'Neutral', mixed: 'Mixed' };

  /* Overall header */
  document.getElementById('res-emoji').textContent = EMOJI[s] || '😐';
  const lbl = document.getElementById('res-label');
  lbl.textContent = LABEL[s] || s;
  lbl.className   = `res-lbl rl-${s}`;
  document.getElementById('res-conf-txt').textContent = `${conf}% confidence`;
  const fill = document.getElementById('res-fill');
  fill.style.width = '0%';
  fill.className   = `conf-fill cf-${s}`;
  setTimeout(() => { fill.style.width = conf + '%'; }, 50);

  const hdr = document.getElementById('res-header');
  hdr.className = `res-header rh-${s}`;

  /* Distribution pills */
  const distBox = document.getElementById('dist-pills');
  if (distBox && data.distribution) {
    distBox.innerHTML = Object.entries(data.distribution)
      .sort((a, b) => b[1] - a[1])
      .map(([k, v]) => `<span class="dpill dp-${k === 'positive' ? 'pos' : k === 'negative' ? 'neg' : 'neu'}">${EMOJI[k] || ''} ${k}: ${v}%</span>`)
      .join('');
  }

  /* ABSA aspects */
  const grid = document.getElementById('absa-grid');
  if (grid && data.aspects) {
    grid.innerHTML = data.aspects.map(a => {
      const ac = a.sentiment;
      return `
        <div class="absa-row ar-${ac}">
          <span class="ar-emoji">${EMOJI[ac] || '😐'}</span>
          <div class="ar-body">
            <div class="ar-tags">
              <span class="ar-asp asp-${ac === 'positive' ? 'pos' : ac === 'negative' ? 'neg' : ac === 'mixed' ? 'mix' : 'neu'}">${a.aspect.toUpperCase()}</span>
              <span class="ar-sent ars-${ac}">${LABEL[ac] || ac}</span>
            </div>
            <div class="ar-clause" title="${escHtml(a.clause)}">"${escHtml(a.clause)}"</div>
          </div>
          <span class="ar-conf">${a.confidence}%</span>
        </div>`;
    }).join('');
  }
}

function clearAnalysis() {
  const ta = document.getElementById('review-ta');
  if (ta) ta.value = '';
  updateCharCount();
  const area = document.getElementById('result-area');
  if (area) area.style.display = 'none';
  if (ta) ta.focus();
}

/* ── Char counter ───────────────────────────────────────────── */
function updateCharCount() {
  const ta = document.getElementById('review-ta');
  const ct = document.getElementById('char-count');
  if (ta && ct) {
    const n = ta.value.length;
    ct.textContent = `${n} / 5000`;
    ct.style.color = n > 4500 ? 'var(--red)' : 'var(--txt3)';
  }
}

/* ── Toast ──────────────────────────────────────────────────── */
function showToast(msg, type = 'info') {
  const container = document.getElementById('toast-container') || createToastContainer();
  const t = document.createElement('div');
  const icons = { success: '✅', danger: '❌', warning: '⚠️', info: 'ℹ️' };
  t.className = `flash fl-${type}`;
  t.innerHTML = `<span>${icons[type] || ''}</span> ${escHtml(msg)}`;
  container.appendChild(t);
  setTimeout(() => t.remove(), 4000);
}
function createToastContainer() {
  const c = document.createElement('div');
  c.id = 'toast-container';
  c.style.cssText = 'position:fixed;top:1rem;right:1rem;z-index:9999;width:300px;display:flex;flex-direction:column;gap:.4rem';
  document.body.appendChild(c); return c;
}

/* ── Mobile sidebar ─────────────────────────────────────────── */
function toggleSidebar() {
  document.querySelector('.sidebar')?.classList.toggle('open');
}

/* ── Delete confirm ─────────────────────────────────────────── */
function confirmDelete(url, msg) {
  if (confirm(msg || 'Delete this item?')) window.location.href = url;
}

/* ── Word cloud ──────────────────────────────────────────────── */
async function loadWordCloud(containerId, sentiment) {
  try {
    const res  = await fetch('/wordcloud-data');
    const data = await res.json();
    const box  = document.getElementById(containerId);
    if (!box) return;
    const words = data[sentiment] || [];
    if (!words.length) { box.innerHTML = '<p class="txt-muted txt-sm" style="width:100%;text-align:center">Not enough data yet.</p>'; return; }
    const maxSize = Math.max(...words.map(w => w.size));
    box.innerHTML = words.map(w => {
      const size = Math.max(11, Math.round(11 + (w.size / maxSize) * 24));
      return `<span class="wc-w wc-${sentiment}" style="font-size:${size}px" title="${w.size} reviews">${w.text}</span>`;
    }).join('');
  } catch (e) {
    console.warn('Word cloud error:', e);
  }
}

/* ── Chart helpers (Chart.js) ────────────────────────────────── */
function getChartColors() {
  const dark = document.documentElement.getAttribute('data-theme') === 'dark';
  return {
    grid:  dark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)',
    text:  dark ? '#8fa3d4' : '#8892b8',
    pos:   '#059669', neg: '#dc2626', neu: '#d97706', mix: '#7c3aed',
    posA:  'rgba(5,150,105,.15)', negA: 'rgba(220,38,38,.15)',
    neuA:  'rgba(217,119,6,.15)',  mixA: 'rgba(124,58,237,.15)',
    indigo:'#6366f1', indigoA:'rgba(99,102,241,.15)',
  };
}

function makePieChart(canvasId, labels, values) {
  const ctx = document.getElementById(canvasId); if (!ctx) return;
  const c = getChartColors();
  return new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{ data: values, backgroundColor: [c.pos, c.neg, c.neu, c.mix],
                   borderWidth: 2, borderColor: 'transparent', hoverOffset: 8 }],
    },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: '65%',
      plugins: {
        legend: { position: 'bottom', labels: { color: c.text, font: { size: 12, family: "'DM Sans'" }, padding: 16 } },
        tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.raw}` } },
      },
    },
  });
}

function makeBarChart(canvasId, labels, values) {
  const ctx = document.getElementById(canvasId); if (!ctx) return;
  const c = getChartColors();
  return new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{ data: values, backgroundColor: [c.posA, c.negA, c.neuA, c.mixA],
                   borderColor: [c.pos, c.neg, c.neu, c.mix], borderWidth: 1.5, borderRadius: 8 }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: c.grid }, ticks: { color: c.text } },
        y: { grid: { color: c.grid }, ticks: { color: c.text, stepSize: 1 }, beginAtZero: true },
      },
    },
  });
}

function makeLineChart(canvasId, labels, values) {
  const ctx = document.getElementById(canvasId); if (!ctx) return;
  const c = getChartColors();
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Reviews',
        data: values,
        borderColor: c.indigo, backgroundColor: c.indigoA,
        borderWidth: 2, fill: true, tension: 0.4,
        pointBackgroundColor: c.indigo, pointRadius: 4, pointHoverRadius: 6,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: c.grid }, ticks: { color: c.text, maxTicksLimit: 7 } },
        y: { grid: { color: c.grid }, ticks: { color: c.text, stepSize: 1 }, beginAtZero: true },
      },
    },
  });
}

/* ── Utilities ──────────────────────────────────────────────── */
function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

/* ── Init ───────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  // Theme btn icon
  const btn = document.getElementById('theme-btn');
  if (btn) btn.textContent = document.documentElement.getAttribute('data-theme') === 'dark' ? '☀️' : '🌙';

  // Char counter
  const ta = document.getElementById('review-ta');
  if (ta) {
    ta.addEventListener('input', updateCharCount);
    // Ctrl+Enter submits
    ta.addEventListener('keydown', e => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') analyze();
    });
    updateCharCount();
  }

  // Auto-dismiss flash messages
  setTimeout(() => {
    document.querySelectorAll('.flash').forEach(f => f.remove());
  }, 5000);
});
