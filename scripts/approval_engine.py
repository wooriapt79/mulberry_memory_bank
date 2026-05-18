"""
approval_engine.py — Mulberry Agent 권한 승인 엔진
==================================================
Spec: trang-agent-approval-system-spec-20260518.md · Issue #35

사용법:
  from scripts.approval_engine import ApprovalEngine, ApprovalResult

  engine = ApprovalEngine()

  # 실행 전 권한 확인
  result = engine.check(
      action_type="github_commit",
      agent_id="MULBERRY-GUARD-LYNN-001",
      description="daily_write.yml 업데이트",
      files=[".github/workflows/lynn_daily_write.yml"],
  )
  if result.approved:
      # 작업 실행
      ...
  else:
      print(f"승인 대기 중 — request_id: {result.request_id}")

권한 레벨:
  L0: 자동 승인 (로그 기록, 상태 조회)
  L1: 자동 승인 + 사후 알림 (GitHub 코멘트 게시)
  L2: 사전 승인 필요 (GitHub 커밋, 외부 API 호출)
  L3: 시니어 승인 필요 (Railway 배포, Passport 수정)
  L4: 합의 승인 필요 (3인 이상 — 전체 시스템 변경)
"""

from __future__ import annotations

import json
import os
import uuid
import yaml
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import requests

# ── 경로 설정 ────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
APPROVAL_DIR = ROOT / "memory_bank" / "approval_requests"
APPROVAL_DIR.mkdir(parents=True, exist_ok=True)

# ── 환경 변수 ────────────────────────────────────────────────────
GITHUB_TOKEN    = os.getenv("GITHUB_TOKEN", "")
GATEWAY_SECRET  = os.getenv("GATEWAY_SECRET", "mulberry-agent-relay-2026")
GATEWAY_URL     = os.getenv(
    "GATEWAY_URL",
    "https://loving-education-production-cc9e.up.railway.app"
)
REPO_OWNER      = os.getenv("MULBERRY_REPO_OWNER", "wooriapt79")
APPROVAL_REPO   = os.getenv("APPROVAL_REPO", "mulberry-research-lab")
APPROVAL_ISSUE  = int(os.getenv("APPROVAL_ISSUE", "35"))   # 승인 요청을 올릴 GitHub Issue 번호
EXPIRY_HOURS    = int(os.getenv("APPROVAL_EXPIRY_HOURS", "8"))


# ── 작업 유형 → 권한 레벨 매핑 ──────────────────────────────────
LEVEL_MAP: dict[str, str] = {
    # L0 — 승인 불필요
    "log_write":        "L0",
    "status_check":     "L0",
    "heartbeat":        "L0",
    "issue_read":       "L0",
    # L1 — 실행 후 알림
    "github_comment":   "L1",
    "pending_post":     "L1",
    "slack_notify":     "L1",
    # L2 — 사전 승인
    "github_commit":    "L2",
    "github_push":      "L2",
    "external_api":     "L2",
    "image_generate":   "L2",
    # L3 — 시니어 승인
    "railway_deploy":   "L3",
    "passport_update":  "L3",
    "env_change":       "L3",
    # L4 — 합의 승인
    "system_change":    "L4",
    "multi_repo_change":"L4",
}

# 레벨별 필요 승인자 수
APPROVERS_REQUIRED: dict[str, int] = {
    "L0": 0,
    "L1": 0,
    "L2": 1,
    "L3": 1,
    "L4": 3,
}

# 레벨별 승인 가능자
APPROVER_ROLES: dict[str, list[str]] = {
    "L2": ["Trang", "Koda"],
    "L3": ["CEO re.eul", "Kbin"],
    "L4": ["CEO re.eul", "Kbin", "Koda"],
}


# ── 데이터 클래스 ────────────────────────────────────────────────

@dataclass
class ApprovalResult:
    approved: bool
    level: str
    request_id: Optional[str] = None
    message: str = ""
    notify_posted: bool = False

    def __bool__(self) -> bool:
        return self.approved


