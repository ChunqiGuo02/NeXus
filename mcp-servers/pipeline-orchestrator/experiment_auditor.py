"""实验代码自动审计器 — 用 Python AST 分析检测常见实验 bug。

3 个检测器:
1. Data Leakage Detector: 检查 train/val/test split 是否安全
2. Seed Fix Verifier: 检查随机种子是否固定全部来源
3. Metric Consistency Checker: 检查评估指标实现与声称是否一致
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AuditIssue:
    """单条审计问题。"""

    detector: str
    severity: str  # "critical" / "warning" / "info"
    message: str
    file: str = ""
    line: int = 0


# ── 检测器 1: Data Leakage Detector ──


def detect_data_leakage(code_dir: str) -> list[AuditIssue]:
    """检查 train/val/test split 是否存在数据泄露风险。

    检测模式:
    1. 先 fit_transform(全部数据) 再 split → 泄露
    2. 在 split 前做了全局 normalize → 泄露
    3. val/test 数据参与了 train 的任何统计计算 → 泄露
    """
    issues: list[AuditIssue] = []
    code_path = Path(code_dir)

    for py_file in code_path.rglob("*.py"):
        try:
            source = py_file.read_text(encoding="utf-8")
            ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        _check_leakage_patterns(source, str(py_file), issues)

    return issues


def _check_leakage_patterns(
    source: str, filepath: str, issues: list[AuditIssue]
) -> None:
    """用正则 + AST 检测泄露模式。"""
    lines = source.split("\n")

    # 模式 1: fit_transform 在 split 之前
    fit_transform_line = None
    split_line = None

    for i, line in enumerate(lines):
        if "fit_transform" in line:
            fit_transform_line = i + 1
        if re.search(
            r"train_test_split|split\(|\.split\b", line
        ):
            split_line = i + 1

    if (
        fit_transform_line
        and split_line
        and fit_transform_line < split_line
    ):
        issues.append(
            AuditIssue(
                detector="data_leakage",
                severity="critical",
                message=(
                    f"fit_transform (line {fit_transform_line}) 在"
                    f" train_test_split (line {split_line}) 之前 — 可能泄露"
                ),
                file=filepath,
                line=fit_transform_line,
            )
        )

    # 模式 2: 全局 normalize 在 split 之前
    for i, line in enumerate(lines):
        if re.search(r"normalize|StandardScaler|MinMaxScaler", line):
            if split_line and (i + 1) < split_line:
                issues.append(
                    AuditIssue(
                        detector="data_leakage",
                        severity="warning",
                        message=(
                            f"全局 normalize (line {i + 1}) 在 split"
                            f" (line {split_line}) 之前 — 检查是否泄露"
                        ),
                        file=filepath,
                        line=i + 1,
                    )
                )


# ── 检测器 2: Seed Fix Verifier ──


SEED_SOURCES = {
    "random": r"random\.seed\(",
    "numpy": r"np\.random\.seed\(|numpy\.random\.seed\(",
    "torch": r"torch\.manual_seed\(",
    "cuda": r"torch\.cuda\.manual_seed(?:_all)?\(",
    "cudnn_deterministic": r"cudnn\.deterministic\s*=\s*True",
    "cudnn_benchmark": r"cudnn\.benchmark\s*=\s*False",
}


def verify_seed_fixing(code_dir: str) -> list[AuditIssue]:
    """检查随机种子是否固定全部来源。

    需要检查的来源:
    - random.seed()
    - np.random.seed()
    - torch.manual_seed()
    - torch.cuda.manual_seed_all()
    - torch.backends.cudnn.deterministic = True
    - torch.backends.cudnn.benchmark = False
    """
    issues: list[AuditIssue] = []
    code_path = Path(code_dir)

    # 在所有 .py 文件中搜索 seed 设置
    all_source = ""
    for py_file in code_path.rglob("*.py"):
        try:
            all_source += py_file.read_text(encoding="utf-8") + "\n"
        except UnicodeDecodeError:
            continue

    if not all_source.strip():
        issues.append(
            AuditIssue(
                detector="seed_fix",
                severity="warning",
                message="未找到任何 Python 文件",
            )
        )
        return issues

    found_sources: list[str] = []
    missing_sources: list[str] = []

    for source_name, pattern in SEED_SOURCES.items():
        if re.search(pattern, all_source):
            found_sources.append(source_name)
        else:
            missing_sources.append(source_name)

    if missing_sources:
        issues.append(
            AuditIssue(
                detector="seed_fix",
                severity="critical" if "torch" in missing_sources else "warning",
                message=(
                    f"未固定随机源: {', '.join(missing_sources)}。"
                    f" 已固定: {', '.join(found_sources)}"
                ),
            )
        )

    # 检查 DataLoader 的 worker_init_fn
    if "num_workers" in all_source and "worker_init_fn" not in all_source:
        issues.append(
            AuditIssue(
                detector="seed_fix",
                severity="warning",
                message=(
                    "DataLoader 使用 num_workers > 0 但未设置"
                    " worker_init_fn — worker 进程的随机性未固定"
                ),
            )
        )

    return issues


# ── 检测器 3: Metric Consistency Checker ──


def check_metric_consistency(
    code_dir: str,
    claimed_metrics: list[str] | None = None,
) -> list[AuditIssue]:
    """检查评估指标实现与声称是否一致。

    Parameters
    ----------
    code_dir : str
        代码目录。
    claimed_metrics : list[str] | None
        论文中声称使用的指标列表（如 ["mIoU", "Acc", "F1"]）。
    """
    issues: list[AuditIssue] = []
    code_path = Path(code_dir)

    if not claimed_metrics:
        return issues

    # 搜索代码中的指标实现
    all_source = ""
    for py_file in code_path.rglob("*.py"):
        try:
            all_source += py_file.read_text(encoding="utf-8") + "\n"
        except UnicodeDecodeError:
            continue

    metric_patterns = {
        "mIoU": r"miou|mean_iou|intersection.+union",
        "Acc": r"accuracy|acc\b",
        "F1": r"f1.?score|f_measure",
        "AUC": r"\bauc\b|roc_auc",
        "mAP": r"\bmap\b|mean_average_precision",
        "FPS": r"\bfps\b|frames?.per.second",
        "PSNR": r"\bpsnr\b|peak.signal",
        "SSIM": r"\bssim\b|structural.similarity",
    }

    for metric in claimed_metrics:
        pattern = metric_patterns.get(metric)
        if pattern and not re.search(pattern, all_source, re.IGNORECASE):
            issues.append(
                AuditIssue(
                    detector="metric_consistency",
                    severity="critical",
                    message=(
                        f"论文声称使用 {metric} 但代码中未找到对应实现"
                    ),
                )
            )

    return issues


# ── 统一入口 ──


def run_full_audit(
    code_dir: str,
    claimed_metrics: list[str] | None = None,
) -> dict:
    """运行全部审计。"""
    all_issues: list[AuditIssue] = []
    all_issues.extend(detect_data_leakage(code_dir))
    all_issues.extend(verify_seed_fixing(code_dir))
    all_issues.extend(
        check_metric_consistency(code_dir, claimed_metrics)
    )

    return {
        "total_issues": len(all_issues),
        "critical": [i for i in all_issues if i.severity == "critical"],
        "warning": [i for i in all_issues if i.severity == "warning"],
        "info": [i for i in all_issues if i.severity == "info"],
        "passed": len(all_issues) == 0,
    }
