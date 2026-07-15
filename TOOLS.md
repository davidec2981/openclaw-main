# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## Related

- [Agent workspace](/concepts/agent-workspace)

## Memory Thresholds (Hardcoded Dist Edit)

File: `diagnostic-71wqFzEw.js` in OpenClaw dist
Backup: same dir, `.bak` suffix
Values set: RSS warn=4GiB, RSS crit=6GiB, Heap warn=3GiB, Heap crit=4GiB
Lost on `openclaw update` — reapply with:
```
cd /root/.nvm/versions/node/v24.18.0/lib/node_modules/openclaw/dist/
cp diagnostic-71wqFzEw.js diagnostic-71wqFzEw.js.bak
sed -i 's/DEFAULT_RSS_WARNING_BYTES = 1536 \* MB/DEFAULT_RSS_WARNING_BYTES = 4096 * MB/'
sed -i 's/DEFAULT_RSS_CRITICAL_BYTES = 3072 \* MB/DEFAULT_RSS_CRITICAL_BYTES = 6144 * MB/'
sed -i 's/DEFAULT_HEAP_WARNING_BYTES = 1024 \* MB/DEFAULT_HEAP_WARNING_BYTES = 3072 * MB/'
sed -i 's/DEFAULT_HEAP_CRITICAL_BYTES = 2048 \* MB/DEFAULT_HEAP_CRITICAL_BYTES = 4096 * MB/'
```
