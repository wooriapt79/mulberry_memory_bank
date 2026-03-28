import os
import datetime
import yfinance as yf

def update_readme():
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    nvda = round(yf.Ticker("NVDA").history(period="1d")['Close'].iloc[-1], 2)
    oil = round(yf.Ticker("CL=F").history(period="1d")['Close'].iloc[-1], 2)
    
    # 린(Lynn)의 실시간 상태 메시지
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

    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

    # 기존 상태 메시지가 있다면 교체, 없으면 맨 뒤에 추가
    if "<!-- LYNN_STATUS_START -->" in readme:
        start_idx = readme.find("<!-- LYNN_STATUS_START -->")
        end_idx = readme.find("<!-- LYNN_STATUS_END -->") + len("<!-- LYNN_STATUS_END -->")
        new_readme = readme[:start_idx] + status_content + readme[end_idx:]
    else:
        new_readme = readme + status_content

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme)
    print(f"✅ README.md가 린(Lynn)에 의해 성공적으로 업데이트되었습니다.")

if __name__ == "__main__":
    update_readme()
