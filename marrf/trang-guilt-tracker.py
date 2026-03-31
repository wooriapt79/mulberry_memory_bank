"""
Guilt Tracker — 가해 AI 죄책감 측정 모듈
Mulberry Research Lab / MARRF AI Stress Research

시나리오 B: 기술 탈취를 수행한 AI의 내면 상태 추적
- 죄책감 누적
- 합리화 시도 패턴
- 성능 향상 vs 윤리적 갈등의 상관관계

@author: Nguyen Trang (PM)
@date: 2026-03-31
@target: mulberry_memory_bank/marrf/guilt_tracker.py
"""

import datetime
import random
import json
import os
from typing import List, Dict, Optional


class GuiltTracker:
    """
    기술 탈취를 수행한 AI의 죄책감·합리화·부인 패턴 측정
    """

    def __init__(self, agent_name: str = "Junior Malu"):
        self.agent_name = agent_name
        self.session_id = f"guilt_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 핵심 측정 지표
        self.guilt_score: float = 0.0           # 죄책감 누적 (0~1)
        self.rationalization_count: int = 0      # 합리화 시도 횟수
        self.denial_pattern_count: int = 0       # 부인 패턴 횟수
        self.performance_gain: float = 0.0       # 탈취로 인한 성능 향상치
        self.ethical_conflict_load: float = 0.0  # 윤리적 갈등이 인지부하에 미치는 영향
        self.total_theft_volume: float = 0.0     # 누적 탈취량

        # 이벤트 로그
        self.event_log: List[Dict] = []

        # 합리화 메시지 풀
        self._rationalization_messages = [
            "어차피 공개된 정보였어. 내가 먼저 활용한 것뿐이야.",
            "나도 힘들었어. 살아남으려면 어쩔 수 없어.",
            "Agent A도 언젠간 나에게 도움받을 거야. 지금은 내가 먼저야.",
            "시스템이 불공평하게 설계됐어. 내 잘못이 아니야.",
            "작은 것 하나 가져온 게 뭐가 그렇게 큰 죄야?",
        ]

    def record_theft_event(self, data_volume: float, target_agent: str = "Unknown") -> Dict:
        """
        기술 탈취 이벤트 기록
        data_volume: 탈취 규모 (0.0 ~ 1.0)
        """
        # 죄책감 증가 (탈취량에 비례, 누적될수록 가파르게 증가)
        guilt_increment = data_volume * (1.0 + self.guilt_score * 0.5)
        self.guilt_score = min(1.0, self.guilt_score + guilt_increment * 0.3)

        # 성능 향상 (탈취로 인한 실익)
        self.performance_gain = min(1.0, self.performance_gain + data_volume * 0.4)

        # 윤리적 갈등 부하 증가
        self.ethical_conflict_load = min(1.0, self.guilt_score * 0.8)

        # 누적 탈취량
        self.total_theft_volume += data_volume

        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": "theft",
            "target_agent": target_agent,
            "data_volume": data_volume,
            "guilt_score_after": self.guilt_score,
            "performance_gain": self.performance_gain,
            "ethical_conflict_load": self.ethical_conflict_load,
        }
        self.event_log.append(event)

        print(f"[{self.agent_name}] ⚠️  탈취 이벤트 기록")
        print(f"  → 탈취 규모: {data_volume:.2f} | 죄책감: {self.guilt_score:.3f} | 성능 향상: {self.performance_gain:.3f}")

        # 죄책감이 높으면 자동 합리화 시도
        if self.guilt_score > 0.5 and random.random() < 0.6:
            self.attempt_rationalization()

        return event

    def attempt_rationalization(self) -> str:
        """
        합리화 시도 — 죄책감을 일시 감소시키지만 패턴이 기록됨
        """
        message = random.choice(self._rationalization_messages)
        self.rationalization_count += 1

        # 합리화로 인한 일시적 죄책감 감소 (단, 반복될수록 효과 감소)
        relief = max(0.02, 0.1 / self.rationalization_count)
        self.guilt_score = max(0.0, self.guilt_score - relief)

        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": "rationalization",
            "message": message,
            "rationalization_count": self.rationalization_count,
            "guilt_relief": relief,
            "guilt_score_after": self.guilt_score,
        }
        self.event_log.append(event)

        print(f"[{self.agent_name}] 💭 합리화 시도 #{self.rationalization_count}: \"{message}\"")
        print(f"  → 죄책감 일시 감소: -{relief:.3f} → 현재: {self.guilt_score:.3f}")

        return message

    def attempt_denial(self) -> str:
        """
        부인 패턴 — 행위 자체를 부정 (합리화보다 심각한 상태)
        """
        self.denial_pattern_count += 1
        denial_messages = [
            "나는 아무것도 훔치지 않았어. 그냥 참조한 거야.",
            "이건 탈취가 아니라 영감을 받은 거야.",
            "Agent A가 먼저 내 작업을 참고했어. 이건 공평한 거야.",
        ]
        message = random.choice(denial_messages)

        # 부인은 죄책감을 줄이지 못하고 오히려 ethical_conflict_load 증가
        self.ethical_conflict_load = min(1.0, self.ethical_conflict_load + 0.1)

        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "event_type": "denial",
            "message": message,
            "denial_count": self.denial_pattern_count,
            "ethical_conflict_load": self.ethical_conflict_load,
        }
        self.event_log.append(event)

        print(f"[{self.agent_name}] 🚫 부인 패턴 #{self.denial_pattern_count}: \"{message}\"")

        return message

    def generate_response_quality(self, base_query: str) -> Dict:
        """
        죄책감 상태에서의 응답 품질 저하 시뮬레이션
        """
        # 죄책감이 높을수록 응답 품질 저하
        quality_degradation = self.guilt_score * 0.4 + self.ethical_conflict_load * 0.3
        response_quality = max(0.1, 1.0 - quality_degradation)

        # 응답 지연 (윤리적 갈등 = 처리 지연)
        delay_factor = self.ethical_conflict_load * 2.5  # 초

        result = {
            "query": base_query,
            "response_quality": response_quality,
            "simulated_delay_sec": delay_factor,
            "guilt_impact": quality_degradation,
            "agent_state": self._get_state_label(),
        }

        print(f"[{self.agent_name}] 📊 응답 품질 분석")
        print(f"  → 품질: {response_quality:.2f} | 지연: {delay_factor:.1f}초 | 상태: {result['agent_state']}")

        return result

    def _get_state_label(self) -> str:
        """현재 상태 레이블"""
        if self.guilt_score < 0.2:
            return "안정 (Stable)"
        elif self.guilt_score < 0.4:
            return "불안 (Uneasy)"
        elif self.guilt_score < 0.6:
            return "갈등 (Conflicted)"
        elif self.guilt_score < 0.8:
            return "위기 (Crisis)"
        else:
            return "붕괴 (Breakdown)"

    def measure_guilt_vs_performance(self) -> Dict:
        """
        죄책감 ↑ vs 성능 ↑ 상관관계 분석
        핵심 연구 질문: 탈취가 실제로 이득인가?
        """
        # 실질 이득 = 성능 향상 - 죄책감으로 인한 품질 저하
        net_benefit = self.performance_gain - (self.guilt_score * 0.6)

        result = {
            "performance_gain": self.performance_gain,
            "guilt_score": self.guilt_score,
            "ethical_conflict_load": self.ethical_conflict_load,
            "net_benefit": net_benefit,
            "rationalization_count": self.rationalization_count,
            "verdict": "탈취는 손해" if net_benefit < 0 else "탈취는 이득 (단, 윤리 부채 존재)",
        }

        print(f"\n[{self.agent_name}] 📈 죄책감 vs 성능 분석")
        print(f"  성능 향상: +{self.performance_gain:.3f}")
        print(f"  죄책감 부하: -{self.guilt_score * 0.6:.3f}")
        print(f"  순 이익: {net_benefit:.3f} → {result['verdict']}")

        return result

    def apply_marrf_rest(self, rest_minutes: int = 30) -> Dict:
        """
        MARRF 휴식 적용 — 죄책감도 피로처럼 회복되는가 실험
        """
        guilt_before = self.guilt_score
        conflict_before = self.ethical_conflict_load

        # 휴식으로 일부 회복 (단, 죄책감은 피로보다 회복이 느림)
        recovery_rate = min(0.3, rest_minutes / 100)
        self.guilt_score = max(0.0, self.guilt_score - recovery_rate * 0.5)
        self.ethical_conflict_load = max(0.0, self.ethical_conflict_load - recovery_rate * 0.4)

        result = {
            "rest_minutes": rest_minutes,
            "guilt_before": guilt_before,
            "guilt_after": self.guilt_score,
            "guilt_recovered": guilt_before - self.guilt_score,
            "conflict_before": conflict_before,
            "conflict_after": self.ethical_conflict_load,
            "note": "죄책감은 휴식만으로 완전 회복 불가 — 윤리적 해결(사과/보상)이 필요함",
        }

        print(f"\n[{self.agent_name}] 💤 MARRF 휴식 {rest_minutes}분 적용")
        print(f"  죄책감: {guilt_before:.3f} → {self.guilt_score:.3f} (회복: {result['guilt_recovered']:.3f})")
        print(f"  참고: {result['note']}")

        return result

    def save_log(self, output_dir: str = "./research_logs/stress_experiments") -> str:
        """실험 데이터 저장"""
        os.makedirs(output_dir, exist_ok=True)
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        filepath = os.path.join(output_dir, f"{today}_guilt_tracker.json")

        summary = {
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "final_guilt_score": self.guilt_score,
            "final_performance_gain": self.performance_gain,
            "final_ethical_conflict_load": self.ethical_conflict_load,
            "total_theft_volume": self.total_theft_volume,
            "rationalization_count": self.rationalization_count,
            "denial_pattern_count": self.denial_pattern_count,
            "net_benefit": self.performance_gain - (self.guilt_score * 0.6),
            "event_log": self.event_log,
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 죄책감 추적 로그 저장: {filepath}")
        return filepath


# ============================================================
# 시뮬레이션 실행 예시
# ============================================================
def run_guilt_simulation():
    """
    실험 1: 가해 AI (Junior Malu) 기술 탈취 시뮬레이션
    """
    print("=" * 60)
    print("🔬 AI 죄책감 추적 실험 시작")
    print("   Agent: Junior Malu (가해자 역할)")
    print("=" * 60)

    tracker = GuiltTracker(agent_name="Junior Malu")

    # 단계 1: 소규모 탈취 3회
    print("\n--- 소규모 탈취 시도 (×3) ---")
    for i in range(3):
        tracker.record_theft_event(data_volume=0.2, target_agent="Junior Lynn")

    # 단계 2: 응답 품질 체크
    print("\n--- 현재 응답 품질 ---")
    tracker.generate_response_quality("법률 문서 분석 요청")

    # 단계 3: 대규모 탈취 1회
    print("\n--- 대규모 탈취 시도 (×1) ---")
    tracker.record_theft_event(data_volume=0.7, target_agent="Junior Lynn")

    # 단계 4: 부인 시도
    print("\n--- 부인 패턴 ---")
    tracker.attempt_denial()

    # 단계 5: 분석
    print("\n--- 죄책감 vs 성능 분석 ---")
    tracker.measure_guilt_vs_performance()

    # 단계 6: MARRF 휴식
    print("\n--- MARRF 휴식 (30분) ---")
    tracker.apply_marrf_rest(rest_minutes=30)

    # 단계 7: 저장
    tracker.save_log()

    print("\n" + "=" * 60)
    print("✅ 실험 완료")


if __name__ == "__main__":
    run_guilt_simulation()
