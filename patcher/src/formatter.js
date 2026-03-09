#!/usr/bin/env node
/**
 * Code Formatter Utility
 * Formats fenced code blocks with readable indentation.
 * Usage: node formatter.js < input.txt
 */

const BRACE_LANGS = new Set(['js', 'javascript', 'ts', 'typescript', 'tsx', 'jsx', 'rs', 'rust', 'c', 'cpp', 'java']);

function countBraces(line) {
  let opens = 0;
  let closes = 0;
  let quote = null;
  let escaped = false;
  for (const ch of line) {
    if (escaped) {
      escaped = false;
      continue;
    }
    if (ch === '\\') {
      escaped = true;
      continue;
    }
    if (quote) {
      if (ch === quote) quote = null;
      continue;
    }
    if (ch === '"' || ch === "'" || ch === '`') {
      quote = ch;
      continue;
    }
    if (ch === '{' || ch === '[' || ch === '(') opens += 1;
    if (ch === '}' || ch === ']' || ch === ')') closes += 1;
  }
  return { opens, closes };
}

function leadingClosers(line) {
  const m = line.match(/^[\}\]\)]+/);
  return m ? m[0].length : 0;
}

function formatBraceCode(code, indentUnit = '  ') {
  const lines = String(code).replace(/\r\n?/g, '\n').split('\n');
  let depth = 0;
  const out = [];
  for (const raw of lines) {
    const t = raw.trim();
    if (!t) {
      out.push('');
      continue;
    }
    const closeAtStart = leadingClosers(t);
    const level = Math.max(depth - closeAtStart, 0);
    out.push(indentUnit.repeat(level) + t);
    const { opens, closes } = countBraces(t);
    depth = Math.max(depth + opens - closes, 0);
  }
  return out.join('\n');
}

function formatJson(code) {
  try {
    return JSON.stringify(JSON.parse(code), null, 2);
  } catch {
    return null;
  }
}

function formatPython(code) {
  if (/[\{\[]/.test(code)) return formatBraceCode(code, '    ');
  const lines = String(code).replace(/\r\n?/g, '\n').split('\n');
  let depth = 0;
  const out = [];
  for (const raw of lines) {
    const t = raw.trim();
    if (!t) {
      out.push('');
      continue;
    }
    const dedent = /^(elif\b|else:|except\b|finally:)/.test(t) ? 1 : 0;
    const level = Math.max(depth - dedent, 0);
    out.push('    '.repeat(level) + t);
    if (t.endsWith(':') && !t.startsWith('#')) depth = level + 1;
    else depth = level;
  }
  return out.join('\n');
}

function formatYaml(code) {
  return String(code);
}

function formatFence(lang, code) {
  const l = String(lang || '').toLowerCase();
  if (l === 'json' || l === 'jsonc') return formatJson(code) ?? code;
  if (BRACE_LANGS.has(l)) return formatBraceCode(code, '  ');
  if (l === 'py' || l === 'python') return formatPython(code);
  if (l === 'yaml' || l === 'yml') return formatYaml(code);
  return code;
}

const formatCodeBlocks = (text) => {
  if (!text || typeof text !== 'string' || !text.includes('```')) return text;
  return text.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)\n```/g, (match, lang, code) => {
    const formatted = formatFence(lang, code);
    return `\`\`\`${lang}\n${formatted}\n\`\`\``;
  });
};

// Read from stdin
let inputData = '';
process.stdin.setEncoding('utf8');

process.stdin.on('data', (chunk) => {
  inputData += chunk;
});

process.stdin.on('end', () => {
  const formatted = formatCodeBlocks(inputData);
  process.stdout.write(formatted);
});
