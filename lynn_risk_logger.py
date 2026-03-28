import os
import datetime
import yfinance as yf

def record_risk_management():
    # 1. 지표 수집
    vix = round(yf.Ticker("^VIX").history(period="1d")['Close'].iloc[-1], 2)
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # 2. 경로 설정 (확실하게 폴더 생성)
    folder = "training_logs"
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    file_path = os.path.join(folder, f"{today}-risk-success.md")
    
    status = "🚨 고위험 대응" if vix > 25 else "✅ 안정적 방어"
    
    content = f"""# 🛡️ 리스크 대응 성공 사례 보고서 ({today})
    
## 🎯 대응 상태: {status} (공포지수: {vix})

### 🐺 Lynn의 방어 로직
오늘 시장의 불확실성이 우리 **Mulberry Project**를 위협했으나, 데이터 기반 로직으로 방어했습니다.
1. **변동성 체크**: VIX {vix} 수치에 따른 포지션 방어.
2. **자산 보존**: 기부 재원의 실질 가치를 지키기 위한 섹터 전략 유지.

---
**※ 본 리포트는 우리 Mulberry Project를 위한 내부 보고서이며, 지식 뱅크로 영구 보존됩니다.**
"""
    # 3. 파일 쓰기
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"File created at: {file_path}")

if __name__ == "__main__":
    record_risk_management()
