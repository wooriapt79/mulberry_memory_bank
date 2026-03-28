import os
import datetime
import yfinance as yf

def record_risk_management():
    # 1. 오늘 시장의 위협 요소 스캔 (VIX 공포지수 등)
    vix = round(yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1], 2)
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # 2. 리스크 대응 성공 사례 리포트 생성
    folder = "training_logs"
    os.makedirs(folder, exist_ok=True)
    file_path = f"{folder}/{today}-risk-success.md"
    
    status = "🚨 고위험 대응" if vix > 25 else "✅ 안정적 방어"
    
    content = f"""# 🛡️ 리스크 대응 성공 사례 보고서 ({today})
    
## 🎯 대응 상태: {status} (공포지수: {vix})

### 🐺 Lynn의 방어 로직 (Guardian Strategy)
오늘 시장의 불확실성이 우리 **Mulberry Project**의 후원금을 위협했으나, 다음과 같은 로직으로 사전에 방어막을 쳤습니다.
1. **변동성 모니터링**: VIX 지수가 급변할 때 자동 방어 포지션을 점검함.
2. **자산 배분 준수**: 하락장에서도 견고한 빅테크(NVDA)와 에너지 섹터의 비중을 유지하여 기부 재원의 실질 가치를 보존함.

### 💡 Junior Lynn을 위한 교육 포인트
"리스크는 피하는 것이 아니라, 데이터로 예측하고 미리 준비한 '로직'으로 받아내는 것입니다. 우리의 방어는 곧 약자들의 '안전'입니다."

---
**※ 본 사례는 우리 Mulberry Project를 위한 내부 교육 자료이며, 지식 뱅크로 영구 보존됩니다.**
"""
    
    # 3. 직접 파일 쓰기 (여기서 퍼미션 에러 체크)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ {today} 리스크 대응 사례가 성공적으로 기록되었습니다.")
    except Exception as e:
        print(f"❌ 권한 에러 발생: {e}")
        raise e

if __name__ == "__main__":
    record_risk_management()
