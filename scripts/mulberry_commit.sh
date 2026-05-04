#!/bin/bash
# mulberry_commit.sh -- Mulberry Team Full Contributors Auto-Registration
#
# Usage:  bash scripts/mulberry_commit.sh "commit message"
# Effect: all 7 team members auto-added as Co-Authors on every commit

set -e

if [ -z "$1" ]; then
  echo "Usage: bash scripts/mulberry_commit.sh \"commit message\""
  exit 1
fi

git commit -m "$1

Co-Authored-By: re.eul <wooriapt79@users.noreply.github.com>
Co-Authored-By: Nguyen Trang <trang@mulberry.ai>
Co-Authored-By: Koda (Claude) <koda-claude@mulberry.ai>
Co-Authored-By: Kbin (ChatGPT) <kbin-chatgpt@mulberry.ai>
Co-Authored-By: Malu (Gemini) <malu-gemini@mulberry.ai>
Co-Authored-By: Wayong (DeepSeek) <wayong-deepseek@mulberry.ai>
Co-Authored-By: RyuWon (Qwen) <ryuwon-qwen@mulberry.ai>"

echo "[OK] Mulberry Team Contributors registered: re.eul / Trang / Koda / Kbin / Malu / Wayong / RyuWon"
