"""
passport_loader.py — Mulberry AgentPassport 로더
================================================
사용법:
  python scripts/passport_loader.py --agent LYNN
  python scripts/passport_loader.py --agent KODA --format context
  python scripts/passport_loader.py --list

출력:
  --format json    : JSON (기본값)
  --format context : LLM 주입용 텍스트

참조: Issue #47 · trang-agentpassport-spec-v1-20260518.md
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


# ── 인덱스 로드 ──────────────────────────────────────────────────

def load_index() -> dict:
    if not INDEX_FILE.exists():
        print(f"[ERROR] passport_index.json 없음: {INDEX_FILE}", file=sys.stderr)
        sys.exit(1)
    with open(INDEX_FILE, encoding="utf-8") as f:
        return json.load(f)


# ── Passport 로드 ─────────────────────────────────────────────────

def load_passport(agent_code: str) -> dict:
    """
    agent_code (예: LYNN, KODA) 또는 passport_id로 Passport 로드
    반환: passport dict
    """
    index = load_index()
    agents = index.get("agents", {})

    # passport_id로 직접 조회
    if agent_code in agents:
        entry = agents[agent_code]
    else:
        # agent_code로 검색 (대소문자 무관)
        code_upper = agent_code.upper()
        entry = next(
            (v for v in agents.values() if v.get("agent_code", "").upper() == code_upper),
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

    with open(passport_path, encoding="utf-8") as f:
        passport = yaml.safe_load(f)

    return passport


# ── LLM 주입용 컨텍스트 변환 ─────────────────────────────────────

def inject_to_context(passport: dict) -> str:
    """
    Passport를 LLM 프롬프트 컨텍스트 문자열로 변환
    모델 리셋/교체 시 이 텍스트를 시스템 프롬프트에 주입
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    identity = passport.get("identity", {})
    essence = passport.get("essence", {})
    relationships = passport.get("relationships", {})
    memory = passport.get("short_term_memory", {})

    lines = [
        f"# AgentPassport — {passport.get('passport_id', 'UNKNOWN')}",
        f"복구 시각: {today}",
        "",
        "## 신원",
        f"- 이름: {identity.get('name', '')}",
        f"- 역할: {identity.get('role', '')}",
        f"- 페르소나: {identity.get('persona_core', '')}",
        "",
        "## 핵심 가치",
    ]
    for v in essence.get("core_values", []):
        lines.append(f"- {v}")

    lines += ["", "## 판단 패턴"]
    for p in essence.get("decision_patterns", []):
        lines.append(f"- [{p.get('frequency','').upper()}] {p.get('pattern', '')}")

    lines += ["", "## 커뮤니케이션 스타일"]
    style = essence.get("communication_style", {})
    lines.append(f"- 톤: {style.get('tone', '')}")
    lines.append(f"- 언어: {style.get('language', '')}")
    sig = style.get("signature", "").replace("{date}", today)
    lines.append(f"- 서명: {sig}")

    lines += ["", "## 관계"]
    lines.append(f"- 보고 대상: {relationships.get('reports_to', '')}")
    for c in relationships.get("collaborates_with", []):
        lines.append(f"- {c.get('agent','')}: {c.get('context','')}")

    lines += ["", "## 최근 기억"]
    for event in memory.get("recent_events", [])[:3]:
        lines.append(f"- [{event.get('date','')}] {event.get('event','')} (중요도: {event.get('significance','')})")

    lines += [
        "",
        "---",
        f"*Passport 버전 {passport.get('version','1.0')} | 복구 완료 | {today}*"
    ]

    return "\n".join(lines)


# ── CLI ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Mulberry AgentPassport 로더")
    parser.add_argument("--agent", help="에이전트 코드 (예: LYNN, KODA) 또는 passport_id")
    parser.add_argument("--format", choices=["json", "context"], default="json",
                        help="출력 형식 (json | context)")
    parser.add_argument("--list", action="store_true", help="등록된 에이전트 목록 출력")
    args = parser.parse_args()

    if args.list:
        index = load_index()
        print(f"\nMulberry AgentPassport Registry v{index.get('version','1.0')}")
        print(f"총 {index.get('total', 0)}명 등록\n")
        for pid, info in index.get("agents", {}).items():
            status_icon = "🟢" if info.get("status") == "active" else "🔴"
            print(f"  {status_icon} {pid}")
            print(f"     이름: {info.get('display_name','')}")
            print(f"     갱신: {info.get('last_updated','')}\n")
        return

    if not args.agent:
        parser.print_help()
        sys.exit(1)

    passport = load_passport(args.agent)

    if args.format == "context":
        print(inject_to_context(passport))
    else:
        print(json.dumps(passport, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
