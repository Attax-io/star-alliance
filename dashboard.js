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
    renderModelControl()
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
// Usage-based numeric level + version, one shared formatter for every card
// type (member / skill / workflow / domain). `item` carries {level, version,
// neverInvoked} as stamped by build.py's stamp_xp(). Never-invoked items
// (level 1, 0 XP) get a distinct "new" marker so they're visually findable.
function levelVersionLabel(item) {
  const lvl = item?.level
  const ver = item?.version
  const parts = []
  if (lvl != null) parts.push(`Level ${lvl}`)
  if (ver) parts.push(`v${ver}`)
  return parts.join(' · ')
}

function levelPillHTML(item, extraClass) {
  const label = levelVersionLabel(item)
  if (!label) return ''
  const neverCls = item?.neverInvoked ? ' tier-pill--new' : ''
  const cls = `tier-pill${extraClass ? ' ' + extraClass : ''}${neverCls}`
  const mark = item?.neverInvoked ? '✦' : '◆'
  return `<span class="${cls}"><span class="tier-mark">${mark}</span> ${label}</span>`
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

let BRAIN_OPTIONS = []
let DOER_OPTIONS = []
let _modelListsLoaded = false
let _modelListsPromise = null

function loadModelLists() {
  // /api/model-lists derives brains/doers from models.json — single source of truth.
  // brains = models with backend === 'claude'; doers = models with role === 'doer'.
  if (_modelListsPromise) return _modelListsPromise
  _modelListsPromise = fetch('/api/model-lists')
    .then(r => r.json())
    .then(lists => {
      BRAIN_OPTIONS = (lists.brains || []).map(id => ({ value: id, label: id }))
      DOER_OPTIONS  = (lists.doers  || []).map(id => ({ value: id, label: id }))
      _modelListsLoaded = true
    })
    .catch(err => {
      console.error('Failed to load /api/model-lists:', err)
      BRAIN_OPTIONS = []
      DOER_OPTIONS  = []
      _modelListsLoaded = true  // unblock render so the user sees an error in the UI rather than a blank control
    })
  return _modelListsPromise
}

function makeSelect(opts, current) {
  const sel = document.createElement('select')
  sel.className = 'model-row__select'
  const blank = document.createElement('option')
  blank.value = ''
  blank.textContent = '—'
  sel.appendChild(blank)
  opts.forEach(o => {
    const op = document.createElement('option')
    op.value = o.value
    op.textContent = o.label
    sel.appendChild(op)
  })
  sel.value = current || ''
  return sel
}

function showRowStatus(span, text, kind) {
  span.textContent = text
  span.className = 'model-row__status visible ' + (kind || '')
  clearTimeout(span._t)
  span._t = setTimeout(() => { span.className = 'model-row__status' }, 2000)
}

async function saveOverride(memberId, brainSel, doerSel, statusSpan, btn) {
  const brain = brainSel.value
  const doer = doerSel.value
  if (!brain || !doer) {
    showRowStatus(statusSpan, 'Select both', 'error')
    return
  }
  btn.disabled = true
  try {
    const resp = await fetch('/api/model-override', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ memberId, brain, doer })
    })
    if (!resp.ok) {
      let msg = 'Save failed'
      try { const j = await resp.json(); if (j.error) msg = j.error } catch {}
      showRowStatus(statusSpan, msg, 'error')
    } else {
      showRowStatus(statusSpan, '✓ Saved', 'saved')
    }
  } catch (err) {
    showRowStatus(statusSpan, 'Network error', 'error')
  } finally {
    btn.disabled = false
  }
}

