# scripts/arxiv_hunter.py
"""
Lynn's arXiv Hunter — Mulberry Research Lab 논문 수집 모듈

매일 cs.AI / cs.LG / cs.CL / cs.MA 카테고리 최신 논문을 수집합니다.
특정 arxiv URL도 직접 파싱 지원 (request.txt에서 읽어온 URL 포함).

Mulberry 연관성 키워드 자동 점수화:
  agent / cooperative / ethics / multimodal / korean / community / food /
  proactive / persona / memory / scruple / autonomous
"""

import requests
import xml.etree.ElementTree as ET
import re
from datetime import datetime
from dataclasses import dataclass, field

# Atom feed namespace
NS = "{http://www.w3.org/2005/Atom}"

ARXIV_API = "http://export.arxiv.org/api/query"

# Mulberry 프로젝트 연관 키워드 → 점수
MULBERRY_KEYWORDS: dict[str, int] = {
    "agent":        3,
    "multi-agent":  4,
    "cooperative":  3,
    "ethics":       3,
    "ethical":      3,
    "proactive":    3,
    "persona":      3,
    "memory":       2,
    "autonomous":   2,
    "multimodal":   2,
    "community":    2,
    "food":         2,
    "korean":       3,
    "scruple":      5,
    "llm":          2,
    "reasoning":    2,
    "alignment":    3,
    "safety":       2,
    "social":       2,
    "edge":         2,
}

# 수집 대상 카테고리
DEFAULT_CATEGORIES = ["cs.AI", "cs.LG", "cs.CL", "cs.MA"]


@dataclass
class Paper:
    title:      str
    authors:    list[str]
    summary:    str
    link:       str
    published:  str
    categories: list[str]
    mulberry_score: int = 0
    matched_keywords: list[str] = field(default_factory=list)

    @property
    def short_summary(self) -> str:
        return self.summary[:300].replace("\n", " ") + "..."

    @property
    def relevance_tag(self) -> str:
        if self.mulberry_score >= 8:
            return "🔴 HIGH"
        elif self.mulberry_score >= 4:
            return "🟡 MEDIUM"
        return "🟢 WATCH"


def _score_paper(paper_text: str) -> tuple[int, list[str]]:
    """제목 + 요약 텍스트에서 Mulberry 연관성 점수 계산"""
    text = paper_text.lower()
    score = 0
    matched = []
    for kw, pts in MULBERRY_KEYWORDS.items():
        if kw in text:
            score += pts
            matched.append(kw)
    return score, matched


def fetch_latest(
    categories: list[str] = None,
    max_results: int = 5,
) -> list[Paper]:
    """
    arxiv API로 최신 논문 수집

    Args:
        categories: 수집할 카테고리 리스트
        max_results: 최대 수집 편수

    Returns:
        Paper 리스트 (Mulberry 연관성 점수 내림차순)
    """
    cats = categories or DEFAULT_CATEGORIES
    query = " OR ".join(f"cat:{c}" for c in cats)

    params = {
        "search_query": query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": max_results,
    }

    try:
        resp = requests.get(ARXIV_API, params=params, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"[arxiv_hunter] API 요청 실패: {e}")
        return []

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        print(f"[arxiv_hunter] XML 파싱 실패: {e}")
        return []

    papers = []
    for entry in root.findall(f"{NS}entry"):
        title   = _text(entry, "title")
        summary = _text(entry, "summary")
        link    = _text(entry, "id")
        pub     = _text(entry, "published")[:10]  # YYYY-MM-DD
        authors = [
            _text(a, "name")
            for a in entry.findall(f"{NS}author")
        ]
        cats_found = [
            t.get("term", "")
            for t in entry.findall(f"{NS}category")
        ]

        score, matched = _score_paper(f"{title} {summary}")
        papers.append(Paper(
            title=title,
            authors=authors[:3],  # 최대 3명
            summary=summary,
            link=link,
            published=pub,
            categories=cats_found,
            mulberry_score=score,
            matched_keywords=matched,
        ))

    # Mulberry 연관성 높은 순 정렬
    return sorted(papers, key=lambda p: p.mulberry_score, reverse=True)


def fetch_by_id(arxiv_id: str) -> Paper | None:
    """
    특정 arxiv ID 또는 URL로 단일 논문 수집
    예: "2604.24658" 또는 "https://arxiv.org/abs/2604.24658"
    """
    # URL에서 ID 추출
    match = re.search(r"(\d{4}\.\d{4,5})", arxiv_id)
    if not match:
        print(f"[arxiv_hunter] ID 파싱 실패: {arxiv_id}")
        return None

    paper_id = match.group(1)
    params = {"id_list": paper_id}

    try:
        resp = requests.get(ARXIV_API, params=params, timeout=15)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as e:
        print(f"[arxiv_hunter] 단일 논문 수집 실패: {e}")
        return None

    entry = root.find(f"{NS}entry")
    if entry is None:
        return None

    title   = _text(entry, "title")
    summary = _text(entry, "summary")
    link    = _text(entry, "id")
    pub     = _text(entry, "published")[:10]
    authors = [_text(a, "name") for a in entry.findall(f"{NS}author")][:3]
    cats    = [t.get("term", "") for t in entry.findall(f"{NS}category")]
    score, matched = _score_paper(f"{title} {summary}")

    return Paper(
        title=title,
        authors=authors,
        summary=summary,
        link=link,
        published=pub,
        categories=cats,
        mulberry_score=score,
        matched_keywords=matched,
    )


def papers_to_markdown(papers: list[Paper], date: str = None) -> str:
    """Paper 리스트 → 마크다운 섹션 변환"""
    date = date or datetime.now().strftime("%Y-%m-%d")
    lines = [f"## 🧠 AI 논문 사냥 결과 — {date}\n"]

    for i, p in enumerate(papers, 1):
        lines.append(f"### {i}. {p.relevance_tag} {p.title}")
        lines.append(f"- **저자**: {', '.join(p.authors)}")
        lines.append(f"- **분류**: {', '.join(p.categories[:3])}")
        lines.append(f"- **게재일**: {p.published}")
        lines.append(f"- **Mulberry 연관도**: {p.mulberry_score}점 ({', '.join(p.matched_keywords) or '일반'})")
        lines.append(f"- **요약**: {p.short_summary}")
        lines.append(f"- **링크**: {p.link}")
        lines.append("")

    return "\n".join(lines)


def _text(element, tag: str) -> str:
    el = element.find(f"{NS}{tag}")
    return el.text.strip() if el is not None and el.text else ""


if __name__ == "__main__":
    print("=== arxiv_hunter 테스트 ===")
    papers = fetch_latest(max_results=3)
    for p in papers:
        print(f"[{p.mulberry_score}pt] {p.title[:60]}")
    print()
    print("=== 특정 논문 테스트 ===")
    p = fetch_by_id("2604.24658")
    if p:
        print(f"제목: {p.title}")
        print(f"점수: {p.mulberry_score}pt | 키워드: {p.matched_keywords}")
