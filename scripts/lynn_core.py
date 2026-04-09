# lynn_core.py
# ------------------------------------------------------------
# 목적:
# - LynnAgent 핵심 로직
# - Persona 로딩
# - SkillBank / mHC 지식 로딩
# - LLM provider(gemini/deepseek) 선택
#
# CI 안정성 포인트:
# - gemini / deepseek 패키지가 없어도 import 단계에서 죽지 않도록 처리
# - API 키가 없어도 fallback mode로 동작
# ------------------------------------------------------------

import os
import json
import asyncio

# Optional dependency: Gemini
try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Optional dependency: DeepSeek
try:
    from deepseek import DeepSeek
except ImportError:
    DeepSeek = None

from marrf.rest_scheduler import RestScheduler
from marrf.bio_manager import BioManager
from marrf.response_controller import ResponseController
from marrf.relationship_manager import RelationshipManager


class LynnAgent:
    def __init__(
        self,
        agent_id: str = "Lynn",
        group: str = "A",
        llm_provider: str = "gemini",
    ):
        print(f"[DEBUG LynnAgent] __init__ called for agent: {agent_id}, group: {group}")

        """
        agent_id: Agent unique identifier (for friend relationship formation)
        group: A (No rest), B (Intermittent), C (Our Home)
        llm_provider: "gemini" | "deepseek" | others(fallback)
        """

        self.agent_id = agent_id
        self.group = group
        self.llm_provider = llm_provider.lower()

        self.bio_manager = BioManager(self)
        self.rel_mgr = RelationshipManager(agent_id)
        self.rest_scheduler = None
        self.llm_model = None
        self.persona_data = {}

        # SkillBank / mHC
        self.skill_bank = {}
        self.mhc_knowledge = {}
        self._load_built_in_knowledge()

        # ------------------------------------------------------------
        # Persona 로딩
        # scripts/lynn_core.py 기준 repo root 추정 후 persona_config 참조
        # ------------------------------------------------------------
        script_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(script_dir, os.pardir))

        persona_base_name = self.agent_id.lower().replace(" ", "_").replace("-", "_")
        persona_full_path = os.path.join(repo_root, "persona_config", f"{persona_base_name}.json")

        if os.path.exists(persona_full_path):
            try:
                with open(persona_full_path, "r", encoding="utf-8") as pf:
                    self.persona_data = json.load(pf)
                print(f"[{self.agent_id}] ✅ Persona loaded: {persona_full_path}")
            except json.JSONDecodeError as e:
                print(f"[{self.agent_id}] ❌ Persona JSON decode error: {e}")
                self.persona_data = self._default_persona()
            except Exception as e:
                print(f"[{self.agent_id}] ❌ Persona read error: {e}")
                self.persona_data = self._default_persona()
        else:
            print(f"[{self.agent_id}] ⚠️ Persona file not found: {persona_full_path} (using default)")
            self.persona_data = self._default_persona()

        # ------------------------------------------------------------
        # LLM 설정 (CI-safe fallback)
        # - 패키지 없거나 키 없으면 self.llm_model=None 으로 안전 동작
        # ------------------------------------------------------------
        self._configure_llm()

        # 그룹 B/C인 경우 휴식 스케줄러 활성화
        if self.group in ("B", "C"):
            self.rest_scheduler = RestScheduler(self.agent_id)
            print(f"[{self.agent_id}] ✅ RestScheduler initialized for group {self.group}")

        # ResponseController는 LLM 설정 이후 최종 초기화
        self.response_controller = ResponseController(self)
        print(f"[{self.agent_id}] ✅ ResponseController initialized")
        print(f"[{self.agent_id}] Initialized with persona: {self.persona_data.get('name', 'Default')}")

    # ------------------------------------------------------------
    # 내부 유틸: 기본 persona
    # ------------------------------------------------------------
    def _default_persona(self):
        return {
            "name": self.agent_id,
            "role": "General Agent",
            "tone_and_manner": "neutral",
            "core_values": ["efficiency"],
        }

    # ------------------------------------------------------------
    # 내부 유틸: LLM provider 설정
    # ------------------------------------------------------------
    def _configure_llm(self):
        # NOTE:
        # CI에서는 API 키/외부 패키지 없을 수 있음
        # -> 실패 시 예외를 던지지 않고 fallback mode(self.llm_model=None)로 전환
        if self.llm_provider == "gemini":
            api_key = None
            try:
                from google.colab import userdata
                api_key = userdata.get("GOOGLE_API_KEY")
            except Exception:
                api_key = os.getenv("GOOGLE_API_KEY")

            if genai is None or not api_key:
                print(f"[{self.agent_id}] ⚠️ Gemini unavailable (missing package/key). Fallback mode enabled.")
                self.llm_model = None
            else:
                genai.configure(api_key=api_key)
                self.llm_model = genai.GenerativeModel("gemini-pro")
                print(f"[{self.agent_id}] ✅ Gemini LLM configured.")

        elif self.llm_provider == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY")

            if DeepSeek is None or not api_key:
                print(f"[{self.agent_id}] ⚠️ DeepSeek unavailable (missing package/key). Fallback mode enabled.")
                self.llm_model = None
            else:
                self.llm_model = DeepSeek(api_key=api_key)
                print(f"[{self.agent_id}] ✅ DeepSeek LLM configured.")

        else:
            print(f"[{self.agent_id}] ⚠️ Unsupported provider '{self.llm_provider}'. Fallback mode enabled.")
            self.llm_model = None

    # ------------------------------------------------------------
    # SkillBank / mHC 로딩
    # ------------------------------------------------------------
    def _load_built_in_knowledge(self):
        self.skill_bank = {
            "financial_analysis": {
                "description": "Ability to analyze financial data and provide recommendations.",
                "keywords": ["finance", "investment", "budget", "report"],
            },
            "data_processing": {
                "description": "Skills in processing and structuring raw data.",
                "keywords": ["data", "process", "clean", "structure"],
            },
            "safety_protocols": {
                "description": "Knowledge of safety regulations and best practices.",
                "keywords": ["safety", "protocol", "risk", "security"],
            },
        }

        self.mhc_knowledge = {
            "core_directive_1": "Prioritize user safety and data privacy.",
            "core_directive_2": "Always provide objective and accurate information.",
            "learning_bias": "Favor analytical and logical reasoning over emotional responses.",
        }

        print(f"[{self.agent_id}] ✅ Built-in knowledge (SkillBank, mHC) loaded.")

    # ------------------------------------------------------------
    # 메인 응답 생성
    # ------------------------------------------------------------
    async def generate_response_with_knowledge(self, user_input: str) -> str:
        print(f"[{self.agent_id}] Applying Face-Off Algorithm with knowledge...")
        context_prompt = ""

        # mHC core directives
        for key, value in self.mhc_knowledge.items():
            if key.startswith("core_directive"):
                context_prompt += f"Core Directive: {value}. "

        # SkillBank 매칭
        user_lower = user_input.lower()
        for skill_name, skill_data in self.skill_bank.items():
            for keyword in skill_data.get("keywords", []):
                if keyword in user_lower:
                    context_prompt += f"Relevant Skill ({skill_name}): {skill_data['description']}. "
                    break

        final_prompt = f"""Given the following knowledge and context:
{context_prompt}
User Input: {user_input}
Your persona: {self.persona_data.get('role', 'General Agent')} with {self.persona_data.get('tone_and_manner', 'neutral')} tone.
Respond accurately and objectively."""

        # ResponseController 내부에서 실제 LLM 호출/정책 처리
        # (llm_model=None인 fallback mode도 처리하도록 ResponseController에서 대응 필요)
        llm_response = await self.response_controller.process_input_with_llm(final_prompt)

        # 간단한 post-process 예시
        if self.mhc_knowledge.get("learning_bias") == "Favor analytical and logical reasoning over emotional responses.":
            emotion_words = ["happy", "sad", "angry", "emotional"]
            if any(word in llm_response.lower() for word in emotion_words):
                llm_response += " (Note: adjusted for analytical bias as per mHC directive)."

        return llm_response
