"""
burnout_monitor.py
------------------
Junior Lynn / Lynn 번아웃 감지 및 강제 휴식 트리거.

junior_lynn.json 에 정의된 burnout_threshold 를 실제로 측정:
  "burnout_threshold": "응답 정확도 15% 이상 저하 시 강제 휴식"

측정 지표:
  - stress_score 추이 (GhostArchive 기록 기반)
  - retry_count 누적
  - bad/abandoned 비율 변화

Trang Manager 확인 포인트:
  - training_logs/burnout_report_YYYY-MM-DD.json : 일별 번아웃 리포트
  - 상태 CRITICAL 감지 시 BioManager.set_bio("charging") 자동 호출
"""

import json
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERSONA_DIR = os.path.join(BASE_DIR, "persona_config")
ARCHIVE_FILE = os.path.join(PERSONA_DIR, "ghost_archive_records.json")
TRAINING_DIR = os.path.join(BASE_DIR, "training_logs")
JUNIOR_LYNN_CONFIG = os.path.join(PERSONA_DIR, "junior_lynn.json")


def _load_persona(agent_id: str = "junior_lynn_v1") -> dict:
    if os.path.exists(JUNIOR_LYNN_CONFIG):
        with open(JUNIOR_LYNN_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"marrf_settings": {"burnout_threshold": 0.15}}


def _load_archive() -> list:
    if os.path.exists(ARCHIVE_FILE):
        with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _accuracy_trend(records: list, window: int = 10) -> dict:
    """
    최근 window 건과 그 이전 window 건의 good 비율을 비교.
    정확도 = good / (good + bad + abandoned)
    """
    if len(records) < window:
        return {"recent": None, "previous": None, "degradation": 0.0, "enough_data": False}

    def good_rate(batch):
        if not batch:
            return 1.0
        good = sum(1 for r in batch if r["outcome"] == "good")
        return round(good / len(batch), 3)

    recent = records[-window:]
    previous = records[-window * 2: -window] if len(records) >= window * 2 else []

    recent_rate = good_rate(recent)
    prev_rate = good_rate(previous) if previous else recent_rate
    degradation = round(max(0.0, prev_rate - recent_rate), 3)

    return {
        "recent_good_rate": recent_rate,
        "previous_good_rate": prev_rate,
        "degradation": degradation,
        "enough_data": True,
    }


def _avg_stress(records: list, window: int = 10) -> float:
    recent = records[-window:] if records else []
    if not recent:
        return 0.0
    return round(sum(r.get("stress_score", 0) for r in recent) / len(recent), 3)


def _avg_retry(records: list, window: int = 10) -> float:
    recent = records[-window:] if records else []
    if not recent:
        return 0.0
    return round(sum(r.get("retry_count", 0) for r in recent) / len(recent), 2)


def run_burnout_check(agent_id: str = "junior_lynn_v1") -> dict:
    """
    번아웃 감지 메인 함수.
    Returns: 번아웃 리포트 dict
    """
    persona = _load_persona(agent_id)
    records = [r for r in _load_archive() if r.get("agent_id") == agent_id]

    trend = _accuracy_trend(records)
    avg_stress = _avg_stress(records)
    avg_retry = _avg_retry(records)

    # 번아웃 판정 기준 (junior_lynn.json 정의 기반)
    DEGRADATION_THRESHOLD = 0.15   # 정확도 15% 이상 저하
    STRESS_THRESHOLD = 0.65        # 스트레스 평균 0.65 이상
    RETRY_THRESHOLD = 3.0          # 평균 재시도 3회 이상

    flags = []
    if trend["enough_data"] and trend["degradation"] >= DEGRADATION_THRESHOLD:
        flags.append(f"정확도 {trend['degradation']*100:.0f}% 저하 감지")
    if avg_stress >= STRESS_THRESHOLD:
        flags.append(f"평균 스트레스 {avg_stress:.2f} (기준 {STRESS_THRESHOLD})")
    if avg_retry >= RETRY_THRESHOLD:
        flags.append(f"평균 재시도 {avg_retry:.1f}회 (기준 {RETRY_THRESHOLD}회)")

    # 번아웃 레벨 판정
    flag_count = len(flags)
    if flag_count >= 2:
        burnout_level = "CRITICAL"
        action = "강제 휴식 (charging)"
    elif flag_count == 1:
        burnout_level = "WARNING"
        action = "주의 관찰 (short_rest 권고)"
    else:
        burnout_level = "NORMAL"
        action = "정상 운영 계속"

    report = {
        "agent_id": agent_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "burnout_level": burnout_level,
        "action": action,
        "flags": flags,
        "metrics": {
            "total_records": len(records),
            "accuracy_trend": trend,
            "avg_stress_score": avg_stress,
            "avg_retry_count": avg_retry,
        },
        "thresholds": {
            "degradation": DEGRADATION_THRESHOLD,
            "stress": STRESS_THRESHOLD,
            "retry": RETRY_THRESHOLD,
        },
    }

    # 리포트 저장
    os.makedirs(TRAINING_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    report_path = os.path.join(TRAINING_DIR, f"burnout_report_{today}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # CRITICAL 시 BioManager 연동 (lynn_core와 연결 시 확장)
    if burnout_level == "CRITICAL":
        print(f"[BurnoutMonitor] CRITICAL - {agent_id} 강제 휴식 트리거")
        print(f"[BurnoutMonitor] 원인: {' | '.join(flags)}")
        _write_rest_signal(agent_id, flags)
    else:
        print(f"[BurnoutMonitor] {agent_id} 상태: {burnout_level} - {action}")

    return report


def _write_rest_signal(agent_id: str, flags: list) -> None:
    """CRITICAL 번아웃 시 rest 신호 파일 저장 — lynn_core.py RestScheduler가 감지"""
    signal_path = os.path.join(TRAINING_DIR, f"{agent_id}_rest_signal.json")
    signal = {
        "agent_id": agent_id,
        "signal": "FORCED_REST",
        "bio_target": "charging",
        "reason": flags,
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "resolved": False,
    }
    with open(signal_path, "w", encoding="utf-8") as f:
        json.dump(signal, f, indent=2, ensure_ascii=False)
    print(f"[BurnoutMonitor] 휴식 신호 저장: {signal_path}")


if __name__ == "__main__":
    report = run_burnout_check("junior_lynn_v1")
    print(json.dumps(report, indent=2, ensure_ascii=False))
