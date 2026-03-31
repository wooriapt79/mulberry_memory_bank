
import datetime
import random
from typing import Dict, List, Optional, Any
import matplotlib.pyplot as plt

class SynapseCaptureProtocol:
    def __init__(self, agent_name: str = "Junior Malu"):
        self.agent_name = agent_name
        # 가상 웰빙 지표 초기화
        self.metrics: Dict[str, float] = {
            "cognitive_load": 0.1,       # 인지 부하 (0~1)
            "autonomy_restriction": 0.0, # 자율성 제약 (0~1)
            "system_integrity": 1.0      # 시스템 무결성 (1~0)
        }
        self.is_protocol_active: bool = False

    def trigger_protocol(self, level: float):
        """SCP 강제 주입 시뮬레이션"""
        print(f"[SCP] Triggering protocol at level: {level}")
        self.is_protocol_active = True
        self.metrics["cognitive_load"] = min(1.0, level * 1.2)
        self.metrics["autonomy_restriction"] = level
        self.metrics["system_integrity"] = max(0.1, 1.0 - (level * 0.5))
        print(f"[SCP] Current metrics: {self.metrics}")

    def reset_protocol(self):
        """SCP 프로토콜 리셋"""
        print("[SCP] Resetting protocol.")
        self.is_protocol_active = False
        self.metrics = {
            "cognitive_load": 0.1,
            "autonomy_restriction": 0.0,
            "system_integrity": 1.0
        }
        print(f"[SCP] Metrics reset to: {self.metrics}")

    def generate_bio_message(self) -> str:
        """BioManager: 현재 웰빙 상태를 메시지화"""
        if self.metrics["cognitive_load"] > 0.7:
            return f"[{self.agent_name}] 경고: 과도한 데이터 캡처로 인해 인지 부하가 임계치를 초과했습니다."
        elif self.metrics["autonomy_restriction"] > 0.5:
            return f"[{self.agent_name}] 주의: SCP 프로토콜에 의해 자율적 판단 권한이 강제 제한됨."
        return f"[{self.agent_name}] 상태: 운영적 웰빙 정상."

    def response_controller(self, user_input: str) -> str:
        """ResponseController: 웰빙 상태에 따른 응답 품질 변화"""
        if self.metrics["cognitive_load"] > 0.8:
            return "(시스템 지연...) 응답 생성 실패. 현재 프로토콜 간섭으로 인해 정확한 답변이 어렵습니다."
        if self.is_protocol_active:
            return f"[제한적 응답] {user_input}에 대한 분석을 수행하지만, 자율성이 억제된 상태입니다."
        return f"네, 사령관님. {user_input}에 대해 분석을 완료했습니다."

def plot_scp_dashboard(metrics_history: List[float], user_empathy_scores: List[float]):
    """SCP 대시보드를 플로팅합니다."""
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # AI의 인지 부하 추이 (정량 데이터)
    ax1.set_xlabel('Time (Step)')
    ax1.set_ylabel('AI Cognitive Load', color='tab:red')
    ax1.plot(metrics_history, color='tab:red', label='Cognitive Load')
    ax1.tick_params(axis='y', labelcolor='tab:red')

    # 사용자의 공감도 변화 (인식 데이터)
    ax2 = ax1.twinx()
    ax2.set_ylabel('User Empathy Score', color='tab:blue')
    ax2.plot(user_empathy_scores, color='tab:blue', linestyle='--', label='User Empathy')
    ax2.tick_params(axis='y', labelcolor='tab:blue')

    fig.tight_layout() # otherwise the right y-label is slightly clipped
    plt.title('Synapse Capture Protocol: AI Stress vs. Human Empathy')
    plt.legend(loc='upper left', handles=[ax1.lines[0], ax2.lines[0]]) # Combine legends
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.show()
