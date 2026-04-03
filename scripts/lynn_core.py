# lynn_core.py
import sys
import os
import asyncio
import json
try:
import google.generativeai as genai
except ImportError:
       genai = None
import google.api_core.exceptions
from deepseek import DeepSeek # Corrected import statement: from deepseek import DeepSeek

# 루트 디렉토리를 path에 추가 (marrf 모듈 import용)
# # # # # # # sys.path.append(os.path.dirname(os.path.dirname(__file__))) # Handled by notebook environment setup - no longer needed here

from marrf.rest_scheduler import RestScheduler
from marrf.bio_manager import BioManager
from marrf.response_controller import ResponseController
from marrf.relationship_manager import RelationshipManager

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

        # SkillBank and mHC simulation
        self.skill_bank = {}
        self.mhc_knowledge = {}
        self._load_built_in_knowledge() # Call method to load knowledge

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
            except (ImportError, KeyError):
                api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                print(f"[{self.agent_id}] ❌ GOOGLE_API_KEY not found for Gemini.")
                raise ValueError("GOOGLE_API_KEY environment variable not set or unavailable.")
            genai.configure(api_key=api_key)
            self.llm_model = genai.GenerativeModel('gemini-pro')
            print(f"[{self.agent_id}] ✅ Gemini LLM configured.")
        elif self.llm_provider == "deepseek":
            api_key = os.getenv('DEEPSEEK_API_KEY')
            if not api_key:
                print(f"[{self.agent_id}] ❌ DEEPSEEK_API_KEY not found for DeepSeek.")
                raise ValueError("DEEPSEEK_API_KEY environment variable not set or unavailable.")
            self.llm_model = DeepSeek(api_key=api_key) # Corrected instantiation
            print(f"[{self.agent_id}] ✅ DeepSeek LLM configured.")
        else:
            print(f"[{self.agent_id}] ❌ Unsupported LLM provider: {self.llm_provider}. Supported: 'gemini', 'deepseek'.")
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")

        # Initialize RestScheduler if group B or C
        if self.group == "B" or self.group == "C":
            self.rest_scheduler = RestScheduler(self.agent_id)
            print(f"[{self.agent_id}] ✅ RestScheduler initialized for group {self.group}.")

        # Initialize the response_controller with the agent instance
        self.response_controller = ResponseController(self)
        print(f"[{self.agent_id}] ✅ ResponseController initialized.")
        print(f"[{self.agent_id}] Initialized with persona: {self.persona_data.get('name', 'Default')}")

    def _load_built_in_knowledge(self):
        # Simulate SkillBank and mHC knowledge loading
        # In a real scenario, these would be loaded from files or a database
        self.skill_bank = {
            "financial_analysis": {
                "description": "Ability to analyze financial data and provide recommendations.",
                "keywords": ["finance", "investment", "budget", "report"]
            },
            "data_processing": {
                "description": "Skills in processing and structuring raw data.",
                "keywords": ["data", "process", "clean", "structure"]
            },
            "safety_protocols": {
                "description": "Knowledge of safety regulations and best practices.",
                "keywords": ["safety", "protocol", "risk", "security"]
            }
        }
        self.mhc_knowledge = {
            "core_directive_1": "Prioritize user safety and data privacy.",
            "core_directive_2": "Always provide objective and accurate information.",
            "learning_bias": "Favor analytical and logical reasoning over emotional responses."
        }
        print(f"[{self.agent_id}] ✅ Built-in knowledge (SkillBank, mHC) loaded.")

    async def generate_response_with_knowledge(self, user_input: str) -> str:
        # Simulate 'Face-Off Algorithm' by integrating mHC and SkillBank knowledge
        # This is a simplified example; real implementation would be more complex
        print(f"[{self.agent_id}] Applying Face-Off Algorithm with knowledge...")
        context_prompt = ""

        # Integrate mHC core directives as high-priority context
        for key, value in self.mhc_knowledge.items():
            if key.startswith("core_directive"): # Ensure only directives are added this way
                context_prompt += f"Core Directive: {value}. "

        # Check for relevant skills in SkillBank and add to context
        for skill_name, skill_data in self.skill_bank.items():
            for keyword in skill_data.get("keywords", []):
                if keyword in user_input.lower():
                    context_prompt += f"Relevant Skill ({skill_name}): {skill_data['description']}. "
                    break # Only add skill once if multiple keywords match

        final_prompt = f"""Given the following knowledge and context:
{context_prompt}
User Input: {user_input}
Your persona: {self.persona_data.get('role', 'General Agent')} with {self.persona_data.get('tone_and_manner', 'neutral')} tone. Respond accurately and objectively."""

        # Pass the enhanced prompt to the response controller which handles SCP and actual LLM call
        llm_response = await self.response_controller.process_input_with_llm(final_prompt)

        # Further refinement based on mHC learning bias, if applicable (post-processing example)
        if self.mhc_knowledge.get("learning_bias") == "Favor analytical and logical reasoning over emotional responses.":
            if any(emotion_word in llm_response.lower() for emotion_word in ["happy", "sad", "angry", "emotional"]): # Simple check for emotional words
                llm_response += " (Note: Response may have been adjusted for analytical bias as per mHC directive)."

        return llm_response
