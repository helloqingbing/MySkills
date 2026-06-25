# Amazon JP Skills Bundle

这个目录保存 Amazon Japan 跨境电商流程相关的 Codex skills。本目录是工程内副本，用于版本管理、审阅和交付；如果要让 Codex 会话自动触发，需要复制到 `~/.codex/skills/` 并重启会话。

## 推荐调用顺序

1. `amazon-jp-sop-orchestrator`：总控状态机、目录结构、artifact contract、阶段 Gate。
2. `amazon-jp-live-data-sync`：清洗 Seller Central、Amazon Ads、库存、退货、评论等实时运营数据。
3. `amazon-data-ingestor`：清洗 POE、SQP、ASIN、搜索词、供应商报价和广告数据。
4. `amazon-opportunity-scorer`：对候选品做机会评分和 Top N 排序。
5. `amazon-risk-auditor`：早筛 IP、合规、FBA、季节性、品牌垄断和运营风险。
6. `amazon-radar-report`：生成机会雷达报告和下一步验证计划。
7. `amazon-jp-sourcing-qc-planner`：把供应商、样品、评论痛点转成 QC 与包装执行计划。
8. `amazon-jp-launch-gate`：SKU 上架前硬门禁，输出 `pass`、`needs_proof` 或 `blocked`。
9. `amazon-review-miner`：挖掘差评痛点，生成产品需求和改进方向。
10. `amazon-jp-listing-aplus-designer`：生成日文 Listing、A+ 模块、图片 brief 和 keyword master。
11. `amazon-jp-seller-central-ops`：生成 Seller Central 字段、flat file、A+ 提交和人工操作清单。
12. `amazon-jp-fba-shipment-planner`：生成 FBA 入仓、标签、箱规、补货和库存风险计划。
13. `amazon-ads-planner`：生成 Sponsored Products 广告结构、预算、否词和 30 天优化计划。
14. `amazon-jp-performance-reviewer`：执行 7/14/30 天和周度经营复盘，输出投放、库存、Listing、QC 动作。

## Skill 清单

- `amazon-ads-planner/`
- `amazon-data-ingestor/`
- `amazon-jp-fba-shipment-planner/`
- `amazon-jp-launch-gate/`
- `amazon-jp-live-data-sync/`
- `amazon-jp-listing-aplus-designer/`
- `amazon-jp-performance-reviewer/`
- `amazon-jp-seller-central-ops/`
- `amazon-jp-sourcing-qc-planner/`
- `amazon-jp-sop-orchestrator/`
- `amazon-opportunity-scorer/`
- `amazon-radar-report/`
- `amazon-review-miner/`
- `amazon-risk-auditor/`

## 重新安装到 Codex

如果后续以本工程目录为来源修改 skill，可以将需要启用的 skill 目录复制回 Codex skills 目录：

```bash
cp -R /Users/yunzhe/workspace/amazonjp/skills/amazon-* ~/.codex/skills/
```

复制后重启 Codex 会话，让新 skill 描述重新加载。