@dataclass
class ApprovalRequest:
    request_id: str
    created_at: str
    status: str                          # pending / approved / rejected / expired
    agent_id: str
    display_name: str
    action_type: str
    level: str
    description: str
    target_repo: str
    files_affected: list[str]
    reason: str
    approvers_required: int
    approvers_responded: list[dict]
    expires_at: str
    extra: dict = field(default_factory=dict)

    def to_yaml_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "created_at": self.created_at,
            "status": self.status,
            "requester": {
                "agent_id": self.agent_id,
                "display_name": self.display_name,
            },
            "action": {
                "type": self.action_type,
                "level": self.level,
                "description": self.description,
                "target_repo": self.target_repo,
                "files_affected": self.files_affected,
                "reason": self.reason,
            },
            "approvers_required": self.approvers_required,
            "approvers_responded": self.approvers_responded,
            "expires_at": self.expires_at,
            **({"extra": self.extra} if self.extra else {}),
        }


# ── 승인 엔진 ────────────────────────────────────────────────────

class ApprovalEngine:
    """
    Mulberry Agent 권한 승인 엔진.
    에이전트 스크립트에서 import하여 사용한다.
    """

    def __init__(
        self,
        agent_id: str = "MULBERRY-SYSTEM",
        display_name: str = "System",
        notify_via_github: bool = True,
    ):
        self.agent_id = agent_id
        self.display_name = display_name
        self.notify_via_github = notify_via_github

    # ── 공개 API ─────────────────────────────────────────────────

    def check(
        self,
        action_type: str,
        description: str = "",
        files: Optional[list[str]] = None,
        target_repo: str = "mulberry_memory_bank",
        reason: str = "",
        **extra,
    ) -> ApprovalResult:
        """
        작업 실행 전 권한 확인.
        L0/L1 → 즉시 승인 반환
        L2/L3/L4 → 승인 요청 파일 생성 + GitHub 알림 → pending 반환
        """
        level = LEVEL_MAP.get(action_type, "L2")

        if level in ("L0", "L1"):
            notify_posted = False
            if level == "L1" and description:
                notify_posted = self._post_l1_notify(action_type, description, target_repo)
            return ApprovalResult(
                approved=True,
                level=level,
                message=f"[{level}] 자동 승인: {action_type}",
                notify_posted=notify_posted,
            )

        # L2 이상: 기존 pending 요청 체크
        existing = self._find_pending(action_type, target_repo)
        if existing:
            status = existing.get("status", "pending")
            if status == "approved":
                return ApprovalResult(
                    approved=True,
                    level=level,
                    request_id=existing["request_id"],
                    message=f"[{level}] 승인 완료: {existing['request_id']}",
                )
            if status == "rejected":
                return ApprovalResult(
                    approved=False,
                    level=level,
                    request_id=existing["request_id"],
                    message=f"[{level}] 거절됨: {existing['request_id']}",
                )
            # 아직 pending — 대기
            return ApprovalResult(
                approved=False,
                level=level,
                request_id=existing["request_id"],
                message=f"[{level}] 승인 대기 중: {existing['request_id']}",
            )

        # 새 승인 요청 생성
        req = self._create_request(
            action_type=action_type,
            level=level,
            description=description,
            files=files or [],
            target_repo=target_repo,
            reason=reason,
            extra=extra,
        )
        self._save_request(req)
        notify_posted = False
        if self.notify_via_github:
            notify_posted = self._post_approval_request(req)

        return ApprovalResult(
            approved=False,
            level=level,
            request_id=req.request_id,
            message=f"[{level}] 승인 요청 생성: {req.request_id}",
            notify_posted=notify_posted,
        )

    def approve(self, request_id: str, approver: str, comment: str = "") -> bool:
        """
        승인 처리 (approval_scanner.py 또는 수동 호출).
        returns True if successfully approved.
        """
        path = APPROVAL_DIR / f"{request_id}.yaml"
        if not path.exists():
            return False
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        now = datetime.now(timezone.utc).isoformat()
        data["approvers_responded"].append({
            "approver": approver,
            "approved_at": now,
            "decision": "approved",
            "comment": comment,
        })
        required = data.get("approvers_required", 1)
        approved_count = sum(
            1 for r in data["approvers_responded"] if r.get("decision") == "approved"
        )
        if approved_count >= required:
            data["status"] = "approved"

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False, indent=2)
        return data["status"] == "approved"

    def reject(self, request_id: str, rejector: str, comment: str = "") -> bool:
        """승인 거절 처리"""
        path = APPROVAL_DIR / f"{request_id}.yaml"
        if not path.exists():
            return False
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        now = datetime.now(timezone.utc).isoformat()
        data["status"] = "rejected"
        data["approvers_responded"].append({
            "approver": rejector,
            "decided_at": now,
            "decision": "rejected",
            "comment": comment,
        })
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False, indent=2)
        return True

    def list_pending(self) -> list[dict]:
        """현재 pending 상태인 요청 목록 반환"""
        results = []
        for p in sorted(APPROVAL_DIR.glob("req-*.yaml")):
            try:
                with open(p, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if data.get("status") == "pending":
                    # 만료 체크
                    expires = data.get("expires_at", "")
                    if expires:
                        exp_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
                        if datetime.now(timezone.utc) > exp_dt:
                            data["status"] = "expired"
                            with open(p, "w", encoding="utf-8") as f:
                                yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False, indent=2)
                            continue
                    results.append(data)
            except Exception:
                continue
        return results

    # ── 내부 메서드 ───────────────────────────────────────────────

    def _create_request(
        self,
        action_type: str,
        level: str,
        description: str,
        files: list[str],
        target_repo: str,
        reason: str,
        extra: dict,
    ) -> ApprovalRequest:
        now = datetime.now(timezone.utc)
        short_id = uuid.uuid4().hex[:6]
        date_str = now.strftime("%Y%m%d")
        request_id = f"req-{short_id}-{date_str}"
        expires_at = (now + timedelta(hours=EXPIRY_HOURS)).strftime("%Y-%m-%dT%H:%M:%SZ")

        return ApprovalRequest(
            request_id=request_id,
            created_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            status="pending",
            agent_id=self.agent_id,
            display_name=self.display_name,
            action_type=action_type,
            level=level,
            description=description,
            target_repo=target_repo,
            files_affected=files,
            reason=reason,
            approvers_required=APPROVERS_REQUIRED.get(level, 1),
            approvers_responded=[],
            expires_at=expires_at,
            extra=extra,
        )

    def _save_request(self, req: ApprovalRequest) -> Path:
        path = APPROVAL_DIR / f"{req.request_id}.yaml"
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(
                req.to_yaml_dict(),
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
                indent=2,
            )
        return path

    def _find_pending(self, action_type: str, target_repo: str) -> Optional[dict]:
        """같은 action_type + repo 의 유효한 pending 요청이 있으면 반환"""
        for p in sorted(APPROVAL_DIR.glob("req-*.yaml"), reverse=True):
            try:
                with open(p, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                action = data.get("action", {})
                if (
                    action.get("type") == action_type
                    and action.get("target_repo") == target_repo
                    and data.get("status") in ("pending", "approved", "rejected")
                ):
                    # 만료 체크
                    expires = data.get("expires_at", "")
                    if expires and data["status"] == "pending":
                        exp_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
                        if datetime.now(timezone.utc) > exp_dt:
                            data["status"] = "expired"
                            with open(p, "w", encoding="utf-8") as f:
                                yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False, indent=2)
                            continue
                    return data
            except Exception:
                continue
        return None

    def _post_l1_notify(self, action_type: str, description: str, target_repo: str) -> bool:
        """L1: 작업 실행 사후 알림 (GitHub 코멘트)"""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        body = (
            f"## 📋 작업 알림 — L1\n\n"
            f"**실행자**: {self.display_name}  \n"
            f"**작업**: `{action_type}` — {description}  \n"
            f"**대상**: `{target_repo}`  \n"
            f"**시각**: {now}  \n\n"
            f"*L1 — 승인 불필요 · 사후 보고*"
        )
        return self._github_comment(body)

    def _post_approval_request(self, req: ApprovalRequest) -> bool:
        """L2/L3/L4: 승인 요청 GitHub 코멘트 게시"""
        level_emoji = {"L2": "🔐", "L3": "🔒", "L4": "🚨"}.get(req.level, "🔐")
        approvers = APPROVER_ROLES.get(req.level, ["팀 리더"])
        files_str = "\n".join(f"  - `{f}`" for f in req.files_affected) if req.files_affected else "  - (파일 명시 없음)"

        body = (
            f"## {level_emoji} 승인 요청 — {req.level}\n\n"
            f"**요청자**: {req.display_name}  \n"
            f"**작업**: `{req.action_type}` — {req.description}  \n"
            f"**대상 저장소**: `{req.target_repo}`  \n"
            f"**영향 파일**:\n{files_str}\n"
            f"**이유**: {req.reason or '(사유 미입력)'}  \n"
            f"**요청 ID**: `{req.request_id}`  \n"
            f"**만료**: {req.expires_at}  \n"
            f"**승인 가능**: {', '.join(approvers)}  \n\n"
            f"승인하려면 아래 코멘트를 달아주세요:\n"
            f"> ✅ approve {req.request_id}\n\n"
            f"거절하려면:\n"
            f"> ❌ reject {req.request_id}"
        )
        return self._github_comment(body)

    def _github_comment(self, body: str) -> bool:
        """GitHub Issue에 코멘트 게시. 실패해도 예외 발생하지 않음."""
        if not GITHUB_TOKEN:
            print(f"[ApprovalEngine] GITHUB_TOKEN 없음 — GitHub 알림 생략")
            return False
        url = f"https://api.github.com/repos/{REPO_OWNER}/{APPROVAL_REPO}/issues/{APPROVAL_ISSUE}/comments"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }
        try:
            resp = requests.post(
                url,
                headers=headers,
                data=json.dumps({"body": body}, ensure_ascii=False).encode("utf-8"),
                timeout=15,
            )
            if resp.status_code == 201:
                print(f"[ApprovalEngine] GitHub 알림 게시 완료: {resp.json()['html_url']}")
                return True
            print(f"[ApprovalEngine] GitHub 알림 실패: {resp.status_code}")
            return False
        except Exception as e:
            print(f"[ApprovalEngine] GitHub 알림 예외: {e}")
            return False


