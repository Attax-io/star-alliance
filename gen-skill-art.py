#!/usr/bin/env python3
"""
Generate 48x48 Fallen Sword-themed SVG icons for each skill.
Patches the 'art' field in guild-data.json.
"""
import json, re

# Each SVG is 48x48 viewBox, dark fantasy RPG icon style.
# Colors: dark bg (#0d0a0e), gold accent (#c8a84b), red (#8b1a1a),
# teal (#1a6b6b), purple (#4a1a6b), silver (#8090a0), green (#1a5c1a)

ARTS = {

"article-creator": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#c8a84b" stroke-width="1"/>
  <!-- scroll -->
  <rect x="10" y="8" width="20" height="28" rx="2" fill="#2a1e0e" stroke="#c8a84b" stroke-width="0.8"/>
  <rect x="10" y="8" width="20" height="5" rx="2" fill="#3a2a10"/>
  <!-- lines of text -->
  <line x1="13" y1="17" x2="27" y2="17" stroke="#c8a84b" stroke-width="1" opacity="0.7"/>
  <line x1="13" y1="21" x2="27" y2="21" stroke="#c8a84b" stroke-width="1" opacity="0.5"/>
  <line x1="13" y1="25" x2="24" y2="25" stroke="#c8a84b" stroke-width="1" opacity="0.5"/>
  <line x1="13" y1="29" x2="27" y2="29" stroke="#c8a84b" stroke-width="1" opacity="0.4"/>
  <!-- quill -->
  <line x1="28" y1="30" x2="40" y2="12" stroke="#c8a84b" stroke-width="1.2"/>
  <path d="M28 30 Q30 25 35 18 Q32 22 28 30Z" fill="#c8a84b" opacity="0.6"/>
  <!-- corner runes -->
  <text x="5" y="10" font-size="5" fill="#c8a84b" opacity="0.5">✦</text>
  <text x="39" y="45" font-size="5" fill="#c8a84b" opacity="0.5">✦</text>
</svg>""",

"brandkit": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#c8a84b" stroke-width="1"/>
  <!-- shield -->
  <path d="M24 8 L36 13 L36 24 Q36 35 24 41 Q12 35 12 24 L12 13 Z" fill="#1a1020" stroke="#c8a84b" stroke-width="1.2"/>
  <!-- inner shield glow -->
  <path d="M24 12 L33 16 L33 24 Q33 32 24 37 Q15 32 15 24 L15 16 Z" fill="none" stroke="#c8a84b" stroke-width="0.6" opacity="0.5"/>
  <!-- crown symbol -->
  <path d="M18 22 L20 18 L24 22 L28 18 L30 22 L30 26 L18 26 Z" fill="#c8a84b" opacity="0.9"/>
  <rect x="18" y="26" width="12" height="2" rx="1" fill="#c8a84b" opacity="0.7"/>
  <!-- corner dots -->
  <circle cx="6" cy="6" r="1.5" fill="#c8a84b" opacity="0.4"/>
  <circle cx="42" cy="6" r="1.5" fill="#c8a84b" opacity="0.4"/>
  <circle cx="6" cy="42" r="1.5" fill="#c8a84b" opacity="0.4"/>
  <circle cx="42" cy="42" r="1.5" fill="#c8a84b" opacity="0.4"/>
</svg>""",

"bug-fix-workflow": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#8b1a1a" stroke-width="1"/>
  <!-- crossed swords (bug battle) -->
  <line x1="12" y1="12" x2="36" y2="36" stroke="#8b3030" stroke-width="2.5"/>
  <line x1="36" y1="12" x2="12" y2="36" stroke="#8b3030" stroke-width="2.5"/>
  <!-- sword hilts -->
  <rect x="10" y="10" width="5" height="2" rx="1" fill="#c8a84b" transform="rotate(-45 12 12)"/>
  <rect x="33" y="10" width="5" height="2" rx="1" fill="#c8a84b" transform="rotate(45 36 12)"/>
  <!-- center impact glyph -->
  <circle cx="24" cy="24" r="5" fill="#1a0808" stroke="#8b1a1a" stroke-width="1"/>
  <text x="24" y="27.5" font-size="7" text-anchor="middle" fill="#c8a84b">✕</text>
  <!-- sparks -->
  <circle cx="24" cy="14" r="1.5" fill="#ff6060" opacity="0.8"/>
  <circle cx="34" cy="24" r="1.5" fill="#ff6060" opacity="0.8"/>
  <circle cx="14" cy="24" r="1.5" fill="#ff6060" opacity="0.8"/>
  <circle cx="24" cy="34" r="1.5" fill="#ff6060" opacity="0.8"/>
</svg>""",

"cleanup": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#8090a0" stroke-width="1"/>
  <!-- broom handle -->
  <line x1="14" y1="10" x2="34" y2="40" stroke="#6a4a20" stroke-width="2.5"/>
  <!-- broom head -->
  <path d="M26 34 Q34 30 38 36 Q34 42 26 40 Z" fill="#8090a0" stroke="#c8a84b" stroke-width="0.8"/>
  <!-- sparkle trails -->
  <circle cx="18" cy="18" r="1.5" fill="#c8a84b" opacity="0.7"/>
  <circle cx="14" cy="26" r="1" fill="#c8a84b" opacity="0.5"/>
  <circle cx="20" cy="30" r="1" fill="#c8a84b" opacity="0.4"/>
  <!-- dust motes -->
  <circle cx="36" cy="16" r="1.5" fill="#8090a0" opacity="0.4"/>
  <circle cx="32" cy="12" r="1" fill="#8090a0" opacity="0.3"/>
  <!-- corner rune -->
  <text x="5" y="10" font-size="5" fill="#8090a0" opacity="0.5">✦</text>
  <text x="39" y="45" font-size="5" fill="#8090a0" opacity="0.5">✦</text>
</svg>""",

"codex-law-translate": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#c8a84b" stroke-width="1"/>
  <!-- book -->
  <rect x="8" y="10" width="32" height="28" rx="2" fill="#1a1020" stroke="#c8a84b" stroke-width="0.8"/>
  <line x1="24" y1="10" x2="24" y2="38" stroke="#c8a84b" stroke-width="0.8" opacity="0.6"/>
  <!-- scales of justice -->
  <line x1="24" y1="14" x2="24" y2="22" stroke="#c8a84b" stroke-width="1"/>
  <line x1="16" y1="22" x2="32" y2="22" stroke="#c8a84b" stroke-width="1"/>
  <circle cx="16" cy="26" r="3" fill="none" stroke="#c8a84b" stroke-width="0.8"/>
  <circle cx="32" cy="26" r="3" fill="none" stroke="#c8a84b" stroke-width="0.8"/>
  <!-- rune text lines -->
  <line x1="12" y1="32" x2="22" y2="32" stroke="#c8a84b" stroke-width="0.7" opacity="0.5"/>
  <line x1="26" y1="32" x2="36" y2="32" stroke="#c8a84b" stroke-width="0.7" opacity="0.5"/>
  <line x1="12" y1="35" x2="20" y2="35" stroke="#c8a84b" stroke-width="0.7" opacity="0.4"/>
</svg>""",

"conquering-campaign": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#8b1a1a" stroke-width="1"/>
  <!-- banner/flag -->
  <line x1="24" y1="8" x2="24" y2="40" stroke="#6a4a20" stroke-width="2"/>
  <path d="M24 10 L38 15 L24 22 Z" fill="#8b1a1a" stroke="#c8a84b" stroke-width="0.8"/>
  <!-- crossed swords beneath flag -->
  <line x1="14" y1="32" x2="22" y2="26" stroke="#8090a0" stroke-width="1.5"/>
  <line x1="16" y1="26" x2="24" y2="32" stroke="#8090a0" stroke-width="1.5"/>
  <!-- star above -->
  <polygon points="24,8 25,11 28,11 26,13 27,16 24,14 21,16 22,13 20,11 23,11" fill="#c8a84b" opacity="0.9"/>
  <!-- bottom runes -->
  <text x="10" y="44" font-size="5" fill="#c8a84b" opacity="0.4">✦ ✦ ✦</text>
</svg>""",

"db-rename-sweep": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#1a6b6b" stroke-width="1"/>
  <!-- database cylinders -->
  <ellipse cx="24" cy="14" rx="12" ry="4" fill="#0a2a2a" stroke="#1a6b6b" stroke-width="0.8"/>
  <rect x="12" y="14" width="24" height="10" fill="#0a2a2a" stroke="#1a6b6b" stroke-width="0.8"/>
  <ellipse cx="24" cy="24" rx="12" ry="4" fill="#0d3a3a" stroke="#1a6b6b" stroke-width="0.8"/>
  <!-- sweep arrow -->
  <path d="M30 30 Q38 28 38 36 Q30 40 22 36" fill="none" stroke="#c8a84b" stroke-width="1.5" marker-end="url(#ar)"/>
  <defs><marker id="ar" markerWidth="4" markerHeight="4" refX="2" refY="2" orient="auto"><path d="M0,0 L4,2 L0,4 Z" fill="#c8a84b"/></marker></defs>
  <!-- label tag -->
  <rect x="10" y="30" width="14" height="8" rx="1" fill="#1a1020" stroke="#c8a84b" stroke-width="0.7"/>
  <line x1="12" y1="33" x2="22" y2="33" stroke="#c8a84b" stroke-width="0.7" opacity="0.7"/>
  <line x1="12" y1="36" x2="20" y2="36" stroke="#c8a84b" stroke-width="0.7" opacity="0.5"/>
</svg>""",

"design-taste-frontend": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#c8a84b" stroke-width="1"/>
  <!-- painter's palette -->
  <ellipse cx="24" cy="24" rx="14" ry="12" fill="#1a1020" stroke="#c8a84b" stroke-width="1"/>
  <ellipse cx="30" cy="20" rx="3" ry="2" fill="#1a1020"/>
  <!-- color blobs on palette -->
  <circle cx="16" cy="20" r="2.5" fill="#8b1a1a"/>
  <circle cx="21" cy="16" r="2.5" fill="#1a6b6b"/>
  <circle cx="27" cy="15" r="2.5" fill="#c8a84b"/>
  <circle cx="32" cy="18" r="2.5" fill="#4a1a6b"/>
  <circle cx="33" cy="26" r="2.5" fill="#1a5c1a"/>
  <!-- brush -->
  <line x1="34" y1="14" x2="42" y2="8" stroke="#6a4a20" stroke-width="2"/>
  <path d="M34 14 Q36 12 38 10 Q35 12 34 14Z" fill="#8090a0"/>
  <!-- thumb hole -->
  <ellipse cx="30" cy="20" rx="2" ry="1.5" fill="#0d0a0e"/>
</svg>""",

"dev-server": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#1a6b6b" stroke-width="1"/>
  <!-- server tower -->
  <rect x="12" y="10" width="24" height="28" rx="2" fill="#0a1a1a" stroke="#1a6b6b" stroke-width="0.8"/>
  <rect x="14" y="13" width="20" height="6" rx="1" fill="#0d2a2a" stroke="#1a6b6b" stroke-width="0.5"/>
  <rect x="14" y="22" width="20" height="6" rx="1" fill="#0d2a2a" stroke="#1a6b6b" stroke-width="0.5"/>
  <rect x="14" y="31" width="20" height="4" rx="1" fill="#0d2a2a" stroke="#1a6b6b" stroke-width="0.5"/>
  <!-- LED lights -->
  <circle cx="31" cy="16" r="1.5" fill="#00ff88" opacity="0.9"/>
  <circle cx="31" cy="25" r="1.5" fill="#1a6b6b" opacity="0.7"/>
  <circle cx="31" cy="33" r="1.5" fill="#c8a84b" opacity="0.7"/>
  <!-- power glow -->
  <circle cx="24" cy="24" r="16" fill="none" stroke="#1a6b6b" stroke-width="0.3" opacity="0.3"/>
</svg>""",

"fallen-sword-design-language": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#c8a84b" stroke-width="1.5"/>
  <!-- THE iconic fallen sword — diagonal, glowing -->
  <defs>
    <linearGradient id="sg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#e8c870"/>
      <stop offset="50%" stop-color="#ffffff"/>
      <stop offset="100%" stop-color="#c8a84b"/>
    </linearGradient>
  </defs>
  <!-- blade -->
  <line x1="10" y1="10" x2="38" y2="38" stroke="url(#sg)" stroke-width="3" stroke-linecap="round"/>
  <!-- glow -->
  <line x1="10" y1="10" x2="38" y2="38" stroke="#c8a84b" stroke-width="6" stroke-linecap="round" opacity="0.15"/>
  <!-- crossguard -->
  <line x1="20" y1="28" x2="28" y2="20" stroke="#c8a84b" stroke-width="3" stroke-linecap="round"/>
  <!-- pommel -->
  <circle cx="11" cy="11" r="3" fill="#1a1218" stroke="#c8a84b" stroke-width="1.2"/>
  <!-- tip spark -->
  <circle cx="37" cy="37" r="2" fill="#ffffff" opacity="0.8"/>
  <!-- corner runes -->
  <text x="5" y="10" font-size="5" fill="#c8a84b" opacity="0.6">✦</text>
  <text x="38" y="45" font-size="5" fill="#c8a84b" opacity="0.6">✦</text>
  <text x="5" y="45" font-size="5" fill="#c8a84b" opacity="0.4">✦</text>
  <text x="38" y="10" font-size="5" fill="#c8a84b" opacity="0.4">✦</text>
</svg>""",

"full-output-enforcement": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#8090a0" stroke-width="1"/>
  <!-- tower shield -->
  <path d="M24 8 L36 12 L36 32 Q36 40 24 44 Q12 40 12 32 L12 12 Z" fill="#0a0a14" stroke="#8090a0" stroke-width="1.2"/>
  <!-- shield boss -->
  <circle cx="24" cy="26" r="6" fill="#1a1a2a" stroke="#8090a0" stroke-width="0.8"/>
  <circle cx="24" cy="26" r="3" fill="#8090a0" opacity="0.6"/>
  <!-- vertical stripe -->
  <line x1="24" y1="12" x2="24" y2="42" stroke="#8090a0" stroke-width="0.8" opacity="0.4"/>
  <!-- horizontal stripe -->
  <line x1="12" y1="26" x2="36" y2="26" stroke="#8090a0" stroke-width="0.8" opacity="0.4"/>
  <!-- enforcement rune -->
  <text x="24" y="21" font-size="7" text-anchor="middle" fill="#c8a84b" opacity="0.8">Ⅲ</text>
</svg>""",

"gpt-taste": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#4a1a6b" stroke-width="1"/>
  <!-- crystal orb — arcane comparison -->
  <circle cx="24" cy="24" r="14" fill="#0e0a1a" stroke="#4a1a6b" stroke-width="1"/>
  <circle cx="24" cy="24" r="10" fill="#14082a" stroke="#6a2a9b" stroke-width="0.6"/>
  <!-- swirl inside -->
  <path d="M24 16 Q30 20 26 24 Q22 28 24 32" fill="none" stroke="#8040c0" stroke-width="1.2" opacity="0.8"/>
  <path d="M24 16 Q18 20 22 24 Q26 28 24 32" fill="none" stroke="#c860ff" stroke-width="0.8" opacity="0.6"/>
  <!-- tasting fork -->
  <line x1="36" y1="10" x2="28" y2="18" stroke="#c8a84b" stroke-width="1.5"/>
  <line x1="34" y1="10" x2="34" y2="14" stroke="#c8a84b" stroke-width="1"/>
  <line x1="38" y1="10" x2="38" y2="14" stroke="#c8a84b" stroke-width="1"/>
  <!-- glow -->
  <circle cx="24" cy="24" r="6" fill="#8040c0" opacity="0.15"/>
</svg>""",

"graphify": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#1a6b6b" stroke-width="1"/>
  <!-- nodes -->
  <circle cx="24" cy="14" r="4" fill="#1a6b6b" stroke="#00c8a0" stroke-width="1"/>
  <circle cx="12" cy="32" r="4" fill="#1a6b6b" stroke="#00c8a0" stroke-width="1"/>
  <circle cx="36" cy="32" r="4" fill="#1a6b6b" stroke="#00c8a0" stroke-width="1"/>
  <circle cx="24" cy="26" r="3" fill="#0a2a2a" stroke="#00c8a0" stroke-width="0.8"/>
  <!-- edges -->
  <line x1="24" y1="18" x2="24" y2="23" stroke="#00c8a0" stroke-width="1" opacity="0.8"/>
  <line x1="21" y1="28" x2="14" y2="30" stroke="#00c8a0" stroke-width="1" opacity="0.8"/>
  <line x1="27" y1="28" x2="34" y2="30" stroke="#00c8a0" stroke-width="1" opacity="0.8"/>
  <line x1="14" y1="30" x2="34" y2="30" stroke="#00c8a0" stroke-width="0.6" opacity="0.4"/>
  <!-- glow pulses -->
  <circle cx="24" cy="14" r="6" fill="none" stroke="#00c8a0" stroke-width="0.5" opacity="0.4"/>
</svg>""",

"guild-log": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#c8a84b" stroke-width="1"/>
  <!-- open tome -->
  <path d="M8 12 Q8 8 12 8 L24 10 L36 8 Q40 8 40 12 L40 38 Q40 42 36 42 L24 40 L12 42 Q8 42 8 38 Z" fill="#2a1a0a" stroke="#c8a84b" stroke-width="0.8"/>
  <line x1="24" y1="10" x2="24" y2="40" stroke="#c8a84b" stroke-width="0.8" opacity="0.6"/>
  <!-- guild seal -->
  <circle cx="24" cy="22" r="6" fill="#1a1000" stroke="#c8a84b" stroke-width="0.8"/>
  <text x="24" y="25" font-size="8" text-anchor="middle" fill="#c8a84b" opacity="0.9">⚔</text>
  <!-- log lines -->
  <line x1="12" y1="30" x2="22" y2="30" stroke="#c8a84b" stroke-width="0.6" opacity="0.5"/>
  <line x1="12" y1="33" x2="20" y2="33" stroke="#c8a84b" stroke-width="0.6" opacity="0.4"/>
  <line x1="26" y1="30" x2="36" y2="30" stroke="#c8a84b" stroke-width="0.6" opacity="0.5"/>
  <line x1="26" y1="33" x2="34" y2="33" stroke="#c8a84b" stroke-width="0.6" opacity="0.4"/>
</svg>""",

"high-end-visual-design": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#c8a84b" stroke-width="1.5"/>
  <!-- diamond gem — high end -->
  <defs>
    <linearGradient id="dg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.9"/>
      <stop offset="40%" stop-color="#c8a84b"/>
      <stop offset="100%" stop-color="#4a2a00"/>
    </linearGradient>
  </defs>
  <polygon points="24,8 36,20 24,40 12,20" fill="url(#dg)" stroke="#c8a84b" stroke-width="1"/>
  <polygon points="24,8 36,20 24,20" fill="#ffffff" opacity="0.25"/>
  <polygon points="24,20 36,20 24,40" fill="#4a2a00" opacity="0.4"/>
  <line x1="12" y1="20" x2="36" y2="20" stroke="#c8a84b" stroke-width="0.8" opacity="0.7"/>
  <!-- sparkles -->
  <circle cx="10" cy="10" r="1.5" fill="#ffffff" opacity="0.7"/>
  <circle cx="40" cy="8" r="1" fill="#ffffff" opacity="0.6"/>
  <circle cx="38" cy="40" r="1.5" fill="#c8a84b" opacity="0.5"/>
</svg>""",

"image-to-code": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#1a6b6b" stroke-width="1"/>
  <!-- image frame -->
  <rect x="8" y="10" width="14" height="14" rx="1" fill="#0a1a0a" stroke="#1a6b6b" stroke-width="0.8"/>
  <circle cx="12" cy="15" r="2" fill="#c8a84b" opacity="0.6"/>
  <path d="M8 20 L12 17 L15 20 L18 16 L22 24 L8 24 Z" fill="#1a6b6b" opacity="0.5"/>
  <!-- arrow -->
  <line x1="24" y1="17" x2="30" y2="17" stroke="#c8a84b" stroke-width="1.5"/>
  <polygon points="30,14 34,17 30,20" fill="#c8a84b"/>
  <!-- code brackets -->
  <text x="32" y="22" font-size="9" fill="#1a6b6b" font-family="monospace">&lt;/&gt;</text>
  <!-- bottom scroll lines -->
  <line x1="8" y1="30" x2="40" y2="30" stroke="#1a6b6b" stroke-width="0.6" opacity="0.5"/>
  <line x1="8" y1="34" x2="36" y2="34" stroke="#1a6b6b" stroke-width="0.6" opacity="0.4"/>
  <line x1="8" y1="38" x2="32" y2="38" stroke="#1a6b6b" stroke-width="0.6" opacity="0.3"/>
</svg>""",

"imagegen-frontend-mobile": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#4a1a6b" stroke-width="1"/>
  <!-- mobile device -->
  <rect x="16" y="8" width="16" height="28" rx="3" fill="#0a0a14" stroke="#4a1a6b" stroke-width="0.8"/>
  <rect x="18" y="11" width="12" height="18" rx="1" fill="#0e0a1a"/>
  <!-- image on screen -->
  <rect x="18" y="11" width="12" height="12" rx="1" fill="#1a0a2a"/>
  <circle cx="21" cy="15" r="2" fill="#c8a84b" opacity="0.6"/>
  <path d="M18 21 L21 18 L24 21 L27 16 L30 23 L18 23 Z" fill="#4a1a6b" opacity="0.7"/>
  <!-- home indicator -->
  <rect x="22" y="32" width="4" height="1.5" rx="1" fill="#4a1a6b"/>
  <!-- sparkle gen glow -->
  <circle cx="38" cy="12" r="4" fill="none" stroke="#8040c0" stroke-width="0.8" opacity="0.6"/>
  <circle cx="38" cy="12" r="2" fill="#8040c0" opacity="0.4"/>
  <line x1="38" y1="8" x2="38" y2="10" stroke="#8040c0" stroke-width="1" opacity="0.7"/>
  <line x1="38" y1="14" x2="38" y2="16" stroke="#8040c0" stroke-width="1" opacity="0.7"/>
  <line x1="34" y1="12" x2="36" y2="12" stroke="#8040c0" stroke-width="1" opacity="0.7"/>
  <line x1="40" y1="12" x2="42" y2="12" stroke="#8040c0" stroke-width="1" opacity="0.7"/>
</svg>""",

"imagegen-frontend-web": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#1a6b6b" stroke-width="1"/>
  <!-- monitor -->
  <rect x="8" y="10" width="32" height="22" rx="2" fill="#0a1a1a" stroke="#1a6b6b" stroke-width="0.8"/>
  <rect x="10" y="12" width="28" height="18" rx="1" fill="#060e0e"/>
  <!-- stand -->
  <rect x="20" y="32" width="8" height="4" rx="1" fill="#1a6b6b" opacity="0.5"/>
  <rect x="17" y="36" width="14" height="2" rx="1" fill="#1a6b6b" opacity="0.4"/>
  <!-- image on screen with gen glow -->
  <circle cx="16" cy="17" r="2.5" fill="#c8a84b" opacity="0.5"/>
  <path d="M10 24 L16 20 L20 24 L24 19 L38 26 L10 26 Z" fill="#1a6b6b" opacity="0.6"/>
  <!-- sparkle -->
  <circle cx="34" cy="14" r="3" fill="#00c8a0" opacity="0.3"/>
  <line x1="34" y1="11" x2="34" y2="12" stroke="#00c8a0" stroke-width="1"/>
  <line x1="34" y1="16" x2="34" y2="17" stroke="#00c8a0" stroke-width="1"/>
  <line x1="31" y1="14" x2="32" y2="14" stroke="#00c8a0" stroke-width="1"/>
  <line x1="36" y1="14" x2="37" y2="14" stroke="#00c8a0" stroke-width="1"/>
</svg>""",

"impeccable": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#c8a84b" stroke-width="1.5"/>
  <!-- radiant star — perfection -->
  <defs>
    <radialGradient id="rg" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#ffffff"/>
      <stop offset="40%" stop-color="#c8a84b"/>
      <stop offset="100%" stop-color="#2a1a00" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <circle cx="24" cy="24" r="18" fill="url(#rg)" opacity="0.15"/>
  <!-- 8-pointed star -->
  <polygon points="24,8 26,20 38,18 28,24 38,30 26,28 24,40 22,28 10,30 20,24 10,18 22,20" fill="#c8a84b" opacity="0.9"/>
  <polygon points="24,13 25.5,21 32,20 26,24 32,28 25.5,27 24,35 22.5,27 18,28 22,24 18,20 22.5,21" fill="#ffffff" opacity="0.6"/>
  <circle cx="24" cy="24" r="3" fill="#ffffff" opacity="0.9"/>
</svg>""",

"industrial-brutalist-ui": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="0" fill="#111111" stroke="#555555" stroke-width="2"/>
  <!-- brutalist grid -->
  <rect x="4" y="4" width="19" height="19" fill="#1a1a1a" stroke="#555" stroke-width="1"/>
  <rect x="25" y="4" width="19" height="19" fill="#222222" stroke="#555" stroke-width="1"/>
  <rect x="4" y="25" width="19" height="19" fill="#222222" stroke="#555" stroke-width="1"/>
  <rect x="25" y="25" width="19" height="19" fill="#1a1a1a" stroke="#555" stroke-width="1"/>
  <!-- heavy typography marks -->
  <text x="7" y="18" font-size="12" fill="#888" font-family="monospace" font-weight="bold">X</text>
  <text x="28" y="18" font-size="9" fill="#c8a84b" font-family="monospace">01</text>
  <text x="10" y="38" font-size="7" fill="#555" font-family="monospace">RAW</text>
  <text x="27" y="38" font-size="7" fill="#555" font-family="monospace">UI</text>
  <!-- cross mark center -->
  <line x1="4" y1="4" x2="44" y2="44" stroke="#333" stroke-width="0.5"/>
  <line x1="44" y1="4" x2="4" y2="44" stroke="#333" stroke-width="0.5"/>
</svg>""",

"minimalist-ui": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="8" y="8" width="32" height="32" rx="4" fill="#111520" stroke="#8090a0" stroke-width="0.8"/>
  <!-- single centered circle — zen -->
  <circle cx="24" cy="24" r="10" fill="none" stroke="#8090a0" stroke-width="1.2"/>
  <circle cx="24" cy="24" r="2" fill="#8090a0"/>
  <!-- minimal lines -->
  <line x1="14" y1="24" x2="18" y2="24" stroke="#8090a0" stroke-width="0.8" opacity="0.5"/>
  <line x1="30" y1="24" x2="34" y2="24" stroke="#8090a0" stroke-width="0.8" opacity="0.5"/>
  <line x1="24" y1="14" x2="24" y2="18" stroke="#8090a0" stroke-width="0.8" opacity="0.5"/>
  <line x1="24" y1="30" x2="24" y2="34" stroke="#8090a0" stroke-width="0.8" opacity="0.5"/>
</svg>""",

"obsidian-markdown": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#4a1a6b" stroke-width="1"/>
  <!-- obsidian crystal shard -->
  <polygon points="24,6 34,20 30,42 18,42 14,20" fill="#0a0014" stroke="#4a1a6b" stroke-width="1"/>
  <polygon points="24,6 34,20 24,16" fill="#1a0a2a" opacity="0.8"/>
  <polygon points="14,20 24,16 18,42" fill="#0e0018" opacity="0.6"/>
  <!-- purple vein lines -->
  <line x1="24" y1="10" x2="22" y2="30" stroke="#6a2a9b" stroke-width="0.8" opacity="0.7"/>
  <line x1="26" y1="14" x2="28" y2="34" stroke="#8040c0" stroke-width="0.6" opacity="0.5"/>
  <!-- markdown hash -->
  <text x="24" y="26" font-size="8" text-anchor="middle" fill="#4a1a6b" opacity="0.8">#</text>
  <!-- glow tip -->
  <circle cx="24" cy="7" r="2" fill="#8040c0" opacity="0.6"/>
</svg>""",

"performance": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#c8a84b" stroke-width="1"/>
  <!-- lightning bolt — speed/power -->
  <polygon points="28,8 16,26 24,26 20,40 34,22 26,22" fill="#c8a84b" stroke="#ffffff" stroke-width="0.5"/>
  <!-- speed lines -->
  <line x1="8" y1="16" x2="14" y2="16" stroke="#c8a84b" stroke-width="1" opacity="0.5"/>
  <line x1="6" y1="22" x2="12" y2="22" stroke="#c8a84b" stroke-width="1" opacity="0.4"/>
  <line x1="8" y1="28" x2="14" y2="28" stroke="#c8a84b" stroke-width="1" opacity="0.3"/>
  <!-- glow -->
  <polygon points="28,8 16,26 24,26 20,40 34,22 26,22" fill="#ffffff" opacity="0.1"/>
</svg>""",

"redesign-existing-projects": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#c8a84b" stroke-width="1"/>
  <!-- phoenix rising — rebirth/redesign -->
  <path d="M24 36 Q14 26 16 16 Q20 8 24 12 Q28 8 32 16 Q34 26 24 36Z" fill="#1a0a00" stroke="#c8a84b" stroke-width="0.8"/>
  <!-- wings -->
  <path d="M16 16 Q8 14 8 22 Q12 24 16 20" fill="#8b3010" stroke="#c8a84b" stroke-width="0.6" opacity="0.8"/>
  <path d="M32 16 Q40 14 40 22 Q36 24 32 20" fill="#8b3010" stroke="#c8a84b" stroke-width="0.6" opacity="0.8"/>
  <!-- flames -->
  <path d="M20 30 Q18 24 24 20 Q30 24 28 30 Q26 26 24 24 Q22 26 20 30Z" fill="#c86020" opacity="0.8"/>
  <path d="M22 32 Q21 28 24 26 Q27 28 26 32 Q24.5 29 24 28 Q23.5 29 22 32Z" fill="#c8a84b" opacity="0.9"/>
  <!-- eye -->
  <circle cx="24" cy="16" r="2" fill="#c8a84b"/>
  <circle cx="24" cy="16" r="1" fill="#0d0a0e"/>
</svg>""",

"skillsmith": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#c8a84b" stroke-width="1"/>
  <!-- anvil -->
  <rect x="12" y="28" width="24" height="8" rx="1" fill="#333" stroke="#c8a84b" stroke-width="0.8"/>
  <rect x="16" y="24" width="16" height="6" rx="1" fill="#2a2a2a" stroke="#c8a84b" stroke-width="0.7"/>
  <!-- hammer -->
  <line x1="30" y1="10" x2="22" y2="24" stroke="#6a4a20" stroke-width="2.5"/>
  <rect x="28" y="8" width="10" height="6" rx="1" fill="#8090a0" stroke="#c8a84b" stroke-width="0.6" transform="rotate(-30 33 11)"/>
  <!-- sparks -->
  <circle cx="22" cy="24" r="1.5" fill="#ff9900" opacity="0.9"/>
  <line x1="20" y1="22" x2="18" y2="20" stroke="#ff9900" stroke-width="1" opacity="0.7"/>
  <line x1="24" y1="21" x2="26" y2="19" stroke="#ff9900" stroke-width="1" opacity="0.6"/>
  <line x1="21" y1="26" x2="19" y2="28" stroke="#ff9900" stroke-width="1" opacity="0.5"/>
  <!-- gear on anvil -->
  <text x="16" y="32" font-size="6" fill="#c8a84b" opacity="0.7">⚙</text>
</svg>""",

"stitch-design-taste": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#c8a84b" stroke-width="1"/>
  <!-- needle and thread -->
  <line x1="10" y1="10" x2="36" y2="36" stroke="#8090a0" stroke-width="1.5"/>
  <ellipse cx="10" cy="10" rx="4" ry="2" fill="#8090a0" stroke="#c8a84b" stroke-width="0.6" transform="rotate(-45 10 10)"/>
  <circle cx="11" cy="9" r="1" fill="#0d0a0e"/>
  <!-- thread spool -->
  <ellipse cx="36" cy="36" rx="5" ry="3" fill="#4a1a6b" stroke="#c8a84b" stroke-width="0.7"/>
  <ellipse cx="36" cy="33" rx="5" ry="3" fill="#4a1a6b" stroke="#c8a84b" stroke-width="0.5"/>
  <!-- stitch dashes -->
  <line x1="16" y1="22" x2="20" y2="22" stroke="#c8a84b" stroke-width="1" opacity="0.6"/>
  <line x1="23" y1="22" x2="27" y2="22" stroke="#c8a84b" stroke-width="1" opacity="0.6"/>
  <line x1="22" y1="26" x2="26" y2="26" stroke="#c8a84b" stroke-width="1" opacity="0.5"/>
  <line x1="19" y1="16" x2="23" y2="16" stroke="#c8a84b" stroke-width="1" opacity="0.5"/>
</svg>""",

"strategies-review": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#8090a0" stroke-width="1"/>
  <!-- chess board fragment -->
  <rect x="8" y="20" width="8" height="8" fill="#1a1020"/>
  <rect x="16" y="20" width="8" height="8" fill="#2a2030"/>
  <rect x="24" y="20" width="8" height="8" fill="#1a1020"/>
  <rect x="32" y="20" width="8" height="8" fill="#2a2030"/>
  <rect x="8" y="28" width="8" height="8" fill="#2a2030"/>
  <rect x="16" y="28" width="8" height="8" fill="#1a1020"/>
  <rect x="24" y="28" width="8" height="8" fill="#2a2030"/>
  <rect x="32" y="28" width="8" height="8" fill="#1a1020"/>
  <!-- king piece -->
  <rect x="21" y="12" width="6" height="8" rx="1" fill="#8090a0" stroke="#c8a84b" stroke-width="0.7"/>
  <line x1="24" y1="8" x2="24" y2="12" stroke="#c8a84b" stroke-width="1.2"/>
  <line x1="22" y1="10" x2="26" y2="10" stroke="#c8a84b" stroke-width="1.2"/>
  <!-- grid border -->
  <rect x="8" y="20" width="32" height="16" fill="none" stroke="#8090a0" stroke-width="0.8"/>
</svg>""",

"supabase": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#1a6b6b" stroke-width="1"/>
  <!-- lightning bolt (supabase-like) in teal -->
  <polygon points="28,8 14,26 24,26 18,40 36,22 26,22" fill="#00c8a0" stroke="#00e8b8" stroke-width="0.5"/>
  <!-- database backing -->
  <ellipse cx="24" cy="36" rx="10" ry="3" fill="#0a2a2a" stroke="#1a6b6b" stroke-width="0.7"/>
  <rect x="14" y="33" width="20" height="3" fill="#0a2a2a" stroke="#1a6b6b" stroke-width="0.7"/>
  <!-- glow -->
  <polygon points="28,8 14,26 24,26 18,40 36,22 26,22" fill="#ffffff" opacity="0.08"/>
</svg>""",

"supabase-postgres-best-practices": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#1a4060" stroke-width="1"/>
  <!-- elephant (postgres) -->
  <ellipse cx="22" cy="26" rx="10" ry="12" fill="#1a3050" stroke="#4080c0" stroke-width="0.8"/>
  <ellipse cx="22" cy="18" rx="8" ry="8" fill="#1a3050" stroke="#4080c0" stroke-width="0.8"/>
  <!-- trunk -->
  <path d="M14 24 Q8 26 10 34 Q12 38 16 36" fill="none" stroke="#4080c0" stroke-width="2" stroke-linecap="round"/>
  <!-- eye -->
  <circle cx="18" cy="17" r="2" fill="#4080c0"/>
  <circle cx="18" cy="17" r="1" fill="#0d0a0e"/>
  <!-- tusk -->
  <path d="M14 22 Q10 20 12 16" fill="none" stroke="#8090a0" stroke-width="1.5"/>
  <!-- checkmark seal -->
  <circle cx="36" cy="14" r="7" fill="#1a6b1a" stroke="#00c840" stroke-width="0.8"/>
  <polyline points="32,14 35,17 40,10" fill="none" stroke="#00c840" stroke-width="1.5" stroke-linecap="round"/>
</svg>""",

"transactions-domain-model": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#c8a84b" stroke-width="1"/>
  <!-- coin/ledger -->
  <circle cx="24" cy="22" r="12" fill="#1a1000" stroke="#c8a84b" stroke-width="1"/>
  <circle cx="24" cy="22" r="9" fill="#0a0800" stroke="#c8a84b" stroke-width="0.6" opacity="0.6"/>
  <text x="24" y="26" font-size="10" text-anchor="middle" fill="#c8a84b" opacity="0.9">₿</text>
  <!-- flow arrows -->
  <path d="M8 36 Q16 32 24 36 Q32 40 40 36" fill="none" stroke="#c8a84b" stroke-width="1" opacity="0.6"/>
  <polygon points="38,33 42,36 38,39" fill="#c8a84b" opacity="0.6"/>
  <!-- domain nodes -->
  <circle cx="8" cy="36" r="2.5" fill="#2a1a00" stroke="#c8a84b" stroke-width="0.7"/>
  <circle cx="40" cy="36" r="2.5" fill="#2a1a00" stroke="#c8a84b" stroke-width="0.7"/>
</svg>""",

"vault-log-compliance": """<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <rect width="48" height="48" fill="#0d0a0e"/>
  <rect x="4" y="4" width="40" height="40" rx="3" fill="#1a1218" stroke="#8b1a1a" stroke-width="1"/>
  <!-- vault door -->
  <circle cx="24" cy="24" r="16" fill="#0a0808" stroke="#8b1a1a" stroke-width="1.5"/>
  <circle cx="24" cy="24" r="12" fill="#0a0808" stroke="#8b3030" stroke-width="0.8"/>
  <!-- dial -->
  <circle cx="24" cy="24" r="6" fill="#1a0808" stroke="#c8a84b" stroke-width="0.8"/>
  <line x1="24" y1="18" x2="24" y2="21" stroke="#c8a84b" stroke-width="1.2"/>
  <!-- bolt handles -->
  <rect x="8" y="22" width="6" height="4" rx="1" fill="#8b1a1a" stroke="#c8a84b" stroke-width="0.6"/>
  <rect x="34" y="22" width="6" height="4" rx="1" fill="#8b1a1a" stroke="#c8a84b" stroke-width="0.6"/>
  <rect x="22" y="8" width="4" height="6" rx="1" fill="#8b1a1a" stroke="#c8a84b" stroke-width="0.6"/>
  <rect x="22" y="34" width="4" height="6" rx="1" fill="#8b1a1a" stroke="#c8a84b" stroke-width="0.6"/>
  <!-- lock symbol -->
  <text x="24" y="26" font-size="6" text-anchor="middle" fill="#c8a84b" opacity="0.9">🔒</text>
</svg>""",

}

# Load guild-data.json
with open("guild-data.json", "r") as f:
    data = json.load(f)

updated = 0
for skill in data["skills"]:
    sid = skill["id"]
    if sid in ARTS:
        # Collapse SVG to single line for JSON storage
        svg = re.sub(r'\n\s*', ' ', ARTS[sid]).strip()
        skill["art"] = svg
        updated += 1
    else:
        print(f"WARNING: no art for {sid}")

with open("guild-data.json", "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Updated {updated}/{len(data['skills'])} skills with art.")
