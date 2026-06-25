# Amazon JP Launch Flow Project

## 目标

将 Amazon Japan 跨境电商从选品、上架、投放到复盘的流程文档收敛到一个独立工程目录，作为团队执行入口。

## 文件结构

- `index.html`：主入口，用法指南与流程执行说明。
- `architecture.html`：覆盖矩阵独立展示页。
- `assets/architecture-coverage.png`：用户确认后的最终覆盖矩阵截图。
- `skills/`：Amazon JP 跨境电商流程相关 Codex skills 的工程内副本，包含研究、执行、实时数据和复盘能力。
- `skills/README.md`：skill 清单、推荐调用顺序和重新安装说明。

## 使用方式

直接打开 `index.html`，先查看覆盖矩阵，再按阶段执行实时数据同步、数据清洗、机会评分、风险审计、供应商/QC、商业验证、Launch Gate、Listing/A+、Seller Central、FBA 上架、广告投放和复盘回流。

## Skill 使用方式

优先从 `skills/amazon-jp-sop-orchestrator/` 作为总控入口读取流程，再按 `skills/README.md` 中的推荐顺序调用各个 specialist skill。工程内副本用于归档和版本管理；如果要让 Codex 会话自动触发这些 skills，需要把对应目录复制到 `~/.codex/skills/` 后重启会话。

## 实战性增强

本工程新增 5 个执行与实时性 skill：

- `amazon-jp-live-data-sync`：把 Seller Central、Amazon Ads、库存、退货、评论等运营导出转成统一 CSV。
- `amazon-jp-sourcing-qc-planner`：把供应商报价、样品和差评痛点转成 QC 检查表。
- `amazon-jp-seller-central-ops`：把上市包转成 Seller Central 字段、flat file 和人工操作清单。
- `amazon-jp-fba-shipment-planner`：计算首批/补货数量、库存天数、标签和箱规检查。
- `amazon-jp-performance-reviewer`：按 7/14/30 天和周度指标输出 scale、optimize、pause 或 kill 动作。
