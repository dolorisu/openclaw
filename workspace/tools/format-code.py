#!/usr/bin/env python3
"""
Code Formatter Tool - Format JSON/YAML code with proper indentation
Usage: python3 format-code.py <language> <input-file>
"""

import sys
import json
import yaml


def format_json(code: str) -> str:
    """Format JSON with 2-space indentation."""
    try:
        parsed = json.loads(code)
        return json.dumps(parsed, indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, ValueError) as e:
        return f"ERROR: Invalid JSON - {e}"


def format_yaml(code: str) -> str:
    """Format YAML with 2-space indentation."""
    try:
        parsed = yaml.safe_load(code)
        return yaml.dump(parsed, indent=2, default_flow_style=False, allow_unicode=True)
    except yaml.YAMLError as e:
        return f"ERROR: Invalid YAML - {e}"


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 format-code.py <json|yaml> <input-file>")
        sys.exit(1)
    
    language = sys.argv[1].lower()
    input_file = sys.argv[2]
    
    try:
        with open(input_file, 'r') as f:
            code = f.read()
        
        if language in ['json', 'jsonc']:
            formatted = format_json(code)
        elif language in ['yaml', 'yml']:
            formatted = format_yaml(code)
        else:
            print(f"ERROR: Unsupported language '{language}'")
            sys.exit(1)
        
        print(formatted)
    except FileNotFoundError:
        print(f"ERROR: File '{input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
