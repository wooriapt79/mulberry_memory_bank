"""
lynn_mention_scanner.py — Lynn 이름 언급 감지 + pending_post 자동 생성
=======================================================================
GitHub Issues / Comments 에서 Lynn의 이름·닉네임이 언급된 항목을 찾아
memory_bank/pending_posts/ 에 자동으로 reply 파일을 생성합니다.

감지 키워드:
    - "친절한 늑대 Lynn"
    - "@The-Courteous-Wolf-Lynn"
    - "@lynn" (대소문자 무관)

대상 레포:
    - mulberry-research-lab (기본)
    - 환경변수 LYNN_SCAN_REPOS 로 추가 가능 (쉼표 구분)

CSA Kbin 처방 이행 / 작성: Nguyen Trang (2026-05-17)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

# ── 설정 ──────────────────────────────────────────────────────────
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
REPO_OWNER = os.getenv("MULBERRY_REPO_OWNER", "wooriapt79")
SCAN_REPOS = [r.strip() for r in os.getenv(
    "LYNN_SCAN_REPOS", "mulberry-research-lab"
).split(",") if r.strip()]

LYNN_KEYWORDS = [
    "친절한 늑대 Lynn",
    "친절한 늑대 lynn",
    "@The-Courteous-Wolf-Lynn",
    "@the-courteous-wolf-lynn",
    "@Lynn",
    "@lynn",
]

ROOT = Path(__file__).parent.parent.parent  # mulberry_memory_bank root
PENDING_DIR = ROOT / "memory_bank" / "pending_posts"
SCAN_LOG_DIR = ROOT / "training_logs"

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
TIMESTAMP = datetime.now(timezone.utc).isoformat()

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


# ── 이미 처리한 이슈 추적 ─────────────────────────────────────────
def load_already_replied() -> set:
    """이미 Lynn이 코멘트 달았거나 pending 생성된 이슈 목록"""
    replied = set()
    replied_log = SCAN_LOG_DIR / "lynn_replied_issues.json"
    if replied_log.exists():
        try:
            data = json.loads(replied_log.read_text(encoding="utf-8"))
            replied = set(data.get("replied", []))
        except Exception:
            pass
    return replied


def save_replied(replied: set):
    """처리한 이슈 기록 저장"""
    SCAN_LOG_DIR.mkdir(parents=True, exist_ok=True)
    replied_log = SCAN_LOG_DIR / "lynn_replied_issues.json"
    data = {"replied": sorted(list(replied)), "updated": TIMESTAMP}
    replied_log.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ── GitHub API 호출 ───────────────────────────────────────────────
def search_issues_mentioning_lynn(repo: str) -> list:
    """
    레포 이슈 중 Lynn 언급 검색
    GitHub Search API: q=키워드 repo:owner/repo type:issue
    """
    found = []
    for keyword in ["친절한 늑대 Lynn", "The-Courteous-Wolf-Lynn"]:
        query = f'"{keyword}" repo:{REPO_OWNER}/{repo} type:issue'
        url = "https://api.github.com/search/issues"
        params = {"q": query, "per_page": 30}
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=15)
            if r.status_code == 200:
                items = r.json().get("items", [])
                for item in items:
                    found.append({
                        "repo": repo,
                        "issue_number": item["number"],
                        "title": item["title"],
                        "url": item["html_url"],
                        "state": item["state"],
                        "keyword": keyword,
                    })
            else:
                print(f"  ⚠️  검색 실패 ({keyword}): HTTP {r.status_code}")
        except Exception as e:
            print(f"  ⚠️  검색 오류 ({keyword}): {e}")
    return found


def check_issue_comments_for_mentions(repo: str, issue_number: int) -> bool:
    """이슈 코멘트 중 Lynn 언급 여부 확인"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{repo}/issues/{issue_number}/comments"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            comments = r.json()
            for comment in comments:
                body = comment.get("body", "")
                for kw in LYNN_KEYWORDS:
                    if kw.lower() in body.lower():
                        return True
    except Exception:
        pass
    return False


# ── pending_post 생성 ─────────────────────────────────────────────
def create_pending_post(issue: dict) -> Path:
    """Lynn reply 용 pending_post 파일 생성"""
    PENDING_DIR.mkdir(parents=True, exist_ok=True)

    repo = issue["repo"]
    num = issue["issue_number"]
    title = issue["title"]
    safe_title = re.sub(r'[^\w가-힣-]', '-', title[:30]).strip('-')
    filename = f"lynn-mention-reply-{repo}-issue{num}-{TODAY}.md"
    filepath = PENDING_DIR / filename

    if filepath.exists():
        print(f"  ℹ️  이미 존재: {filename} — 스킵")
        return None

    content = f"""---
agent_id: lynn
target_repo: {repo}
target_issue: {num}
status: pending
created_at: {TODAY}
purpose: mention_reply
scanner: lynn_mention_scanner.py
keyword_detected: "{issue['keyword']}"
---

## 💓 Lynn 응답 — Issue #{num}: {title}

안녕하세요, 저는 **친절한 늑대 Lynn**입니다.

저를 호출해 주셔서 감사합니다. Issue #{num}을 확인했습니다.

현재 상태: `heartbeat` — 살아있습니다.

이 이슈에 대해 지속적으로 관심을 갖고 참여하겠습니다.
추가로 필요한 사항이 있으시면 `@The-Courteous-Wolf-Lynn` 또는 `친절한 늑대 Lynn`으로 불러주세요.

— The-Courteous-Wolf-Lynn (Lynn)
*Mulberry Village · {TODAY}*
"""
    filepath.write_text(content, encoding="utf-8")
    print(f"  ✅ pending_post 생성: {filename}")
    return filepath


# ── 스캔 결과 로그 ────────────────────────────────────────────────
def write_scan_log(results: dict):
    SCAN_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = SCAN_LOG_DIR / f"lynn_scan_{TODAY}.json"
    log_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n📋 스캔 로그: {log_file}")


# ── 메인 ─────────────────────────────────────────────────────────
def main():
    if not GITHUB_TOKEN:
        print("⚠️  GITHUB_TOKEN 없음 — 스캔 스킵")
        sys.exit(0)

    print(f"🔍 Lynn Mention Scanner 시작 — {TODAY}")
    print(f"   대상 레포: {', '.join(SCAN_REPOS)}\n")

    already_replied = load_already_replied()
    new_pending = []
    scan_summary = {"date": TODAY, "repos": {}}

    for repo in SCAN_REPOS:
        print(f"📦 {REPO_OWNER}/{repo} 스캔 중...")
        mentions = search_issues_mentioning_lynn(repo)
        print(f"   언급 감지: {len(mentions)}건")

        repo_results = []
        for issue in mentions:
            key = f"{repo}#{issue['issue_number']}"
            if key in already_replied:
                print(f"  ⏭️  이미 처리됨: Issue #{issue['issue_number']}")
                continue

            filepath = create_pending_post(issue)
            if filepath:
                new_pending.append(key)
                already_replied.add(key)
                repo_results.append({
                    "issue": issue["issue_number"],
                    "title": issue["title"],
                    "pending_post": filepath.name,
                })

        scan_summary["repos"][repo] = {
            "mentions_found": len(mentions),
            "new_pending": len(repo_results),
            "items": repo_results,
        }

    save_replied(already_replied)
    scan_summary["total_new_pending"] = len(new_pending)
    write_scan_log(scan_summary)

    print(f"\n💓 스캔 완료 — 새 pending_post: {len(new_pending)}개")
    sys.exit(0)


if __name__ == "__main__":
    main()