# ── CLI (테스트용) ────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ApprovalEngine CLI 테스트")
    parser.add_argument("--action", default="github_commit", help="action_type")
    parser.add_argument("--agent", default="MULBERRY-GUARD-LYNN-001")
    parser.add_argument("--name", default="친절한 늑대 Lynn")
    parser.add_argument("--desc", default="테스트 커밋")
    parser.add_argument("--repo", default="mulberry_memory_bank")
    parser.add_argument("--list", action="store_true", help="pending 목록 출력")
    args = parser.parse_args()

    engine = ApprovalEngine(agent_id=args.agent, display_name=args.name)

    if args.list:
        pending = engine.list_pending()
        print(f"\nPending 승인 요청: {len(pending)}건\n")
        for p in pending:
            print(f"  [{p['action']['level']}] {p['request_id']}")
            print(f"    작업: {p['action']['description']}")
            print(f"    만료: {p['expires_at']}\n")
    else:
        result = engine.check(
            action_type=args.action,
            description=args.desc,
            target_repo=args.repo,
        )
        print(f"\n결과: {'✅ 승인' if result.approved else '⏳ 대기'}")
        print(f"레벨: {result.level}")
        print(f"메시지: {result.message}")
        if result.request_id:
            print(f"요청 ID: {result.request_id}")
