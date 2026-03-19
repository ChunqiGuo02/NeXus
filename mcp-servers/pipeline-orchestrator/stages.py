"""Pipeline stage 定义 — 14 个 stage 的状态机（含条件回退 + 3 轮审稿）。

每个 stage 定义了：
- 对应的 skill 和 SKILL.md 路径
- 期望产出文件
- 是否硬卡点
- 是否支持 subagent 并行
- 下一阶段 / 回退阶段
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Stage:
    """Pipeline 中一个阶段的完整定义。"""

    name: str
    skill: str
    description: str
    expected_outputs: list[str]
    is_hard_checkpoint: bool = False
    parallel: bool = False
    parallel_unit: str | None = None  # "paper" / "reviewer" / "module"
    max_parallel: int = 1
    requires_model_switch: bool = False
    next_stage: str | None = None
    instructions: str = ""
    # v2: 条件回退
    rollback_stage: str | None = None
    rollback_condition: str = ""
    # v2: 标记子阶段（3 轮审稿 sub-stages）
    is_sub_stage: bool = False
    parent_stage: str | None = None
    # v3: 全局超时检测（小时）
    max_hours: float = 24.0


# ---------- 14 个 Pipeline Stages ---------- #

STAGES: dict[str, Stage] = {}


def _register(stage: Stage) -> Stage:
    STAGES[stage.name] = stage
    return stage


# === Stage 0: Insight Interview（v2 新增）===
_register(Stage(
    name="insight_interview",
    skill="omni-orchestrator",
    description="用户水平评估 + 领域知识注入 / Domain Onboarding",
    expected_outputs=[
        "project_state.json",  # 包含 user_level + user_insights
    ],
    next_stage="survey_search",
    max_hours=2.0,
    instructions=(
        "Pipeline 启动阶段。\n"
        "1. 评估用户水平（Expert/Intermediate/Novice）\n"
        "2. Expert: 提取用户领域直觉、初步想法、必读论文、已知的坑\n"
        "3. Novice: Domain Onboarding — 自动概览领域 landscape\n"
        "4. 记录目标 venue\n"
        "5. 将全部信息写入 project_state.json 的 user_insights 字段"
    ),
))

# === Stage 1 ===
_register(Stage(
    name="survey_search",
    skill="literature-survey",
    description="文献搜索 + Scope Freeze + Corpus Freeze",
    expected_outputs=[
        "corpus_ledger.json",
    ],
    is_hard_checkpoint=True,
    next_stage="survey_fetch",
    max_hours=4.0,
    instructions=(
        "执行 literature-survey skill 的 Step 1（搜索）。\n"
        "1. 与用户确认搜索范围（Scope Freeze 卡点）\n"
        "2. 执行搜索，展示文献矩阵\n"
        "3. 用户确认后（Corpus Freeze 卡点）进入下一阶段\n"
        "4. 将结果写入 corpus_ledger.json"
    ),
))

# === Stage 2 ===
_register(Stage(
    name="survey_fetch",
    skill="literature-survey",
    description="论文获取 + 引用验证 + 证据提取（可并行）",
    expected_outputs=[
        "evidence_graph.json",
        "artifacts/survey.md",
    ],
    parallel=True,
    parallel_unit="paper",
    max_parallel=5,
    next_stage="evidence_audit",
    max_hours=8.0,
    instructions=(
        "执行 literature-survey skill 的 Step 2-5。\n"
        "\n"
        "⚡ Subagent 并行调度（推荐）:\n"
        "  每篇论文分配一个独立 subagent，最多 5 路并行。\n"
        "  每个 subagent 的输入: corpus_ledger.json 中的单条论文信息\n"
        "  每个 subagent 的输出: papers/{paper_id}/claims.json + paper.md\n"
        "  subagent 之间不共享 context → 避免 claim 提取相互干扰\n"
        "  全部 subagent 完成后，主 agent 合并:\n"
        "    - 合并 claims → evidence_graph.json\n"
        "    - 生成 artifacts/survey.md 综述\n"
        "    - 触发 pattern-promoter（如 claims 够多）\n"
        "\n"
        "单 subagent 任务:\n"
        "  1. fetch_paper() 获取全文\n"
        "  2. citation-verifier 验证引用\n"
        "  3. claim-extractor 提取证据\n"
        "  4. 写回 papers/{paper_id}/ 目录"
    ),
))

# === Stage 3 ===
_register(Stage(
    name="evidence_audit",
    skill="evidence-auditor",
    description="证据质量审计 + Research Frontier Check（QG1）",
    expected_outputs=[
        "evidence_audit.md",
    ],
    next_stage="ideation",
    max_hours=4.0,
    instructions=(
        "执行 evidence-auditor skill 全流程。\n"
        "1. 抽样审计 evidence_graph.json 中的 claims\n"
        "2. 回溯验证每条 claim 与原文的一致性\n"
        "3. 输出 evidence_audit.md 审计报告\n"
        "4. 修正 inaccurate claims"
    ),
))

# === Stage 4 ===
_register(Stage(
    name="ideation",
    skill="idea-brainstorm",
    description="ToT 构思 + Elo 锦标赛 + SDP 红队攻击 + Idea Approval",
    expected_outputs=[
        "hypothesis_board.json",
        "dialogue/tot_survivors.md",
        "dialogue/ideas_v1.md",
    ],
    is_hard_checkpoint=True,
    requires_model_switch=True,
    next_stage="deep_dive",
    max_hours=6.0,
    instructions=(
        "执行 idea-brainstorm skill 全流程。\n"
        "Novice 模式: 先执行 Phase 0 Direction Recommendation。\n"
        "1. Research Frontier Check（QG1）\n"
        "2. Gap Analysis + 研究图谱\n"
        "3. ToT 三层探索 + Portfolio Ideation（3-4-3）\n"
        "   - 含 Assumption-Breaking + Failure Mining 策略\n"
        "4. Elo 锦标赛排名（Flash 淘汰 + Pro 决赛）\n"
        "5. SDP 红队攻击（需切换到 Codex/GPT 5.4）\n"
        "6. ⛔ Idea Approval 硬卡点 — 等待用户选择"
    ),
))

# === Stage 5 ===
_register(Stage(
    name="deep_dive",
    skill="deep-dive",
    description="精读选定 idea 的 nearest prior art（可并行）+ 2 hop citation expansion",
    expected_outputs=[],
    parallel=True,
    parallel_unit="paper",
    max_parallel=3,
    next_stage="novelty_check",
    instructions=(
        "执行 deep-dive skill。\n"
        "\n"
        "⚡ Subagent 并行调度（推荐）:\n"
        "  每篇精读论文分配一个独立 subagent，最多 3 路并行。\n"
        "  每个 subagent 的输入: 论文 ID + hypothesis_board.json 中选定的 idea\n"
        "  每个 subagent 的输出: artifacts/deep_dive_{paper_id}.md\n"
        "  subagent 之间不共享 context → 独立精读，不互相影响分析结论\n"
        "  全部 subagent 完成后，主 agent 汇总关键发现到 evidence_graph.json\n"
        "\n"
        "单 subagent 任务:\n"
        "  1. 获取论文全文（如未解析）\n"
        "  2. 按精读模板逐节分析\n"
        "  3. 2 hop citation expansion（被引 + 引用的引用）\n"
        "  4. GitHub 代码分析（如有开源 baseline）\n"
        "  5. 提取 Limitation/Future Work 作为后续 ideation 输入\n"
        "  6. 输出 artifacts/deep_dive_{paper_id}.md"
    ),
))

# === Stage 6 ===
_register(Stage(
    name="novelty_check",
    skill="novelty-checker",
    description="新颖性风险评估 + Novelty Risk Gate",
    expected_outputs=[
        "hypothesis_board.json",
    ],
    is_hard_checkpoint=True,
    next_stage="experiment_design",
    rollback_stage="ideation",
    rollback_condition="overall_risk 为 high 或 unknown 且用户选择换 idea",
    instructions=(
        "执行 novelty-checker skill。\n"
        "1. 多轮 Prior Art 搜索（直接 + 组合 + 反向 + 引用链）\n"
        "2. 碰撞风险分析（high/medium/low/unknown）\n"
        "3. 差异化分析\n"
        "4. ⛔ Novelty Risk Gate — overall_risk 为 unknown/high 时：\n"
        "   - 可选择继续（接受风险）\n"
        "   - 或 rollback 到 ideation 换 idea"
    ),
))

# === Stage 7 ===
_register(Stage(
    name="experiment_design",
    skill="experiment-runner",
    description="项目初始化 + SDP 架构审查 + QG3 实验设计 + Baseline 时效性检查",
    expected_outputs=[
        "experimental_design.md",
    ],
    is_hard_checkpoint=True,
    requires_model_switch=True,
    next_stage="pilot_experiment",
    instructions=(
        "执行 experiment-runner skill 的 Step 1-2.0。\n"
        "1. 项目初始化（模板选择 + 数据集准备 + Baseline 获取）\n"
        "2. Baseline 时效性检查（发表超过 2 年需补充新 baseline）\n"
        "3. Ablation 计划自动生成（每个 novel component 一个变体）\n"
        "4. 环境配置（本地/远程）\n"
        "5. SDP 架构审查（Opus → GPT 5.4）\n"
        "6. ⛔ Architecture Approval 硬卡点\n"
        "7. 实验设计计划 + Core Novelty Invariant\n"
        "8. ⛔ QG3 Experimental Design 硬卡点"
    ),
))

# === Stage 8: Pilot Experiment（v2 新增）===
_register(Stage(
    name="pilot_experiment",
    skill="experiment-runner",
    description="10% 规模预验证 — 小数据/少 epoch 验证核心方法可行性",
    expected_outputs=[
        "artifacts/pilot_results.json",
    ],
    is_hard_checkpoint=True,
    next_stage="experiment_run",
    rollback_stage="ideation",
    rollback_condition="pilot 结果完全不支持核心假设",
    instructions=(
        "在 full experiment 前先做 pilot 验证。\n"
        "1. 用 10% 数据或 toy dataset 运行核心方法\n"
        "2. 检查：方法能否跑通？\n"
        "3. 检查：在 toy 上是否有预期趋势？\n"
        "4. ⛔ Pilot Gate：\n"
        "   - Pass: 有正向趋势 → 继续到 full experiment_run\n"
        "   - Fail: 完全不 work → rollback 到 ideation\n"
        "   - Partial: 部分 work → 可选 REFINE（调整后重试 pilot）\n"
        "5. 记录 pilot 结果到 artifacts/pilot_results.json"
    ),
    max_hours=8.0,
))

# === Stage 9 ===
_register(Stage(
    name="experiment_run",
    skill="experiment-runner",
    description="全规模代码生成 + 训练 + Code Audit + 结果分析 + 统计严谨性检查 + QG4",
    expected_outputs=[
        "artifacts/experiment_report.md",
        "artifacts/experiment_results.json",
    ],
    parallel=True,
    parallel_unit="module",
    max_parallel=3,
    next_stage="venue_fit_check",
    rollback_stage="experiment_design",
    rollback_condition="实验结果不支持核心假设且无法通过调参改善",
    instructions=(
        "执行 experiment-runner skill 的 Step 2-5。\n"
        "1. 代码生成（data.py → model.py → train.py → evaluate.py）\n"
        "2. 训练与调试（含 Attempt Budget + 3-Strike 熔断）\n"
        "3. 多 seed 运行（≥3 seeds）+ 报告 mean ± std\n"
        "4. Ablation 实验全部执行（对应 experiment_design 中每个 novel component）\n"
        "5. 结果分析 + 图表生成\n"
        "6. ⚠️ Experiment Code Audit（v2.1 新增）：\n"
        "   a. data loader 的 train/val/test split 是否有数据泄露？\n"
        "   b. 评估指标实现是否与论文声称的一致？\n"
        "   c. random seed 是否 fix 了所有随机性（numpy+torch+cuda+dataloader）？\n"
        "   d. baseline 复现代码是否与原论文描述一致？\n"
        "   e. 记录审查结果到 artifacts/code_audit.md\n"
        "7. Experiment Story Bridge → experiment_story.md\n"
        "8. QG4 + 统计严谨性检查（seeds ≥3, error bars, significance test）\n"
        "9. 如果结果不支持假设 → 可 rollback 到 experiment_design (REFINE) 或 ideation (PIVOT)"
    ),
    max_hours=72.0,
))

# === Stage 10: Venue Fit Check（v2 新增）===
_register(Stage(
    name="venue_fit_check",
    skill="omni-orchestrator",
    description="Venue 匹配度 + Positioning Strategy + Reviewer 预测 + Significance Argument",
    expected_outputs=[
        "artifacts/venue_fit_report.md",
    ],
    is_hard_checkpoint=True,
    next_stage="writing",
    instructions=(
        "在写作前验证 venue 匹配度并制定定位策略。\n"
        "1. 加载目标 venue 的 Venue Playbook\n"
        "2. 评估 contribution 类型是否匹配 venue 偏好\n"
        "3. ⚠️ Positioning Strategy（v2.2 新增）：\n"
        "   a. 选择定位：method paper / empirical study / benchmark / theory / application?\n"
        "   b. 确定 Framing：强调 novelty / practical impact / theoretical depth?\n"
        "   c. 选择参照系：Related Work 应该和哪类工作做对比？\n"
        "   d. Significance Argument：这个问题影响多少人？解决后领域会怎么变？\n"
        "4. 预测可能的 reviewer profile\n"
        "5. 生成 top-10 预期审稿问题 + 预备回答\n"
        "6. ⛔ Venue Fit Gate：\n"
        "   - 如明显不匹配 → 建议换 venue 或调整 framing\n"
        "   - 输出 artifacts/venue_fit_report.md（含 positioning strategy）"
    ),
))

# === Stage 11 ===
_register(Stage(
    name="writing",
    skill="paper-writing",
    description="Persuasion-Driven 写作 + Weakness Preemption + SDP + Figure 1 Gate + Rebuttal Appendix",
    expected_outputs=[
        "artifacts/draft_final.tex",
        "artifacts/story_skeleton.json",
    ],
    requires_model_switch=True,
    next_stage="review_round1",
    instructions=(
        "执行 paper-writing skill 的 Step 1-5（含 v2.2 新增说服力层）。\n"
        "1. Story Skeleton 大纲 + One-Sentence Summary Test（v2.2）\n"
        "   → 必须用一句话概括论文核心贡献，如不能则论文缺焦点\n"
        "2. Weakness Preemption Plan（v2.2）\n"
        "   → 列出 top-5 审稿人可能攻击点，为每个攻击点准备预防性论述\n"
        "3. Exemplar Analysis（找 3 篇目标 venue 的 oral/spotlight 论文作为风格参考）\n"
        "4. SDP 双模型辩论起草（Gemini → Opus → GPT 5.4 润色）\n"
        "   → 写作时要求 Narrative Momentum（v2.2）：每段结尾自然引出下一段动机\n"
        "5. Figure 1 Quality Gate（v2.2）\n"
        "   → Figure 1 必须自解释核心 idea，不需读正文即可理解\n"
        "6. 去 AI 味\n"
        "7. QG5 出版标准检查\n"
        "8. Claims↔Paper 交叉验证\n"
        "9. Fresh Eyes Test\n"
        "10. Rebuttal-Ready Appendix（v2.2）\n"
        "    → 每个潜在弱点在 appendix 预备补充实验/解释\n"
        "11. LaTeX 编译\n"
        "12. Reproducibility Checklist 自动生成"
    ),
))

# === Stage 12a: Review Round 1（v2: 拆分为 3 轮）===
_register(Stage(
    name="review_round1",
    skill="multi-reviewer",
    description="第 1 轮全面审稿：Domain-Calibrated SDP 双模型 6 审稿人",
    expected_outputs=[
        "artifacts/review_round1.json",
    ],
    parallel=True,
    parallel_unit="reviewer",
    max_parallel=6,
    requires_model_switch=True,
    next_stage="revise_round1",
    is_sub_stage=True,
    parent_stage="review",
    max_hours=8.0,
    instructions=(
        "执行 multi-reviewer skill 全流程（第 1 轮）。\n"
        "\n"
        "⚡ Subagent 并行调度（必须）:\n"
        "  审稿必须使用 subagent 以保证 Context Isolation。\n"
        "  串行生成多个 reviewer 会导致意见趋同（后面的 reviewer 受前面影响）。\n"
        "\n"
        "  Batch 1 (Antigravity/Gemini 侧): 3 个 subagent 并行\n"
        "    每个 subagent 输入: draft_final.tex + domain_taste_profile.json + 单个 persona\n"
        "    每个 subagent 输出: dialogue/review_{reviewer_id}.json\n"
        "    subagent 之间完全隔离 → R-A/B/C 独立审稿\n"
        "\n"
        "  切换到 Codex (用户手动切换):\n"
        "    生成 dialogue/sdp_handoff.json (含完整 domain_taste + 3 个 persona)\n"
        "    → sdp_handoff_generator.generate_handoff('review', project_dir, 3)\n"
        "\n"
        "  Batch 2 (Codex/GPT 侧): \n"
        "    - Codex 桌面端: 3 个 subagent 并行 R-D/E/F\n"
        "    - Codex VSCode 插件: 串行 R-D/E/F (prompt 强制独立)\n"
        "\n"
        "  主 agent 合并全部 6 份审稿 → artifacts/review_round1.json\n"
        "\n"
        "0. ⚠️ Domain-Calibrated Reviewer（v2.1 新增）：\n"
        "   a. 从 domain_taste_profile.json 生成 reviewer persona\n"
        "   b. 每个 persona 包含 ≥3 条 domain taste 检查项\n"
        "   c. 确保至少 1 个 reviewer 是'该子领域 senior researcher'角色\n"
        "1. 拒稿信预演（主 agent 自我攻击，在 subagent 之前）\n"
        "2. 分发 subagent 执行独立审稿\n"
        "3. 合并结果 + Score Distribution 检查"
    ),
))

# === Stage 12b: Revise Round 1 ===
_register(Stage(
    name="revise_round1",
    skill="paper-writing",
    description="第 1 轮审后修改",
    expected_outputs=[
        "artifacts/draft_final.tex",
    ],
    next_stage="review_round2",
    is_sub_stage=True,
    parent_stage="review",
    instructions=(
        "根据 review_round1.json 修改论文。\n"
        "1. 按 must_fix 列表逐项修改\n"
        "2. 用 \\blue{} 标注修改\n"
        "3. 更新 draft_final.tex"
    ),
))

# === Stage 12c: Review Round 2 ===
_register(Stage(
    name="review_round2",
    skill="multi-reviewer",
    description="第 2 轮复审：修改部分 + 对抗型 reviewer 找遗漏",
    expected_outputs=[
        "artifacts/review_round2.json",
    ],
    requires_model_switch=True,
    next_stage="revise_round2",
    is_sub_stage=True,
    parent_stage="review",
    instructions=(
        "执行第 2 轮审稿。\n"
        "1. 只审查 Round 1 修改过的部分\n"
        "2. 新增 1 个对抗型 reviewer（专门找 Round 1 遗漏的弱点）\n"
        "3. 生成 artifacts/review_round2.json"
    ),
))

# === Stage 12d: Revise Round 2 ===
_register(Stage(
    name="revise_round2",
    skill="paper-writing",
    description="第 2 轮审后修改",
    expected_outputs=[
        "artifacts/draft_final.tex",
    ],
    next_stage="review_round3_meta",
    is_sub_stage=True,
    parent_stage="review",
    instructions=(
        "根据 review_round2.json 修改论文。\n"
        "1. 处理 Round 2 发现的遗漏问题\n"
        "2. 更新 draft_final.tex"
    ),
))

# === Stage 12e: Meta-Review（AC 终审）===
_register(Stage(
    name="review_round3_meta",
    skill="multi-reviewer",
    description="第 3 轮 Meta-Review：模拟 AC 做 accept/reject 决策",
    expected_outputs=[
        "artifacts/meta_review.json",
    ],
    is_hard_checkpoint=True,
    requires_model_switch=True,
    next_stage="final_revise",
    rollback_stage="experiment_run",
    rollback_condition="Meta-Review 判定 reject 且原因是实验不充分",
    is_sub_stage=True,
    parent_stage="review",
    instructions=(
        "执行 Meta-Review 终审。\n"
        "1. 模拟 Area Chair 视角\n"
        "2. 综合 Round 1+2 所有 reviewer 意见\n"
        "3. 做最终 accept/reject 决策\n"
        "4. ⛔ Meta-Review Gate：\n"
        "   - Accept → 进入 final_revise 做最终打磨\n"
        "   - Reject（实验不足）→ rollback 到 experiment_run 补实验\n"
        "   - Reject（idea 问题）→ rollback 到 ideation\n"
        "   - Reject（venue 不匹配）→ 建议换 venue 后重投"
    ),
))

# === Stage 13: Final Revise ===
_register(Stage(
    name="final_revise",
    skill="paper-writing",
    description="最终打磨 + Final Novelty Sweep + Compliance + 引用一致性 + Evolution Memory",
    expected_outputs=[
        "artifacts/draft_final.tex",
        "artifacts/reproducibility_checklist.md",
    ],
    next_stage=None,  # Pipeline 终点
    instructions=(
        "最终打磨阶段。\n"
        "1. ⚠️ Final Novelty Sweep（v2.1 新增）：\n"
        "   a. 在 arXiv/Semantic Scholar 搜索最近 3 个月的同 topic 论文\n"
        "   b. 如发现 concurrent work → 在 Related Work 中引用并说明差异\n"
        "   c. 如发现高度重叠 → ⛔ 暂停投稿，评估是否需要调整贡献声明\n"
        "2. Pre-submission Compliance Scan（匿名化、页数、必要章节）\n"
        "3. 最终引用一致性扫描（bib ↔ \\cite{} 双向检查）\n"
        "4. Reproducibility Checklist 最终审核\n"
        "5. LaTeX 最终编译\n"
        "6. 触发 evolution-memory 蒸馏"
    ),
))


# ---------- Stage 顺序列表 ---------- #

STAGE_ORDER: list[str] = [
    "insight_interview",
    "survey_search",
    "survey_fetch",
    "evidence_audit",
    "ideation",
    "deep_dive",
    "novelty_check",
    "experiment_design",
    "pilot_experiment",
    "experiment_run",
    "venue_fit_check",
    "writing",
    "review_round1",
    "revise_round1",
    "review_round2",
    "revise_round2",
    "review_round3_meta",
    "final_revise",
]


def get_stage(name: str) -> Stage:
    """根据名称获取 stage，不存在则 raise KeyError。"""
    return STAGES[name]


def get_next_stage(name: str) -> Stage | None:
    """获取下一个 stage，如果已是终点返回 None。"""
    stage = STAGES[name]
    if stage.next_stage is None:
        return None
    return STAGES[stage.next_stage]


def get_rollback_stage(name: str) -> Stage | None:
    """获取回退目标 stage。"""
    stage = STAGES[name]
    if stage.rollback_stage is None:
        return None
    return STAGES[stage.rollback_stage]


def build_subagent_tasks(
    stage: Stage,
    items: list[dict],
) -> list[dict]:
    """为可并行 stage 生成 subagent 任务列表。"""
    if not stage.parallel:
        return []

    tasks = []
    for i, item in enumerate(items[: stage.max_parallel]):
        task = {
            "id": f"{stage.name}_sub_{i}",
            "item": item,
            "parallel_unit": stage.parallel_unit,
            "instructions": (
                f"处理 {stage.parallel_unit}: {item.get('id', item.get('title', str(i)))}\n"
                f"按照 {stage.skill} skill 的指令执行。\n"
                f"完成后返回结构化结果 JSON。"
            ),
        }
        tasks.append(task)
    return tasks
