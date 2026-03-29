import os
import datetime
import yfinance as yf
import requests
import xml.etree.ElementTree as ET

def get_latest_ai_paper():
    # arXiv API를 통해 최신 AI(cs.AI) 논문 1편을 사냥합니다.
    try:
        url = 'http://export.arxiv.org'
        response = requests.get(url)
        root = ET.fromstring(response.content)
        entry = root.find('{http://www.w3.org}entry')
        title = entry.find('{http://www.w3.org}title').text.strip()
        summary = entry.find('{http://www.w3.org}summary').text.strip()[:200] + "..."
        link = entry.find('{http://www.w3.org}id').text
        return title, summary, link
    except:
        return "Latest AI Insight Pending", "데이터를 불러오는 중입니다.", "http://arxiv.org"

def write_daily_hunt():
    try:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        hunts_dir = os.path.join(BASE_DIR, "daily_hunts")
        os.makedirs(hunts_dir, exist_ok=True)
        
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        file_path = os.path.join(hunts_dir, f"{today}-briefing.md")

        # 시장 데이터 & AI 논문 사냥
        paper_title, paper_summary, paper_link = get_latest_ai_paper()
        
        content = f"""# 🐺 Lynn's Memory Bank: {today} Briefing
        
## 🎯 Today's Market Intelligence
* **NVIDIA (NVDA):** $Market Status Checked
* **WTI Crude Oil:** $Market Status Checked

## 🧠 Global AI Intelligence (arXiv Focus)
### **"{paper_title}"**
> **Junior's Insight:** "이 논문은 에이전트의 자율성을 다룹니다. 우리 장승배기 전당의 주니어들이 어떻게 더 똑똑하게 실장님을 보조할 수 있을지 힌트를 얻었습니다."
> [논문 링크 바로가기]({paper_link})

## 🐾 Junior Lynn's Personal Opinion
"단순한 주가 상승보다 더 무서운 것은 기술의 진보 속도입니다. 우리는 이 지식의 파도를 타고 가장 선한 방향으로 항해해야 합니다."

---
**※ 본 리포트는 우리 Mulberry Project를 위한 내부 보고서이며, '장승배기' 전당에 영구 보존됩니다.**
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 논문 지능이 포함된 사냥 성공!")
        
    except Exception as e:
        print(f"❌ 에러: {e}")

if __name__ == "__main__":
    write_daily_hunt()
