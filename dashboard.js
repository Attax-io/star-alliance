// Star Alliance Dashboard — data wiring
// Launch: node serve.cjs → http://localhost:4178/dashboard.html

async function boot() {
  try {
    const GUILD = await fetch('guild-data.json').then(r => r.json())
    renderHeader(GUILD)
    renderStats(GUILD)
    renderRoster(GUILD)
    renderLog(GUILD)
    renderWorkflows(GUILD)
    renderDomains(GUILD)
    const fv = document.getElementById('footer-version')
    if (fv) fv.textContent = 'v' + (GUILD.meta.version || '4')
  } catch (err) {
    console.error('Dashboard boot failed:', err)
    const page = document.querySelector('.page')
    if (page) page.insertAdjacentHTML('afterbegin',
      '<p style="color:#c9a227;padding:2rem;font-family:monospace">⚠ Could not load guild-data.json — run: node serve.cjs</p>')
  }
}

function renderHeader(g) {
  const vEl = document.querySelector('.tag-version')
  if (vEl) vEl.textContent = 'v' + (g.meta?.version || '4')
  const dEl = document.querySelector('.tag-date')
  if (dEl && g.meta?.generated) {
    const d = new Date(g.meta.generated)
    dEl.textContent = d.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
  }
}

function renderStats(g) {
  const todayISO = (g.meta?.generated || '').slice(0, 10)
  const active = (g.log?.entries || []).filter(e => e.date === todayISO).length
  const map = {
    'stat-members':   g.meta?.counts?.members   ?? 0,
    'stat-skills':    g.meta?.counts?.skills     ?? 0,
    'stat-workflows': g.meta?.counts?.workflows  ?? 0,
    'stat-active':    active
  }
  Object.entries(map).forEach(([id, val]) => {
    const el = document.getElementById(id)
    if (el) el.textContent = val
  })
}

function renderRoster(g) {
  const grid = document.getElementById('member-grid')
  if (!grid) return
  grid.innerHTML = ''
  ;(g.members || []).forEach(m => grid.appendChild(memberCard(m)))
}

function memberCard(m) {
  const color = m.color || '#c9a227'
  const article = document.createElement('article')
  article.className = 'member-card'
  article.style.setProperty('--member-color', color)

  const topbar = document.createElement('div')
  topbar.className = 'member-card__topbar'

  const body = document.createElement('div')
  body.className = 'member-card__body'

  const img = document.createElement('img')
  img.className = 'member-card__portrait'
  img.src = `art/member-art/${m.id}.png`
  img.alt = m.name || ''
  img.onerror = function () {
    this.style.display = 'none'
    const initials = (m.name || 'M').split(' ').filter(w => w !== 'The').map(w => w[0]).join('')
    const mono = document.createElement('div')
    mono.className = 'member-card__monogram'
    mono.textContent = initials
    mono.style.cssText = `width:88px;height:88px;border-radius:10px;background:var(--surface-2);display:flex;align-items:center;justify-content:center;font-size:1.5rem;font-weight:600;color:${color};border:1px solid ${color}40;flex-shrink:0;`
    this.parentNode.insertBefore(mono, this)
  }

  const info = document.createElement('div')
  info.className = 'member-card__info'

  const h3 = document.createElement('h3')
  h3.className = 'member-card__name'
  h3.textContent = m.name || ''

  const role = document.createElement('p')
  role.className = 'member-card__meta'
  role.textContent = m.role || ''

  const statusDiv = document.createElement('div')
  statusDiv.className = 'member-card__status'
  const s = m.status || 'ready'
  statusDiv.innerHTML = `<span class="status-dot status-dot--${s}"></span><span class="status-text">${s.charAt(0).toUpperCase()+s.slice(1)}</span><span class="tier-pill"><span class="tier-mark">◆</span> ${m.conferred || ''}</span>`

  const metaRow = document.createElement('div')
  metaRow.className = 'member-card__meta-row'
  const skillCount = m.skills?.length ?? 0
  metaRow.innerHTML = `<span class="meta-chip"><span class="chip-glyph">⬡</span> ${m.model || ''}</span><span class="meta-chip">${skillCount} skills</span>`

  info.append(h3, role, statusDiv, metaRow)
  body.append(img, info)
  article.append(topbar, body)
  return article
}

function renderLog(g) {
  const list = document.getElementById('log-list')
  if (!list) return
  list.innerHTML = ''
  ;(g.log?.entries || []).slice(0, 8).forEach(e => {
    const li = document.createElement('li')
    li.className = 'log-entry'
    li.innerHTML = `<span class="log-dot"></span><div class="log-body"><div class="log-meta"><span class="log-date">${e.date||''}</span><span class="log-tag tag-${e.type||'chore'}">${e.type||''}</span><span class="log-actor">${e.who||''}</span></div><div class="log-title">${e.title||''}</div></div>`
    list.appendChild(li)
  })
}

function renderWorkflows(g) {
  const list = document.getElementById('workflow-list')
  if (!list) return
  list.innerHTML = ''
  const cats = {}
  ;(g.workflows || []).forEach(w => {
    const c = w.category || 'Other'
    cats[c] = (cats[c] || 0) + 1
  })
  Object.keys(cats).sort().forEach(cat => {
    const li = document.createElement('li')
    li.className = 'workflow-row'
    li.innerHTML = `<span class="workflow-name">${cat}</span><span class="workflow-count">${cats[cat]}</span>`
    list.appendChild(li)
  })
}

function renderDomains(g) {
  const grid = document.getElementById('domain-grid')
  if (!grid) return
  grid.innerHTML = ''
  ;(g.domains || []).forEach(d => {
    const card = document.createElement('div')
    card.className = 'domain-card'
    card.style.setProperty('--domain-color', d.color || '#c9a227')
    const skillCount = d.skills?.length ?? 0
    card.innerHTML = `<div class="domain-card__strip"></div><div class="domain-card__body"><h3 class="domain-card__name">${d.name||''}</h3><p class="domain-card__tagline">${d.tagline||''}</p><p class="domain-card__count">${skillCount} skills</p></div>`
    grid.appendChild(card)
  })
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot)
} else {
  boot()
}