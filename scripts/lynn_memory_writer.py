# scripts/lynn_memory_writer.py
"""
Lynn's Daily Memory Writer — Mulberry Memory Bank 핵심 실행 파일

매일 실행:
  1. arxiv 최신 AI 논문 5편 수집 (arxiv_hunter.py)
  2. request.txt의 특정 URL도 별도 수집
  3. yfinance 시장 데이터 (NVDA / WTI)
  4. daily_hunts/{today}-briefing.md 저장
  5. agent_activity.md 자동 업데이트

버그 수정 이력 (2026-05-04):
  - arxiv URL: 홈페이지 → API 엔드포인트
  - XML namespace: {http://www.w3.org} → {http://www.w3.org/2005/Atom}
  - yfinance 실제 데이터 연동
  - agent_activity.md 자동 업데이트 추가
"""

import os
import sys
import datetime

# 같은 scripts/ 폴더의 arxiv_hunter import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from arxiv_hunter import fetch_latest, fetch_by_id, papers_to_markdown

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_market_data() -> dict:
    """yfinance로 실제 시장 데이터 수집"""
    data = {
        "NVDA": {"price": "N/A", "change": "N/A"},
        "WTI":  {"price": "N/A", "change": "N/A"},
        "BTC":  {"price": "N/A", "change": "N/A"},
    }
    try:
        import yfinance as yf
        tickers = {"NVDA": "NVDA", "WTI": "CL=F", "BTC": "BTC-USD"}
        for label, symbol in tickers.items():
            t = yf.Ticker(symbol)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                prev  = hist["Close"].iloc[-2]
                today = hist["Close"].iloc[-1]
                chg   = ((today - prev) / prev) * 100
                data[label] = {
                    "price":  f"${today:,.2f}",
                    "change": f"{chg:+.2f}%",
                }
            elif len(hist) == 1:
                price = hist["Close"].iloc[-1]
                data[label] = {"price": f"${price:,.2f}", "change": "N/A"}
    except Exception as e:
        print(f"[market] 데이터 수집 실패: {e}")
    return data


def read_request_url() -> str | None:
    """request.txt에서 특정 arxiv URL 추출"""
    req_path = os.path.join(BASE_DIR, "request.txt")
    if not os.path.exists(req_path):
        return None
    try:
        with open(req_path, "r", encoding="utf-8") as f:
            content = f.read()
        import re
        match = re.search(r"https?://arxiv\.org/abs/[\w.]+", content)
        return match.group(0) if match else None
    except Exception:
        return None


def update_agent_activity(today: str, paper_count: int, top_title: str) -> None:
    """agent_activity.md에 오늘 수집 결과 기록"""
    path = os.path.join(BASE_DIR, "agent_activity.md")
    entry = (
        f"\n### {today} — Lynn Daily Hunt\n"
        f"- 수집 논문: {paper_count}편\n"
        f"- 최고 연관 논문: {top_title[:80]}\n"
        f"- 상태: ✅ 완료\n"
    )
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(entry)
        print(f"[activity] agent_activity.md 업데이트 완료")
    except Exception as e:
        print(f"[activity] 업데이트 실패: {e}")


def write_daily_hunt() -> None:
    """메인 실행 — 브리핑 파일 생성"""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    hunts_dir = os.path.join(BASE_DIR, "daily_hunts")
    os.makedirs(hunts_dir, exist_ok=True)
    file_path = os.path.join(hunts_dir, f"{today}-briefing.md")

    print(f"[Lynn] {today} 사냥 시작...")

    # 1. arxiv 최신 논문 5편 수집
    print("[Lynn] arxiv 논문 수집 중...")
    papers = fetch_latest(max_results=5)

    # 2. request.txt 특정 URL 수집
    req_url = read_request_url()
    special_section = ""
    if req_url:
        print(f"[Lynn] 특별 지령 논문 수집: {req_url}")
        sp = fetch_by_id(req_url)
        if sp:
            special_section = (
                f"\n## 🎯 특별 지령 논문 (request.txt)\n\n"
                f"**{sp.title}**\n"
                f"- 저자: {', '.join(sp.authors)}\n"
                f"- 게재일: {sp.published}\n"
                f"- Mulberry 연관도: {sp.mulberry_score}pt ({', '.join(sp.matched_keywords) or '일반'})\n"
                f"- 요약: {sp.short_summary}\n"
                f"- 링크: {sp.link}\n"
            )

    # 3. 시장 데이터
    print("[Lynn] 시장 데이터 수집 중...")
    market = get_market_data()

    # 4. 브리핑 파일 작성
    papers_md = papers_to_markdown(papers, today)
    top_title = papers[0].title if papers else "N/A"

    content = f"""# 🐺 Lynn's Daily Briefing — {today}

> *"기술은 보이지 않게 — 사람이 중심, AI는 도구"* — Mulberry 장승배기 정신

---

## 📈 시장 현황

| 자산 | 가격 | 변동 |
|------|------|------|
| NVIDIA (NVDA) | {market['NVDA']['price']} | {market['NVDA']['change']} |
| WTI 원유 | {market['WTI']['price']} | {market['WTI']['change']} |
| Bitcoin | {market['BTC']['price']} | {market['BTC']['change']} |

---

{special_section}

{papers_md}

---

## 🌿 Lynn's Mulberry 인사이트

오늘 수집된 {len(papers)}편 논문 중 Mulberry와 가장 높은 연관성:
**{top_title[:80]}**

이 논문이 우리 장승배기 헌법, Jr. Agent 교육, 또는 Scruple-Time 엔진에
기여할 수 있는 인사이트를 Research Lab 이슈로 제안드립니다.

---

*Maintained by Lynn (The Courteous Wolf) | {today}*
*mulberry_memory_bank/daily_hunts/ — 장승배기 전당 영구 보존*
"""

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[Lynn] 브리핑 저장 완료: {file_path}")

    # 5. agent_activity.md 업데이트
    update_agent_activity(today, len(papers), top_title)

    print(f"[Lynn] [OK] {today} 사냥 완료 - {len(papers)}편 수집")


if __name__ == "__main__":
    write_daily_hunt()
