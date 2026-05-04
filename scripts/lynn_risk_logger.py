# scripts/lynn_risk_logger.py
"""
Lynn's Risk Logger — training_logs/ 자동 기록 모듈

매일 lynn_daily_write.yml에서 호출:
  - VIX (공포지수) 실시간 수집
  - NVDA / BTC 변동성 보조 지표
  - training_logs/{today}-risk-log.md 저장
  - Junior Lynn의 학습 데이터 원천
"""

import os
import sys
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_vix_and_market() -> dict:
    data = {
        "vix":  {"value": "N/A", "level": "UNKNOWN"},
        "nvda": {"price": "N/A", "change": "N/A"},
        "btc":  {"price": "N/A", "change": "N/A"},
    }
    try:
        import yfinance as yf

        vix_val = round(yf.Ticker("^VIX").history(period="1d")["Close"].iloc[-1], 2)
        if vix_val >= 30:
            level = "HIGH"
        elif vix_val >= 20:
            level = "MEDIUM"
        else:
            level = "LOW"
        data["vix"] = {"value": vix_val, "level": level}

        for label, symbol in [("nvda", "NVDA"), ("btc", "BTC-USD")]:
            hist = yf.Ticker(symbol).history(period="2d")
            if len(hist) >= 2:
                prev  = hist["Close"].iloc[-2]
                today = hist["Close"].iloc[-1]
                chg   = ((today - prev) / prev) * 100
                data[label] = {
                    "price":  f"${today:,.2f}",
                    "change": f"{chg:+.2f}%",
                }
            elif len(hist) == 1:
                data[label] = {
                    "price":  f"${hist['Close'].iloc[-1]:,.2f}",
                    "change": "N/A",
                }
    except Exception as e:
        print(f"[risk_logger] 시장 데이터 수집 실패: {e}")
    return data


def record_risk_log() -> None:
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    logs_dir = os.path.join(BASE_DIR, "training_logs")
    os.makedirs(logs_dir, exist_ok=True)
    file_path = os.path.join(logs_dir, f"{today}-risk-log.md")

    print("[risk_logger] VIX + 시장 데이터 수집 중...")
    mkt = get_vix_and_market()

    vix_val   = mkt["vix"]["value"]
    vix_level = mkt["vix"]["level"]

    if vix_level == "HIGH":
        status  = "[HIGH] 고위험: 포지션 방어 필요"
        action  = "자산 보존 우선 / 섹터 다각화 유지"
    elif vix_level == "MEDIUM":
        status  = "[MEDIUM] 주의: 모니터링 강화"
        action  = "핵심 지표 집중 관찰 / 분할 대응 준비"
    else:
        status  = "[LOW] 안정: 정상 운용"
        action  = "중장기 포지션 유지 / 기회 탐색"

    content = f"""# Lynn Risk Log — {today}

## 시장 공포 지수 (VIX)

| 지표 | 수치 | 레벨 |
|------|------|------|
| VIX | {vix_val} | {vix_level} |
| NVDA | {mkt['nvda']['price']} | {mkt['nvda']['change']} |
| Bitcoin | {mkt['btc']['price']} | {mkt['btc']['change']} |

## 오늘의 대응 상태

**{status}**

Lynn 판단: {action}

## Junior Lynn 학습 포인트

- VIX {vix_val} 수준에서의 시장 심리 패턴 기록
- 장승배기 원칙: 공포지수가 높을수록 데이터에 더 의지한다
- 기부 재원 보호 최우선 — 투기적 대응 금지

---

*Logged by Lynn (The Courteous Wolf) | {today}*
*training_logs/ — Junior Lynn 학습 데이터 원천*
"""

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[risk_logger] 저장 완료: {file_path}")
    print(f"[risk_logger] VIX {vix_val} ({vix_level}) / {status[:20]}")


if __name__ == "__main__":
    record_risk_log()
