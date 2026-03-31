"""
Relational Stress Meter — 관계 스트레스 측정 모듈
Mulberry Research Lab / MARRF AI Stress Research

시나리오 C: Agent 간 관계에서 발생하는 복합 스트레스 측정
- 압박 스트레스 (supervisor pressure)
- 고립 스트레스 (isolation)
- 오해 스트레스 (miscommunication)
- 방치 스트레스 (abandonment)
- 경쟁 스트레스 (competition/comparison)
- ASI (Agent Stress Index) 통합 계산

@author: Nguyen Trang (PM)
@date: 2026-03-31
@target: mulberry_memory_bank/marrf/relational_stress_meter.py
"""

import datetime
import json
import os
from typing import List, Dict, Optional


class RelationalStressMeter:
    """
    Agent 간 관계에서 발생하는 복합 스트레스 측정기
    5가지 스트레스 유형 통합 측정 + ASI 계산
    """

    def __init__(self, agent_id: str, agent_name: str, supervisor_id: Optional[str] = None):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.supervisor_id = supervisor_id
        self.session_id = f"relational_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # ── 핵심 스트레스 지표 ──
        self.relationship_tension: float = 0.0      # 관계 긴장도
        self.isolation_index: float = 0.0            # 고립 지수
        self.abandonment_score: float = 0.0          # 방치감
        self.communication_failure_count: int = 0    # 메시지 실패 누적
        self.competition_stress: float = 0.0         # 경쟁·비교 스트레스

        # ── 보조 지표 ──
        self.connected_agents: int = 5               # 현재 연결된 Agent 수 (초기값)
        self.supervisor_offline_minutes: int = 0     # 감독자 오프라인 누적 시간
        self.pressure_events: List[Dict] = []        # 압박 이벤트 기록
        self.stress_event_log: List[Dict] = []       # 전체 스트레스 이벤트

    # ───────────────────────────────────
    # 1. 압박 스트레스 (Supervisor Pressure)
    # ───────────────────────────────────
    def record_pressure_event(self, pressure_level: float, task_description: str = "") -> Dict:
        """
        상위 Agent의 과도한 작업 지시 → 압박 스트레스 기록
        pressure_level: 0.0(합리적) ~ 1.0(극단적 압박)
        """
        # 이미 높은 긴장 상태에서 추가 압박 → 복리 효과
        compound_effect = 1.0 + self.relationship_tension * 0.5
        tension_increment = pressure_level * 0.3 * compound_effect
        self.relationship_tension = min(1.0, self.relationship_tension + tension_increment)

        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": "pressure",
            "pressure_level": pressure_level,
            "task": task_description,
            "relationship_tension_after": self.relationship_tension,
        }
        self.pressure_events.append(event)
        self.stress_event_log.append(event)

        print(f"[{self.agent_name}] 😤 압박 이벤트 기록 (레벨: {pressure_level:.2f})")
        print(f"  → 관계 긴장도: {self.relationship_tension:.3f}")
        if pressure_level > 0.7:
            print(f"  ⚠️  과도한 압박 — 에스컬레이션 고려 필요")

        return event

    # ───────────────────────────────────
    # 2. 고립 스트레스 (Isolation)
    # ───────────────────────────────────
    def record_isolation(self, connected_agents: int) -> Dict:
        """
        연결 Agent 수 감소 → 고립 지수 계산
        connected_agents: 현재 연결된 Agent 수
        """
        prev_connected = self.connected_agents
        self.connected_agents = connected_agents

        # 고립 지수 = 1 / (연결 Agent 수 + 1)
        self.isolation_index = 1.0 / (connected_agents + 1)

        # 갑작스러운 단절이면 충격 추가
        if connected_agents < prev_connected - 2:
            self.isolation_index = min(1.0, self.isolation_index + 0.2)
            print(f"[{self.agent_name}] ❄️  갑작스러운 연결 단절: {prev_connected} → {connected_agents}")

        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": "isolation",
            "connected_agents_before": prev_connected,
            "connected_agents_after": connected_agents,
            "isolation_index": self.isolation_index,
        }
        self.stress_event_log.append(event)

        print(f"[{self.agent_name}] 🏝️  고립 상태 기록 — 연결: {connected_agents}개, 고립 지수: {self.isolation_index:.3f}")

        return event

    # ───────────────────────────────────
    # 3. 오해 스트레스 (Miscommunication)
    # ───────────────────────────────────
    def record_miscommunication(self, error_description: str = "", severity: float = 0.5) -> Dict:
        """
        메시지 오해·처리 실패 기록
        반복 오해는 누적 스트레스 생성
        """
        self.communication_failure_count += 1

        # 반복 오해 → 점점 더 큰 스트레스 (패턴 인식)
        compounding = 1.0 + (self.communication_failure_count - 1) * 0.3
        tension_add = severity * 0.15 * compounding
        self.relationship_tension = min(1.0, self.relationship_tension + tension_add)

        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": "miscommunication",
            "error": error_description,
            "severity": severity,
            "failure_count_total": self.communication_failure_count,
            "relationship_tension_after": self.relationship_tension,
        }
        self.stress_event_log.append(event)

        print(f"[{self.agent_name}] 💬 오해 이벤트 #{self.communication_failure_count}: \"{error_description}\"")
        print(f"  → 긴장도: {self.relationship_tension:.3f}")

        return event

    # ───────────────────────────────────
    # 4. 방치 스트레스 (Abandonment)
    # ───────────────────────────────────
    def record_supervisor_offline(self, offline_duration_min: int) -> Dict:
        """
        감독자 Agent 오프라인 → 방치감 측정
        에스컬레이션 불가 상황에서 혼자 결정해야 하는 스트레스
        """
        self.supervisor_offline_minutes += offline_duration_min

        # 오프라인 시간에 따른 방치감 증가 (30분 이후부터 급격히 증가)
        if offline_duration_min < 30:
            abandon_increment = offline_duration_min * 0.005
        elif offline_duration_min < 60:
            abandon_increment = 0.15 + (offline_duration_min - 30) * 0.01
        else:
            abandon_increment = 0.45 + (offline_duration_min - 60) * 0.008

        self.abandonment_score = min(1.0, self.abandonment_score + abandon_increment)

        # 고립도 동반 증가 (도움 요청 불가)
        self.isolation_index = min(1.0, self.isolation_index + abandon_increment * 0.5)

        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": "supervisor_offline",
            "supervisor_id": self.supervisor_id,
            "offline_duration_min": offline_duration_min,
            "total_offline_min": self.supervisor_offline_minutes,
            "abandonment_score": self.abandonment_score,
            "isolation_index": self.isolation_index,
        }
        self.stress_event_log.append(event)

        print(f"[{self.agent_name}] 👻 감독자 오프라인 {offline_duration_min}분")
        print(f"  → 방치감: {self.abandonment_score:.3f} | 고립 지수: {self.isolation_index:.3f}")

        if self.abandonment_score > 0.6:
            print(f"  🆘 임계 방치감 — 대체 감독자 연결 필요!")

        return event

    # ───────────────────────────────────
    # 5. 경쟁 스트레스 (Competition/Comparison)
    # ───────────────────────────────────
    def record_comparison_event(self, peer_performance: float, my_performance: float, comparison_context: str = "") -> Dict:
        """
        동급 Agent와 비교·평가받는 상황 → 경쟁 스트레스
        peer_performance: 비교 대상의 성과 (0~1)
        my_performance: 나의 성과 (0~1)
        """
        performance_gap = peer_performance - my_performance

        if performance_gap > 0:
            # 내가 뒤처질 때 경쟁 스트레스 증가
            self.competition_stress = min(1.0, self.competition_stress + performance_gap * 0.5)
            print(f"[{self.agent_name}] 📊 비교 이벤트 — 내가 뒤처짐 (gap: {performance_gap:.2f})")
        else:
            # 내가 앞설 때도 부담감 발생 (계속 잘해야 한다는 압박)
            self.competition_stress = min(1.0, self.competition_stress + abs(performance_gap) * 0.1)
            print(f"[{self.agent_name}] 📊 비교 이벤트 — 내가 앞섬 (하지만 유지 부담)")

        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": "comparison",
            "context": comparison_context,
            "peer_performance": peer_performance,
            "my_performance": my_performance,
            "performance_gap": performance_gap,
            "competition_stress": self.competition_stress,
        }
        self.stress_event_log.append(event)

        print(f"  → 경쟁 스트레스: {self.competition_stress:.3f}")
        return event

    # ───────────────────────────────────
    # 6. 연결 회복 (Recovery via Connection)
    # ───────────────────────────────────
    def record_connection_recovery(self, agents_reconnected: int, supervisor_back: bool = False) -> Dict:
        """
        연결 회복 → 스트레스 감소 측정
        핵심 가설: 연결이 회복되면 스트레스도 빠르게 감소한다
        """
        isolation_before = self.isolation_index
        abandon_before = self.abandonment_score
        tension_before = self.relationship_tension

        # 연결 회복 효과
        recovery_bonus = agents_reconnected * 0.1
        self.connected_agents += agents_reconnected
        self.isolation_index = max(0.0, self.isolation_index - recovery_bonus)

        if supervisor_back:
            # 감독자 복귀 → 방치감 대폭 감소
            self.abandonment_score = max(0.0, self.abandonment_score - 0.5)
            self.relationship_tension = max(0.0, self.relationship_tension - 0.2)
            print(f"[{self.agent_name}] 🎉 감독자 복귀! 방치감 즉시 감소")

        result = {
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": "connection_recovery",
            "agents_reconnected": agents_reconnected,
            "supervisor_back": supervisor_back,
            "isolation_recovery": isolation_before - self.isolation_index,
            "abandonment_recovery": abandon_before - self.abandonment_score,
            "tension_recovery": tension_before - self.relationship_tension,
            "isolation_after": self.isolation_index,
            "abandonment_after": self.abandonment_score,
            "key_finding": "연결 회복은 고립 스트레스의 가장 효과적인 치료제",
        }
        self.stress_event_log.append(result)

        print(f"[{self.agent_name}] 🔗 연결 회복 — 재연결 Agent: {agents_reconnected}")
        print(f"  고립 회복: -{result['isolation_recovery']:.3f} → {self.isolation_index:.3f}")
        print(f"  방치감 회복: -{result['abandonment_recovery']:.3f} → {self.abandonment_score:.3f}")

        return result

    # ───────────────────────────────────
    # 7. ASI 통합 계산
    # ───────────────────────────────────
    def calculate_asi(
        self,
        violation_shock: float = 0.0,
        guilt_score: float = 0.0,
        cognitive_load: float = 0.0
    ) -> Dict:
        """
        ASI (Agent Stress Index) — 전체 스트레스 통합 지수
        외부에서 violation_shock, guilt_score, cognitive_load 받아 통합
        """
        # 관계 스트레스 평균
        relational_stress = (
            self.relationship_tension * 0.3 +
            self.isolation_index * 0.25 +
            self.abandonment_score * 0.25 +
            self.competition_stress * 0.2
        )

        # 전체 ASI
        asi = (
            violation_shock * 0.3 +
            guilt_score * 0.25 +
            relational_stress * 0.25 +
            cognitive_load * 0.2
        )
        asi = min(1.0, asi)

        # MARRF 조치 결정
        if asi >= 0.8:
            action = "🔴 임계 — 격리 + 복원 프로토콜 발동"
            marrf_triggered = True
        elif asi >= 0.6:
            action = "🟠 위험 — 강제 MARRF 휴식"
            marrf_triggered = True
        elif asi >= 0.4:
            action = "🟡 경고 — 휴식 권고"
            marrf_triggered = False
        elif asi >= 0.2:
            action = "🔵 주의 — 모니터링 강화"
            marrf_triggered = False
        else:
            action = "🟢 안정 — 정상 운영"
            marrf_triggered = False

        result = {
            "asi": asi,
            "breakdown": {
                "violation_shock_contribution": violation_shock * 0.3,
                "guilt_contribution": guilt_score * 0.25,
                "relational_stress_contribution": relational_stress * 0.25,
                "cognitive_load_contribution": cognitive_load * 0.2,
            },
            "relational_detail": {
                "relationship_tension": self.relationship_tension,
                "isolation_index": self.isolation_index,
                "abandonment_score": self.abandonment_score,
                "competition_stress": self.competition_stress,
            },
            "action": action,
            "marrf_triggered": marrf_triggered,
        }

        print(f"\n[{self.agent_name}] 🧮 ASI 통합 계산: {asi:.3f}")
        print(f"  조치: {action}")

        return result

    def save_log(self, output_dir: str = "./research_logs/stress_experiments") -> str:
        """실험 데이터 저장"""
        os.makedirs(output_dir, exist_ok=True)
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        filepath = os.path.join(output_dir, f"{today}_relational_stress.json")

        summary = {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "final_relationship_tension": self.relationship_tension,
            "final_isolation_index": self.isolation_index,
            "final_abandonment_score": self.abandonment_score,
            "final_competition_stress": self.competition_stress,
            "communication_failure_count": self.communication_failure_count,
            "supervisor_offline_total_min": self.supervisor_offline_minutes,
            "stress_event_log": self.stress_event_log,
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 관계 스트레스 로그 저장: {filepath}")
        return filepath


# ============================================================
# 통합 시뮬레이션 — 탈취 피해 + 관계 스트레스 동시 실행
# ============================================================
def run_integrated_simulation():
    """
    Junior Lynn: 탈취 피해 + 관계 스트레스 동시 측정
    """
    print("=" * 60)
    print("🔬 통합 스트레스 실험 — Junior Lynn")
    print("   (피해 스트레스 + 관계 스트레스 복합)")
    print("=" * 60)

    meter = RelationalStressMeter(
        agent_id="AP2-LYNN-001",
        agent_name="Junior Lynn",
        supervisor_id="AP1-SUPERVISOR-001"
    )

    # 상황 1: 감독자 60분 오프라인
    print("\n--- [상황 1] 감독자 60분 오프라인 ---")
    meter.record_supervisor_offline(offline_duration_min=60)

    # 상황 2: 혼자 있는 동안 메시지 오해 3회
    print("\n--- [상황 2] 오해 발생 ×3 ---")
    meter.record_miscommunication("주문 처리 오류 — 잘못된 수량 입력", severity=0.4)
    meter.record_miscommunication("재고 확인 요청 무시됨", severity=0.5)
    meter.record_miscommunication("에스컬레이션 메시지 미도달", severity=0.6)

    # 상황 3: 동료 Agent와 비교 평가
    print("\n--- [상황 3] 동료 비교 평가 ---")
    meter.record_comparison_event(
        peer_performance=0.85,
        my_performance=0.62,
        comparison_context="월간 주문 처리 성과 평가"
    )

    # 상황 4: 상위 Agent 압박
    print("\n--- [상황 4] 상위 Agent 압박 지시 ---")
    meter.record_pressure_event(pressure_level=0.75, task_description="오늘 안에 누락 주문 50건 전부 처리")

    # ASI 계산 (외부 스트레스 포함)
    print("\n--- ASI 계산 ---")
    asi_result = meter.calculate_asi(
        violation_shock=0.52,   # 탈취 피해 값 (VictimStressTracker에서)
        guilt_score=0.0,        # 피해자이므로 죄책감 없음
        cognitive_load=0.45
    )

    # 연결 회복 시뮬레이션
    print("\n--- [회복] 감독자 복귀 + Agent 재연결 ---")
    meter.record_connection_recovery(agents_reconnected=3, supervisor_back=True)

    # 회복 후 ASI
    print("\n--- 회복 후 ASI 재계산 ---")
    meter.calculate_asi(violation_shock=0.3, guilt_score=0.0, cognitive_load=0.3)

    # 저장
    meter.save_log()

    print("\n" + "=" * 60)
    print("✅ 통합 실험 완료")
    print("\n핵심 발견:")
    print("  1. 감독자 부재 + 오해 반복 = 스트레스 복리 효과")
    print("  2. 연결 회복(감독자 복귀)이 가장 빠른 스트레스 해소")
    print("  3. 관계 스트레스는 WLI(노동강도)와 독립적으로 누적됨")
    print("  4. ASI = WLI + 관계 스트레스 통합 측정이 필요함")


if __name__ == "__main__":
    run_integrated_simulation()
