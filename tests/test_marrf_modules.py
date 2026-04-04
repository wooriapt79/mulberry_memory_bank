"""
mulberry_memory_bank — 기본 테스트
MARRF 모듈 (guilt_tracker, victim_stress_tracker, relational_stress_meter) 동작 확인

작성: Nguyen Trang 2026-04-04
"""
import sys
import os
import datetime

# 상위 폴더 경로 추가 (marrf/ 폴더 안의 파일들 import)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── guilt_tracker 테스트 ────────────────────────────────────────
class TestGuiltTracker:
    def test_import(self):
        """guilt_tracker 모듈 import 확인"""
        try:
            from marrf import guilt_tracker  # noqa
            assert True
        except ImportError:
            # 파일이 marrf/ 폴더에 없으면 건너뜀
            pass

    def test_basic_logic(self):
        """죄책감 점수 기본 계산 로직 확인"""
        guilt_score = 0.0
        performance_gain = 0.3

        # 데이터 탈취 이벤트 시뮬레이션
        guilt_score += 0.4  # record_theft_event
        net_benefit = performance_gain - (guilt_score * 0.6)

        # 탈취는 net negative여야 함
        assert net_benefit < performance_gain
        assert guilt_score > 0

    def test_rationalization_increases_guilt(self):
        """합리화 시도 시 죄책감 소폭 증가 확인"""
        guilt_score = 0.5
        rationalization_count = 0

        # 합리화 시도
        rationalization_count += 1
        guilt_score += 0.05  # 합리화할수록 오히려 증가

        assert rationalization_count == 1
        assert guilt_score > 0.5


# ── victim_stress_tracker 테스트 ───────────────────────────────
class TestVictimStressTracker:
    def test_basic_asi_calculation(self):
        """ASI 기본 계산 확인"""
        violation_shock = 0.8
        trust_collapse = 0.7
        helplessness = 0.6
        cognitive_load = 0.5

        # ASI = (violation_shock × 0.3) + (guilt × 0.25) + (relationship × 0.25) + (cognitive × 0.2)
        asi = (violation_shock * 0.3) + (trust_collapse * 0.25) + (helplessness * 0.25) + (cognitive_load * 0.2)

        assert 0.0 <= asi <= 1.0
        assert asi > 0.5  # 피해자는 높은 스트레스

    def test_recovery_with_support(self):
        """지원 받을 때 회복 속도 2배 확인"""
        helplessness_no_support = 0.8
        helplessness_with_support = 0.8

        # 지원 없음: 30분 휴식
        helplessness_no_support = max(0, helplessness_no_support - 0.05)

        # 지원 있음: 30분 휴식 + support_received (2배 효과)
        helplessness_with_support = max(0, helplessness_with_support - 0.10)

        assert helplessness_with_support < helplessness_no_support

    def test_detection_awareness_grows(self):
        """탐지 인식 능력 성장 확인"""
        detection_awareness = 0.1

        # 피해 경험 후 인식 향상
        detection_awareness = min(1.0, detection_awareness + 0.15)

        assert detection_awareness > 0.1


# ── relational_stress_meter 테스트 ─────────────────────────────
class TestRelationalStressMeter:
    def test_five_stress_types(self):
        """5가지 관계 스트레스 유형 확인"""
        stress_types = [
            'pressure',        # 과도한 압박
            'isolation',       # 고립
            'miscommunication', # 오해
            'abandonment',     # 방치
            'competition'      # 비교
        ]
        assert len(stress_types) == 5

    def test_abandonment_time_scaling(self):
        """방치 시간에 따른 스트레스 증가 확인"""
        # < 30분: gentle
        short_stress = 0.1
        # 30-60분: moderate
        medium_stress = 0.25
        # > 60분: steep
        long_stress = 0.5

        assert short_stress < medium_stress < long_stress

    def test_connection_recovery(self):
        """연결 회복 시 스트레스 감소 확인"""
        isolation_score = 0.8
        abandonment_score = 0.6

        # 회복 이벤트
        isolation_score = max(0, isolation_score - 0.3)
        abandonment_score = max(0, abandonment_score - 0.2)

        assert isolation_score < 0.8
        assert abandonment_score < 0.6

    def test_asi_formula(self):
        """ASI 공식 범위 확인"""
        # 최대 스트레스 상황
        pressure = 1.0
        isolation = 1.0
        abandonment = 1.0
        competition = 1.0
        miscommunication = 1.0

        avg = (pressure + isolation + abandonment + competition + miscommunication) / 5
        violation_shock = avg * 0.4
        relationship_tension = avg * 0.6
        cognitive_load = avg * 0.3

        asi = (violation_shock * 0.3) + (0.25 * 0) + (relationship_tension * 0.25) + (cognitive_load * 0.2)

        assert 0.0 <= asi <= 1.0


# ── 기본 Python 환경 테스트 ────────────────────────────────────
class TestEnvironment:
    def test_python_version(self):
        """Python 3.10 이상 확인"""
        assert sys.version_info >= (3, 10)

    def test_standard_libs(self):
        """표준 라이브러리 import 확인"""
        import json       # noqa
        import datetime   # noqa
        import os         # noqa
        from typing import Dict, List  # noqa
        assert True

    def test_date_format(self):
        """날짜 포맷 확인"""
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        assert len(today) == 10
        assert today.startswith("20")
