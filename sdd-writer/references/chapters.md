# 章节内容指引（Chapter Playbook）

这套 SDD 骨架一共六章，固定顺序、固定章名。填内容时每一章有各自的"该写什么、不该写什么"和推荐子节。

## 第 1 章 · 总览（4 节，短）

| 子节 | 必含 | 避免 |
|---|---|---|
| 1.1 系统定位 | 一段话讲清"这是什么、用于什么场景、关键机制一句话" | 不写 ROI / KPI 这类非技术指标 |
| 1.2 范围与边界 | `two-col` 两栏：In Scope（绿）+ Out of Scope（玫瑰），每栏 5-7 行 | 不要列细节实现 |
| 1.3 核心不变式 | `card-grid` 行排列（`grid-template-columns: 1fr`），6 条左右，每条 1-2 行 | 不要写"实现细节"，只写"不变事实" |
| 1.4 术语表 | 表格：术语 + 定义。5-10 条专有名词 | 不要抄通用词（API、DB 这种） |

**不变式（Invariants）是整篇文档的锚点**——后面所有章节都要能映射回这几条不变式。典型的不变式范式：
- 唯一性：「任意时刻 X 只能存在一个」
- 顺序性：「Y 必须发生在 Z 之前」
- 安全门：「当 Φ 条件满足时才能 P，否则返回 CONFLICT」
- 幂等性：「操作 O 重复执行等价于执行一次」

## 第 2 章 · 概要设计（4 节）

| 子节 | 必含 |
|---|---|
| 2.1 分层架构 | 一张 SVG 架构图（见 `references/svg-diagram.md`）+ 一两段描述。图 1 的画布默认 1100×720 |
| 2.2 核心模块与依赖 | **必须拆两个 h3 子节**：2.2.1 模块速览（`card-grid` 每模块一卡）+ 2.2.2 源码目录树（`<div class="tree">` 列顶层目录与关键文件） |
| 2.3 主要数据流 | 2-4 个典型 flow（启动、变更、故障、扩缩），每个起 `<h3>`，配短段落；复杂 flow 可加 SVG 时序图 |
| 2.4 设计原则 | 项目级原则 5-8 条，有名词（SSOT、CAS、FSM……）就用加粗突出 |

### 2.2.1 模块速览（卡片）

8-12 张 `.card`，每张 `--accent` 用语义色（核心主干 emerald、存储 cyan、写入 violet、异步 amber/orange、扩展 rose、外围 slate）。每张卡一句话职责 + 代表类/文件名，**不要**在卡片里堆文件列表——那是目录树的活。

### 2.2.2 源码目录树（必写）

用 `<div class="panel"><div class="tree">...</div></div>` 画一棵顶层目录树。这节的价值是回答两个问题：

1. **文件在哪**——读者读完卡片知道"有 cache 模块"，但不知道"LRU 实现在哪个文件"。目录树给出具体路径。
2. **新增能力该落在哪里**——树结束后附一段经验规则（`<p>` 正文），用"① 改公有 API → 头文件；② 核心主干改动 → 主模块；③ 改持久化格式 → 存储模块；④ 替换系统调用 → 抽象层；⑤ 非核心、默认关闭特性 → 扩展目录"这类梯度，最好举本项目一个真实例子（某 PR 落在了哪里、为什么那样放）。

**铺排顺序**（不要按字母序）：

```
公开 API（include/ / api/ / pkg/）
    ↓
核心主干（业务中枢 / 调度器 / 主循环）
    ↓
存储 / 持久化格式（table/ / storage/ / disk/）
    ↓
系统抽象（env/ / fs/ / net/ / runtime/）
    ↓
配置 · 可观测 · 底层工具
    ↓
扩展 / 可选特性（utilities/ / plugins/ / contrib/）
    ↓
构建 · 测试 · 工具 · 语言绑定
```

**注释规范**：

- 顶层目录用 `← XXX（N 文件）` 标注职责 + 规模。
- 关键文件用 `· <code>ClassName</code>（N 行）` 标注代表类 + 行数（行数让读者对复杂度有量感）。
- 对合并命名的文件用 `.{h,cc}` / `.{h,c}` 简写避免两行。
- 用 `<span class="dir">目录名/</span>` 给目录名上色，用 `<span class="note">注释</span>` 给注释做灰色弱化。

