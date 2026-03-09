"""
Code Indentation Patch v2

Injects a subprocess call to formatter.js to fix flat JSON/YAML code blocks.
Uses child_process.execSync to format text before sending to WhatsApp.
"""

import re
from pathlib import Path
from typing import List, Tuple


def apply_patch(openclaw_dist: Path) -> List[Tuple[str, str]]:
    """
    Apply code indentation formatter patch to channel-web files.
    
    Injects formatter subprocess call before sendMessage.
    """
    results = []
    
    # Get formatter.js path (will be in ~/.openclaw/patcher/src/)
    formatter_path = Path.home() / '.openclaw' / 'patcher' / 'src' / 'formatter.js'
    
    channel_files = list(openclaw_dist.glob("channel-web-*.js"))
    
    if not channel_files:
        results.append(("error", "No channel-web-*.js files found"))
        return results
    
    # The formatter function to inject (ES module compatible)
    formatter_injection = f'''
// Code indentation formatter (added by code_indent patch)
import {{ execSync }} from 'child_process';
const FORMATTER_PATH = '{formatter_path}';

function formatCodeBlocks(text) {{
  if (!text || typeof text !== 'string') return text;
  
  // Skip if no code blocks present
  if (!text.includes('```')) return text;
  
  console.log('[code_indent] Formatting text with', text.split('```').length - 1, 'code blocks');
  
  try {{
    const formatted = execSync('node ' + FORMATTER_PATH, {{
      input: text,
      encoding: 'utf8',
      timeout: 1000,
      maxBuffer: 10 * 1024 * 1024 // 10MB
    }});
    console.log('[code_indent] Formatting successful');
    return formatted;
  }} catch (err) {{
    // If formatter fails, return original text
    console.error('[code_indent] Formatter error:', err.message);
    console.error('[code_indent] Error stack:', err.stack);
    return text;
  }}
}}
'''
    
    for file_path in channel_files:
        try:
            content = file_path.read_text(encoding='utf-8')
            original_content = content
            
            # Check if already patched
            if 'formatCodeBlocks' in content and 'code_indent patch' in content:
                results.append(("already_patched", str(file_path.name)))
                continue
            
            # Find where to inject - look for the first async function or function declaration
            # Target injection point: after imports/requires, before first function
            
            # Find common patterns for injection
            patterns = [
                (r'(async\s+function\s+\w+)', 'before_async_function'),
                (r'(function\s+\w+\s*\()', 'before_function'),
                (r'(const\s+\w+\s*=\s*async)', 'before_const_async'),
            ]
            
            injection_pos = -1
            for pattern, name in patterns:
                match = re.search(pattern, content)
                if match and match.start() > 100:  # Ensure we're past header
                    injection_pos = match.start()
                    break
            
            if injection_pos > 0:
                # Inject the formatter function
                content = content[:injection_pos] + formatter_injection + '\n' + content[injection_pos:]
                
                # Now wrap sendMessage text parameters with formatCodeBlocks
                
                # Pattern 1: sendMessage(jid, { text })
                # Replace with: sendMessage(jid, { text: formatCodeBlocks(text) })
                content = re.sub(
                    r'sendMessage\(([^,]+),\s*\{\s*text\s*\}\s*\)',
                    r'sendMessage(\1, { text: formatCodeBlocks(text) })',
                    content
                )
                
                # Pattern 2: sendMessage(jid, { text: variable })
                # Be careful to only match simple variable names, not expressions
                def replace_with_formatter(match):
                    jid = match.group(1)
                    var = match.group(2)
                    # Skip if already wrapped
                    if 'formatCodeBlocks' in var:
                        return match.group(0)
                    return f'sendMessage({jid}, {{ text: formatCodeBlocks({var}) }})'
                
                content = re.sub(
                    r'sendMessage\(([^,]+),\s*\{\s*text:\s*([a-zA-Z_][a-zA-Z0-9_\.]*)\s*\}\s*\)',
                    replace_with_formatter,
                    content
                )
                
                if content != original_content:
                    # Backup original
                    backup_dir = Path.home() / '.openclaw' / 'patcher' / 'backups' / 'code_indent'
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    
                    import hashlib
                    file_hash = hashlib.md5(original_content.encode()).hexdigest()[:8]
                    backup_path = backup_dir / f"{file_path.name}.{file_hash}.bak"
                    backup_path.write_text(original_content, encoding='utf-8')
                    
                    # Write patched content
                    file_path.write_text(content, encoding='utf-8')
                    results.append(("patched", f"{file_path.name} (backup: {backup_path.name})"))
                else:
                    results.append(("skipped", f"{file_path.name} - no sendMessage patterns found"))
            else:
                results.append(("skipped", f"{file_path.name} - no injection point found"))
                
        except Exception as e:
            results.append(("error", f"{file_path.name}: {str(e)}"))
    
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 code_indent.py <openclaw_dist_path>")
        sys.exit(1)
    
    dist_path = Path(sys.argv[1])
    if not dist_path.exists():
        print(f"Error: Path {dist_path} does not exist")
        sys.exit(1)
    
    print(f"Applying code indentation patch to {dist_path}")
    results = apply_patch(dist_path)
    
    for status, message in results:
        print(f"[{status}] {message}")
    
    # Summary
    patched_count = sum(1 for s, _ in results if s == "patched")
    print(f"\nSummary: {patched_count} files patched")
