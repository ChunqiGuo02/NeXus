"""NeXus Pipeline Orchestrator MCP Server v3

确定性 pipeline 驱动：stage 路由 + 条件回退 + 3 轮递进审稿 +
产出验证 + subagent 并行调度 + reject-resubmit 重入 +
v3: 断点续跑 + 决策日志 + 上下文摘要 + stage 超时检测。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastmcp import FastMCP

from stages import (
    STAGES, STAGE_ORDER, get_stage, get_next_stage,
    get_rollback_stage, build_subagent_tasks,
)
from validators import validate_stage

mcp = FastMCP(
    "pipeline-orchestrator",
    instructions=(
        "NeXus Pipeline Orchestrator v3 — 管理研究 pipeline 的状态机。\n"
        "在 pipeline 模式下，agent 必须通过此 server 获取当前阶段指令、"
        "验证产出、推进/回退到下一/上一阶段。不要自行判断当前应执行哪个 skill。"
    ),
)


def _load_state(project_dir: str) -> dict:
    """加载 project_state.json，不存在则返回默认初始状态。"""
    state_path = Path(project_dir) / "project_state.json"
    default = {
        "project_name": Path(project_dir).name,
        "current_stage": "insight_interview",
        "user_level": "intermediate",  # expert/intermediate/novice
        "user_insights": {},
        "target_venue": None,
        "autopilot": False,
        "sdp_mode": "full",             # v3: full/lite/same_model
        "checkpoints_passed": [],
        "stages_completed": [],
        "rollback_history": [],
        "decision_log": [],             # v3: 用户决策记录
        "review_cycle": 0,
        "stage_start_time": None,       # v3: 当前 stage 开始时间
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        if state_path.exists():
            data = json.loads(state_path.read_text(encoding="utf-8"))
            for key, val in default.items():
                if key not in data:
                    data[key] = val
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return default


def _save_state(project_dir: str, state: dict) -> None:
    """保存 project_state.json。"""
    state_path = Path(project_dir) / "project_state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    state_path.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _resolve_skill_path(project_dir: str, skill_name: str) -> str:
    """解析 skill 的 SKILL.md 路径。优先 workspace，其次全局。"""
    workspace_root = Path(project_dir).parent
    ws_path = workspace_root / ".agents" / "skills" / skill_name / "SKILL.md"
    if ws_path.exists():
        return str(ws_path)
    global_path = Path.home() / ".gemini" / "antigravity" / "skills" / skill_name / "SKILL.md"
    if global_path.exists():
        return str(global_path)
    return f".agents/skills/{skill_name}/SKILL.md"


def _build_parallel_items(stage_name: str, project_dir: str) -> list[dict]:
    """从项目数据中提取可并行处理的条目列表。"""
    if stage_name == "survey_fetch":
        data = _load_json_safe(project_dir, "corpus_ledger.json")
        if data and isinstance(data, dict):
            return [
                {"id": e.get("id", f"paper_{i}"), "title": e.get("title", "")}
                for i, e in enumerate(data.get("entries", []))
            ]

    elif stage_name == "deep_dive":
        data = _load_json_safe(project_dir, "hypothesis_board.json")
        if data and isinstance(data, dict):
            for h in data.get("hypotheses", []):
                if h.get("selected"):
                    return [
                        {"id": art.get("paper_id", f"art_{i}"), "title": art.get("title", "")}
                        for i, art in enumerate(
                            h.get("novelty_risk", {}).get("nearest_prior_art", [])
                        )
                    ]

    elif stage_name == "experiment_run":
        return [
            {"id": "baseline", "title": "Baseline 复现"},
            {"id": "proposed", "title": "提出方法实现"},
            {"id": "evaluation", "title": "评估脚本"},
        ]

    elif stage_name == "review_round1":
        return [
            {"id": f"reviewer_{c}", "title": f"Reviewer {c} ({t})"}
            for c, t in [
                ("A", "严格型"), ("B", "创新型"), ("C", "读者型"),
                ("D", "严格型"), ("E", "创新型"), ("F", "读者型"),
            ]
        ]

    return []


def _load_json_safe(project_dir: str, rel_path: str) -> dict | None:
    """安全加载 JSON 文件。"""
    p = Path(project_dir) / rel_path
    try:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _get_selected_idea_title(project_dir: str) -> str | None:
    """获取选定 idea 的标题。"""
    data = _load_json_safe(project_dir, "hypothesis_board.json")
    if data and isinstance(data, dict):
        for h in data.get("hypotheses", []):
            if h.get("selected"):
                return h.get("title", h.get("id", "unknown"))
    return None


def _check_stage_timeout(state: dict, stage_name: str) -> dict | None:
    """检查当前 stage 是否超时。超时返回警告 dict，正常返回 None。"""
    start_time = state.get("stage_start_time")
    if not start_time or stage_name not in STAGES:
        return None
    try:
        start = datetime.fromisoformat(start_time)
        elapsed = (datetime.now(timezone.utc) - start).total_seconds() / 3600
        max_h = get_stage(stage_name).max_hours
        if elapsed > max_h:
            return {
                "status": "timeout_warning",
                "stage_name": stage_name,
                "elapsed_hours": round(elapsed, 1),
                "max_hours": max_h,
                "message": (
                    f"Stage '{stage_name}' 已运行 {elapsed:.1f}h（预期 ≤{max_h}h）。"
                    f"建议审视当前状态，避免 rabbit hole。"
                ),
                "options": ["continue", "skip", "rollback"],
            }
    except (ValueError, TypeError):
        pass
    return None


# ============================================================
# MCP Tools
# ============================================================


@mcp.tool()
def advance_pipeline(project_dir: str) -> dict:
    """获取当前 pipeline 阶段的精确执行指令。

    在 pipeline 模式下，agent 必须通过此 tool 获取当前阶段的指令，
    而不是自行判断。返回值中包含要执行的 skill、详细指令、是否需要
    subagent 并行、是否为硬卡点、回退信息、上下文摘要等。

    Args:
        project_dir: 项目目录的绝对路径

    Returns:
        包含当前阶段完整信息的字典
    """
    state = _load_state(project_dir)
    current = state.get("current_stage", "insight_interview")

    if current is None or current not in STAGES:
        return {
            "status": "completed",
            "message": "Pipeline 已全部完成。",
            "stages_completed": state.get("stages_completed", []),
        }

    # v3: 断点续跑 integrity check
    completed = state.get("stages_completed", [])
    if current != "insight_interview":
        try:
            idx = STAGE_ORDER.index(current)
            prev = STAGE_ORDER[idx - 1]
            is_rollback = bool(state.get("rollback_history"))
            is_reentry = bool(state.get("reentry_history"))
            if prev not in completed and not is_rollback and not is_reentry:
                return {
                    "status": "integrity_warning",
                    "message": (
                        f"前序 stage '{prev}' 未标记为 completed。"
                        f"可能是上次中断导致。建议先验证 '{prev}' 的产出。"
                    ),
                    "recovery_suggestion": (
                        f"调用 recover_pipeline('{project_dir}') 自动修复，"
                        f"或 complete_stage('{prev}') 手动确认。"
                    ),
                }
        except ValueError:
            pass

    # v3: 超时检测
    timeout = _check_stage_timeout(state, current)
    if timeout:
        return timeout

    # 记录 stage 开始时间（仅首次进入时）
    if not state.get("stage_start_time"):
        state["stage_start_time"] = datetime.now(timezone.utc).isoformat()
        _save_state(project_dir, state)

    stage = get_stage(current)

    # 构建 subagent 任务
    parallel_items = _build_parallel_items(current, project_dir) if stage.parallel else []
    subagent_tasks = build_subagent_tasks(stage, parallel_items)

    result = {
        "status": "active",
        "stage_name": stage.name,
        "stage_description": stage.description,
        "skill": stage.skill,
        "skill_path": _resolve_skill_path(project_dir, stage.skill),
        "instructions": stage.instructions,
        "expected_outputs": stage.expected_outputs,
        "is_hard_checkpoint": stage.is_hard_checkpoint,
        "requires_model_switch": stage.requires_model_switch,
        "autopilot": state.get("autopilot", False),
        "user_level": state.get("user_level", "intermediate"),
        "sdp_mode": state.get("sdp_mode", "full"),
        "parallel": stage.parallel,
        "next_stage": stage.next_stage,
        "stages_completed": completed,
        "progress": f"{len(completed)}/{len(STAGE_ORDER)}",
    }

    # v3: 上下文摘要 — 每次新对话自动获得足够的上下文
    result["context_summary"] = {
        "user_level": state.get("user_level"),
        "target_venue": state.get("target_venue"),
        "selected_idea": _get_selected_idea_title(project_dir),
        "recent_decisions": state.get("decision_log", [])[-3:],
        "rollback_count": len(state.get("rollback_history", [])),
        "key_constraints": state.get("user_insights", {}).get("constraints", []),
    }

    # 回退信息
    if stage.rollback_stage:
        result["rollback"] = {
            "enabled": True,
            "target_stage": stage.rollback_stage,
            "condition": stage.rollback_condition,
            "instruction": (
                f"如果条件满足（{stage.rollback_condition}），\n"
                f"调用 complete_stage('{stage.name}', result='rollback') 回退到 '{stage.rollback_stage}'。"
            ),
        }
    else:
        result["rollback"] = {"enabled": False}

    if stage.parallel and subagent_tasks:
        result["subagent_dispatch"] = {
            "enabled": True,
            "parallel_unit": stage.parallel_unit,
            "max_parallel": stage.max_parallel,
            "tasks": subagent_tasks,
            "aggregate_instructions": (
                f"每个 subagent 完成后返回结构化 JSON 结果。\n"
                f"主 agent 收集所有结果后聚合写入对应文件，\n"
                f"然后调用 complete_stage('{stage.name}') 验证并推进。"
            ),
        }
    else:
        result["subagent_dispatch"] = {"enabled": False}

    if stage.requires_model_switch:
        sdp_mode = state.get("sdp_mode", "full")
        if sdp_mode == "lite":
            result["model_switch_note"] = (
                "⚠️ SDP Lite 模式：仅保留最关键的 1 次跨模型交互。\n"
                "参见 sdp-protocol skill 的 Lite SDP 模板。"
            )
        elif sdp_mode == "same_model":
            result["model_switch_note"] = (
                "⚠️ Same-Model Adversarial 模式：用对抗 prompt 替代跨模型。\n"
                "不需要切换插件，但质量可能略降。"
            )
        else:
            result["model_switch_note"] = (
                "⚠️ 此阶段涉及 SDP 跨模型协作。\n"
                "subagent 无法切换模型，SDP handoff 仍需用户手动完成。\n"
                "参见 sdp-protocol skill 的 handoff 模板。"
            )

    return result


@mcp.tool()
def complete_stage(
    project_dir: str,
    stage_name: str,
    result: str = "pass",
) -> dict:
    """验证当前阶段产出并推进/回退 pipeline。

    在完成一个 stage 的工作后，必须调用此 tool 验证产出。
    result 参数控制推进行为：
    - "pass": 验证产出 → 推进到 next_stage
    - "rollback": 触发条件回退 → 跳转到 rollback_stage
    - "skip": 跳过验证直接推进（仅限非硬卡点）

    Args:
        project_dir: 项目目录的绝对路径
        stage_name: 要验证的阶段名称
        result: "pass" | "rollback" | "skip"

    Returns:
        验证结果 + 下一阶段指令
    """
    state = _load_state(project_dir)
    current = state.get("current_stage")

    if stage_name not in STAGES:
        return {"status": "error", "message": f"未知 stage: {stage_name}"}

    if stage_name != current:
        return {
            "status": "error",
            "message": (
                f"当前 stage 是 '{current}'，不能操作 '{stage_name}'。"
                f"请先完成当前 stage。"
            ),
        }

    stage = get_stage(stage_name)

    # --- Rollback ---
    if result == "rollback":
        rollback = get_rollback_stage(stage_name)
        if rollback is None:
            return {
                "status": "error",
                "message": f"Stage '{stage_name}' 没有定义回退目标。",
            }

        state.setdefault("rollback_history", []).append({
            "from_stage": stage_name,
            "to_stage": rollback.name,
            "reason": stage.rollback_condition,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        state["current_stage"] = rollback.name
        state["stage_start_time"] = None  # v3: 重置 stage 计时
        _save_state(project_dir, state)

        return {
            "status": "rolled_back",
            "from_stage": stage_name,
            "to_stage": rollback.name,
            "reason": stage.rollback_condition,
            "rollback_count": len(state["rollback_history"]),
            "next": advance_pipeline(project_dir),
        }

    # --- Normal validation ---
    if result != "skip":
        missing = validate_stage(stage_name, project_dir)
        if missing:
            return {
                "status": "blocked",
                "stage_name": stage_name,
                "missing": missing,
                "message": f"Stage '{stage_name}' 产出不完整，请补全后重试。",
            }

        # v4: Compliance check — 防 LLM 跳步
        from compliance_checker import check_compliance

        compliance = check_compliance(stage_name, project_dir)
        if not compliance["compliant"]:
            return {
                "status": "compliance_failed",
                "stage_name": stage_name,
                "compliance": compliance,
                "message": (
                    f"Stage '{stage_name}' 合规检查未通过。"
                    f"缺少: {[f['rule'] for f in compliance['failed']]}"
                ),
            }

    # --- Advance ---
    completed = state.get("stages_completed", [])
    if stage_name not in completed:
        completed.append(stage_name)
    state["stages_completed"] = completed

    if stage.is_hard_checkpoint:
        passed = state.get("checkpoints_passed", [])
        if stage_name not in passed:
            passed.append(stage_name)
        state["checkpoints_passed"] = passed

    next_stage = get_next_stage(stage_name)
    if next_stage:
        state["current_stage"] = next_stage.name
    else:
        state["current_stage"] = None

    state["stage_start_time"] = None  # v3: 重置 stage 计时
    _save_state(project_dir, state)

    resp = {
        "status": "advanced",
        "completed_stage": stage_name,
        "stages_completed": completed,
        "progress": f"{len(completed)}/{len(STAGE_ORDER)}",
    }

    if next_stage:
        resp["next"] = advance_pipeline(project_dir)
    else:
        resp["next"] = {
            "status": "completed",
            "message": "🎉 Pipeline 全部完成！论文已就绪。触发 evolution-memory 蒸馏。",
        }

    return resp


@mcp.tool()
def reenter_pipeline(
    project_dir: str,
    reentry_stage: str,
    reviewer_feedback_path: str = "",
) -> dict:
    """从任意 stage 重新进入 pipeline（用于真实投稿被拒后重入）。

    支持携带真实 reviewer comments 重入 pipeline。系统会将
    reviewer_feedback_path 写入 project_state.json，后续 stage
    可以读取并据此调整行为。

    Args:
        project_dir: 项目目录的绝对路径
        reentry_stage: 要重入的阶段名称
        reviewer_feedback_path: 可选，reviewer comments 文件路径

    Returns:
        重入后的阶段指令
    """
    if reentry_stage not in STAGES:
        return {"status": "error", "message": f"未知 stage: {reentry_stage}"}

    state = _load_state(project_dir)
    state["current_stage"] = reentry_stage
    state["stage_start_time"] = None  # v3: 重置计时

    if reviewer_feedback_path:
        state.setdefault("reentry_history", []).append({
            "stage": reentry_stage,
            "reviewer_feedback": reviewer_feedback_path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    _save_state(project_dir, state)

    return {
        "status": "reentered",
        "reentry_stage": reentry_stage,
        "reviewer_feedback": reviewer_feedback_path or None,
        "next": advance_pipeline(project_dir),
    }


@mcp.tool()
def recover_pipeline(project_dir: str) -> dict:
    """从中断状态恢复 pipeline。扫描全部产出文件，推断实际进度。

    当 pipeline 因网络断开、context window 用尽等原因中断时，
    调用此 tool 可以自动检测哪些 stage 的产出已完整，修正
    stages_completed 列表，并定位到正确的 current_stage。

    Args:
        project_dir: 项目目录的绝对路径

    Returns:
        恢复状态报告
    """
    state = _load_state(project_dir)
    actual_completed = []

    for name in STAGE_ORDER:
        missing = validate_stage(name, project_dir)
        if not missing:
            actual_completed.append(name)
        else:
            break  # 首个不完整的 stage

    state["stages_completed"] = actual_completed

    if actual_completed:
        last_done = actual_completed[-1]
        next_s = get_next_stage(last_done)
        state["current_stage"] = next_s.name if next_s else None
    else:
        state["current_stage"] = "insight_interview"

    state["stage_start_time"] = None  # 重置计时
    _save_state(project_dir, state)

    return {
        "status": "recovered",
        "actual_completed": actual_completed,
        "current_stage": state["current_stage"],
        "progress": f"{len(actual_completed)}/{len(STAGE_ORDER)}",
        "message": (
            f"已恢复。检测到 {len(actual_completed)} 个已完成的 stage。"
            f"当前 stage: {state['current_stage']}"
        ),
    }


@mcp.tool()
def log_decision(
    project_dir: str,
    stage: str,
    decision: str,
    rationale: str = "",
    alternatives: list[str] | None = None,
) -> dict:
    """记录用户在硬卡点的决策及理由，供后续 stage 参考。

    在每个硬卡点（Idea Approval、Novelty Risk Gate 等）用户做出
    决策后，调用此 tool 记录决策和理由。后续 stage 的 agent 可以
    通过 advance_pipeline 的 context_summary 读取这些记录。

    Args:
        project_dir: 项目目录的绝对路径
        stage: 做出决策的阶段名称
        decision: 决策内容
        rationale: 决策理由
        alternatives: 考虑过的其他选项

    Returns:
        记录结果
    """
    state = _load_state(project_dir)
    state.setdefault("decision_log", []).append({
        "stage": stage,
        "decision": decision,
        "rationale": rationale,
        "alternatives_considered": alternatives or [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    _save_state(project_dir, state)

    return {
        "status": "logged",
        "total_decisions": len(state["decision_log"]),
        "message": f"已记录 stage '{stage}' 的决策。",
    }


@mcp.tool()
def get_pipeline_status(project_dir: str) -> dict:
    """查看 pipeline 全局状态。

    返回所有阶段的完成情况、当前进度、autopilot 状态、
    回退历史、决策日志等。

    Args:
        project_dir: 项目目录的绝对路径

    Returns:
        pipeline 全局状态概览
    """
    state = _load_state(project_dir)
    completed = set(state.get("stages_completed", []))
    current = state.get("current_stage")

    stages_status = []
    for name in STAGE_ORDER:
        stage = get_stage(name)
        if name in completed:
            status = "✅ completed"
        elif name == current:
            status = "🔄 in_progress"
        else:
            status = "⬜ pending"

        stages_status.append({
            "name": name,
            "status": status,
            "description": stage.description,
            "is_hard_checkpoint": stage.is_hard_checkpoint,
            "parallel": stage.parallel,
            "has_rollback": stage.rollback_stage is not None,
            "max_hours": stage.max_hours,
        })

    return {
        "project_name": state.get("project_name", "unknown"),
        "current_stage": current,
        "user_level": state.get("user_level", "intermediate"),
        "target_venue": state.get("target_venue"),
        "autopilot": state.get("autopilot", False),
        "sdp_mode": state.get("sdp_mode", "full"),
        "progress": f"{len(completed)}/{len(STAGE_ORDER)}",
        "checkpoints_passed": state.get("checkpoints_passed", []),
        "rollback_history": state.get("rollback_history", []),
        "decision_log": state.get("decision_log", []),
        "stages": stages_status,
        "created_at": state.get("created_at"),
        "updated_at": state.get("updated_at"),
    }

@mcp.tool()
def check_stage_compliance(project_dir: str, stage_name: str) -> dict:
    """检查指定 stage 是否通过合规检查（防 LLM 跳步）。

    独立于 complete_stage 使用，可在 stage 执行过程中提前检查。

    Args:
        project_dir: 项目目录的绝对路径
        stage_name: 要检查的阶段名称

    Returns:
        合规检查结果
    """
    from compliance_checker import check_compliance

    return check_compliance(stage_name, project_dir)


@mcp.tool()
def generate_sdp_handoff_file(
    project_dir: str,
    task_type: str,
    reviewer_count: int = 3,
) -> dict:
    """生成 SDP 交接文件用于跨模型/跨插件任务。

    在需要切换到 Codex/GPT 之前调用。生成自包含的指令文件
    dialogue/sdp_handoff.json，GPT 只需读取此文件即可执行任务。

    支持的 task_type: review, red_team, arch_review, polish

    Args:
        project_dir: 项目目录的绝对路径
        task_type: 任务类型
        reviewer_count: 审稿人数量（仅 review 类型）

    Returns:
        生成的 handoff 内容摘要
    """
    from sdp_handoff_generator import generate_handoff

    handoff = generate_handoff(task_type, project_dir, reviewer_count)
    return {
        "status": "generated",
        "task_type": task_type,
        "output_path": "dialogue/sdp_handoff.json",
        "briefing_length": len(
            handoff.get("domain_context", "")
        ),
        "reviewer_count": len(handoff.get("reviewers", [])),
        "message": (
            "已生成 SDP handoff 文件。"
            "请切到 Codex，让 GPT 读取 dialogue/sdp_handoff.json。"
        ),
    }


if __name__ == "__main__":
    mcp.run()
