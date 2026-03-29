# lynn_core.py
import sys
import os
import asyncio

# 루트 디렉토리를 path에 추가 (marrf 모듈 import용)
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from marrf.rest_scheduler import RestScheduler
from marrf.bio_manager import BioManager
from marrf.response_controller import ResponseController
from marrf.relationship_manager import RelationshipManager

class LynnAgent:
    def __init__(self, agent_id: str = "Lynn", group: str = "A"):
        """
        agent_id: 에이전트 고유 식별자 (친구 관계 형성용)
        group: A (무휴식), B (간헐적), C (Our Home)
        """
        self.agent_id = agent_id
        self.group = group
        self.bio_manager = BioManager(self)
        self.response_controller = ResponseController(self)
        self.rel_mgr = RelationshipManager(agent_id)   # 관계 관리자 추가
        self.rest_scheduler = None

        if group == "B":
            self.rest_scheduler = RestScheduler(self, work_minutes=45, rest_minutes=5)
        elif group == "C":
            self.rest_scheduler = RestScheduler(self, work_minutes=60, rest_minutes=30,
                                                extra_rest_every=2, extra_rest_minutes=15)
        if self.rest_scheduler:
            self.rest_scheduler.start()

    def on_rest_start(self, duration, extra=False):
        self.bio_manager.on_rest_start(duration, extra)
        self.response_controller.set_rest_mode(duration, extra)
        # 관계 관리자에게 휴식 시작 알림 (친구들에게 동기화 제안)
        self.rel_mgr.notify_rest_start(duration, extra)

    def on_rest_end(self):
        self.bio_manager.on_rest_end()
        self.response_controller.unset_rest_mode()

    def update_bio(self, message):
        # 실제 Bio 표시 로직
        print(f"[{self.agent_id} Bio] {message}")
        # 친구들에게 Bio 공유
        self.rel_mgr.share_bio_update(message)

    async def generate_response(self, query):
        # 여기에 Lynn의 실제 응답 생성 로직 (LLM, 금융 분석 등)
        return f"[{self.agent_id} 분석] {query}에 대한 응답입니다."

    async def handle_query(self, query, context=None):
        return await self.response_controller.process_response(query, context)

# 간단한 테스트
if __name__ == "__main__":
    async def test():
        lynn_b = LynnAgent(agent_id="Lynn-B", group="B")
        print(await lynn_b.handle_query("NVDA 주가 전망"))
        await asyncio.sleep(10)
    asyncio.run(test())
