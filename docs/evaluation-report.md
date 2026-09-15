# SecurePR Agent 离线评测说明

更新日期：2026-09-15

这份文档说明简历与作品集里“100 条 PR Diff 离线评测”的数据来源、比较方式和适用边界。它用于复核作品集中的工程实验，不代表生产环境安全效果。

## 评测问题

实验比较两条使用相同模型和单条 PR Token 预算的审查链路：

- `multi-llm-no-critic`：Lead、Security、Correctness/Reliability；
- `full-agentic`：在相同链路中加入独立 Critic。

比较目标是观察 Critic 对问题识别、误报控制和高风险问题召回的影响。评测脚本会在固定顺序的同一批样本上运行两组方案，并在隐藏 Holdout 上生成配对差值与 bootstrap 置信区间。

## 数据集

- 文件：[`evaluation_data/pr_diff_100.jsonl`](../evaluation_data/pr_diff_100.jsonl)
- 共 100 条合成受控 PR Diff：40 条风险样本、60 条干净样本；
- Validation 80 条，Holdout 20 条；
- 每条风险样本包含期望路径、行号区间、CWE、严重度及是否应评论等标签；
- 预测与标签按规范化文件路径、CWE 和行号匹配，默认允许行号距离不超过 2 行，并执行一对一匹配，避免一条预测重复命中多个标签。

这批数据由项目生成器构造，适合验证评测链路和受控消融，不满足生产证明门槛。仓库中的生产门槛要求至少 300 条带真实公开 PR 或私有历史 PR 来源的人工标注数据，并要求训练、验证、隐藏 Holdout 的仓库隔离。

## 已记录结果

简历与作品集保留的同口径汇总如下：

| 指标 | 无 Critic 方案 | 完整 Agentic 方案 | 差值 |
| --- | ---: | ---: | ---: |
| F1 | 81.9% | 91.3% | +9.4 个百分点 |
| 高风险召回率 | 84.2% | 94.7% | +10.5 个百分点 |
| 干净 PR 准确率 | — | 91.7% | — |

以上数值是既有本地评测的汇总记录。本次文档同步时，仓库中没有保留该次运行的逐条模型输出、模型版本快照和完整 JSON 报告，因此不能从当前提交单独重算出完全相同的数值。数据集、运行脚本和计算逻辑已经公开，后续复跑结果应连同模型名、运行时间、数据集哈希、逐条输出与生成报告一起提交。

## 复跑方式

运行脚本：[`scripts/run_agentic_evaluation.py`](../scripts/run_agentic_evaluation.py)

```powershell
$env:SECUREPR_LLM_BASE_URL = '<OpenAI-compatible base URL>'
$env:SECUREPR_LLM_API_KEY = '<API key>'
$env:SECUREPR_LLM_MODEL = '<model name>'
$env:SECUREPR_LLM_PROVIDER = '<provider>'

python scripts/run_agentic_evaluation.py evaluation_data/pr_diff_100.jsonl `
  --allow-non-production-data `
  --output output/agentic-evaluation/evaluation.json
```

`--allow-non-production-data` 只允许受控数据运行评测，同时保持生产证明与上线门禁关闭。API Key 只能通过环境变量传入，不应写入仓库或评测报告。

## 结果边界

- 合成样本覆盖的是预设风险模式，不能代表真实仓库的语言、依赖、业务上下文和误报分布；
- 结果依赖具体模型版本、温度、提示词、工具输出、Token/时间预算与运行时状态；
- “干净 PR 准确率”只表示这批干净样本未被错误标记的比例；
- 自动生成的发现与修复仍需人工审查，当前数据不能支持“生产级安全效果”或“普遍优于其他方案”的结论。
