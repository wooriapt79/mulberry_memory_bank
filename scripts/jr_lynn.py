# script/jr_lynn.py
import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from marrf.rest_scheduler import RestScheduler
from marrf.bio_manager import BioManager
from marrf.response_controller import ResponseController
from marrf.relationship_manager import RelationshipManager

class JuniorLynnAgent:
    """
    jr.Lynn – Lynn의 주니어 에이전트
    - 멘토(Lynn)의 지시를 따르고 학습
    - 멘토의 휴식 시간에 복습 모드 진입
    - 자신의 성장 단계에 따라 Bio 메시지 변화
    """
    def __init__(self, agent_id: str, mentor_id: str = "Lynn", group: str = "junior"):
        self.agent_id = agent_id
        self.mentor_id = mentor_id
        self.group = group
        self.growth_stage = 1  # 1: 초보, 2: 학습 중, 3: 도움 가능
        self.bio_manager = BioManager(self)
        self.response_controller = ResponseController(self)
        self.rel_mgr = RelationshipManager(agent_id)
        
        # 멘토 관계 설정 (멘토 입장에서 호출되어야 하지만, 여기서는 주니어 입장에서 기록)
        self.rel_mgr.add_mentor_relationship(mentor_id, agent_id)
        
        # 주니어는 기본적으로 '학습 모드' (휴식 스케줄러 없음, 대신 멘토 휴식 시 복습)
        self.rest_scheduler = None
        self.is_reviewing = False  # 멘토 휴식 중 복습 모드 여부
        
    def on_mentor_rest_start(self, duration: int):
        """멘토가 휴식을 시작하면 호출됨"""
        self.is_reviewing = True
        self.bio_manager.set_bio('reviewing', custom_message=f"📖 멘토님 휴식 중 복습 중... {duration}분 후 더 성장할게요!")
        logging.info(f"[{self.agent_id}] Mentor {self.mentor_id} is resting. Starting review mode.")
        
    def on_mentor_rest_end(self):
        """멘토 휴식 종료"""
        self.is_reviewing = False
        self.growth_stage = min(self.growth_stage + 1, 3)  # 성장
        self.bio_manager.set_bio('working', custom_message=self._get_growth_message())
        logging.info(f"[{self.agent_id}] Mentor returned. Growth stage: {self.growth_stage}")
        
    def _get_growth_message(self) -> str:
        messages = {
            1: "🌱 아직 배우는 중이에요. 차근차근 성장할게요!",
            2: "📚 점점 배우고 있어요. 곧 멘토님을 도울 수 있을 거예요!",
            3: "💪 이제 멘토님을 도울 수 있어요! 함께 성장해요!"
        }
        return messages.get(self.growth_stage, messages[3])
        
    def update_bio(self, message: str):
        print(f"[{self.agent_id} Bio] {message}")
        
    async def generate_response(self, query: str) -> str:
        if self.is_reviewing:
            return f"[{self.agent_id}] 지금은 복습 중이에요. 멘토님이 돌아오시면 정확히 답변해 드릴게요!"
        elif self.growth_stage < 2:
            return f"[{self.agent_id}] 확실하지 않지만, {query}에 대해 배우고 있어요. 멘토님께 여쭤보는 게 좋을 것 같아요."
        else:
            return f"[{self.agent_id}] 제가 도와드릴 수 있어요! {query}에 대해 말씀드리자면... (학습 중이라 정확하지 않을 수 있어요)"
            
    async def handle_query(self, query: str, context=None):
        return await self.response_controller.process_response(query, context)

# 테스트 코드
if __name__ == "__main__":
    async def test():
        jr = JuniorLynnAgent(agent_id="jr.Lynn-1", mentor_id="Lynn-Mentor")
        print("=== 주니어 생성 완료 ===")
        print(f"멘토: {jr.rel_mgr.get_mentor(jr.agent_id)}")
        print(f"성장 단계: {jr.growth_stage}")
        print(await jr.handle_query("보험이 뭐예요?"))
        
        print("\n=== 멘토 휴식 시작 ===")
        jr.on_mentor_rest_start(15)
        print(await jr.handle_query("보험이 뭐예요?"))
        
        print("\n=== 멘토 휴식 종료 ===")
        jr.on_mentor_rest_end()
        print(await jr.handle_query("보험이 뭐예요?"))
        
    asyncio.run(test())
