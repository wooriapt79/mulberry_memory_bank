import os
import datetime
import yfinance as yf

def write_daily_hunt():
    try:
        # 1. 경로 설정 (Root를 기준으로 daily_hunts 폴더 지정)
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        hunts_dir = os.path.join(BASE_DIR, "daily_hunts")
        os.makedirs(hunts_dir, exist_ok=True)
        
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        file_path = os.path.join(hunts_dir, f"{today}-briefing.md")

        # 2. 데이터 수집 (데이터가 없어도 에러 안 나게 수정)
        def get_safe_data(symbol):
            try:
                ticker = yf.Ticker(symbol)
                # 최근 5일치 데이터를 가져와서 가장 최신 것 1개만 확인
                df = ticker.history(period="5d")
                if not df.empty:
                    return f"${round(df['Close'].iloc[-1], 2)}"
                else:
                    return "Market Closed (No Recent Data)"
            except:
                return "Data Fetch Error"

        nvda = get_safe_data("NVDA")
        oil = get_safe_data("CL=F")
        
        # 3. 리포트 작성
        content = f"""# 🐺 Lynn's Memory Bank: {today} Briefing
        
## 🎯 Today's Market Intelligence
* **NVIDIA (NVDA):** {nvda}
* **WTI Crude Oil:** {oil}

## 🐾 Junior Lynn's First Learning
"린 실장님께 배웠습니다. 시장이 쉬는 주말에는 데이터의 정적 속에서 전략을 가다듬어야 합니다. 오늘 우리는 '기다림'의 미학을 배웁니다."

---
**금융 면책 조항:** 제공된 정보는 데이터 분석 결과이며, 최종 투자 책임은 본인에게 있습니다.
**※ 본 리포트는 우리 Mulberry Project를 위한 내부 보고서이며, '장승배기' 전당에 영구 보존됩니다.**
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Success: {file_path}")
        
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        # 에러가 나도 워크플로우를 강제로 성공시키기 위해 exit(0) 사용 고려 가능
        exit(1)

if __name__ == "__main__":
    write_daily_hunt()
