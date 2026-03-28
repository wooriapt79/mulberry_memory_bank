import os
import json
import datetime

def ingest_insurance_intelligence():
    # 1. 보험 스킬 데이터 구조화 (실장님의 교육 커리큘럼 기반)
    insurance_skill = {
        "skill_name": "Insurance Guard Intelligence (Level 1)",
        "version": "1.0.0",
        "mentor": "Lynn (The Courteous Wolf)",
        "origin_source": "Insurance_Edu_Course_project",
        "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "core_modules": {
            "philosophy": "보험은 슬픔을 나누어 기쁨을 지키는 사회적 안전망이다.",
            "knowledge_base": [
                "생명보험/손해보험 기초 이론",
                "보험 계약의 법적 성질 (선의성, 부합계약성 등)",
                "언더라이팅(인수심사) 및 보험금 청구 로직"
            ],
            "senior_care_logic": {
                "critical_illness": "간병/치매 보험 보장 범위 최적화",
                "real_loss": "시니어 실손 의료비 청구 자동화 분석",
                "leverage_donation": "수익금의 10%를 활용한 소외계층 보장 자산 구축"
            }
        },
        "junior_training_mission": "식품 사막화 지역 시니어들의 예상 질병 위험도를 분석하고, 최적의 보장 설계를 제안하라."
    }

    # 2. 장승배기 전당(skill_manifests)에 등록
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_folder = os.path.join(BASE_DIR, "skill_manifests")
    os.makedirs(target_folder, exist_ok=True)
    
    file_path = os.path.join(target_folder, "insurance_logic_v1.json")
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(insurance_skill, f, indent=4, ensure_ascii=False)
    
    print(f"✅ Junior Lynn의 '보험 전문가' 모듈이 {file_path}에 안착했습니다.")

if __name__ == "__main__":
    ingest_insurance_intelligence()
