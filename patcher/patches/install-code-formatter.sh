#!/bin/bash
# Code Formatter Patcher for OpenClaw
# Auto-install: Run this script to patch OpenClaw gateway

TARGET="$HOME/.npm-global/lib/node_modules/openclaw/dist/outbound-biHc8dAV.js"
BACKUP="${TARGET}.backup.codeformatter"

echo "🔧 Installing Code Formatter Patch..."

if [ ! -f "$TARGET" ]; then
    echo "❌ OpenClaw not found!"
    exit 1
fi

cp "$TARGET" "$BACKUP"

# Apply patch
python3 << PYTHON
import re
with open("$TARGET", "r") as f:
    content = f.read()

patch = """
	// CODE-FORMATTER-PATCH
	if (text && typeof text === \"string\") {
		if ((text.startsWith(\"[\") && text.endsWith(\"]\")) ||
		    (text.startsWith(\"{\") && text.endsWith(\"}\"))) {
			try {
				const parsed = JSON.parse(text);
				text = JSON.stringify(parsed, null, 2);
				console.log(\"[CODE-FORMATTER] JSON formatted\");
			} catch (e) {}
		}
	}
"""

content = re.sub(r"(let text = body;)", r"\1" + patch, content)

with open("$TARGET", "w") as f:
    f.write(content)
PYTHON

echo "✅ Patch installed!"
echo "🔄 Restarting gateway..."
systemctl --user restart openclaw-gateway
echo "✅ Done!"

