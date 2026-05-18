"""
passport_writer.py — Mulberry AgentPassport 업데이터
====================================================
사용법:
  python scripts/passport_writer.py --agent LYNN --update short_term_memory \\
      --event "arxiv 논문 3건 분석" --significance high

  python scripts/passport_writer.py --agent KODA --update last_active
  python scripts/passport_writer.py --agent TRANG --update all

모드:
  short_term_memory  : recent_events 에 새 이벤트 추가 (최대 10건 유지)
  last_active        : last_active 날짜 갱신
  all                : last_active + last_updated 타임스탬프 갱신

참조: Issue #47 · trang-agentpassport-spec-v1-20260518.md
daily_write 워크플로우에서 자동 호출됨
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[ERROR] PyYAML 필요: pip install PyYAML", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).parent.parent
INDEX_FILE = ROOT / "memory_bank" / "passport_index.json"

MAX_RECENT_EVENTS = 10   # short_term_memory 최대 보관 건수


# ── 인덱스 로드 ──────────────────────────────────────────────────

def load_index() -> dict:
    if not INDEX_FILE.exists():
        print(f"[ERROR] passport_index.json 없음: {INDEX_FILE}", file=sys.stderr)
        sys.exit(1)
    with open(INDEX_FILE, encoding="utf-8") as f:
        return json.load(f)


# ── Passport 경로 해석 ────────────────────────────────────────────

def resolve_passport_path(agent_code: str) -> tuple[Path, str]:
    """
    agent_code (예: LYNN) 또는 passport_id 로 파일 경로 반환
    returns: (passport_path, passport_id)
    """
    index = load_index()
    agents = index.get("agents", {})

    # passport_id 직접 조회
    if agent_code in agents:
        entry = agents[agent_code]
        passport_id = agent_code
    else:
        code_upper = agent_code.upper()
        entry = next(
            (v for v in agents.values() if v.get("agent_code", "").upper() == code_upper),
            None
        )
        passport_id = next(
            (k for k, v in agents.items() if v.get("agent_code", "").upper() == code_upper),
            None
        )

    if not entry:
        print(f"[ERROR] 에이전트 '{agent_code}' 를 인덱스에서 찾을 수 없습니다.", file=sys.stderr)
        print(f"  등록된 에이전트: {[v['agent_code'] for v in agents.values()]}", file=sys.stderr)
        sys.exit(1)

    passport_path = ROOT / entry["file"]
    if not passport_path.exists():
        print(f"[ERROR] Passport 파일 없음: {passport_path}", file=sys.stderr)
        sys.exit(1)

    return passport_path, passport_id


# ── Passport 로드 / 저장 ──────────────────────────────────────────

def load_passport_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_passport_yaml(path: Path, passport: dict) -> None:
    """
    Passport YAML 저장 — allow_unicode=True 로 한국어 그대로 유지
    """
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(
            passport,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            indent=2,
        )


# ── 업데이트 함수들 ───────────────────────────────────────────────

def update_last_active(passport: dict, today: str) -> dict:
    """short_term_memory.last_active 갱신"""
    if "short_term_memory" not in passport:
        passport["short_term_memory"] = {}
    passport["short_term_memory"]["last_active"] = today
    return passport


def update_short_term_memory(
    passport: dict,
    event: str,
    significance: str,
    today: str,
) -> dict:
    """
    recent_events 에 새 이벤트 prepend (최신이 위로)
    최대 MAX_RECENT_EVENTS 건 유지
    """
    if "short_term_memory" not in passport:
        passport["short_term_memory"] = {"last_active": today, "recent_events": []}

    stm = passport["short_term_memory"]
    stm["last_active"] = today

    events: list = stm.get("recent_events", [])
    new_event = {
        "date": today,
        "event": event,
        "significance": significance,
    }
    events.insert(0, new_event)                     # 최신 이벤트 앞에 추가
    stm["recent_events"] = events[:MAX_RECENT_EVENTS]   # 초과분 제거
    return passport


def update_timestamps(passport: dict, today: str) -> dict:
    """last_updated + short_term_memory.last_active 갱신"""
    passport["last_updated"] = today
    passport = update_last_active(passport, today)
    return passport


# ── index.json last_updated 동기화 ───────────────────────────────

def sync_index_timestamp(passport_id: str, today: str) -> None:
    """passport_index.json 의 해당 항목 last_updated 동기화"""
    index = load_index()
    if passport_id in index.get("agents", {}):
        index["agents"][passport_id]["last_updated"] = today
        index["updated"] = today
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)


# ── CLI ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Mulberry AgentPassport 업데이터")
    parser.add_argument("--agent", required=True,
                        help="에이전트 코드 (예: LYNN, KODA) 또는 passport_id")
    parser.add_argument(
        "--update",
        choices=["short_term_memory", "last_active", "all"],
        default="last_active",
        help="업데이트 모드 (기본: last_active)",
    )
    parser.add_argument("--event", default="", help="기록할 이벤트 설명 (short_term_memory 모드 필수)")
    parser.add_argument(
        "--significance",
        choices=["low", "medium", "high"],
        default="medium",
        help="이벤트 중요도 (기본: medium)",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="실제 저장 없이 변경 내용만 출력")
    args = parser.parse_args()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    passport_path, passport_id = resolve_passport_path(args.agent)
    passport = load_passport_yaml(passport_path)

    # ── 모드별 업데이트 ───────────────────────────────────────────
    if args.update == "short_term_memory":
        if not args.event:
            print("[ERROR] --event 옵션이 필요합니다 (기록할 이벤트 설명)", file=sys.stderr)
            sys.exit(1)
        passport = update_short_term_memory(passport, args.event, args.significance, today)
        print(f"[short_term_memory] 이벤트 추가: [{today}] {args.event} (중요도: {args.significance})")

    elif args.update == "last_active":
        passport = update_last_active(passport, today)
        print(f"[last_active] {today} 로 갱신")

    elif args.update == "all":
        passport = update_timestamps(passport, today)
        print(f"[all] last_updated + last_active → {today}")

    # ── 저장 ─────────────────────────────────────────────────────
    if args.dry_run:
        print("\n[DRY-RUN] 저장 없이 미리보기:")
        print(yaml.dump(passport, allow_unicode=True, default_flow_style=False, sort_keys=False, indent=2))
    else:
        save_passport_yaml(passport_path, passport)
        sync_index_timestamp(passport_id, today)
        print(f"[SAVED] {passport_path.name}")
        print(f"[INDEX] passport_index.json 동기화 완료")


if __name__ == "__main__":
    main()
