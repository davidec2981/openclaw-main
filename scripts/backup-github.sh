#!/usr/bin/env bash
set -e
DATE=$(date -u '+%Y-%m-%d %H:%M UTC')

backup_repo() {
  local dir=$1 label=$2
  cd "$dir"
  if [[ -n $(git status --porcelain) ]]; then
    git add -A
    git commit -m "Auto-backup ${DATE}" || true
  fi
  git push origin master 2>&1 || echo "[$label] push failed"
  echo "[$label] done"
}

backup_repo /root/.openclaw/workspace            "openclaw-main"
backup_repo /root/.openclaw/workspace-trading     "openclaw-trading"
backup_repo /root/.openclaw/workspace-airdrop     "openclaw-airdrop"
backup_repo /root/.openclaw/workspace-polyclaw    "openclaw-polyclaw"
backup_repo /root/.openclaw/workspace-robocop     "openclaw-robocop"
backup_repo /root/.openclaw/workspace-aihf        "openclaw-aihf"

echo "=== Backup completo: ${DATE} ==="
