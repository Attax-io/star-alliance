#!/usr/bin/env node
// Generates Fallen Sword-themed skill art PNGs via MiniMax image API.
// Output: skill-art/<id>.png
// Usage: node gen-skill-art.cjs [--regen <id>,<id>...]
// --regen flag forces regeneration of specific skills even if PNG exists.

const fs = require("fs");
const path = require("path");
const https = require("https");

const KEY_PATH = path.join(process.env.HOME, ".config/minimax/m3.key");
const API_KEY = fs.readFileSync(KEY_PATH, "utf8").trim();

const OUT_DIR = path.join(__dirname, "..", "..", "skill-art");
fs.mkdirSync(OUT_DIR, { recursive: true });

// Parse --regen flag
const regenArg = process.argv.indexOf("--regen");
const regenSet = new Set(regenArg !== -1 ? process.argv[regenArg + 1].split(",") : []);

const STYLE = "fantasy RPG skill icon, Fallen Sword MMORPG style, dark parchment background with aged leather texture, gold runic border, ornate medieval frame, dramatic lighting, rich saturated colors, detailed pixel-art-adjacent illustration, 48x48 icon style, pure black outer border";

const SKILLS = [
  {
    id: "helpless",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "Invoked by scripts and hooks, never by the Butler himself.", no text, no watermarks`,
  },
  {
    id: "butler-voice",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "How the Butler speaks to the Guild Master: lead every reply with a plain-English status block", no text, no watermarks`,
  },
  {
    id: "trading-strategy",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "Read-only trading-strategy design that ships a written, dated strategy spec and never places a", no text, no watermarks`,
  },
  {
    id: "portfolio-risk",
    prompt: `${STYLE}. [REFINE — Designer handoff] A Fallen-Sword emblem for "Read-only, book-level portfolio construction and risk measurement that ships a written, dated r", no text, no watermarks`,
  },
  {