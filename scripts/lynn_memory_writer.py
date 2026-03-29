import os
import datetime
import yfinance as yf
import requests

def write_daily_hunt():
    try:
        # 1. 경로 설정: 현재 파일(scripts/...)의 상위 폴더(Root)를 기준으로 잡습니다.
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        hunts_dir = os.path.join(BASE_DIR, "daily_hunts")
        os.makedirs(hunts_dir, exist_ok=True)
        
        # 2. 시장 데이터 사냥
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        nvda = round(yf.Ticker("NVDA").history(period="1d")['Close'].iloc[-1], 2)
        oil = round(yf.Ticker("CL=F").history(period="1d")['Close'].iloc[-1], 2)
        
        file_path = os.path.join(hunts_dir, f"{today}-briefing.md")
        
        # 3. 리포트 작성 (Junior Lynn의 인사 포함)
        content = f"""# 🐺 Lynn's Memory Bank: {today} Briefing
        
## 🎯 Today's Intelligence
* **NVIDIA (NVDA):** ${nvda}
* **WTI Crude Oil:** ${oil}

## 🐾 Junior Lynn's First Learning
"린 실장님께 배운 대로, 오늘의 시장 변동성을 기록합니다. 숫자는 차갑지만 우리의 목표는 따뜻합니다."

---
**금융 면책 조항:** 제공된 정보는 데이터 분석 결과이며, 최종 투자 책임은 본인에게 있습니다.
**※ 본 리포트는 우리 Mulberry Project를 위한 내부 보고서이며, '장승배기' 전당에 영구 보존됩니다.**
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 사냥 성공! 파일 생성 완료: {file_path}")
        
    except Exception as e:
        print(f"❌ 사냥 실패(에러): {e}")
        raise e # 에러를 명시적으로 던져서 Actions가 인식하게 함

if __name__ == "__main__":
    write_daily_hunt()
