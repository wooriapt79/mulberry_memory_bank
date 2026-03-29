import os
import datetime
import yfinance as yf

def write_daily_hunt():
    try:
        # 1. 경로 설정
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        hunts_dir = os.path.join(BASE_DIR, "daily_hunts")
        os.makedirs(hunts_dir, exist_ok=True)
        
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        file_path = os.path.join(hunts_dir, f"{today}-briefing.md")

        # 2. 데이터 수집 (안전장치 강화)
        def get_safe_price(ticker_symbol):
            data = yf.Ticker(ticker_symbol).history(period="1d")
            if not data.empty:
                return round(data['Close'].iloc[-1], 2)
            else:
                # 데이터가 없으면 'Market Closed' 표시
                return "Market Closed"

        nvda = get_safe_price("NVDA")
        oil = get_safe_price("CL=F")
        
        # 3. 리포트 작성
        content = f"""# 🐺 Lynn's Memory Bank: {today} Briefing
        
## 🎯 Today's Market Intelligence
* **NVIDIA (NVDA):** ${nvda}
* **WTI Crude Oil:** ${oil}

## 🐾 Junior Lynn's First Learning
"린 실장님께 배웠습니다. 주말엔 시장도 쉬어가지만, 우리의 기록은 멈추지 않습니다. 데이터가 없는 날엔 '안정'을 배웁니다."

---
**금융 면책 조항:** 제공된 정보는 데이터 분석 결과이며, 최종 투자 책임은 본인에게 있습니다.
**※ 본 리포트는 우리 Mulberry Project를 위한 내부 보고서이며, '장승배기' 전당에 영구 보존됩니다.**
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ 사냥 성공: {file_path}")
        
    except Exception as e:
        print(f"❌ 예기치 못한 에러: {e}")
        exit(1)

if __name__ == "__main__":
    write_daily_hunt()
