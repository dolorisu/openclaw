#!/usr/bin/env node
/**
 * Code Formatter Utility
 * Formats JSON/YAML code blocks in text with proper indentation
 * Usage: node formatter.js < input.txt
 */

// No YAML support for now, only JSON formatting

const formatCodeBlocks = (text) => {
  if (!text || typeof text !== 'string') return text;
  
  // Match ```language\ncode\n``` blocks
  return text.replace(/```(json|jsonc)\n([\s\S]*?)\n```/g, (match, lang, code) => {
    if (lang === 'json' || lang === 'jsonc') {
      try {
        // Parse and re-stringify with 2-space indentation
        const parsed = JSON.parse(code);
        const formatted = JSON.stringify(parsed, null, 2);
        return `\`\`\`${lang}\n${formatted}\n\`\`\``;
      } catch (e) {
        // If parsing fails, return original
        return match;
      }
    }
    return match;
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