**裁剪原则**：只列对理解架构有帮助的条目，不穷举。测试文件、CI 脚本、第三方依赖、示例、语言绑定原则上只给到一级目录注释（"← RocksJava JNI 绑定"），不展开内部结构。总高度目标 60-120 行——再多读者会跳过。

**示例片段**：

```html
<div class="panel">
  <div class="tree">
<span class="dir">myproject/</span>
├── <span class="dir">include/myproject/</span>       <span class="note">← 公开 API（唯一保证稳定的头文件）</span>
│   ├── client.h                    <span class="note">· <code>class Client</code></span>
│   └── options.h                   <span class="note">· ClientOptions · Read/WriteOptions</span>
│
├── <span class="dir">core/</span>                        <span class="note">← 主调度（42 文件）</span>
│   ├── scheduler.{h,cc}            <span class="note">· <code>class Scheduler</code>（1240 行）</span>
│   └── <span class="dir">worker/</span>                   <span class="note">· 后台线程池实现</span>
│
├── <span class="dir">utilities/</span>                    <span class="note">← 可选扩展（默认关闭）</span>
│   └── <span class="dir">retry/</span>                    <span class="note">· 指数退避策略</span>
│
├── <span class="dir">test_util/</span>                    <span class="note">← 测试基础设施</span>
└── Makefile / CMakeLists.txt       <span class="note">· 双构建系统</span>
  </div>
</div>
<p>判断"新增能力放哪"的经验规则：① 改公有 API → <code>include/</code>；② 核心调度改动 → <code>core/</code>；③ 非核心、默认关闭 → <code>utilities/</code>。例如 PR #123 引入的重试策略走的就是第 ③ 条。</p>
```

目录树是 2.2 的强制部分。只给卡片不给树 = 读者知道"有什么"，但不知道"在哪里"，第 3 章详细设计就会反复切换"我说的 XxxManager 源码究竟在哪"——目录树一次性解决。

## 第 3 章 · 详细设计（变长，占全文主体）

按模块分节，每节一个 h2（3.1 / 3.2 …），每节内部再用 h3 拆算法和代码路径。推荐模式：

```
3.1 <模块名>
  3.1.1 数据结构（直接贴结构体/proto 定义）
  3.1.2 核心算法（分步骤讲，每步能映射到代码文件名）
  3.1.3 生命周期（状态机 / 关键转移）
  3.1.4 并发与锁
  3.1.5 失败语义与恢复
```

- 贴代码用 `<pre><code>...</code></pre>`，**不要**贴超过 30 行。重点给结构签名、核心循环、关键 goroutine。
- 行内引用函数名、文件名、配置 key 用 `<code>`——这是整篇文档的基本节奏。
- **每个算法小节末尾**都要点出它如何支撑第 1 章的不变式，保持首尾呼应。

### 3.x 控制流 / IO 路径流程图（必画）

在"网络 / 事件循环 / 请求处理"所在的那节末尾追加一个 `<h3>N.x.y 控制流</h3>`，用**泳道式 SVG**展示一次典型请求从入到出的每一步。要求：

- 泳道语义是"执行者边界"：线程 / 进程 / 节点（例如 `KERNEL / IO THREAD / MAIN THREAD / BIO THREAD`，或 `CLIENT / API / WORKER / DB / QUEUE`）。
- 每一步用 ①②③… 编号标在连线旁，让读者能按顺序读。
- 同步路径用实线 + 实心箭头；异步 / 旁路用虚线 + 对应语义色（参考 svg-diagram.md 的配色）。
- **必画，哪怕系统看似简单**——能画出泳道图意味着你已经搞清楚边界，这是详细设计章节的价值所在。

### 3.x 异步任务时序图（有几个异步子系统就画几张）

系统里任何"跨线程、跨进程、跨节点、跨网络"的协作都要单独配一张 UML 风格时序图。常见候选：

- 持久化 / 快照（fork CoW、WAL 刷盘）。
- 主从复制 / 一致性协议握手（PSYNC、Raft、Paxos 的 prepare/accept）。
- 故障切换 / 选举 / leader lease 续约。
- 后台 GC / 压缩 / 迁移 / rebalance。
- 消息队列投递 / 重试 / ack。
- 外部回调 / webhook / pub-sub 广播。

