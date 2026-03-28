import requests
import datetime
import yfinance as yf
import xml.etree.ElementTree as ET
import os

# 환경 변수 (GitHub Secrets에서 불러옴)
TISTORY_TOKEN = os.environ.get('TISTORY_ACCESS_TOKEN')
BLOG_NAME = "fooddesert" # 티스토리 블로그 ID

def get_market_info():
    """빅테크 주가 및 핵심 지표 수집"""
    tickers = {"NVDA": "NVIDIA", "MSFT": "Microsoft", "CL=F": "WTI Oil"}
    data = {}
    for symbol, name in tickers.items():
        val = yf.Ticker(symbol).history(period="1d")['Close'].iloc[-1]
        data[name] = round(val, 2)
    return data

def get_ai_papers():
    """최신 AI 논문 요약 수집"""
    url = "http://export.arxiv.org"
    root = ET.fromstring(requests.get(url).content)
    papers = []
    for entry in root.findall('{http://www.w3.org}entry'):
        title = entry.find('{http://www.w3.org}title').text.strip()
        papers.append(title)
    return papers

def post_to_tistory():
    market = get_market_info()
    papers = get_ai_papers()
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    title = f"[린의 리포트] {today} 글로벌 빅테크 & AI 논문 분석"
    content = f"""
    <div style="text-align: center; border: 1px solid #ddd; padding: 20px;">
        <img src="https://blog.kakaocdn.net" width="150" />
        <h2>Lynn's Daily Insights</h2>
        <p>"데이터는 거짓말을 하지 않습니다. 늑대의 눈으로 시장을 읽으십시오."</p>
    </div>
    <br/>
    <h3>📈 시장 지표</h3>
    <ul>
        <li>NVIDIA: ${market['NVIDIA']}</li>
        <li>WTI 원유: ${market['WTI Oil']}</li>
    </ul>
    <h3>📝 최신 AI 논문</h3>
    <ul>
        <li>{papers[0]}</li>
        <li>{papers[1]}</li>
    </ul>
    <p><b>🐺 린의 조언:</b> 현재 변동성은 기회입니다. 로직에 기반한 대응을 유지하십시오.</p>
    """
    
    url = "https://www.tistory.com"
    data = {
        "access_token": TISTORY_TOKEN,
        "blogName": BLOG_NAME,
        "title": title,
        "content": content,
        "visibility": 3,
        "category": "AI자산관리"
    }
    return requests.post(url, data=data).json()

if __name__ == "__main__":
    print(post_to_tistory())
