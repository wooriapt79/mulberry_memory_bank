# lynn_core.py
import asyncio
from marrf.rest_scheduler import RestScheduler
from marrf.bio_manager import BioManager
from marrf.response_controller import ResponseController

class LynnAgent:
    def __init__(self, group="A"):  # group: A (무휴식), B (간헐적), C (Our Home)
        self.group = group
        self.bio_manager = BioManager(self)
        self.response_controller = ResponseController(self)
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

    def on_rest_end(self):
        self.bio_manager.on_rest_end()
        self.response_controller.unset_rest_mode()

    def update_bio(self, message):
        # 실제 Bio 표시 로직 (예: 로그, API 호출, DB 저장)
        print(f"[Lynn Bio] {message}")
        # 추가로 mulberry_memory_bank의 상태 기록 기능과 연동 가능

    async def generate_response(self, query):
        # 여기에 Lynn의 실제 응답 생성 로직 (LLM, 금융 분석 등)
        # 예: return await some_llm_call(query)
        return f"[Lynn 분석] {query}에 대한 응답입니다."

    async def handle_query(self, query, context=None):
        return await self.response_controller.process_response(query, context)

# 간단한 테스트
if __name__ == "__main__":
    async def test():
        lynn_b = LynnAgent(group="B")
        print(await lynn_b.handle_query("NVDA 주가 전망"))
        await asyncio.sleep(10)  # 실제로는 스케줄러가 동작
    asyncio.run(test())
