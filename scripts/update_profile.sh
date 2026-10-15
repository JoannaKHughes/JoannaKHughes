#!/bin/bash
# Daily profile rebuild on magpie: build, commit if anything changed, push over SSH.
# cron: 15 6 * * * /mnt/ssd/github/JoannaKHughes/scripts/update_profile.sh >> $HOME/profile_update.log 2>&1
REPO="$(cd "$(dirname "$0")/.." && pwd)"
exec 9>/tmp/profile_update.lock
flock -n 9 || exit 0
cd "$REPO" || exit 1
echo "== $(date '+%F %T')"
git pull --rebase -q || { echo "pull failed"; exit 1; }
python3 scripts/build_profile.py || { echo "build failed"; exit 1; }
git add README.md assets/
git diff --cached --quiet || git commit -q -m "Update profile $(date '+%F')"
git push -q || echo "push failed"
