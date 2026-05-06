"""
guardian_bridge.py
------------------
LAB face_off_*.py 철학을 BANK Lynn/Jr.Lynn 이 실제로 사용하게 연결하는 브릿지.

장승배기 헌법 구현:
  - GuardianAlgorithm : 거래 수익의 10% 사회 환원 계산
  - GhostArchive      : 모든 협상 기록 (좋은 것도, 나쁜 것도) — 에이전트의 해마

Trang Manager 확인 포인트:
  - ghost_archive_records.json : 누적 거래 기록
  - guardian_contribution.json : 환원 누계
  - face_off_*.py (LAB) 설계와 1:1 호환 구조 유지
"""

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Literal

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERSONA_DIR = os.path.join(BASE_DIR, "persona_config")
ARCHIVE_FILE = os.path.join(PERSONA_DIR, "ghost_archive_records.json")
CONTRIBUTION_FILE = os.path.join(PERSONA_DIR, "guardian_contribution.json")


# ── GuardianAlgorithm (face_off_social.py 호환) ───────────────────────────────

class GuardianAlgorithm:
    """수익의 10%를 사회에 환원 — 장승배기 헌법 1조"""

    RATE = 0.10

    @staticmethod
    def calculate_contribution(profit: float, rate: float = 0.10) -> float:
        return round(profit * rate, 2)

    @classmethod
    def record_contribution(cls, agent_id: str, profit: float) -> dict:
        contribution = cls.calculate_contribution(profit)

        os.makedirs(PERSONA_DIR, exist_ok=True)
        if os.path.exists(CONTRIBUTION_FILE):
            with open(CONTRIBUTION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {"total_donated": 0.0, "records": []}

        entry = {
            "agent_id": agent_id,
            "profit": profit,
            "contribution": contribution,
            "rate": cls.RATE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        data["records"].append(entry)
        data["total_donated"] = round(data["total_donated"] + contribution, 2)

        with open(CONTRIBUTION_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[Guardian] {agent_id} 환원액: {contribution} (누계: {data['total_donated']})")
        return entry


# ── GhostArchive (face_off_intelligence.py 호환) ──────────────────────────────

@dataclass
class NegotiationRecord:
    transaction_id: str
    agent_id: str
    customer_id: str
    outcome: Literal["good", "bad", "abandoned"]
    workflow_stage: str
    stress_level: str           # LOW / MEDIUM / HIGH / CRITICAL
    stress_score: float         # 0.0~1.0
    retry_count: int
    agent_bio_status: str       # online / rest / lunch / travel
    summary: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class GhostArchive:
    """
    에이전트의 해마 (Hippocampus).
    전원이 꺼져도(Ghost가 돼도) 기록은 남는다.
    좋은 협상도, 나쁜 협상도 — 모두 저장.
    """

    def __init__(self):
        os.makedirs(PERSONA_DIR, exist_ok=True)

    def _load(self) -> list:
        if os.path.exists(ARCHIVE_FILE):
            with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save(self, records: list) -> None:
        with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

    def record(self, entry: NegotiationRecord) -> None:
        records = self._load()
        records.append(asdict(entry))
        self._save(records)
        print(f"[GhostArchive] 기록 완료: {entry.transaction_id} / {entry.outcome}")

    def recall(self, customer_id: str) -> list:
        """고객 ID로 과거 협상 이력 조회 — 기억 복원"""
        return [r for r in self._load() if r.get("customer_id") == customer_id]

    def pattern_summary(self) -> dict:
        """
        좋은/나쁜 협상의 패턴 분석.
        스트레스 HIGH 상태에서 나쁜 협상 비율을 계산.
        """
        records = self._load()
        if not records:
            return {"total": 0, "good": 0, "bad": 0, "abandoned": 0, "stress_bad_rate": 0.0}

        total = len(records)
        good = sum(1 for r in records if r["outcome"] == "good")
        bad = sum(1 for r in records if r["outcome"] == "bad")
        abandoned = sum(1 for r in records if r["outcome"] == "abandoned")

        high_stress = [r for r in records if r["stress_level"] in ("HIGH", "CRITICAL")]
        stress_bad = sum(1 for r in high_stress if r["outcome"] in ("bad", "abandoned"))
        stress_bad_rate = round(stress_bad / len(high_stress), 2) if high_stress else 0.0

        return {
            "total": total,
            "good": good,
            "bad": bad,
            "abandoned": abandoned,
            "stress_bad_rate": stress_bad_rate,
            "insight": (
                f"스트레스 HIGH 상태에서 부정 결과 비율: {stress_bad_rate * 100:.0f}%"
                if high_stress else "스트레스 데이터 없음"
            ),
        }


# ── 통합 실행 헬퍼 ────────────────────────────────────────────────────────────

def complete_transaction(
    transaction_id: str,
    agent_id: str,
    customer_id: str,
    outcome: Literal["good", "bad", "abandoned"],
    workflow_stage: str,
    stress_score: float,
    retry_count: int,
    agent_bio_status: str,
    summary: str,
    profit: float = 0.0,
) -> dict:
    """
    거래 완료 시 호출하는 단일 진입점.
    1. GhostArchive 기록
    2. GuardianAlgorithm 10% 환원 계산 (profit > 0 && outcome == good 시)
    """
    stress_level = (
        "CRITICAL" if stress_score >= 0.8 else
        "HIGH" if stress_score >= 0.6 else
        "MEDIUM" if stress_score >= 0.35 else
        "LOW"
    )

    record = NegotiationRecord(
        transaction_id=transaction_id,
        agent_id=agent_id,
        customer_id=customer_id,
        outcome=outcome,
        workflow_stage=workflow_stage,
        stress_level=stress_level,
        stress_score=stress_score,
        retry_count=retry_count,
        agent_bio_status=agent_bio_status,
        summary=summary,
    )
    GhostArchive().record(record)

    contribution = None
    if outcome == "good" and profit > 0:
        contribution = GuardianAlgorithm.record_contribution(agent_id, profit)

    return {
        "transaction_id": transaction_id,
        "outcome": outcome,
        "stress_level": stress_level,
        "contribution": contribution,
    }


if __name__ == "__main__":
    result = complete_transaction(
        transaction_id="TX-TEST-001",
        agent_id="junior_lynn_v1",
        customer_id="C-999",
        outcome="good",
        workflow_stage="closing",
        stress_score=0.25,
        retry_count=1,
        agent_bio_status="online",
        summary="보험 상품 협상 완료. 고객 만족.",
        profit=100.0,
    )
    print("[TEST]", result)
    print("[PATTERN]", GhostArchive().pattern_summary())
