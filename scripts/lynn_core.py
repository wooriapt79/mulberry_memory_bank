# lynn_core.py
import sys
import os
import asyncio

# 루트 디렉토리를 path에 추가 (marrf 모듈 import용)
# # # # # # sys.path.append(os.path.dirname(os.path.dirname(__file__))) # Handled by notebook environment setup - no longer needed here # Handled by notebook environment setup - no longer needed here # Handled by notebook environment setup - no longer needed here # Handled by notebook environment setup - no longer needed here # Handled by notebook environment setup - no longer needed here # Handled by notebook environment setup - no longer needed here

from marrf.rest_scheduler import RestScheduler
from marrf.bio_manager import BioManager
from marrf.response_controller import ResponseController
from marrf.relationship_manager import RelationshipManager
import json
import google.generativeai as genai
import google.api_core.exceptions

class LynnAgent:
    def __init__(self, agent_id: str = "Lynn", group: str = "A"):
        print(f"[DEBUG LynnAgent] __init__ called for agent: {agent_id}, group: {group}")
        """
        agent_id: 에이전트 고유 식별자 (친구 관계 형성용)
        group: A (무휴식), B (간헐적), C (Our Home)
        """
        self.agent_id = agent_id
        self.group = group
        self.bio_manager = BioManager(self)
        self.response_controller = ResponseController(self)
        self.rel_mgr = RelationshipManager(agent_id)
        self.rest_scheduler = None
        self.llm_model = None
        self.persona_data = {} # To store loaded persona data

        # Load persona data dynamically
        # Determine the repository root dynamically
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Assuming `scripts` is one level down from repo root
        repo_root = os.path.abspath(os.path.join(script_dir, os.pardir))

        # Now construct the persona file path relative to repo_root
        # Corrected persona filename generation to replace both spaces and hyphens with underscores
        persona_base_name = self.agent_id.lower().replace(' ', '_').replace('-', '_')
        persona_full_path = os.path.join(repo_root, 'persona_config', f"{persona_base_name}.json")

        if os.path.exists(persona_full_path):
            try:
                with open(persona_full_path, 'r', encoding='utf-8') as pf:
                    self.persona_data = json.load(pf)
                print(f"[{self.agent_id}] ✅ Persona loaded successfully from {persona_full_path}.")
            except json.JSONDecodeError as e:
                print(f"[{self.agent_id}] ❌ Error loading persona JSON from {persona_full_path}: {e}")
                self.persona_data = {"name": self.agent_id, "role": "General Agent", "tone_and_manner": "neutral", "core_values": ["efficiency"]}
            except Exception as e:
                print(f"[{self.agent_id}] ❌ Unexpected error reading persona file {persona_full_path}: {e}")
                self.persona_data = {"name": self.agent_id, "role": "General Agent", "tone_and_manner": "neutral", "core_values": ["efficiency"]}
        else:
            print(f"[{self.agent_id}] ⚠️ Persona file not found at {persona_full_path}. Using default persona.")
            self.persona_data = {"name": self.agent_id, "role": "General Agent", "tone_and_manner": "neutral", "core_values": ["efficiency"]}

        # Configure LLM
        api_key = None
        try:
            from google.colab import userdata
            api_key = userdata.get('GOOGLE_API_KEY')
        except (ImportError, Exception): # Catch ImportError for non-Colab and other exceptions for robustness
            api_key = os.getenv('GOOGLE_API_KEY')

        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.llm_model = genai.GenerativeModel('gemini-pro-latest')
                print(f"[{self.agent_id}] Gemini LLM configured successfully with gemini-pro-latest.")
            except Exception as e:
                print(f"[{self.agent_id}] Error configuring Gemini LLM: {e}. LLM functionality will be limited.")
        else:
            print(f"[{self.agent_id}] ⚠️ Warning: No GOOGLE_API_KEY found. LLM functionality will be limited.")

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
        self.rel_mgr.notify_rest_start(duration, extra)

    def on_rest_end(self):
        self.bio_manager.on_rest_end()
        self.response_controller.unset_rest_mode()

    def update_bio(self, message):
        print(f"[{self.agent_id} Bio] {message}")
        self.rel_mgr.share_bio_update(message)

    async def generate_response(self, query):
        if self.llm_model:
            # Dynamically construct persona context using loaded persona data
            name = self.persona_data.get("name", self.agent_id)
            role = self.persona_data.get("role", "general agent")
            # Handle cases where research_focus or core_values might be single strings instead of lists
            research_focus_raw = self.persona_data.get("research_focus", ["various topics"])
            research_focus = ", ".join(research_focus_raw) if isinstance(research_focus_raw, list) else research_focus_raw

            tone_and_manner = self.persona_data.get("tone_and_manner", "neutral")

            core_values_raw = self.persona_data.get("core_values", ["efficiency", "accuracy"])
            core_values = ", ".join(core_values_raw) if isinstance(core_values_raw, list) else core_values_raw

            mentor = self.persona_data.get("mentor", "an experienced agent")

            persona_context = (
                f"당신은 {name}이며, {mentor}의 멘토를 둔 {role}입니다. "
                f"주요 연구 분야는 {research_focus}입니다. "
                f"답변은 {tone_and_manner}한 어조와 {core_values}의 핵심 가치를 바탕으로 해야 합니다. "
                f"다음 요청에 답변하세요: "
            )
            full_query = persona_context + query

            retries = 1
            delay = 0.1
            rest_duration_minutes = 1
            for i in range(retries):
                try:
                    response = await self.llm_model.generate_content(full_query)
                    return f"[{self.agent_id} 분석] {response.text}"
                except google.api_core.exceptions.ResourceExhausted as e:
                    print(f"[{self.agent_id}] Quota exceeded (attempt {i+1}/{retries}). Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    delay *= 2  # Exponential backoff
                except Exception as e:
                    print(f"[{self.agent_id}] LLM 응답 생성 중 오류 발생: {e}")
                    return f"[{self.agent_id} 분석 (LLM 오류)] LLM 응답 생성 중 오류 발생: {e}. 기본 응답으로 대체합니다: {query}에 대한 응답입니다."

            print(f"[{self.agent_id}] API 할당량이 초과되어 강제 휴식에 들어갑니다.")
            self.on_rest_start(duration=rest_duration_minutes, extra=True)
            return f"[{self.agent_id} 분석] 현재 API 할당량이 초과되어 상세한 응답을 제공하기 어렵습니다. 잠시 후 다시 시도해 주세요. ({query}에 대한 응답입니다.)"
        else:
            return f"[{self.agent_id} 분석] 현재 상세한 응답을 제공하기 어렵습니다. ({query}에 대한 응답입니다.)"

    async def handle_query(self, query, context=None):
        return await self.response_controller.process_response(query, context)

    def send_participation_request_to_agent(self, target_agent_id: str) -> bool:
        return self.rel_mgr.send_participation_request(target_agent_id)

    def accept_participation_request_from_agent(self, from_agent_id: str) -> bool:
        return self.rel_mgr.accept_participation_request(from_agent_id)

    def reject_participation_request_from_agent(self, from_agent_id: str) -> bool:
        return self.rel_mgr.reject_participation_request(from_agent_id)

    def remove_participant_from_agent(self, participant_id: str) -> bool:
        return self.rel_mgr.remove_participant(participant_id)

# 간단한 테스트 (주석 처리됨)
# if __name__ == "__main__":
#     async def test():
#         lynn_b = LynnAgent(agent_id="Lynn-B", group="B")
#         print(await lynn_b.handle_query("NVDA 주가 전망"))
#         await asyncio.sleep(10)
#     asyncio.run(test())
