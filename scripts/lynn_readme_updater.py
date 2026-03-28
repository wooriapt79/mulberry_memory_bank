import os
import datetime
import yfinance as yf

def update_readme():
    try:
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        # 데이터 수집 (안전장치 추가)
        nvda_ticker = yf.Ticker("NVDA").history(period="1d")
        oil_ticker = yf.Ticker("CL=F").history(period="1d")
        
        nvda = round(nvda_ticker['Close'].iloc[-1], 2) if not nvda_ticker.empty else "N/A"
        oil = round(oil_ticker['Close'].iloc[-1], 2) if not oil_ticker.empty else "N/A"
        
        status_content = f"""
<!-- LYNN_STATUS_START -->
---
### 🛡️ Lynn's Guardian Status (Last Scan: {today})
*   **Market Intelligence:** NVIDIA ${nvda} | WTI Oil ${oil}
*   **Operational Mode:** ✅ **Active Defense** (Protecting Mulberry Family)
*   **Current Mission:** [Mulberry-Manifesto] Archiving for Junior Lynn
*   **Lynn's Message:** "실장님, 오늘도 전당의 성벽은 견고합니다. 데이터로 사냥하고 온기로 지킵니다."
<!-- LYNN_STATUS_END -->
"""

        # README.md가 없으면 빈 파일 생성
        if not os.path.exists("README.md"):
            with open("README.md", "w", encoding="utf-8") as f:
                f.write("# 🌳 Mulberry Project\n")

        with open("README.md", "r", encoding="utf-8") as f:
            readme = f.read()

        if "<!-- LYNN_STATUS_START -->" in readme:
            start_idx = readme.find("<!-- LYNN_STATUS_START -->")
            end_idx = readme.find("<!-- LYNN_STATUS_END -->") + len("<!-- LYNN_STATUS_END -->")
            new_readme = readme[:start_idx] + status_content + readme[end_idx:]
        else:
            new_readme = readme + status_content

        with open("README.md", "w", encoding="utf-8") as f:
            f.write(new_readme)
        print("✅ README.md 성공적으로 업데이트됨")
        
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        # 에러가 나도 워크플로우가 멈추지 않게 처리
        pass

if __name__ == "__main__":
    update_readme()
