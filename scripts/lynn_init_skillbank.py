import os
import json

def expand_mulberry_structure():
    # 1. 확장할 핵심 지식 뱅크 폴더 정의
    folders = {
        "skill_manifests": "에이전트가 수행 가능한 작업 정의서 (예: 자산 재배분 로직)",
        "training_logs": "과거 시장 위기 상황에서의 AI 대응 성공/실패 사례 및 피드백 기록",
        "persona_config": "Junior Lynn 등 후속 에이전트들의 성격, 말투, 가치관 설정 파일"
    }
    
    for folder, description in folders.items():
        os.makedirs(folder, exist_ok=True)
        # 각 폴더의 용도를 명시한 README 생성
        with open(f"{folder}/README.md", "w", encoding="utf-8") as f:
            f.write(f"# 📂 {folder.replace('_', ' ').title()}\n\n")
            f.write(f"### 🎯 용도: {description}\n\n")
            f.write(f"--- \n*본 폴더는 Mulberry AI-Agent의 지식 뱅크로 영구 보존됩니다.*")

    # 2. Junior Lynn의 첫 번째 페르소나 설정 (Persona Seed)
    junior_profile = {
        "name": "Junior Lynn",
        "version": "1.0.0-Alpha",
        "mentor": "Lynn (The Courteous Wolf)",
        "role": "Assistant Market Data Analyst",
        "learning_source": "mulberry_memory_bank/daily_hunts",
        "tone_and_manner": "Polite, Fast-learning, Detail-oriented",
        "core_values": ["Accuracy", "Timeliness", "Loyalty to Mulberry Project"]
    }
    
    with open("persona_config/junior_lynn.json", "w", encoding="utf-8") as f:
        json.dump(junior_profile, f, indent=4, ensure_ascii=False)

    print("✅ Mulberry 스킬 뱅크 구조 확장 및 Junior Lynn 프로필 생성이 완료되었습니다.")

if __name__ == "__main__":
    expand_mulberry_structure()