每张时序图至少包含：actor 头部（带语义色）+ 竖向 lifeline + 横向消息箭头 + 阻塞窗口（色块覆盖 lifeline）+ 并发活动提示（斜体文字或辅助色块）+ 失败分支（rose 色虚线），最后一行用 callout-like 文字给"断线 / 异常重连"等分支情况。

**判断要不要画**：读者看完文字后如果还会问"谁先谁后？阻塞在哪？哪里可以并行？异常怎么办？"——就必须画。只会画一张分层架构图然后全靠文字脑补是详细设计章节的最大失分项。

### 3.x 数据结构内存布局（存储类 / 数据库 / 协议类必画）

给每个核心结构体 / 对象 / 编码配一张**字节条图**（byte-strip layout），按 SVG 画布 `1060×160~340` 的横条形式展示字段在内存中的排布。见 `references/svg-diagram.md`"内存布局条图"一节的完整配方。

**一个正文页至少回答三问：**
1. 这条 malloc 包含哪些字段？按 offset 顺序画出来。
2. 哪些字段是<strong>内嵌</strong>（省一次 malloc）？用实底色块突出。
3. 何时升级 / 迁移到另一种表示？配表格给"触发阈值"。

**典型候选**：

- 对象头（robj / key）+ 可选内嵌 key / TTL 元数据。
- 变长字符串头的多种尺寸变体（如 sdshdr8/16/32）。
- dict / hashtable 的 bucket 指针数组 + dictEntry 链。
- 紧凑数组（listpack / ziplist）及其 entry 子结构。
- 复合容器（quicklist / stream-rax）的节点 + 节点内子结构。
- 多级 / 概率结构（skiplist / HNSW layer）的层级可视化。
- ring buffer / circular log 的 head/tail 游标与多 consumer cursor。

画完字段条后紧跟一张"<strong>编码升级阈值</strong>"表：列"小容量编码 / 条目数阈值 / 字节阈值 / 升级后结构"，把<code>*-max-listpack-*</code>、<code>*-max-intset-*</code> 这类运维配置项显式化。

### 3.x 关键结构体解剖（任何 C / Rust / Go 项目都值得写）

对**主事件循环、请求上下文、后台 worker、线程池 slot**这几类"贯穿全程的实例"，专门开一个 `<h3>` 小节做结构体级解剖。做法：

1. 贴不超过 30 行的结构体定义（含字段注释），关键位域 / 指针顶格说明。
2. 紧跟若干条"字段语义 + 生命周期 + 谁会读 / 写"的 bullet。
3. 最后点出该结构体如何支撑第 1 章哪条不变式。

结构体解剖和数据结构布局图是互补的——前者讲**字段关系**，后者讲**字节位置**。

### 3.x 周期任务 / cron 清单（进程型系统必画）

任何有"后台线程/协程/tick"的系统，都有个 serverCron/workerLoop/ticker 管一大堆琐事。在对应模块小节用<strong>表格</strong>列出：任务名 / 节拍（every-tick / periodic N / conditional）/ 作用。

这张表的意义：告诉读者"系统空闲时也在做什么"——定期过期、rehash 补搬、心跳、metrics 采样、阈值检测都该显式登记。

### 3.x 策略选型场景表（可选策略型的模块必画）

像 eviction / load-balance / consistency-level / retry-policy / compression-level 这种"有一组可选枚举"的参数，用表格给每个选项配：**淘汰/选择目标 + 排序依据 + 推荐场景 + 不推荐场景**。别只列名字——光知道"allkeys-lru"读者不会选，"哪种 workload 用哪个"才是信息。

### 3.x 性能优化点合集（可选）

对"近半年专门为此模块做的一堆小 PR"开一张表：<strong>PR# / 优化 / 原理</strong>。这比正文散点提及更易汇总，也是第 5 章 AI 影响证据的天然素材。

## 第 3.N 章 · 版本演进（强烈推荐新增）

基于 git 历史 + CHANGELOG / release notes 做的"3-5 年变更叙事"，放在详细设计章的最末节（如 § 3.8）。骨架固定 5-6 小节：

