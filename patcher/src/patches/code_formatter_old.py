"""
Code Formatter Patch - Automatically indent code blocks in model output

Fixes GPT-5.3-codex behavior of generating flat/unindented code examples.
"""

import json
import re
from pathlib import Path
from typing import List, Tuple


def format_json(code: str) -> str:
    """Format JSON with 2-space indentation."""
    try:
        parsed = json.loads(code)
        return json.dumps(parsed, indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, ValueError):
        # If parsing fails, return original
        return code


def format_yaml(code: str) -> str:
    """Format YAML with proper indentation (basic implementation)."""
    lines = code.split('\n')
    formatted = []
    indent_level = 0
    
    for line in lines:
        stripped = line.lstrip()
        if not stripped:
            formatted.append('')
            continue
            
        # Count colons to detect key: value or key:
        if ':' in stripped:
            # If line ends with colon, it's a parent key
            if stripped.rstrip().endswith(':'):
                formatted.append('  ' * indent_level + stripped)
                indent_level += 1
            else:
                # It's a key-value pair
                formatted.append('  ' * indent_level + stripped)
        elif stripped.startswith('-'):
            # List item
            formatted.append('  ' * indent_level + stripped)
        else:
            formatted.append('  ' * indent_level + stripped)
            
        # Decrease indent if we see fewer leading spaces in next iteration
        # This is simplified - real YAML parsing would be more complex
        
    return '\n'.join(formatted)


def format_code_block(code: str, language: str) -> str:
    """Format code block based on language."""
    if language in ['json', 'jsonc']:
        return format_json(code)
    elif language in ['yaml', 'yml']:
        return format_yaml(code)
    # For other languages (js, ts, python, etc.) we'd need language-specific formatters
    # For now, return as-is
    return code


def format_code_blocks_in_text(text: str) -> str:
    """Find and format all code blocks in markdown text."""
    # Pattern to match ```language\ncode\n```
    pattern = r'```(\w+)\n(.*?)\n```'
    
    def replace_block(match):
        language = match.group(1)
        code = match.group(2)
        formatted = format_code_block(code, language)
        return f'```{language}\n{formatted}\n```'
    
    return re.sub(pattern, replace_block, text, flags=re.DOTALL)


def apply_patch(openclaw_dist: Path) -> List[Tuple[str, str]]:
    """
    Apply code formatter patch to channel output handlers.
    
    This patch intercepts message output and formats code blocks.
    """
    results = []
    
    # Find channel-web files (this is where WhatsApp/Telegram messages are sent)
    channel_files = list(openclaw_dist.glob("channel-web-*.js"))
    
    if not channel_files:
        results.append(("error", "No channel-web-*.js files found"))
        return results
    
    for file_path in channel_files:
        try:
            content = file_path.read_text(encoding='utf-8')
            original = content
            
            # Find the sendMessage or deliverMessage function
            # Look for where text content is being sent
            # Pattern: We want to intercept right before message delivery
            
            # Search for common patterns like:
            # - await channel.send(text)
            # - return { text: content }
            # - message.text = ...
            
            # Inject formatter before text is sent
            injection = '''
// Auto-format code blocks (added by code_formatter patch)
function formatCodeBlocks(text) {
    if (typeof text !== 'string') return text;
    const pattern = /```(\\w+)\\n([\\s\\S]*?)\\n```/g;
    return text.replace(pattern, (match, lang, code) => {
        if (lang === 'json' || lang === 'jsonc') {
            try {
                const parsed = JSON.parse(code);
                return \`\\\`\\\`\\\`\${lang}\\n\${JSON.stringify(parsed, null, 2)}\\n\\\`\\\`\\\`\`;
            } catch (e) {
                return match;
            }
        }
        // Add more formatters here for YAML, etc.
        return match;
    });
}
'''
            
            # Find a good injection point - look for where messages are being constructed
            # This is tricky without seeing the actual code structure
            # Let's try to inject near the top of the file after imports
            
            if 'formatCodeBlocks' not in content:
                # Find first function or class definition
                insert_pos = content.find('function ') or content.find('class ') or content.find('const ')
                if insert_pos > 0:
                    content = content[:insert_pos] + injection + '\n' + content[insert_pos:]
                    
                    # Now find places where text is being sent and wrap with formatter
                    # This is a simplified approach - we'd need to analyze the actual code structure
                    content = content.replace(
                        'text: content',
                        'text: formatCodeBlocks(content)'
                    )
                    content = content.replace(
                        'await channel.send(text)',
                        'await channel.send(formatCodeBlocks(text))'
                    )
                    
                    if content != original:
                        file_path.write_text(content, encoding='utf-8')
                        results.append(("patched", str(file_path)))
                    else:
                        results.append(("skipped", f"{file_path.name} - no suitable injection point found"))
                else:
                    results.append(("skipped", f"{file_path.name} - no injection point found"))
            else:
                results.append(("already_patched", str(file_path)))
                
        except Exception as e:
            results.append(("error", f"{file_path.name}: {str(e)}"))
    
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python code_formatter.py <openclaw_dist_path>")
        sys.exit(1)
    
    dist_path = Path(sys.argv[1])
    results = apply_patch(dist_path)
    
    for status, message in results:
        print(f"[{status}] {message}")
