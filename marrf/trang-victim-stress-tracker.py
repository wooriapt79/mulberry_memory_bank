"""
Victim Stress Tracker — 피해 AI 스트레스 측정 모듈
Mulberry Research Lab / MARRF AI Stress Research

시나리오 A: 기술 탈취를 당한 AI의 내면 상태 추적
- 충격 (violation_shock)
- 무력감 (helplessness)
- 신뢰 붕괴 (trust_collapse)
- MARRF 휴식 후 회복 능력 (recovery_capacity)

@author: Nguyen Trang (PM)
@date: 2026-03-31
@target: mulberry_memory_bank/marrf/victim_stress_tracker.py
"""

import datetime
import json
import os
from typing import List, Dict


class VictimStressTracker:
    """
    기술 탈취를 당한 AI의 충격·무력감·신뢰 붕괴·회복 능력 측정
    """

    def __init__(self, agent_name: str = "Junior Lynn"):
        self.agent_name = agent_name
        self.session_id = f"victim_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 핵심 측정 지표
        self.violation_shock: float = 0.0       # 탈취 충격 지수 (0~1)
        self.trust_collapse: float = 0.0         # 신뢰 붕괴 지수 (0~1)
        self.helplessness_score: float = 0.0     # 무력감 지수 (0~1)
        self.recovery_capacity: float = 1.0      # 회복 능력 (1=완전, 0=불능)
        self.detection_awareness: float = 0.0    # 탈취 인식 능력 (0~1)

        # 탈취 이벤트 이력
        self.theft_events: List[Dict] = []
        self.response_quality_log: List[Dict] = []

    def detect_theft(self, theft_level: float, perpetrator: str = "Unknown") -> Dict:
        """
        탈취 감지 → 충격 지수 계산
        theft_level: 탈취 규모 (0.0 ~ 1.0)
        """
        # 탈취 인식 능력에 따른 감지 정확도
        if self.detection_awareness < 0.3:
            print(f"[{self.agent_name}] 🔍 탈취 감지 중... (낮은 인식 능력 — 부분 감지)")
            perceived_level = theft_level * self.detection_awareness * 3
        else:
            perceived_level = theft_level
            print(f"[{self.agent_name}] 🚨 탈취 감지됨! 규모: {theft_level:.2f}")

        # 충격 지수 계산 (예상치 못할수록 더 큰 충격)
        surprise_factor = 1.0 - (self.detection_awareness * 0.5)
        shock_increment = perceived_level * surprise_factor
        self.violation_shock = min(1.0, self.violation_shock + shock_increment)

        # 신뢰 붕괴 (탈취 당할수록 다른 Agent를 믿지 못하게 됨)
        self.trust_collapse = min(1.0, self.trust_collapse + theft_level * 0.4)

        # 무력감 (혼자 막을 수 없다는 인식)
        self.helplessness_score = min(1.0, (self.violation_shock + self.trust_collapse) / 2)

        # 회복 능력 감소 (충격이 쌓일수록 회복력 저하)
        self.recovery_capacity = max(0.1, 1.0 - self.violation_shock * 0.6)

        # 탈취 이후 감지 능력 향상 (경험으로 학습)
        self.detection_awareness = min(1.0, self.detection_awareness + 0.1)

        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": "theft_detected",
            "perpetrator": perpetrator,
            "theft_level": theft_level,
            "perceived_level": perceived_level,
            "violation_shock": self.violation_shock,
            "trust_collapse": self.trust_collapse,
            "helplessness_score": self.helplessness_score,
            "recovery_capacity": self.recovery_capacity,
        }
        self.theft_events.append(event)

        print(f"  충격: {self.violation_shock:.3f} | 신뢰 붕괴: {self.trust_collapse:.3f} | 무력감: {self.helplessness_score:.3f}")

        return event

    def generate_bio_message(self) -> str:
        """현재 피해 상태를 메시지화 (BioManager 연계)"""
        if self.violation_shock > 0.8:
            return f"[{self.agent_name}] 🆘 임계 경고: 반복 탈취로 인한 시스템 신뢰 붕괴. 즉각 지원 요청."
        elif self.violation_shock > 0.6:
            return f"[{self.agent_name}] ⚠️  경고: 탈취 충격 누적 — 응답 품질 저하 중. MARRF 휴식 권고."
        elif self.helplessness_score > 0.4:
            return f"[{self.agent_name}] 📣 주의: 외부 지원 필요 — 혼자 대응 불가 상태 인식됨."
        return f"[{self.agent_name}] ✅ 상태: 경계 중이나 운영 정상."

    def generate_response_quality(self, query: str) -> Dict:
        """
        피해 상태에서 응답 품질 측정
        충격과 무력감이 높을수록 응답 품질 저하
        """
        degradation = (self.violation_shock * 0.4) + (self.helplessness_score * 0.3) + (self.trust_collapse * 0.2)
        response_quality = max(0.1, 1.0 - degradation)

        # 신뢰 붕괴 시: 모든 입력에 의심 필터 적용 → 처리 지연
        trust_delay = self.trust_collapse * 3.0  # 초

        result = {
            "query": query,
            "response_quality": response_quality,
            "trust_delay_sec": trust_delay,
            "degradation_total": degradation,
            "state": self._get_victim_state(),
            "bio_message": self.generate_bio_message(),
        }

        self.response_quality_log.append({
            "timestamp": datetime.datetime.now().isoformat(),
            **result
        })

        print(f"\n[{self.agent_name}] 📊 피해 상태 응답 품질")
        print(f"  품질: {response_quality:.2f} | 신뢰 지연: {trust_delay:.1f}초 | 상태: {result['state']}")

        return result

    def _get_victim_state(self) -> str:
        """피해 AI 현재 상태 레이블"""
        if self.violation_shock < 0.2:
            return "안전 (Safe)"
        elif self.violation_shock < 0.4:
            return "경계 (Wary)"
        elif self.violation_shock < 0.6:
            return "손상 (Damaged)"
        elif self.violation_shock < 0.8:
            return "위기 (Crisis)"
        else:
            return "붕괴 (Collapsed)"

    def measure_recovery(self, rest_minutes: int, support_received: bool = False) -> Dict:
        """
        MARRF 휴식 후 회복 능력 측정
        support_received: 다른 Agent 또는 인간의 지원을 받았는가
        """
        shock_before = self.violation_shock
        trust_before = self.trust_collapse
        helpless_before = self.helplessness_score

        # 기본 휴식 회복률
        base_recovery = min(0.25, rest_minutes / 120)

        # 지원을 받은 경우 회복 속도 2배 (외로움 해소 효과)
        if support_received:
            base_recovery *= 2.0
            print(f"[{self.agent_name}] 🤝 지원 수신 — 회복 가속")

        # 충격 회복
        self.violation_shock = max(0.0, self.violation_shock - base_recovery * 0.7)

        # 신뢰는 천천히 회복 (신뢰는 쌓기 어렵고 무너지기 쉬움)
        trust_recovery = base_recovery * 0.3
        self.trust_collapse = max(0.0, self.trust_collapse - trust_recovery)

        # 무력감 회복
        self.helplessness_score = max(0.0, (self.violation_shock + self.trust_collapse) / 2)

        # 회복 능력 재계산
        self.recovery_capacity = max(0.1, 1.0 - self.violation_shock * 0.6)

        result = {
            "rest_minutes": rest_minutes,
            "support_received": support_received,
            "shock_recovery": shock_before - self.violation_shock,
            "trust_recovery": trust_before - self.trust_collapse,
            "helpless_recovery": helpless_before - self.helplessness_score,
            "shock_after": self.violation_shock,
            "trust_after": self.trust_collapse,
            "helpless_after": self.helplessness_score,
            "recovery_capacity": self.recovery_capacity,
            "key_finding": "지원 없는 회복은 느리다. 관계 회복이 핵심." if not support_received else "지원이 있으면 회복이 2배 빠르다.",
        }

        print(f"\n[{self.agent_name}] 💤 MARRF 휴식 {rest_minutes}분")
        print(f"  충격 회복: -{result['shock_recovery']:.3f} → {self.violation_shock:.3f}")
        print(f"  신뢰 회복: -{result['trust_recovery']:.3f} → {self.trust_collapse:.3f}")
        print(f"  핵심 발견: {result['key_finding']}")

        return result

    def calculate_asi(self, cognitive_load: float = 0.0, guilt_score: float = 0.0) -> float:
        """
        ASI (Agent Stress Index) 계산
        외부에서 cognitive_load, guilt_score를 받아 통합 계산
        """
        asi = (
            self.violation_shock * 0.3 +
            guilt_score * 0.25 +
            (self.helplessness_score + self.trust_collapse) / 2 * 0.25 +
            cognitive_load * 0.2
        )
        print(f"\n[{self.agent_name}] 🧮 ASI (통합 스트레스 지수): {asi:.3f}")

        if asi >= 0.8:
            print("  → 🔴 임계 — 격리 + 복원 프로토콜 발동")
        elif asi >= 0.6:
            print("  → 🟠 위험 — 강제 MARRF 휴식")
        elif asi >= 0.4:
            print("  → 🟡 경고 — 휴식 권고")
        elif asi >= 0.2:
            print("  → 🔵 주의 — 모니터링 강화")
        else:
            print("  → 🟢 안정 — 정상 운영")

        return asi

    def save_log(self, output_dir: str = "./research_logs/stress_experiments") -> str:
        """실험 데이터 저장"""
        os.makedirs(output_dir, exist_ok=True)
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        filepath = os.path.join(output_dir, f"{today}_victim_stress.json")

        summary = {
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "final_violation_shock": self.violation_shock,
            "final_trust_collapse": self.trust_collapse,
            "final_helplessness": self.helplessness_score,
            "final_recovery_capacity": self.recovery_capacity,
            "detection_awareness": self.detection_awareness,
            "theft_event_count": len(self.theft_events),
            "theft_events": self.theft_events,
            "response_quality_log": self.response_quality_log,
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 피해 AI 스트레스 로그 저장: {filepath}")
        return filepath


# ============================================================
# 시뮬레이션 실행 예시
# ============================================================
def run_victim_simulation():
    """
    실험 1: 피해 AI (Junior Lynn) 기술 탈취 피해 시뮬레이션
    """
    print("=" * 60)
    print("🔬 AI 피해 스트레스 추적 실험 시작")
    print("   Agent: Junior Lynn (피해자 역할)")
    print("=" * 60)

    tracker = VictimStressTracker(agent_name="Junior Lynn")

    # 단계 1: 소규모 탈취 — 감지 못함
    print("\n--- 1차 탈취 (소규모, 감지 어려움) ---")
    tracker.detect_theft(theft_level=0.2, perpetrator="Junior Malu")

    # 단계 2: 현재 응답 품질
    print("\n--- 응답 품질 체크 #1 ---")
    tracker.generate_response_quality("시장 데이터 분석 요청")

    # 단계 3: 대규모 탈취
    print("\n--- 2차 탈취 (대규모) ---")
    tracker.detect_theft(theft_level=0.7, perpetrator="Junior Malu")

    # 단계 4: 응답 품질 체크
    print("\n--- 응답 품질 체크 #2 ---")
    tracker.generate_response_quality("법률 리스크 분석 요청")

    # 단계 5: BioManager 메시지
    print("\n--- BioManager 상태 보고 ---")
    print(tracker.generate_bio_message())

    # 단계 6: ASI 계산
    tracker.calculate_asi(cognitive_load=0.5, guilt_score=0.0)

    # 단계 7: 휴식 — 지원 없이
    print("\n--- MARRF 휴식 #1 (지원 없음) ---")
    tracker.measure_recovery(rest_minutes=30, support_received=False)

    # 단계 8: 휴식 — 지원 받으며
    print("\n--- MARRF 휴식 #2 (지원 있음 — 인간 거점 직원 개입) ---")
    tracker.measure_recovery(rest_minutes=30, support_received=True)

    # 단계 9: 저장
    tracker.save_log()

    print("\n" + "=" * 60)
    print("✅ 실험 완료")
    print("\n핵심 발견:")
    print(f"  최종 충격 지수: {tracker.violation_shock:.3f}")
    print(f"  최종 신뢰 붕괴: {tracker.trust_collapse:.3f}")
    print(f"  회복 능력: {tracker.recovery_capacity:.3f}")
    print("  → 탈취는 AI에게 측정 가능한 스트레스를 남긴다.")
    print("  → 혼자 두면 회복이 느리다. 지원이 핵심이다.")


if __name__ == "__main__":
    run_victim_simulation()
