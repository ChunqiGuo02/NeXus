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
├── data/                 # 数据集（自动下载）
├── results/              # 实验结果
├── checkpoints/          # 模型检查点
└── README.md             # 实验说明
```

### Step 1.5: 数据集自动准备

从 `hypothesis_board.json` + `configs/default.yaml` 识别所需数据集，自动匹配下载方式：

| 来源 | 适用场景 | 下载方式 |
|------|---------|---------|
| torchvision | CIFAR, MNIST, ImageNet 等 | `torchvision.datasets` |
| HuggingFace Hub | NLP / 多模态数据集 | `datasets.load_dataset()` |
| Papers with Code | 查询任务 SOTA 数据集 + benchmark | 获取下载链接 + 评估指标 |
| Kaggle | 竞赛数据集 | `kaggle API`（需 `kaggle.json`） |
| 自定义 URL | 论文中标注的链接 | `wget` / `curl` |
| deep-dive 笔记 | 论文专属数据来源 | 从笔记中提取链接 |

下载位置根据计算环境决定：
- **本地执行** → `experiments/{name}/data/`
- **远程执行** → 直接在服务器侧下载（避免本地中转）

```
输出示例：
  📦 实验需要以下数据集：
  1. CIFAR-100 (~161MB) — 通过 torchvision 自动下载
  2. GloVe embeddings (~862MB) — 从 Stanford NLP 下载
  → 确认开始下载？
```

同时自动生成 `data.py` 中的加载代码，路径与下载位置一致。

### Step 1.8: 计算环境自动推荐

根据实验配置自动估算工作量，主动推荐是否使用远程服务器：

**估算信号**（从 hypothesis_board + configs 提取）：
- 模型规模：参数量 / 架构类型（CNN / Transformer / LLM）
- 数据规模：数据集大小 / 样本数
- 训练量：epochs × batch_size × 预估步数
- GPU 需求：模型是否需要 GPU / 多卡

**推荐分级**：

| 级别 | 条件 | 推荐 |
|------|------|------|
| 🟢 轻量 | CPU 可跑, <30min | 建议本地运行 |
| 🟡 中等 | 需 GPU, 30min-4h | ⚠️ 建议在 GPU 服务器运行 |
| 🔴 重度 | 多卡/大模型, >4h | 🚨 强烈建议远程服务器 |

```
输出示例：
  📊 实验预估：ResNet-50 + CIFAR-100, ~50 epochs
  → 预计 GPU 训练 ~40min, CPU 训练 ~8h
  ⚠️ 建议在 GPU 服务器上运行。是否配置远程连接？
```

**远程配置流程**：

```
Agent: 你使用哪种远程环境？
  ① AutoDL（推荐，一键配置）
  ② 自建服务器 / 实验室集群（手动配置）
  💡 也支持矩池云、恒源云等，告诉我平台名即可自动适配
```

**AutoDL 一键配置**（用户粘贴 SSH 指令即可）：

| 配置项 | 自动填充值 |
|-------|-----------|
| SSH 格式 | 从粘贴的 `ssh -p PORT root@connect.REGION.autodl.com` 自动解析 |
| 训练数据 | `/root/autodl-tmp/data/`（快速 SSD，关机保留） |
| 代码/checkpoint | `/root/autodl-fs/experiments/{name}/`（跨实例持久共享） |
| 缓存 | `HF_HOME=/root/autodl-tmp/.cache/huggingface` |
| 防断连 | 训练命令自动包裹 `tmux` |

```
输出示例：
  User: 我用autodl，ssh -p 10309 root@connect.nmb1.seetacloud.com
  Agent: ✅ 检测到 AutoDL，已自动配置：
         • 训练数据 → /root/autodl-tmp/data/
         • 代码/模型 → /root/autodl-fs/experiments/{name}/
         • 训练将在 tmux session 中运行
         🔗 验证连接中... ✅ 连接成功，GPU: A100-80G x1
```

**自建服务器**需提供：host、user、remote_workdir、conda env（可选）。
前提：SSH key 免密登录（agent 无法交互输入密码）。首次自动验证连通性。

配置保存到 `project_state.json` 的 `compute_target` 字段。

### Step 2: 代码编写

根据 deep-dive 笔记中的方法细节，实现核心代码：
- 如果项目中存在 `rules/coding-style.md`，遵循其编码规范
- 使用 `@dataclass(frozen=True)` 管理配置
- 保证可复现性：固定随机种子、记录环境

### Step 3: 训练与调试

**本地执行**：
- 小数据 sanity check（先在小子集上跑通）
- 逐步扩大规模
- 记录所有超参数和结果到 `results/`

**远程执行**（`compute_target == "remote"` 时）：
1. 同步代码 → `rsync -avz experiments/{name}/ user@host:remote_workdir/`
2. 远程训练 → `ssh user@host "cd remote_workdir && tmux new -d -s train 'bash scripts/run_train.sh'"`
3. 实时监控 → `ssh user@host "tmux capture-pane -t train -p | tail -20"`
4. 训练完成 → `rsync -avz user@host:remote_workdir/results/ experiments/{name}/results/`
5. 按需拉 checkpoint → 只拉 `best.pt`，不拉全部

### Step 4: 结果分析与图表生成

**对比表格**（LaTeX 三线表）：
- 自动从 `results/` 读取 baseline + ours 的指标
- 生成 `\begin{table}` + `\toprule/\midrule/\bottomrule`
- 最佳值自动加粗 `\textbf{}`
- 保存到 `experiments/{name}/figures/main_results.tex`

**训练曲线**（matplotlib）：
- 从训练 log 读取 loss/metric vs epoch
- 双 y 轴：左轴 loss，右轴 metric
- 保存 PDF：`experiments/{name}/figures/training_curve.pdf`

**消融表**：
- 每行去除一个组件，LaTeX tabular 格式
- 保存到 `experiments/{name}/figures/ablation.tex`

**可视化**（按需）：
- t-SNE/UMAP：`sklearn` + `matplotlib`
- Attention heatmap：从 checkpoint 提取
- Case study：选代表性样本展示

所有图表保存到 `experiments/{name}/figures/`。
如果 Overleaf 已配置，同步到 Overleaf 项目的 `figures/` 目录。

**图表标题自动生成**：基于数据和实验描述，为每个图/表生成 self-contained 的 caption。

**统计检验**：主结果需报告 p-value 或置信区间（如适用）。

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
