# ACTIVE.md (What this file is for)

This is the pointer file so we do not accidentally use legacy patch flow.

Use this script only:
`~/.openclaw/patches/apply-multibubble-dist-patch.py`

Standard run order:
1) `--status`
2) `--strict`
3) restart `openclaw-gateway`
4) test `/reset` + group multi-bubble

If docs conflict, trust `README.md` + script output.
