# Amazon JP Launch OS TODO

目标：把当前流程从“生成清单”升级为“证据校验 + 状态机 + 真实 SKU 回归样例”。

## P0 - 生产级安全线

- [ ] 建立 `workflow_state.json`
  - 记录当前 SKU 的 lifecycle state、当前 Gate、最近决策、阻塞项、下一动作。
  - 区分 lifecycle state、gate decision、post-launch action，避免混用 `status`。

- [ ] 建立 `gate_decisions.csv`
  - 字段建议：`run_id`, `launch_id`, `sku`, `gate`, `decision`, `reason`, `owner`, `approver`, `decision_at`, `next_action`, `due_date`。
  - 每次 Gate 决策必须留痕。

- [ ] 建立 `artifact_manifest.csv`
  - 字段建议：`artifact_path`, `artifact_type`, `source_file`, `date_range`, `generated_at`, `row_count`, `checksum`, `owner`, `freshness`, `blocking_gap`。
  - 所有 CSV、截图、报告、Seller Central/FBA 证据都必须进入 manifest。

- [ ] 建立 `report_manifest.csv`
  - 覆盖 Seller Central、Amazon Ads、库存、退货、评论、Business Report、Search Term Report。
  - 必须记录导出时间、覆盖日期、行数、hash、是否 stale。

- [ ] 增加严格 Launch Gate validator
  - 强制校验必备 controls 全量存在。
  - 缺控制项、缺证据、缺 owner、缺日期、缺来源时不能 `pass`。
  - `user confirmation` 只能作为备注，不能作为合规/IP/JAN/FBA/claim proof 的 pass 证据。

- [ ] 修正 Performance Reviewer 的放量规则
  - 缺关键指标、报表过期、时间窗不足、无库存/退货/广告数据时输出 `needs_proof`。
  - 禁止在数据不足时默认 `scale`。

## P1 - 真实 SKU Golden Run

- [ ] 选择 1 个真实 SKU 作为 golden run
  - 产品名称
  - SKU
  - 类目 / product type
  - 品牌状态
  - 是否新建 ASIN
  - JAN/GTIN 或豁免状态
  - 目标售价
  - 目标毛利
  - 目标首批发货数量
  - 目标上线时间

- [ ] 准备选品与市场数据
  - POE / SQP 导出
  - 竞品 ASIN 列表
  - 竞品价格、评论数、评分
  - 核心关键词
  - Search Query Performance 数据
  - Keepa 或价格/BSR 趋势
  - 竞品 1-3 星评论导出或摘录

- [ ] 准备供应商与成本证据
  - 供应商报价
  - MOQ
  - 样品结果
  - 产品尺寸 / 重量
  - 包装尺寸 / 重量
  - 箱规
  - 头程报价
  - HS code / 关税 / 清关费用
  - FBA fee calculator 截图或结果
  - Referral fee
  - 仓储、退货、损耗预估

- [ ] 准备合规与上架证据
  - 类目限制截图
  - JAN/GTIN 或豁免证明
  - Brand Registry / 授权证明
  - IP 检索或商标风险证据
  - 标签/说明书图片
  - 认证/检测报告
  - claim proof
  - FBA 限制/危险品审核结果
  - Seller Central 必填字段或 flat file

- [ ] 准备后台执行证据
  - ASIN 创建结果
  - Parent/Child 变体关系
  - Listing 上传成功截图
  - A+ 提交/批准状态
  - Listing suppressed 检查
  - FNSKU 标签
  - FBA shipment plan
  - 箱唛 / box content
  - 入仓 / 接收状态

- [ ] 准备广告与复盘数据
  - 广告 campaign 导出
  - Search Term Report
  - Business Report
  - 库存报告
  - 退货报告
  - 评论/评分变化
  - ACOS / TACOS / CTR / CVR / CPC
  - Sessions / Orders / Sales / Ad Spend

## P2 - 实战能力增强

- [ ] 建立 Amazon JP 类目合规矩阵
  - 先覆盖 home / pet / outdoor。
  - 按类目列出认证、标签、进口、FBA、claim 禁区和证据样例。

- [ ] 升级 Seller Central 字段级 SOP
  - product type
  - browse node
  - variation theme
  - JAN/GTIN
  - 图片字段
  - A+ 提交
  - compliance fields
  - flat file 常见报错处理
  - 上传成功截图验收标准

- [ ] 升级 FBA control tower
  - shipment ID
  - ship-from / destination FC
  - carrier / forwarder
  - tracking
  - carton qty
  - FNSKU 状态
  - box content 状态
  - ETD / ETA
  - received qty
  - discrepancy qty
  - customs docs status

- [ ] 升级 Sourcing / QC
  - supplier_url
  - 营业执照
  - 验厂状态
  - 质量体系
  - 产能
  - 付款条款
  - incoterm
  - AQL
  - defect_class
  - batch_lot
  - CAPA
  - golden sample

- [ ] 升级 Amazon Ads 执行级结构
  - 拆分 `campaigns`, `ad_groups`, `targets`, `negatives`, `budgets`。
  - 增加 `campaign_id`, `ad_group_id`, `target_id`, `state`, `bid_strategy`, `placement_adjustment`。
  - 预算只在 campaign 层出现，避免误读成每个关键词独立预算。

- [ ] 建立退货根因闭环
  - 新增 `returns_root_cause.csv`。
  - 按退货率、退货原因、供应商/批次、QC 项、CAPA、负责人、截止日、关闭验证指标追踪。

## 最小可开始资料

如果先跑 MVP golden run，至少需要：

- [ ] 1 个 SKU 的基础资料
- [ ] 3-5 个竞品 ASIN
- [ ] 核心关键词列表
- [ ] 供应商报价
- [ ] 产品/包装尺寸重量
- [ ] 目标售价
- [ ] FBA fee 估算
- [ ] 竞品评论或差评摘录
- [ ] 类目/JAN/IP/标签/FBA 限制的现有证据

## 验收标准

- [ ] 1 个真实 SKU 从 `raw_exports` 跑到 `performance.actions.csv`。
- [ ] 每个 Gate 都有 `gate_decisions.csv` 留痕。
- [ ] 每个关键文件都进入 `artifact_manifest.csv`。
- [ ] 每份运营报表都进入 `report_manifest.csv`。
- [ ] Launch Gate 不允许缺 evidence 时 pass。
- [ ] Seller Central / FBA 人工步骤必须绑定截图或文件 proof。
- [ ] Performance Reviewer 在数据不足时不能输出 `scale`。