async function renderModelControl() {
  const grid = document.getElementById('model-control-grid')
  if (!grid) return
  grid.innerHTML = ''

  const members = window._GUILD_MEMBERS || []
  if (!members.length) return

  // Pull brains/doers from the registry-derived endpoint before rendering rows.
  await loadModelLists()

  let overrides = {}
  fetch('/api/model-override').then(r => r.json()).then(data => {
    overrides = data || {}
    members.forEach(m => {
      const row = grid.querySelector(`[data-mid="${CSS.escape(m.id)}"]`)
      if (!row) return
      const ov = overrides[m.id]
      if (ov) {
        row._brainSel.value = ov.brain || ''
        row._doerSel.value = ov.doer || ''
      }
    })
  }).catch(() => {})

  members.forEach(m => {
    const row = document.createElement('div')
    row.className = 'model-row'
    row.dataset.mid = m.id

    const name = document.createElement('span')
    name.className = 'model-row__name'
    name.textContent = m.name || m.id

    const brainSel = makeSelect(BRAIN_OPTIONS, '')
    const doerSel = makeSelect(DOER_OPTIONS, '')

    const statusSpan = document.createElement('span')
    statusSpan.className = 'model-row__status'

    const btn = document.createElement('button')
    btn.className = 'model-row__save'
    btn.textContent = 'Save'
    btn.addEventListener('click', () => saveOverride(m.id, brainSel, doerSel, statusSpan, btn))

    row._brainSel = brainSel
    row._doerSel = doerSel
    row.append(name, brainSel, doerSel, btn, statusSpan)
    grid.appendChild(row)
  })
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
  img.src = `art/member-art-thumb/${m.id}.png`
  img.alt = m.name || ''
  img.loading = 'lazy'
  img.decoding = 'async'
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
  statusDiv.innerHTML = `<span class="status-dot status-dot--${s}"></span><span class="status-text">${s.charAt(0).toUpperCase()+s.slice(1)}</span>${levelPillHTML(m)}`

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
  const memberLevelLine = levelVersionLabel(m)
  tooltip.innerHTML = `${(m.summary || m.description || '')}${memberLevelLine ? '<br><span style="color:var(--gold);font-size:0.66rem">' + memberLevelLine + (m.neverInvoked ? ' · never invoked' : '') + '</span>' : ''}`
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
    thumb.className = 'skill-thumb' + (skillObj?.neverInvoked ? ' skill-thumb--new' : '')
    const count = skillMemberCount(sid)
    const levelVerLine = levelVersionLabel(skillObj)
    const accent = skillDomainAccent(sid)
    if (accent) thumb.style.setProperty('--thumb-accent', accent.color)
    const img = document.createElement('img')
    img.src = `art/skill-art-thumb/${sid}.png`
    img.alt = skillObj?.name || sid
    img.loading = 'lazy'
    img.decoding = 'async'
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
    tip.innerHTML = `<strong style="color:${hl}">${skillObj?.name || sid}</strong><br>${(skillObj?.blurb || '').slice(0, 120)}<br><span style="color:${hl};font-size:0.66rem">${count} member${count===1?'':'s'}${levelVerLine ? ' · ' + levelVerLine : ''}${skillObj?.neverInvoked ? ' · never invoked' : ''}${accent ? ' · ' + accent.domainName : ''}</span>`
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
    thumb.className = 'workflow-thumb' + (w.neverInvoked ? ' workflow-thumb--new' : '')
    const img = document.createElement('img')
    img.src = `art/workflow-art-thumb/${w.id}.png`
    img.alt = w.name || ''
    img.loading = 'lazy'
    img.decoding = 'async'
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
    const wfLevelLine = levelVersionLabel(w)
    tip.innerHTML = `<strong>${w.name || ''}</strong><br><em style='color:var(--gold);font-size:0.68rem'>${w.category||''}</em><br>${w.tagline || ''}${whenSnippet ? '<br><span style=opacity:.7>' + whenSnippet + '</span>' : ''}${memberNames ? '<br><span style="color:var(--gold);font-size:0.66rem">Members: ' + memberNames + '</span>' : ''}${wfLevelLine ? '<br><span style="color:var(--gold);font-size:0.66rem">' + wfLevelLine + (w.neverInvoked ? ' · never invoked' : '') + '</span>' : ''}`
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
    const versionBadge = d.version
      ? `<span class="tier-pill domain-card__version"><span class="tier-mark">◆</span> v${d.version}</span>`
      : ''
    card.innerHTML = `<div class="domain-card__strip"></div><div class="domain-card__body"><div class="domain-card__title-row"><h3 class="domain-card__name">${d.name||''}</h3>${versionBadge}</div><p class="domain-card__tagline">${d.tagline||''}</p><p class="domain-card__count">${skillCount} skills</p></div>`
    grid.appendChild(card)

    if (d.version) {
      const history = (d.versionHistory || []).slice(-10).reverse()
      const tip = document.createElement('div')
      tip.className = 'card-tooltip'
      const rows = history.map(h => {
        const label = h.version ? `v${h.version}` : (h.slug || '')
        const detail = h.slug && h.version ? h.slug : (h.date || '')
        return `<div>${label}${detail ? ' <span style="opacity:.6">' + detail + '</span>' : ''}</div>`
      }).join('')
      tip.innerHTML = `<strong style="color:var(--gold)">${d.name||''} — v${d.version}</strong><br><span style="font-size:0.66rem;opacity:.75">${d.versionSource||''}</span>${rows ? '<div style="margin-top:6px;font-size:0.66rem">' + rows + '</div>' : ''}`
      card.appendChild(tip)
    }
  })
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot)
} else {
  boot()
}