| 小节 | 内容 | 组件 |
|---|---|---|
| 3.N.1 版本时间线 | 一张 SVG 点线图：横轴时间 + 每个 release 一个节点，节点色按代际区分 | 见 `references/svg-diagram.md` "版本时间线"一节 |
| 3.N.2 数据结构演进 | 表格：版本 / 变更 / 位置 / 影响 | `<div class="panel" style="padding:0"><table>` |
| 3.N.3 IO &amp; 网络演进 | 同上，聚焦网络 / 并发 / 协议 | 同上 |
| 3.N.4 内存 &amp; 性能演进 | 同上，聚焦内存经济 / CPU / cache | 同上 |
| 3.N.5 新增命令 / 新 API 速查 | 表格（可用 rowspan 分组）：主题 / 命令签名 / 引入版本 / 说明 | `<table>` 加 `<td rowspan="N">` |
| 3.N.6 设计总结 | `card-grid` 4 张卡，把上面三张表提炼成 4 条长期趋势 | `.card` 四卡 |

**规则**：
- 每条变更都要带 <strong>源码位置</strong>（文件名或 PR 号）。没有位置的变更是道听途说，不写。
- "新增命令 / 新 API 速查" 对 SDK 用户是最有价值的一节——即使其他表偷懒，这张别偷懒。
- 表格用 `td.key` 黄色突出版本号，`td.scene` 紫色放主题列。

## 第 4 章 · 测试场景与覆盖度（5 节）

| 子节 | 组件 |
|---|---|
| 4.1 覆盖度概览 | `scoreboard`：左分值右维度条。推荐维度：场景广度 / 时序并发断言 / 幂等 Panic 恢复 / 故障边界 / e2e 集成 / 性能基线 |
| 4.2 场景矩阵 | 表格：# / 场景 / 位置 / 特征 / 评分。配 `tag` 刻度说明 |
| 4.3 关键场景深度 | 3-4 个最有代表性的场景，每个 h3 一段深描，引用具体测试函数名 |
| 4.4 覆盖盲区与建议 | 表格：盲区 / 现状 / 建议补强 / 优先级；末尾 `callout.amber` 点明"高优先级是分布式难题" |
| 4.5 测试运行参考 | `<pre>` 放 5-6 条典型 `go test` / `pytest` 命令 |

测试章最容易写空。**判断标准**：读者能否从 4.2 的矩阵直接找到对应源码测试文件、从 4.3 学到"这个系统值得信任的核心证据是什么"。

## 第 5 章 · AI 辅助工程实践（6 节，固定内容）

这一章大部分内容可以复用本模板里已写好的版本——四角色分工、双检查点、Async Guardrail、四条工程原则都是项目级约定，不同项目基本通用。只需改：

- **5.5 AI 对代码库的实际影响**：举 3-5 条**本项目** git log 的证据（"isolate"/"split"/"generalize" 动词频率，test-only commit 占比，CLAUDE.md 的位置）。
- **5.6 AI 协作的工程风险**：列出本项目观察到的实际问题（Rubric 无版本化、skill 数量、inspiration 归档等）。

其余四节（角色、双检查点、Async Guardrail、四原则）如果项目采用同一套 CLAUDE.md 约定，**建议原文保留**，这本身就是这套方法论的一部分。

## 第 6 章 · 优劣点（4 节）

| 子节 | 组件 |
|---|---|
| 6.1 优势 | `card-grid`，每卡 `--accent: var(--emerald)`。4-8 条 |
| 6.2 劣势 / 待改进 | `card-grid`，每卡 `--accent: var(--rose)` 或 `--amber`。同等数量 |
| 6.3 综合评分 | `scoreboard`。维度：架构合理性 / 可扩展性 / 可靠性 / 可观测性 / 可维护性 / AI 工程协作 |
| 6.4 结论 | 一段正文 + 两个 `callout`（emerald 核心优势 3 条、amber 主要改进 3 条）。 |

**打分校准**：8.5–9.2 是"生产就绪"区间；9.3+ 需要有硬数据支撑（压测基线、故障演练记录）；7.0 以下要在 6.2 里明确列出阻断项。不要给每一维都打 9+，失去参考意义。

## 侧栏 side-nav 的维护

模板末尾有一份完整的 side-nav 模板，章节顺序与 id 已经对齐。**每次改章节结构时**：

