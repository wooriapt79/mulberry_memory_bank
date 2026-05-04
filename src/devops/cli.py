# src/devops/cli.py
"""
Mulberry Code Hygiene CLI — RyuWon (流願)

사용법:
  python -m src.devops.cli <path> [--threshold 80] [--output report.txt]
"""

import argparse
import sys
from pathlib import Path

from .handoff_checker import HandoffReadinessChecker


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mulberry Handoff Readiness Checker — '코드 위생은 윤리다'"
    )
    parser.add_argument("path", help="검사할 파일 또는 디렉토리 경로")
    parser.add_argument("--threshold", type=int, default=80,
                        help="인계 합격 점수 (기본: 80)")
    parser.add_argument("--output", type=str, default=None,
                        help="결과 저장 파일 경로")
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f"[ERROR] 경로가 존재하지 않습니다: {target}")
        sys.exit(1)

    # 디렉토리면 .py 파일 전체 검사
    files = list(target.rglob("*.py")) if target.is_dir() else [target]
    files = [f for f in files if "__pycache__" not in str(f)]

    if not files:
        print("[WARN] 검사할 .py 파일이 없습니다.")
        sys.exit(0)

    all_notes = []
    any_failed = False

    for f in files:
        checker = HandoffReadinessChecker(str(f), threshold=args.threshold)
        report = checker.check()
        print(report.handoff_note)
        if report.feedback:
            for line in report.feedback:
                print(f"  - {line}")
        if not report.passed:
            any_failed = True
        all_notes.append(report.handoff_note + "\n".join(report.feedback))

    if args.output:
        Path(args.output).write_text("\n\n".join(all_notes), encoding="utf-8")
        print(f"\n[SAVED] 결과 저장: {args.output}")

    if any_failed:
        print("\n[HOLD] 인계 보류 — 점수 기준 미달 파일이 있습니다.")
        sys.exit(1)
    else:
        print("\n[PASS] 모든 파일이 인계 준비 기준을 통과했습니다.")
        sys.exit(0)


if __name__ == "__main__":
    main()
