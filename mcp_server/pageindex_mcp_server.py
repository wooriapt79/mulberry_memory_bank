
import os
from pageindex import PageIndexEngine
from mcp.server import Server, tool

# 와룡이 설정해둔 API 키를 엔진에 연결 (DeepSeek 사용)
# 환경변수에 이미 등록되어 있다면 아래와 같이 호출됩니다.
engine = PageIndexEngine(model="deepseek-chat") 

server = Server("mulberry-pageindex")

@tool()
async def search_document(query: str, pdf_path: str) -> str:
    """PDF 문서에서 질문과 가장 관련된 구절을 찾아 반환합니다."""
    # PageIndex 엔진을 통해 문서 내 정답과 출처를 추출
    result = engine.query(pdf_path, query)
    return f"📄 출처: {result['source']}\n💡 답변: {result['answer']}"

if __name__ == "__main__":
    server.run()
