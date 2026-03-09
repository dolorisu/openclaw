"""
Code Indentation Fixer Patch

Automatically formats JSON/YAML code blocks in WhatsApp messages
to have proper indentation (2 spaces per level).

Fixes GPT-5.3-codex behavior of generating flat/unindented code.
"""

import re
from pathlib import Path
from typing import List, Tuple


FORMATTER_FUNCTION = '''
// Code block formatter (added by code_indent_fixer patch)
function formatCodeBlocks(text) {
  if (!text || typeof text !== 'string') return text;
  
  // Match ```language\\ncode\\n``` blocks
  return text.replace(/```(json|jsonc|yaml|yml)\\n([\\s\\S]*?)\\n```/g, (match, lang, code) => {
    if (lang === 'json' || lang === 'jsonc') {
      try {
        const parsed = JSON.parse(code);
        const formatted = JSON.stringify(parsed, null, 2);
        return \`\\\`\\\`\\\`\${lang}\\n\${formatted}\\n\\\`\\\`\\\`\`;
      } catch (e) {
        // If JSON parsing fails, return original
        return match;
      }
    } else if (lang === 'yaml' || lang === 'yml') {
      try {
        // Basic YAML indentation fixer
        const lines = code.split('\\n');
        const formatted = [];
        let indent = 0;
        
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) {
            formatted.push('');
            continue;
          }
          
          // Decrease indent for lines that don't start with whitespace after colons
          if (trimmed.match(/^[a-zA-Z_]/)) {
            // Check if previous line increased indent
            const prevLine = formatted[formatted.length - 1];
            if (prevLine && prevLine.trim().endsWith(':')) {
              indent += 1;
            }
          }
          
          // Add list items at current indent
          if (trimmed.startsWith('-')) {
            formatted.push('  '.repeat(Math.max(0, indent - 1)) + trimmed);
          } else if (trimmed.includes(':')) {
            // Key-value or parent key
            formatted.push('  '.repeat(indent) + trimmed);
            if (trimmed.endsWith(':')) {
              // This will increase indent for next iteration
            } else {
              // Reset indent after value
            }
          } else {
            formatted.push('  '.repeat(indent) + trimmed);
          }
        }
        
        return \`\\\`\\\`\\\`\${lang}\\n\${formatted.join('\\n')}\\n\\\`\\\`\\\`\`;
      } catch (e) {
        return match;
      }
    }
    return match;
  });
}
'''


def apply_patch(openclaw_dist: Path) -> List[Tuple[str, str]]:
    """
    Apply code indentation fixer patch to channel-web files.
    
    Intercepts text before sendMessage and formats code blocks.
    """
    results = []
    
    channel_files = list(openclaw_dist.glob("channel-web-*.js"))
    
    if not channel_files:
        results.append(("error", "No channel-web-*.js files found"))
        return results
    
    for file_path in channel_files:
        try:
            content = file_path.read_text(encoding='utf-8')
            original_content = content
            
            # Check if already patched
            if 'formatCodeBlocks' in content:
                results.append(("already_patched", str(file_path.name)))
                continue
            
            # Find a good injection point - after imports, before first function
            # Look for common patterns in bundled JS
            injection_markers = [
                'async function',
                'function ',
                'const ',
                'var ',
                'let '
            ]
            
            injection_pos = -1
            for marker in injection_markers:
                pos = content.find(marker)
                if pos > 100:  # Make sure we're past any header comments
                    injection_pos = pos
                    break
            
            if injection_pos > 0:
                # Inject the formatter function
                content = content[:injection_pos] + FORMATTER_FUNCTION + '\n\n' + content[injection_pos:]
                
                # Now replace all sendMessage calls to format text
                # Pattern 1: sendMessage(jid, { text })
                content = re.sub(
                    r'sendMessage\(([^,]+),\s*{\s*text\s*}\s*\)',
                    r'sendMessage(\1, { text: formatCodeBlocks(text) })',
                    content
                )
                
                # Pattern 2: sendMessage(jid, { text: someVar })
                content = re.sub(
                    r'sendMessage\(([^,]+),\s*{\s*text:\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}\s*\)',
                    r'sendMessage(\1, { text: formatCodeBlocks(\2) })',
                    content
                )
                
                # Pattern 3: { text: "literal" } - but only if it's likely a message payload
                # This is trickier, need to be careful not to break other code
                
                if content != original_content:
                    file_path.write_text(content, encoding='utf-8')
                    results.append(("patched", str(file_path.name)))
                else:
                    results.append(("skipped", f"{file_path.name} - no changes made"))
            else:
                results.append(("skipped", f"{file_path.name} - no injection point found"))
                
        except Exception as e:
            results.append(("error", f"{file_path.name}: {str(e)}"))
    
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 code_indent_fixer.py <openclaw_dist_path>")
        sys.exit(1)
    
    dist_path = Path(sys.argv[1])
    if not dist_path.exists():
        print(f"Error: Path {dist_path} does not exist")
        sys.exit(1)
    
    print(f"Applying code indentation fixer patch to {dist_path}")
    results = apply_patch(dist_path)
    
    for status, message in results:
        print(f"[{status}] {message}")
    
    # Summary
    patched_count = sum(1 for s, _ in results if s == "patched")
    print(f"\nSummary: {patched_count} files patched")
