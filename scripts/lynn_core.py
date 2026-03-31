# lynn_core.py
--- Content of '/content/mulberry_memory_bank/scripts/lynn_core_corrected.py' ---
# lynn_core.py
import sys
import os
import asyncio

# 루트 디렉토리를 path에 추가 (marrf 모듈 import용)
# # # # # # # sys.path.append(os.path.dirname(os.path.dirname(__file__))) # Handled by notebook environment setup - no longer needed here # Handled by notebook environment setup - no longer needed here # Handled by notebook environment setup - no longer needed here # Handled by notebook environment setup - no longer needed here # Handled by notebook environment setup - no longer needed here # Handled by notebook environment setup - no longer needed here # Handled by notebook environment setup - no longer needed here

from marrf.rest_scheduler import RestScheduler
from marrf.bio_manager import BioManager
from marrf.response_controller import ResponseController
from marrf.relationship_manager import RelationshipManager
import json
import google.generativeai as genai
import google.api_core.exceptions
from deepseek.client import DeepSeekLLM

class LynnAgent:
    def __init__(self, agent_id: str = "Lynn", group: str = "A", llm_provider: str = "gemini"):
        print(f"[DEBUG LynnAgent] __init__ called for agent: {agent_id}, group: {group}")
        """
        agent_id: Agent unique identifier (for friend relationship formation)
        group: A (No rest), B (Intermittent), C (Our Home)
        llm_provider: LLM service provider to use ("gemini" or "deepseek")
        """
        self.agent_id = agent_id
        self.group = group
        self.llm_provider = llm_provider.lower()
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

        # Configure LLM based on provider
        api_key = None
        if self.llm_provider == "gemini":
            try:
                from google.colab import userdata
                api_key = userdata.get('GOOGLE_API_KEY')
            except (ImportError, Exception):
                api_key = os.getenv('GOOGLE_API_KEY')

            if api_key:
                try:
                    genai.configure(api_key=api_key)
                    self.llm_model = genai.GenerativeModel('gemini-pro-latest')
                    print(f"[{self.agent_id}] Gemini LLM configured successfully with gemini-pro-latest.")
                except Exception as e:
                    print(f"[{self.agent_id}] Error configuring Gemini LLM: {e}. LLM functionality will be limited.")
            else:
                print(f"[{self.agent_id}] ⚠️ Warning: No GOOGLE_API_KEY found for Gemini. LLM functionality will be limited.")
        elif self.llm_provider == "deepseek":
            api_key = os.getenv('DEEPSEEK_API_KEY')
            if api_key:
                try:
                    # Ensure deepseek.api.DeepSeekLLM is imported at the top of the file
                    self.llm_model = DeepSeekLLM(api_key=api_key, model='deepseek-chat')
                    print(f"[{self.agent_id}] DeepSeek LLM configured successfully with deepseek-chat.")
                except Exception as e:
                    print(f"[{self.agent_id}] Error configuring DeepSeek LLM: {e}. LLM functionality will be limited.")
            else:
                print(f"[{self.agent_id}] ⚠️ Warning: No DEEPSEEK_API_KEY found. LLM functionality will be limited.")
        else:
            print(f"[{self.agent_id}] ❌ Error: Unsupported LLM provider: {self.llm_provider}. LLM functionality will be limited.")

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
            name = self.persona_data.get("name", self.agent_id)
            role = self.persona_data.get("role", "general agent")
            research_focus_raw = self.persona_data.get("research_focus", ["various topics"])
            research_focus = ", ".join(research_focus_raw) if isinstance(research_focus_raw, list) else research_focus_raw

            tone_and_manner = self.persona_data.get("tone_and_manner", "neutral")

            core_values_raw = self.persona_data.get("core_values", ["efficiency", "accuracy"])
            core_values = ", ".join(core_values_raw) if isinstance(core_values_raw, list) else core_values_raw

            mentor = self.persona_data.get("mentor", "an experienced agent")

            persona_context = (
                f"You are {name}, a {role} mentored by {mentor}. "
                f"Your main research area is {research_focus}. "
                f"Your responses should be {tone_and_manner} in tone and based on the core values of {core_values}. "
                f"Answer the following request: "
            )
            full_query = persona_context + query

            retries = 1
            delay = 0.1
            rest_duration_minutes = 1

            if self.llm_provider == "gemini":
                for i in range(retries):
                    try:
                        response = await self.llm_model.generate_content(full_query)
                        return f"[{self.agent_id} Analysis] {response.text}"
                    except google.api_core.exceptions.ResourceExhausted as e:
                        print(f"[{self.agent_id}] Quota exceeded (attempt {i+1}/{retries}). Retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
                        delay *= 2
                    except Exception as e:
                        print(f"[{self.agent_id}] LLM response generation error: {e}")
                        return f"[{self.agent_id} Analysis (LLM error)] LLM response generation error: {e}. Substituting with default response: Response for {query}."

                print(f"[{self.agent_id}] API quota exceeded, forcing rest.")
                self.on_rest_start(duration=rest_duration_minutes, extra=True)
                return f"[{self.agent_id} Analysis] API quota currently exceeded. Unable to provide detailed response. Please try again later. (Response for {query}.)"
            elif self.llm_provider == "deepseek":
                try:
                    messages = [{"role": "user", "content": full_query}]
                    response = await self.llm_model.chat(messages=messages)
                    return f"[{self.agent_id} Analysis] {response.choices[0].message.content}"
                except Exception as e:
                    print(f"[{self.agent_id}] DeepSeek LLM response generation error: {e}")
                    return f"[{self.agent_id} Analysis (DeepSeek LLM error)] {e}. Substituting with default response: Response for {query}."
            else:
                return f"[{self.agent_id} Analysis] Unsupported LLM provider. (Response for {query}.)"
        else:
            return f"[{self.agent_id} Analysis] Unable to provide detailed response. (Response for {query}.)"

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

# Simple test (commented out)
# if __name__ == "__main__":
#     async def test():
#         lynn_b = LynnAgent(agent_id="Lynn-B", group="B")
#         print(await lynn_b.handle_query("NVDA stock outlook"))
#         await asyncio.sleep(10)
#     asyncio.run(test())
