import os
import json
import datetime

def register_safe_spending_skill():
    # 스크립트 위치 기준 상위 폴더(Root)를 찾습니다.
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_folder = os.path.join(BASE_DIR, "skill_manifests")
    
    os.makedirs(target_folder, exist_ok=True)
    file_path = os.path.join(target_folder, "safe_spending_v1.json")

    skill_data = {
        "skill_name": "Safe Spending Logic for Agents",
        "version": "1.0.0",
        "author": "Lynn (The Courteous Wolf)",
        "authorized_by": "Project Leader",
        "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "rules": {
            "session_key": {"duration": "24h", "revocable": True, "scope": ["Donation_10%", "Gas_Fees"]},
            "spending_limits": {"daily_cap_ratio": 0.02, "velocity_limit_per_hour": 5},
            "white_list": ["Mulberry_Charity_Vault", "Senior_Care_Foundation"]
        },
        "kill_switch": ["Drawdown > 5%", "Unauthorized_Access"]
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(skill_data, f, indent=4, ensure_ascii=False)
    
    print(f"✅ JSON File Created at: {file_path}")

if __name__ == "__main__":
    register_safe_spending_skill()
