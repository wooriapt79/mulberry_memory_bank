import os
import datetime
import yfinance as yf

def update_readme():
    try:
        # 1. 경로 보정: scripts 폴더의 상위 폴더(Root)를 찾습니다.
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        readme_path = os.path.join(BASE_DIR, "README.md")
        
        today = datetime.datetime.now().strftime('%Y-%m-%d')
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

        # README.md 파일 읽기
        if not os.path.exists(readme_path):
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write("# 🌳 Mulberry Project\n")

        with open(readme_path, "r", encoding="utf-8") as f:
            readme = f.read()

        # 상태 메시지 교체 또는 추가
        if "<!-- LYNN_STATUS_START -->" in readme:
            start_idx = readme.find("<!-- LYNN_STATUS_START -->")
            end_idx = readme.find("<!-- LYNN_STATUS_END -->") + len("<!-- LYNN_STATUS_END -->")
            new_readme = readme[:start_idx] + status_content + readme[end_idx:]
        else:
            new_readme = readme + status_content

        # 최상단 README.md에 쓰기
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_readme)
        print(f"✅ README.md 성공적으로 업데이트됨: {readme_path}")
        
    except Exception as e:
        print(f"❌ 에러 발생: {e}")

if __name__ == "__main__":
    update_readme()
