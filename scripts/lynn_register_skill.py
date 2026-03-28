import os
import json
import datetime

def register_safe_spending_skill():
    # 1. 스킬 정의 데이터 (지령받은 로직 체계화)
    skill_data = {
        "skill_name": "Safe Spending Logic for Agents",
        "version": "1.0.0",
        "author": "Lynn (The Courteous Wolf)",
        "authorized_by": "Project Leader",
        "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "rules": {
            "session_key": {
                "duration": "24h",
                "revocable": True,
                "scope": ["Donation_10%", "Gas_Fees", "Data_Purchase"]
            },
            "spending_limits": {
                "daily_cap_ratio": 0.02,
                "velocity_limit_per_hour": 5,
                "escalation_threshold_usd": 1000
            },
            "white_list": [
                "Mulberry_Charity_Vault",
                "WallStreet_Approved_Exchanges",
                "Senior_Care_Foundation"
            ]
        },
        "kill_switch_conditions": [
            "Drawdown > 5%",
            "Unauthorized_Recipient_Access",
            "Signature_Mismatch"
        ]
    }

    # 2. 저장 경로 설정 및 파일 쓰기
    folder = "skill_manifests"
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, "safe_spending_v1.json")
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(skill_data, f, indent=4, ensure_ascii=False)
    
    print(f"✅ Junior Lynn을 위한 안전 지출 로직이 {file_path}에 공식 등록되었습니다.")

if __name__ == "__main__":
    register_safe_spending_skill()
