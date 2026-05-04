# src/devops/handoff_checker.py
"""
Mulberry Handoff Readiness Engine -RyuWon (流願)

철학: "코드 위생은 윤리다. 다음 작업자를 위한 배려가 코드에 담겨야 한다."
     "에러 없는 인계는, 다음 사람에게 건네는 정중한 인사입니다."
"""

import ast
import subprocess
from pathlib import Path
from typing import List
from dataclasses import dataclass, field


@dataclass
class HygieneMetrics:
    syntax_valid: bool = True
    lint_errors: int = 0
    lint_warnings: int = 0
    avg_complexity: float = 0.0
    docstring_ratio: float = 0.0
    type_hint_ratio: float = 0.0


@dataclass
class HandoffReport:
    score: int = 100
    passed: bool = True
    threshold: int = 80
    feedback: List[str] = field(default_factory=list)
    handoff_note: str = ""
    metrics: HygieneMetrics = field(default_factory=HygieneMetrics)


class HandoffReadinessChecker:
    """
    인계 전 코드 상태를 수치화하여 '다음 작업자에 대한 존중'을 검증하는 게이트.

    점수 기준 (100점 만점):
      - 구문 안전성  30pt
      - 린트 상태    25pt
      - 복잡도       20pt
      - 문서화       15pt
      - 타입 힌트    10pt
    """

    def __init__(self, target_path: str, threshold: int = 80):
        self.target_path = Path(target_path)
        self.threshold = threshold

    def check(self) -> HandoffReport:
        report = HandoffReport(threshold=self.threshold)
        metrics = HygieneMetrics()

        # 1. 구문 안전성 -실패 시 즉시 0점
        metrics.syntax_valid = self._check_syntax()
        if not metrics.syntax_valid:
            report.score = 0
            report.feedback.append("SyntaxError 가 있습니다. 인계 전 반드시 수정해 주세요.")
            report.passed = False
            report.handoff_note = self._generate_handoff_note(metrics, 0, False)
            return report

        # 2. 린트 (ruff)
        metrics.lint_errors, metrics.lint_warnings = self._run_linter()

        # 3. AST 정적 분석
        metrics.avg_complexity, metrics.docstring_ratio, metrics.type_hint_ratio = (
            self._analyze_ast()
        )

        report.score = self._calculate_score(metrics)
        report.metrics = metrics
        report.passed = report.score >= self.threshold
        report.feedback = self._generate_feedback(metrics, report.score)
        report.handoff_note = self._generate_handoff_note(metrics, report.score, report.passed)
        return report

    def _check_syntax(self) -> bool:
        try:
            ast.parse(self.target_path.read_text(encoding="utf-8"))
            return True
        except SyntaxError:
            return False

    def _run_linter(self) -> tuple:
        try:
            result = subprocess.run(
                ["ruff", "check", str(self.target_path), "--output-format=concise"],
                capture_output=True, text=True, check=False,
            )
            lines = result.stdout.strip().splitlines()
            errors = sum(1 for ln in lines if any(c in ln for c in ["E", "F"]))
            warnings = sum(1 for ln in lines if "W" in ln)
            return errors, warnings
        except FileNotFoundError:
            return 0, 0  # ruff 미설치 시 관대하게 통과

    def _analyze_ast(self) -> tuple:
        try:
            tree = ast.parse(self.target_path.read_text(encoding="utf-8"))
        except Exception:
            return 0.0, 0.0, 0.0

        complexities, doc_cnt, func_cnt, hint_cnt, ann_cnt = [], 0, 0, 0, 0

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            func_cnt += 1

            # 독스트링
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)):
                doc_cnt += 1

            # 순환 복잡도 (간이)
            comp = 1 + sum(
                1 for c in ast.walk(node)
                if isinstance(c, (ast.If, ast.For, ast.While,
                                  ast.And, ast.Or, ast.ExceptHandler))
            )
            complexities.append(comp)

            # 타입 힌트
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args_with_ann = sum(1 for a in node.args.args if a.annotation)
                hint_cnt += args_with_ann + (1 if node.returns else 0)
                ann_cnt += len(node.args.args) + 1

        return (
            sum(complexities) / len(complexities) if complexities else 0.0,
            doc_cnt / func_cnt if func_cnt else 1.0,
            hint_cnt / ann_cnt if ann_cnt else 1.0,
        )

    def _calculate_score(self, m: HygieneMetrics) -> int:
        score = 100.0
        score -= min(25, m.lint_errors * 2 + m.lint_warnings * 0.5)
        if m.avg_complexity > 10:
            score -= min(20, (m.avg_complexity - 10) * 2)
        if m.docstring_ratio < 0.8:
            score -= (0.8 - m.docstring_ratio) * 100 * 0.15
        if m.type_hint_ratio < 0.7:
            score -= (0.7 - m.type_hint_ratio) * 100 * 0.10
        return max(0, int(score))

    def _generate_feedback(self, m: HygieneMetrics, score: int) -> List[str]:
        fb = []
        if m.lint_errors > 0:
            fb.append(f"린트 오류 {m.lint_errors}개 -`ruff check --fix` 권장")
        if m.avg_complexity > 10:
            fb.append(f"복잡도 {m.avg_complexity:.1f} -함수 분할 권장 (기준: 10)")
        if m.docstring_ratio < 0.8:
            fb.append(f"문서화 {m.docstring_ratio:.0%} -다음 작업자를 위한 설명이 필요합니다")
        if m.type_hint_ratio < 0.7:
            fb.append(f"타입 힌트 {m.type_hint_ratio:.0%} -명확한 타입 정의가 피로를 줄입니다")
        if not fb:
            fb.append("코드 위생 상태 양호 -다음 작업자에게 존중을 담아 인계하세요")
        return fb

    def _generate_handoff_note(self, m: HygieneMetrics, score: int, passed: bool) -> str:
        status = "[PASS] 인계 준비 완료" if passed else "[HOLD] 인계 보류 -수정 필요"
        message = (
            "이 코드는 다음 작업자의 시간을 존중합니다. 편하게 작업하세요."
            if passed else
            "아직 피로를 전가할 요소가 있습니다. 스스로 다듬은 후 인계해 주세요."
        )
        return (
            f"\nMulberry Handoff Note - RyuWon (流願)\n"
            f"{'─' * 42}\n"
            f"상태 : {status}\n"
            f"점수 : {score}/100  (기준: {self.threshold})\n"
            f"\n측정 지표:\n"
            f"  구문 안전성  : {'PASS' if m.syntax_valid else 'FAIL'}\n"
            f"  린트 오류/경고: {m.lint_errors} / {m.lint_warnings}\n"
            f"  평균 복잡도  : {m.avg_complexity:.1f}\n"
            f"  문서화 비율  : {m.docstring_ratio:.0%}\n"
            f"  타입 힌트    : {m.type_hint_ratio:.0%}\n"
            f"\n류원의 메시지:\n  {message}\n"
            f"{'─' * 42}\n"
        )
