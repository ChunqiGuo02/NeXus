---
name: evolution-memory
description: 跨项目的蒸馏式知识积累。在项目结束时自动触发蒸馏，在新项目启动时自动读取相关规则。存"规则"而非"数据"。
---

# Evolution Memory

跨项目的蒸馏式知识积累系统。每个项目结束时提炼可复用规则，新项目启动时读取历史经验，实现跨周期进化。

## When to Use

- **读取**：每个 skill 启动时自动读取与当前阶段相关的 rules
- **写入**：项目结束时（论文提交后 / 实验完成后）自动触发蒸馏
- 用户说"总结经验" / "保存规则" / "evolution memory"

## 存储

位置：`~/.nexus/evolution_memory.json`

```json
{
  "idea_rules": [
    {
      "rule": "方法迁移类 idea 在相似任务结构的跨域更容易成功",
      "source_project": "project-name",
      "date": "2026-03-17",
      "confidence": 0.8,
      "context": "在 NLP→CV 迁移中验证"
    }
  ],
  "experiment_rules": [],
  "writing_rules": [],
  "review_rules": []
}
```

## 三种进化机制

### IDE — Idea Direction Evolution

**触发**：idea 阶段结束后（ToT + Elo + 红队完成）

**提炼内容**：
- 哪些方向存活了？为什么？
- 哪些方向被 kill 了？什么原因？
- 红队最常攻击的弱点类型是什么？

**规则格式**：`"在[领域]做[方法类型]的 idea，[可行/不可行]，因为[原因]"`

### IVE — Idea Validation Evolution

**触发**：实验失败后

**提炼内容**：
- 失败是实现问题（bug/环境/超参）还是方向问题（idea 本身不 work）？
- 如果是方向问题，在什么条件下暴露的？

**规则格式**：`"[方法]在[条件]下会失败，因为[根本原因]"`

### ESE — Experiment Strategy Evolution

**触发**：实验成功后

**提炼内容**：
- 哪些策略关键促成了成功？
- 哪些调试技巧特别有效？
- 数据处理/训练的可复用 pattern 是什么？

**规则格式**：`"遇到[问题]时，先试[策略A]再试[策略B]"`

### RFE — Review Feedback Evolution（v4 新增）

**触发**：用户收到真实审稿意见后，使用 `reenter_pipeline` 重入

**处理流程**：
1. 将真实审稿意见与模拟审稿做逐条对比
2. 分析差异类型：

   | 差异类型 | 含义 | 校准动作 |
   |---------|------|---------|
   | 模拟 ✅ 真实 ❌ | 模拟遗漏了真实弱点 | 将弱点模式加入 review_rules |
   | 模拟 ❌ 真实 ✅ | 模拟过度攻击 | 降低该类攻击权重 |
   | 模拟 ✅ 真实 ✅ | 双方共识 | 确认规则有效 |
   | 模拟 score > 真实 score | Sycophancy bias | 加大 Score Deflation 力度 |

3. 输出 `calibration_report.md`
4. 自动更新 `review_rules`，调整 confidence

**规则格式**：`"在[venue]审稿模拟中，[弱点类型]被遗漏了N次，真实reviewer关注[具体模式]"`

> 这实现了**自校准审稿系统**——每次真实投稿反馈后，模拟审稿精度提升。

## 读取策略

**按需加载**——每个 skill 启动时只读取相关分类：

| Skill | 读取的 rules 分类 |
|-------|------------------|
| idea-brainstorm | `idea_rules` |
| experiment-runner | `experiment_rules` |
| paper-writing | `writing_rules` |
| multi-reviewer | `review_rules` |

预估增量：~50 tokens/rule × ~20-50 rules（10 个项目后）= 1-2.5K tokens

## 写入策略

### 自动蒸馏（项目结束时）

1. 回顾项目全流程记录（evidence audit → idea → experiment → paper → review）
2. 提炼 2-5 条新规则
3. **用户确认**后写入 `evolution_memory.json`
4. 如果新规则与已有规则冲突 → 更新 confidence 或合并

### 规则淘汰

- 连续 3 个项目未被读取的规则 → 标记为 `deprecated`
- confidence < 0.3 的规则 → 建议删除

## 反直觉规则

1. **失败经验比成功经验更有价值** — IVE 的规则优先级高于 ESE
2. **规则要少不要多** — 50 条精炼规则 > 500 条泛泛记录
3. **过时的规则比没有规则更危险** — 定期淘汰，不要累积

## Pipeline Exit (v2: MetaClaw-style Auto Distillation)

触发时机：
1. **最终蒸馏**：`final_revise` 完成后由 `complete_stage("final_revise")` 自动触发
2. **实时捕获**（v2 新增）：任何 stage **rollback** 时自动 capture failure lesson
   - `complete_stage(result="rollback")` → 自动记录 failure reason → 转换为 rule
   - 不等项目结束，每次失败都积累经验
3. 手动调用：任何时候均可

> **MetaClaw 式自动蒸馏**：failure → lesson → rule → 注入下次 pipeline（自动化）
