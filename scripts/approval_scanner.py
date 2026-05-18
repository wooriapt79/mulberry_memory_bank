"""
approval_scanner.py — Mulberry 승인 코멘트 스캐너
==================================================
Spec: trang-agent-approval-system-spec-20260518.md · Issue #35

사용법:
  python scripts/approval_scanner.py                  # 기본 실행
  python scripts/approval_scanner.py --days 1         # 최근 1일 코멘트만 스캔
  python scripts/approval_scanner.py --dry-run        # 실제 저장 없이 감지만 출력
  python scripts/approval_scanner.py --repo mulberry-research-lab --issue 35

GitHub Actions 통합:
  - name: Approval Scanner
    run: python scripts/approval_scanner.py
    continue-on-error: true

스캔 패턴:
  ✅ approve req-{id}   → 승인
  ❌ reject  req-{id}   → 거절
"""

import json
import os
import re
import sys
import yaml
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

# ── 경로 설정 ────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
APPROVAL_DIR = ROOT / "memory_bank" / "approval_requests"
SCAN_LOG = ROOT / "memory_bank" / "essence_logs" / "approval_scan_log.jsonl"
APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
SCAN_LOG.parent.mkdir(parents=True, exist_ok=True)

# ── 환경 변수 ────────────────────────────────────────────────────
GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN", "")
REPO_OWNER     = os.getenv("MULBERRY_REPO_OWNER", "wooriapt79")
APPROVAL_REPO  = os.getenv("APPROVAL_REPO", "mulberry-research-lab")
APPROVAL_ISSUE = int(os.getenv("APPROVAL_ISSUE", "35"))
SCAN_DAYS      = int(os.getenv("APPROVAL_SCAN_DAYS", "2"))

# ── 패턴 ────────────────────────────────────────────────────────
APPROVE_PATTERN = re.compile(r"✅\s*approve\s+(req-[a-f0-9]+-\d{8})", re.IGNORECASE)
REJECT_PATTERN  = re.compile(r"❌\s*reject\s+(req-[a-f0-9]+-\d{8})", re.IGNORECASE)

# 알려진 승인자 (GitHub 사용자명 또는 이름)
KNOWN_APPROVERS = {
    "wooriapt79":   "CEO re.eul",
    "re-eul":       "CEO re.eul",
    "kbin-gpt":     "Kbin",
    "trang-pm":     "Trang",
    "koda-claude":  "Koda",
}


