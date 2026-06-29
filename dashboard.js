// Star Alliance Dashboard — data wiring
// Launch: node serve.cjs → http://localhost:4178/dashboard.html

async function boot() {
  try {
    const GUILD = await fetch('guild-data.json').then(r => r.json())
    window._GUILD_SKILLS = GUILD.skills || []
    window._GUILD_MEMBERS = GUILD.members || []
    window._GUILD_DOMAINS = GUILD.domains || []
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

function skillMemberCount(sid) {
  return (window._GUILD_MEMBERS || []).filter(m => (m.skills || []).includes(sid)).length
}

function skillDomainAccent(sid) {
  // returns {color, domainName} if the skill is specific to a project domain, else null
  const projectDomains = (window._GUILD_DOMAINS || []).filter(d => d.id !== 'star-alliance')
  for (const d of projectDomains) {
    if ((d.skills || []).includes(sid)) return { color: d.color || '#c9a227', domainName: d.name || '' }
  }
  return null
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

  const portraitWrap = document.createElement('div')
  portraitWrap.className = 'member-portrait-wrap'
  portraitWrap.appendChild(img)
  body.append(portraitWrap, info)
  article.append(topbar, body)

  const tooltip = document.createElement('div')
  tooltip.className = 'card-tooltip'
  tooltip.textContent = m.summary || m.description || ''
  portraitWrap.appendChild(tooltip)

  const strip = document.createElement('div')
  strip.className = 'member-skills-strip'
  const memberSkillIds = m.skills || []
  // sort skill ids alphabetically by display NAME (fallback to id)
  const sortedSkillIds = [...memberSkillIds].sort((a, b) => {
    const na = ((window._GUILD_SKILLS || []).find(s => s.id === a)?.name || a).toLowerCase()
    const nb = ((window._GUILD_SKILLS || []).find(s => s.id === b)?.name || b).toLowerCase()
    return na.localeCompare(nb)
  })
  // build a lookup of skill id -> skill object
  sortedSkillIds.forEach(sid => {
    const skillObj = (window._GUILD_SKILLS || []).find(s => s.id === sid)
    const thumb = document.createElement('div')
    thumb.className = 'skill-thumb'
    const count = skillMemberCount(sid)
    const lvl = skillObj?.level || ''
    const accent = skillDomainAccent(sid)
    if (accent) thumb.style.setProperty('--thumb-accent', accent.color)
    const img = document.createElement('img')
    img.src = `art/skill-art/${sid}.png`
    img.alt = skillObj?.name || sid
    img.onerror = function() {
      this.style.display = 'none'
      const fb = document.createElement('div')
      fb.style.cssText = 'width:100%;height:100%;display:flex;align-items:center;justify-content:center;font-size:1.1rem;'
      fb.textContent = skillObj?.icon || '⚔'
      thumb.insertBefore(fb, thumb.firstChild)
    }
    thumb.appendChild(img)
    const tip = document.createElement('div')
    tip.className = 'card-tooltip'
    const hl = accent ? accent.color : 'var(--gold)'
    tip.innerHTML = `<strong style="color:${hl}">${skillObj?.name || sid}</strong><br>${(skillObj?.blurb || '').slice(0, 120)}<br><span style="color:${hl};font-size:0.66rem">${count} member${count===1?'':'s'} · ${lvl}${accent ? ' · ' + accent.domainName : ''}</span>`
    thumb.appendChild(tip)
    strip.appendChild(thumb)
  })
  article.appendChild(strip)

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
  const grid = document.createElement('div')
  grid.className = 'workflow-icon-grid'
  ;(g.workflows || []).forEach(w => {
    const thumb = document.createElement('div')
    thumb.className = 'workflow-thumb'
    const img = document.createElement('img')
    img.src = `art/workflow-art/${w.id}.png`
    img.alt = w.name || ''
    img.onerror = function() {
      this.style.display = 'none'
      const fb = document.createElement('div')
      fb.style.cssText = 'width:100%;height:100%;display:flex;align-items:center;justify-content:center;font-size:1.4rem;'
      fb.textContent = w.icon || '⚙'
      thumb.insertBefore(fb, thumb.firstChild)
    }
    thumb.appendChild(img)
    const tip = document.createElement('div')
    tip.className = 'card-tooltip'
    const whenSnippet = w.when ? w.when.slice(0, 100) : ''
    const memberIds = [...new Set((w.steps||[]).map(s => s.actor).filter(a => a && a.startsWith('the-')))]
    const memberNames = memberIds.map(id => ((window._GUILD_MEMBERS||[]).find(m => m.id === id)?.name) || id).join(', ')
    tip.innerHTML = `<strong>${w.name || ''}</strong><br><em style='color:var(--gold);font-size:0.68rem'>${w.category||''}</em><br>${w.tagline || ''}${whenSnippet ? '<br><span style=opacity:.7>' + whenSnippet + '</span>' : ''}${memberNames ? '<br><span style="color:var(--gold);font-size:0.66rem">Members: ' + memberNames + '</span>' : ''}`
    thumb.appendChild(tip)
    grid.appendChild(thumb)
  })
  list.appendChild(grid)
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