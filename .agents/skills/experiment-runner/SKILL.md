---
name: experiment-runner
description: 管理实验代码的搭建、运行、结果分析。当用户说"做实验"、"跑代码"、"build project"、"experiment"时触发。
---

# experiment-runner

管理从项目搭建到结果分析的完整实验流程。

## 执行流程

### Step 1: 项目初始化

根据 `hypothesis_board.json` 中选定的 idea，创建实验项目结构：

```
experiments/{experiment_name}/
├── src/
│   ├── model.py          # 模型定义
│   ├── data.py           # 数据加载
│   ├── train.py          # 训练循环
│   ├── evaluate.py       # 评估脚本
│   └── utils.py          # 工具函数
├── configs/
│   └── default.yaml      # 超参数配置
├── scripts/
│   ├── run_train.sh      # 训练启动脚本
│   └── run_eval.sh       # 评估启动脚本
├── results/              # 实验结果
├── checkpoints/          # 模型检查点
└── README.md             # 实验说明
```

### Step 2: 代码编写

根据 deep-dive 笔记中的方法细节，实现核心代码：
- 遵循 `rules/coding-style.md`（如果存在）
- 使用 `@dataclass(frozen=True)` 管理配置
- 保证可复现性：固定随机种子、记录环境

### Step 3: 训练与调试

- 小数据 sanity check（先在小子集上跑通）
- 逐步扩大规模
- 记录所有超参数和结果到 `results/`

### Step 4: 结果分析

- 生成对比表格（vs baselines）
- 绘制训练曲线
- 消融实验
- 统计显著性检验

### Step 5: 结果写回

将关键结果写入：
- `evidence_graph.json`（作为新的 `result` claims，标注自己论文为来源）
- `artifacts/experiment_report.md`
- 更新 `project_state.json` phase → "experimenting"

## 可复现性规则

| 要求 | 实现方式 |
|------|---------|
| 随机种子固定 | 所有随机操作使用 `seed=42` |
| 环境记录 | `pip freeze > requirements.txt` |
| 配置记录 | 每次运行保存 config snapshot |
| 检查点保存 | 每 N epoch 保存 checkpoint |
| 结果版本化 | results/{timestamp}/ |
