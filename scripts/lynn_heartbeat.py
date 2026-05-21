"""
lynn_heartbeat.py — Lynn 생존 신호 기록기
==========================================
성공이든 실패든 변경이 없든,
반드시 training_logs/lynn_status_YYYY-MM-DD.json 을 생성합니다.

CSA Kbin 처방 (2026-05-17):
    "실패하거나 할 일이 없어도 살아있다고 말하는 장치"

상태 흐름:
    briefing 생성됨  -> state: active
    failure_log 있음 -> state: failure
    rest_signal 있음 -> state: resting
    변경 없음        -> state: heartbeat

작성: Nguyen Trang (2026-05-17)
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
TRAINING_LOGS = ROOT / "training_logs"
DAILY_HUNTS = ROOT / "daily_hunts"
MEMORY_BANK = ROOT / "memory_bank"
PENDING_DIR = MEMORY_BANK / "pending_posts"

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
TIMESTAMP = datetime.now(timezone.utc).isoformat()
STATUS_FILE = TRAINING_LOGS / f"lynn_status_{TODAY}.json"


def detect_state():
    details = {}

    rest_signal_files = list(ROOT.glob("**/rest_signal*.json"))
    if rest_signal_files:
        latest = max(rest_signal_files, key=lambda f: f.stat().st_mtime)
        details["rest_signal_file"] = str(latest)
        return "resting", details

    today_briefings = []
    if DAILY_HUNTS.exists():
        today_briefings = [f for f in DAILY_HUNTS.rglob("*") if f.is_file() and TODAY in f.name]
    if today_briefings:
        details["briefings"] = [str(f) for f in today_briefings]
        return "active", details

    failure_files = []
    if TRAINING_LOGS.exists():
        failure_files = [f for f in TRAINING_LOGS.glob(f"*failure*{TODAY}*")]
    if failure_files:
        details["failure_logs"] = [str(f) for f in failure_files]
        return "failure", details

    processed_dir = PENDING_DIR / "_processed" if PENDING_DIR.exists() else None
    if processed_dir and processed_dir.exists():
        today_processed = [f for f in processed_dir.glob("*.md") if TODAY in f.name]
        if today_processed:
            details["relay_processed"] = len(today_processed)
            return "active", details

    return "heartbeat", details


def build_status(state, details):
    script_results = {
        "arxiv_hunter": os.getenv("LYNN_ARXIV_EXIT", "unknown"),
        "risk_logger": os.getenv("LYNN_RISK_EXIT", "unknown"),
        "memory_writer": os.getenv("LYNN_MEMORY_EXIT", "unknown"),
        "burnout_monitor": os.getenv("LYNN_BURNOUT_EXIT", "unknown"),
        "relay": os.getenv("LYNN_RELAY_EXIT", "unknown"),
    }

    pending_count = 0
    if PENDING_DIR.exists():
        pending_count = len([f for f in PENDING_DIR.glob("*.md") if not f.name.startswith("_")])

    state_messages = {
        "active":    "Lynn 정상 작동 — 오늘 briefing 생성 완료",
        "failure":   "Lynn 오류 감지 — failure log 기록됨",
        "resting":   "Lynn 휴식 중 — rest_signal 활성",
        "heartbeat": "Lynn 생존 확인 — 오늘 처리할 항목 없음",
    }

    return {
        "date": TODAY,
        "timestamp": TIMESTAMP,
        "run_id": str(uuid.uuid4()),   # 매 실행마다 고유값 — git 항상 변경 감지
        "agent": "The-Courteous-Wolf-Lynn",
        "state": state,
        "message": state_messages.get(state, f"Lynn state: {state}"),
        "details": details,
        "scripts": script_results,
        "pending_posts_count": pending_count,
        "generated_by": "lynn_heartbeat.py (Kbin 처방 v1, 2026-05-17)",
    }


def main():
    print("Lynn heartbeat 시작 —", TODAY)

    state, details = detect_state()
    status = build_status(state, details)

    TRAINING_LOGS.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"heartbeat 기록: {STATUS_FILE}")
    print(f"state   : {status['state']}")
    print(f"message : {status['message']}")
    print("Lynn은 살아있습니다.")
    sys.exit(0)


if __name__ == "__main__":
    main()