1. section 的 `id` 保持稳定（`ov-*` / `hld-*` / `dd-*` / `ts-*` / `ai-*` / `pros`/`cons`/`scoring`/`verdict`），这样锚点不失效。
2. 若增加新的 3.x 小节，在第 3 章的侧栏列表里添一个 `<li>`。
3. 页面底部的 scroll-spy JS 无需修改——它自动为所有 `<section>` 建立 IntersectionObserver。

## 元信息

- **文档语言**：默认中文；术语保留英文（FSM、CAS、SSOT 等）。
- **字数参考**：CCManager SDD 全文 ~5000 字中文，完整 HTML 约 1900 行。小型项目目标 1000-2500 字（~800 行 HTML）。
- **日期格式**：footer 用 `Generated YYYY-MM-DD`，今天的日期由 Claude 在生成时填。

## 第 3.M 章 · 配置参数速查（第 3 章最后一节，必写）

给运维 / SRE 一张"一打开就能抄参数"的速查页。来源于 <strong>实际配置文件</strong>（<code>redis.conf</code> / <code>*.yaml</code> / <code>flags.go</code> / <code>env.default</code>），<strong>不要编造默认值</strong>。如果源码仓库没有可直接读的默认值文件，跳过这节或明确标注"defaults sourced from docs/xxx.md"。

### 骨架

固定 7-10 个子节，每节一个 `<h3>` + 一张 `<table>`。分组顺序按"用户最先调的参数在前"：

1. 网络 &amp; 协议（端口、bind、timeout、keepalive、io-threads / workers）
2. TLS / 安全（证书、协议版本、身份认证）
3. 持久化 / 存储（快照、日志、WAL、策略）
4. 复制 / 多副本
5. 集群 / 分片
6. 内存 / 驱逐 / 缓存
7. 性能 / 后台任务（hz、cron、tick、并发度）
8. 数据结构 / 编码阈值（有则列）
9. 安全 / ACL / 鉴权
10. 可观测性（slowlog、latency、trace、metrics）

每张表固定四列（顺序别改）：

```html
<div class="panel" style="padding:0">
  <table>
    <thead><tr><th>参数</th><th>默认值</th><th>说明</th><th>调优提示</th></tr></thead>
    <tbody>
      <tr><td class="key">io-threads</td><td>1</td><td>IO 线程数，&gt;1 启用多线程 IO</td><td><span class="tag amber">hot</span>CPU≥4 核建议 2-4</td></tr>
    </tbody>
  </table>
</div>
```

### 规则

- 默认值未设 / 注释状态用 `<td class="no">未设</td>` 或 `<td class="no">—</td>`。
- <strong>"hot" 标签</strong>：默认值在多数生产环境都需要调整的参数用 `<span class="tag amber">hot</span>` 起头放在"调优提示"列。一张表里的 hot 不要多于 30%，否则失去聚焦意义。
- 参数名用 `<td class="key">`（琥珀），突出可复制性。
- 调优提示一句话，能给出"什么场景调什么方向"。不要只写"按需调整"——没信息量。
- 每节 5-15 行，太少可合并两组，太多拆成 a/b 子节。

### 两个结尾 callout 很重要

在最后一张表之后，加两条总结：

```html
<div class="callout emerald">
  <strong>运行时动态修改：</strong>大多数参数支持 <code>CONFIG SET</code> / <code>SIGHUP reload</code> 在线生效。
  <strong>不支持</strong>在线修改的典型有 XXX / YYY / ZZZ（列 3-6 项）。
</div>
<div class="callout amber">
  <strong>分组优先级：</strong>部署新实例时按 hot 顺序校对一次：A / B / C / ...。其他 80% 保持默认即可。
</div>
```

前一个 callout 给运维"哪些要重启"的心智模型；后一个给一张<strong>最简 checklist</strong>——这张 checklist 就是新人接手时第一眼要看的东西。

### 为什么这节必写

一份没有参数速查的 SDD 对运维 SRE 几乎没用——他/她会直接去翻源码。把这节写好，这份文档就有了"接到告警能快速定位"的实用价值，而不只是"评审时翻一翻"的装饰。它和 § 3.N 版本演进是一对：演进讲"过去 3-5 年怎么走到这里"，配置速查讲"现在这里长什么样"。