class ApprovalScanner:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.results = {
            "scanned_comments": 0,
            "approvals_found": 0,
            "rejections_found": 0,
            "already_processed": 0,
            "errors": 0,
        }

    # ── 공개 API ─────────────────────────────────────────────────

    def run(self, repo: str = None, issue: int = None, days: int = None) -> dict:
        """
        메인 스캔 실행.
        returns: 처리 결과 요약 dict
        """
        target_repo = repo or APPROVAL_REPO
        target_issue = issue or APPROVAL_ISSUE
        scan_days = days or SCAN_DAYS

        if not GITHUB_TOKEN:
            print("[Scanner] GITHUB_TOKEN 없음 — 스캔 불가", file=sys.stderr)
            return {"error": "GITHUB_TOKEN not set"}

        print(f"[Scanner] 스캔 시작: {REPO_OWNER}/{target_repo}#{target_issue} (최근 {scan_days}일)")

        comments = self._fetch_recent_comments(target_repo, target_issue, scan_days)
        print(f"[Scanner] 코멘트 {len(comments)}건 수신")

        for comment in comments:
            self.results["scanned_comments"] += 1
            self._process_comment(comment)

        # 만료된 요청 처리
        expired = self._expire_old_requests()

        summary = {
            **self.results,
            "expired": expired,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dry_run": self.dry_run,
        }
        self._write_scan_log(summary)
        self._print_summary(summary)
        return summary

    # ── 내부 메서드 ───────────────────────────────────────────────

    def _fetch_recent_comments(self, repo: str, issue: int, days: int) -> list[dict]:
        """GitHub Issue 코멘트 목록 조회 (최근 N일)"""
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        url = f"https://api.github.com/repos/{REPO_OWNER}/{repo}/issues/{issue}/comments"
        params = {"since": since, "per_page": 100}
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=20)
            if resp.status_code == 200:
                return resp.json()
            print(f"[Scanner] GitHub API 오류: {resp.status_code} — {resp.text[:200]}", file=sys.stderr)
            return []
        except Exception as e:
            print(f"[Scanner] 코멘트 조회 예외: {e}", file=sys.stderr)
            self.results["errors"] += 1
            return []

    def _process_comment(self, comment: dict) -> None:
        """단일 코멘트에서 approve/reject 패턴 감지 후 처리"""
        body = comment.get("body", "")
        commenter = comment.get("user", {}).get("login", "unknown")
        comment_id = comment.get("id")
        created_at = comment.get("created_at", "")

        # approve 패턴 확인
        approve_matches = APPROVE_PATTERN.findall(body)
        for request_id in approve_matches:
            approver_name = KNOWN_APPROVERS.get(commenter, commenter)
            self._handle_approval(request_id, approver_name, body, comment_id, created_at)

        # reject 패턴 확인
        reject_matches = REJECT_PATTERN.findall(body)
        for request_id in reject_matches:
            rejector_name = KNOWN_APPROVERS.get(commenter, commenter)
            self._handle_rejection(request_id, rejector_name, body, comment_id, created_at)

    def _handle_approval(
        self,
        request_id: str,
        approver: str,
        comment_body: str,
        comment_id: int,
        created_at: str,
    ) -> None:
        path = APPROVAL_DIR / f"{request_id}.yaml"
        if not path.exists():
            print(f"[Scanner] 요청 파일 없음: {request_id} (알 수 없는 요청 ID)")
            return

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # 이미 처리된 경우
        if data.get("status") in ("approved", "rejected"):
            self.results["already_processed"] += 1
            return

        # 만료 확인
        expires = data.get("expires_at", "")
        if expires:
            exp_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > exp_dt:
                data["status"] = "expired"
                if not self.dry_run:
                    self._save_yaml(path, data)
                print(f"[Scanner] 만료된 요청: {request_id}")
                return

        # 중복 승인 체크 (같은 승인자가 이미 승인했는지)
        already_approved_by = [
            r.get("approver") for r in data.get("approvers_responded", [])
            if r.get("decision") == "approved"
        ]
        if approver in already_approved_by:
            self.results["already_processed"] += 1
            return

        # 승인 기록 추가
        approval_record = {
            "approver": approver,
            "approved_at": created_at,
            "decision": "approved",
            "github_comment_id": comment_id,
        }
        if "approvers_responded" not in data:
            data["approvers_responded"] = []
        data["approvers_responded"].append(approval_record)

        # 필요 승인 수 충족 여부
        approved_count = sum(
            1 for r in data["approvers_responded"] if r.get("decision") == "approved"
        )
        required = data.get("approvers_required", 1)
        if approved_count >= required:
            data["status"] = "approved"
            print(f"[Scanner] ✅ 승인 완료: {request_id} (by {approver})")
        else:
            print(f"[Scanner] 승인 진행 중: {request_id} ({approved_count}/{required})")

        self.results["approvals_found"] += 1
        if not self.dry_run:
            self._save_yaml(path, data)

    def _handle_rejection(
        self,
        request_id: str,
        rejector: str,
        comment_body: str,
        comment_id: int,
        created_at: str,
    ) -> None:
        path = APPROVAL_DIR / f"{request_id}.yaml"
        if not path.exists():
            print(f"[Scanner] 요청 파일 없음: {request_id}")
            return

        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data.get("status") in ("approved", "rejected"):
            self.results["already_processed"] += 1
            return

        data["status"] = "rejected"
        if "approvers_responded" not in data:
            data["approvers_responded"] = []
        data["approvers_responded"].append({
            "approver": rejector,
            "decided_at": created_at,
            "decision": "rejected",
            "github_comment_id": comment_id,
        })
        print(f"[Scanner] ❌ 거절: {request_id} (by {rejector})")
        self.results["rejections_found"] += 1
        if not self.dry_run:
            self._save_yaml(path, data)

    def _expire_old_requests(self) -> int:
        """만료 시각이 지난 pending 요청을 expired 로 변경"""
        count = 0
        now = datetime.now(timezone.utc)
        for p in APPROVAL_DIR.glob("req-*.yaml"):
            try:
                with open(p, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data.get("status") != "pending":
                    continue
                expires = data.get("expires_at", "")
                if expires:
                    exp_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
                    if now > exp_dt:
                        data["status"] = "expired"
                        if not self.dry_run:
                            self._save_yaml(p, data)
                        count += 1
            except Exception:
                continue
        if count:
            print(f"[Scanner] 만료 처리: {count}건")
        return count

    def _save_yaml(self, path: Path, data: dict) -> None:
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False, indent=2)

    def _write_scan_log(self, summary: dict) -> None:
        if self.dry_run:
            return
        try:
            with open(SCAN_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(summary, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def _print_summary(self, summary: dict) -> None:
        mode = " [DRY-RUN]" if summary["dry_run"] else ""
        print(f"\n[Scanner] 완료{mode}")
        print(f"  스캔 코멘트: {summary['scanned_comments']}건")
        print(f"  승인 감지:   {summary['approvals_found']}건")
        print(f"  거절 감지:   {summary['rejections_found']}건")
        print(f"  이미 처리됨: {summary['already_processed']}건")
        print(f"  만료 처리:   {summary['expired']}건")


# ── CLI ──────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Mulberry 승인 코멘트 스캐너")
    parser.add_argument("--repo", default=None, help="스캔할 GitHub 레포 (기본: APPROVAL_REPO 환경변수)")
    parser.add_argument("--issue", type=int, default=None, help="스캔할 Issue 번호")
    parser.add_argument("--days", type=int, default=None, help="최근 N일 코멘트 스캔 (기본: 2)")
    parser.add_argument("--dry-run", action="store_true", help="실제 저장 없이 출력만")
    parser.add_argument("--list-pending", action="store_true", help="pending 요청 목록 출력")
    args = parser.parse_args()

    if args.list_pending:
        pending = sorted(APPROVAL_DIR.glob("req-*.yaml"))
        print(f"\nApproval Requests ({len(pending)}건):\n")
        for p in pending:
            try:
                with open(p, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                status_icon = {
                    "pending": "⏳",
                    "approved": "✅",
                    "rejected": "❌",
                    "expired": "🕐",
                }.get(data.get("status", ""), "❓")
                action = data.get("action", {})
                print(f"  {status_icon} {data['request_id']}")
                print(f"     작업: [{action.get('level','')}] {action.get('description','')}")
                print(f"     만료: {data.get('expires_at','')}\n")
            except Exception:
                print(f"  ⚠️  {p.name} (파싱 오류)")
        return

    scanner = ApprovalScanner(dry_run=args.dry_run)
    scanner.run(repo=args.repo, issue=args.issue, days=args.days)


if __name__ == "__main__":
    main()
