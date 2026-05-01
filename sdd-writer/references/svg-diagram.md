# SVG 架构图配方

本文件记录 SDD 里架构图（图 1 · 分层架构）的画法约定。所有 SVG 都放在 `<div class="diagram-container">` 内，宽度自适应。

## 画布与坐标系

- `viewBox="0 0 1100 720"`（横向架构图的默认尺寸）。纵向流程图可用 `0 0 900 1000`。
- 左侧 30px 预留给层标签；右下预留 LEGEND 图例。
- 层分布（典型四层系统）：EXTERNAL `y≈60`，GATEWAY `y≈180`，RUNTIME `y≈340`，PERSIST/DATA `y≈580`。

## 可访问性（a11y，必写）

每张 `<svg>` 开头都必须包含 `role="img"` + `<title>` + `<desc>`。title 一句话概括图名，desc 一段话概括"这张图在讲什么"——截屏失败或读屏器场景下，这两行就是读者能拿到的全部信息。

```svg
<svg viewBox="0 0 1100 720" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="figN-title figN-desc">
  <title id="figN-title">图 N · 一句话图名</title>
  <desc id="figN-desc">这张图按 XX 泳道展示 YY 流程，重点是 ZZ……（60-120 字）</desc>
  <!-- 其余 defs / rect / text 不变 -->
</svg>
```

`figN-title` 与 `figN-desc` 的 ID 必须在整份文档里唯一（常用 `fig<数字>-title`）。`aria-labelledby` 同时引用两者。

## 必备 defs

所有图的 `<defs>` 里先放三样东西：网格 pattern、三色箭头 marker。

```svg
<defs>
  <pattern id="gridMain" width="40" height="40" patternUnits="userSpaceOnUse">
    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="0.5"/>
  </pattern>
  <marker id="mArr"       markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#64748b"/></marker>
  <marker id="mArrCyan"   markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#22d3ee"/></marker>
  <marker id="mArrViolet" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto"><polygon points="0 0, 10 3.5, 0 7" fill="#a78bfa"/></marker>
</defs>
<rect width="1100" height="720" fill="url(#gridMain)"/>
```

网格让整张图有坐标感，也是"技术文档风"的签名。

## 颜色语义（与外层 CSS 变量一致）

| 变量           | HEX        | 在架构图里的含义                           |
| -------------- | ---------- | ------------------------------------------ |
| `--cyan`       | `#22d3ee`  | RPC / HTTP 层，核心入站流量                |
| `--emerald`    | `#34d399`  | 业务主干 / 数据面 RPC                      |
| `--violet`     | `#a78bfa`  | 持久化 / etcd / 写入路径                   |
| `--rose`       | `#fb7185`  | 数据面（DB/Redis shards）/ watch / 反向流  |
| `--orange`     | `#fb923c`  | 事件 / 异步 / 周期 tick                    |
| `--amber`      | `#fbbf24`  | 告警 / 阈值                                |
| `--slate`      | `#94a3b8`  | 外部客户端，中性                           |
| `#1e293b`      | 暗色       | 边框 / 网格线                              |
| `#0f172a`      | 实底       | 盒体填充底色                               |

## 节点（矩形盒）

标准节点是"色块底 + 同色描边 + 白色标题 + 同色副标题 + 灰色正文行"的四段结构：

```svg
<rect x="130" y="340" width="240" height="160" rx="6" fill="#0f172a"/>
<rect x="130" y="340" width="240" height="160" rx="6" fill="rgba(8,51,68,0.4)" stroke="#22d3ee" stroke-width="1.5"/>
<text x="250" y="368" fill="white"   font-family="Inter"         font-size="12" font-weight="600" text-anchor="middle">模块名</text>
<text x="250" y="385" fill="#22d3ee" font-family="JetBrains Mono" font-size="9"  text-anchor="middle">职责一句话</text>
<line x1="145" y1="400" x2="355" y2="400" stroke="#1e293b" stroke-width="1"/>
<text x="250" y="420" fill="#e2e8f0" font-family="JetBrains Mono" font-size="9"  text-anchor="middle">内部条目 1</text>
```

- 先一层 `#0f172a` 实底盖掉网格，再覆一层 `rgba(...,.4)` 语义色 + 描边，避免网格透出。
- 标题 Inter 12 粗，副标题 JetBrains Mono 9，正文行 9。
- `rx="6"` 是所有盒的统一圆角。

## 连线

- 普通 RPC/HTTP：`stroke="#64748b" stroke-width="1.5"` + `marker-end="url(#mArr)"`。
- 数据面 RPC：`stroke="#34d399"` + `url(#mArr)`。
- 主干写入 etcd：`stroke="#22d3ee"` + `url(#mArrCyan)`。
- etcd → 模块（watch）：`stroke="#fb7185"` + `stroke-dasharray="4,3"` + `url(#mArr)`。
- 模块间弱连接（dispatch）：`stroke="#334155" stroke-dasharray="3,3"`，无箭头。

## 分组框

用虚线框把一组节点归到"子系统"里：

```svg
<rect x="100" y="300" width="900" height="220" rx="10" fill="none" stroke="#334155" stroke-width="1.5" stroke-dasharray="8,4"/>
<text x="120" y="322" fill="#94a3b8" font-family="JetBrains Mono" font-size="10" letter-spacing="2">CONTROLRUNTIME</text>
```

左上角放大写字母 label + letter-spacing，SaaS 控制台的典型做法。

## LEGEND 图例

右下角固定放图例，便于读者对照连线颜色：

```svg
<g transform="translate(100, 690)">
  <text x="0"   y="0" fill="#475569" font-family="JetBrains Mono" font-size="9" letter-spacing="1">LEGEND</text>
  <line x1="80"  y1="-3" x2="110" y2="-3" stroke="#22d3ee" stroke-width="1.5"/><text x="115" y="0" fill="#94a3b8" font-family="JetBrains Mono" font-size="9">HTTP/RPC</text>
  <line x1="200" y1="-3" x2="230" y2="-3" stroke="#a78bfa" stroke-width="1.5"/><text x="235" y="0" fill="#94a3b8" font-family="JetBrains Mono" font-size="9">etcd write</text>
  <line x1="320" y1="-3" x2="350" y2="-3" stroke="#fb7185" stroke-width="1.5" stroke-dasharray="4,3"/><text x="355" y="0" fill="#94a3b8" font-family="JetBrains Mono" font-size="9">etcd watch</text>
  <line x1="440" y1="-3" x2="470" y2="-3" stroke="#34d399" stroke-width="1.5"/><text x="475" y="0" fill="#94a3b8" font-family="JetBrains Mono" font-size="9">data-plane RPC</text>
</g>
```

## 反复出现的手法

1. **层标签大写**：`<text fill="#475569" font-size="10" letter-spacing="2">EXTERNAL</text>`——留 30px 左边距、竖向排布、字距宽。
2. **盒内分隔线**：标题/副标题区和条目区之间，`<line stroke="#1e293b" stroke-width="1"/>`。
3. **周期事件**用 amber，一次性事件用 violet：和 `.pill.periodic` / `.pill.onetime` 呼应。
4. **标题不要带句号**，条目一行一句，避免折行。

避免用 `<foreignObject>` 嵌入 HTML——保持纯 SVG，方便后续 PNG 导出。

---

## 控制流 / IO 路径流程图（泳道式）

第 3 章里用来讲"一次请求从进到出"的泳道图。画布默认 `viewBox="0 0 1100 620"`（层少时 560，层多时 720）。

### 泳道划分

泳道语义 = "执行者边界"。常见组合：

- 系统内部：`KERNEL / IO THREAD / MAIN THREAD / BIO THREAD`
- 单体 HTTP 服务：`CLIENT / API / SERVICE / DB / CACHE`
- 微服务链路：`CLIENT / GATEWAY / UPSTREAM / DOWNSTREAM / MQ`
- 离线管道：`CRON / WORKER POOL / STORAGE / NOTIFY`

把大写泳道名放在左侧 30px 处，用横向虚线分隔：

```svg
<text x="30" y="60"  fill="#475569" font-family="JetBrains Mono" font-size="10" letter-spacing="2">KERNEL</text>
<line x1="130" y1="120" x2="1080" y2="120" stroke="#334155" stroke-width="0.8" stroke-dasharray="3,3"/>
<text x="30" y="180" fill="#475569" font-family="JetBrains Mono" font-size="10" letter-spacing="2">IO THREAD</text>
<line x1="130" y1="250" x2="1080" y2="250" stroke="#334155" stroke-width="0.8" stroke-dasharray="3,3"/>
```

### 步骤编号

每条连线旁加 ①②③… 编号，让读者能按顺序阅读全流程：

```svg
<line x1="220" y1="95" x2="220" y2="148" stroke="#22d3ee" stroke-width="1.5" marker-end="url(#ioArrCyan)"/>
<text x="240" y="125" fill="#22d3ee" font-family="JetBrains Mono" font-size="9">① readable</text>
```

### 连线语义

- 实线 + 同步色（青/绿）：同步 IO / 主路径。
- 虚线 + rose / amber：异步 fan-out（持久化、复制、后台任务）。
- 细虚线（灰）+ 无箭头：心跳 / 弱耦合。

### LEGEND

右下 LEGEND 要至少解释 "同步 IO / 主线程 / 异步 / propagate fan-out" 四类线型。

---

## 异步任务时序图（UML 风格）

第 3 章里用来讲"fork 子进程 / 主从复制握手 / 故障切换 / 后台 GC / 消息队列投递"等跨执行者协作。每张图聚焦**一个**异步子系统。画布默认 `viewBox="0 0 1100 780"`（分支多时到 860）。

### Actor 头 + lifeline

每个 actor 顶部一个语义色方块，正下方一条竖向虚线 lifeline 贯穿全图：

```svg
<!-- Actor header -->
<rect x="80" y="40" width="160" height="40" rx="6" fill="#0f172a"/>
<rect x="80" y="40" width="160" height="40" rx="6" fill="rgba(20,83,45,0.35)" stroke="#34d399" stroke-width="1.5"/>
<text x="160" y="65" fill="white" font-family="Inter" font-size="12" font-weight="600" text-anchor="middle">Main thread</text>

<!-- Lifeline -->
<line x1="160" y1="80" x2="160" y2="750" stroke="#334155" stroke-width="0.8" stroke-dasharray="4,4"/>
```

颜色约定与架构图一致：主线程 emerald / 子进程 violet / 外部客户端 slate / 内核 slate / 异步线程或副本 rose、amber。

### 消息箭头

```svg
<!-- Synchronous call: solid + marker -->
<line x1="180" y1="155" x2="598" y2="155" stroke="#64748b" stroke-width="1.5" marker-end="url(#seqArr)"/>
<text x="200" y="148" fill="#e2e8f0" font-family="JetBrains Mono" font-size="10">fork()</text>

<!-- Reply / async data: dashed -->
<line x1="578" y1="315" x2="222" y2="315" stroke="#34d399" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#seqArrEmerald)"/>
<text x="240" y="309" fill="#34d399" font-family="JetBrains Mono" font-size="10">backlog[offset+1..tail]</text>
```

在左侧 30-50px 空白区用 `t1 / t2 / t3 …` 给每一步打时间戳标签。

### 阻塞窗口（activation）

当某个 actor 在一段时间里"占用 CPU / 持有锁 / 挂起"时，在其 lifeline 上覆一个同色半透明矩形：

```svg
<rect x="360" y="195" width="40" height="140" fill="rgba(67,20,76,0.3)" stroke="#a78bfa" stroke-width="1"/>
```

这比单纯画箭头更能传达"此时这边在忙"。

### 决策分支

用小型菱形 + 两条不同颜色的外出箭头表示"命中 / 未命中"的分叉：

```svg
<polygon points="580,195 620,220 580,245 540,220" fill="rgba(251,191,36,0.15)" stroke="#fbbf24" stroke-width="1.5"/>
<text x="580" y="217" fill="#fbbf24" font-family="Inter" font-size="10" font-weight="600" text-anchor="middle">match?</text>
<text x="640" y="215" fill="#34d399" font-family="JetBrains Mono" font-size="10">yes (partial)</text>
<text x="640" y="250" fill="#fb7185" font-family="JetBrains Mono" font-size="10">no (full)</text>
```

### 阶段分组

图太长时用 Phase 徽章 + 水平分割线切分：

```svg
<rect x="40" y="95" width="70" height="30" rx="4" fill="rgba(34,211,238,0.08)" stroke="#22d3ee" stroke-width="1"/>
<text x="75" y="114" fill="#22d3ee" font-family="JetBrains Mono" font-size="10" font-weight="600" text-anchor="middle">PHASE A</text>
<line x1="30" y1="395" x2="1070" y2="395" stroke="#fb7185" stroke-width="1" stroke-dasharray="2,6" opacity="0.5"/>
<text x="550" y="390" fill="#fb7185" font-family="JetBrains Mono" font-size="9" letter-spacing="2">— OR —</text>
```

阶段典型命名：`HANDSHAKE / PARTIAL / FULL RESYNC / STEADY`，或 `SUBMIT / PROCESS / ACK / RETRY`。

### 异常 / 失败分支

用 rose 色虚线 + 底部 callout-like 矩形说明"断线 / 超时 / 回滚"：

```svg
<rect x="35" y="765" width="1040" height="40" rx="6" fill="rgba(251,113,133,0.05)" stroke="#fb7185" stroke-width="1" stroke-dasharray="4,3"/>
<text x="50" y="790" fill="#fb7185" font-family="JetBrains Mono" font-size="10">disconnect: replica reconnects → back to PHASE A with last known (replid, offset)</text>
```

### 并发活动提示

当主 actor 在"等异步子任务"时，用 amber 虚线箭头 + 斜体提示文字标注"这边仍在服务 / 累积 backlog"：

```svg
<line x1="580" y1="490" x2="260" y2="490" stroke="#fbbf24" stroke-width="1.2" stroke-dasharray="4,3"/>
<text x="300" y="484" fill="#fbbf24" font-family="JetBrains Mono" font-size="9">(master keeps serving clients, writes into backlog)</text>
```

### LEGEND

时序图的 LEGEND 至少解释 "actor 色 / 同步消息 / 异步消息 / 失败分支 / 心跳"。放在画布最底部 `translate(100, H-15)`。

### 检查表

画完一张时序图前先核对：

- [ ] 每个 actor 头都有语义色块 + Inter 标题。
- [ ] 每条 lifeline 都贯穿全图底部。
- [ ] 至少一个阻塞窗口用色块表达（证明你思考过"谁在忙"）。
- [ ] 所有分支（成功/失败）都画出，失败分支用 rose 色。
- [ ] 左侧有时间戳编号 t1..tN。
- [ ] 底部有 LEGEND。

---

## 内存布局条图（byte-strip）

用来讲"一次 malloc 里字段的实际排布"。画布 `viewBox="0 0 1060 H"`，H = 120（单行）~ 340（双行 + 多节点）。核心元件：一条水平条，里面紧贴着若干矩形方块，每个方块一个字段。

### 标准字段块

```svg
<rect x="0"  y="0" width="60" height="34" fill="#0f172a"/>
<rect x="0"  y="0" width="60" height="34" fill="rgba(52,211,153,0.2)" stroke="#34d399" stroke-width="1.2"/>
<text x="30" y="15" fill="#34d399" font-family="JetBrains Mono" font-size="10" text-anchor="middle">len:u8</text>
<text x="30" y="28" fill="#34d399" font-family="JetBrains Mono" font-size="8"  text-anchor="middle">1 byte</text>
```

两层 rect 是必须的：第一层 `#0f172a` 实底盖网格，第二层半透明语义色 + 描边。第一行字段名，第二行尺寸（`u8`/`u16`/`u32` 或 `1 byte` / `8 bytes`）。

### 颜色语义（字段分类）

| 颜色 | 含义 |
|---|---|
| `rgba(8,51,68,.4)` + 青 stroke | 头部 / 元数据位域（type、flags、refcount） |
| `rgba(52,211,153,.2)` + 绿 stroke | 基础数据字段（len、alloc） |
| `rgba(251,191,36,.2)` + 琥珀 stroke | flags / 枚举位 |
| `rgba(167,139,250,.2)` + 紫 stroke | TTL / 时间戳 / 过期 |
| `rgba(61,7,47,.35)` + 玫瑰 stroke | 内嵌 key / 载荷数据 |
| `rgba(30,41,59,.5)` + slate stroke | value 区 / 中性缓冲 |
| `rgba(20,83,45,.3)` + 绿 stroke | 指针（`*ptr`） |

### 多变体并排（如 sdshdr8/16/32）

把多个变体竖向堆叠，左侧 labels 用 `font-family="JetBrains Mono" font-size="10"`，右侧同一起点 `x=170` 绘制字段条。宽度根据字段字节数按比例——让"32 位变体"看起来就比"8 位变体"宽。

### 内嵌区的强调

把"这几个字段是同一次 malloc 的"用一条底部绿色虚线连起来：

```svg
<line x1="240" y1="178" x2="640" y2="178" stroke="#34d399" stroke-width="1" stroke-dasharray="3,3"/>
<text x="440" y="194" fill="#34d399" font-family="JetBrains Mono" font-size="10" text-anchor="middle">一次 malloc 同时拿下 header + key</text>
```

### 多级结构（如 skiplist）

多层水平线 + 节点圆圈 + 连接线，每层用不同颜色：

```svg
<text x="-20" y="30" fill="#fb7185" font-family="JetBrains Mono" font-size="10">L3</text>
<line x1="0" y1="25" x2="800" y2="25" stroke="#1e293b" stroke-width="1"/>
<circle cx="0" cy="25" r="8" fill="#0f172a" stroke="#fb7185" stroke-width="1.5"/>
<line x1="8" y1="25" x2="352" y2="25" stroke="#fb7185" stroke-width="1.5"/>
<!-- repeat for L2, L1; L1 is densest -->
```

高层用 rose / amber / emerald 渐次，最底层最密。

### 链表节点 + 压缩分区

双向链表节点把指针/标志/载荷做成一个小方框 + 一条 `*prev *next` 文字行，节点之间用灰色箭头：

```svg
<rect x="280" y="70" width="170" height="90" rx="6" fill="#0f172a"/>
<rect x="280" y="70" width="170" height="90" rx="6" fill="rgba(52,211,153,0.15)" stroke="#34d399" stroke-width="1.2"/>
<text x="365" y="108" fill="#34d399" font-family="JetBrains Mono" font-size="9" text-anchor="middle">*prev  *next</text>
<!-- 压缩节点改 rgba(167,139,250,.15) + violet stroke -->
<line x1="450" y1="115" x2="479" y2="115" stroke="#64748b" stroke-width="1.2" marker-end="url(#mArr)"/>
```

### 检查表

- [ ] 条宽与字节数成比例？
- [ ] 每个字段有名字 + 尺寸两行？
- [ ] 内嵌区有底部虚线 + "一次 malloc" 标注？
- [ ] 颜色语义和其他图一致（指针都是绿 / 过期都是紫 / flag 都是琥珀）？

---

## Ring Buffer（环形缓冲）可视化

用来讲 replication backlog、WAL buffer、slot-migration queue 这类"固定大小 + head/tail 游标 + 多 consumer"的结构。

### 骨架

```svg
<!-- backlog strip (长条) -->
<rect x="0" y="0" width="1000" height="60" rx="6" fill="rgba(30,41,59,0.4)" stroke="#334155"/>

<!-- used segments (可绕回两段) -->
<rect x="0"   y="0" width="280" height="60" fill="rgba(52,211,153,0.18)" stroke="#34d399"/>
<rect x="640" y="0" width="360" height="60" fill="rgba(52,211,153,0.18)" stroke="#34d399"/>

<!-- overwritten gap -->
<rect x="280" y="0" width="360" height="60" fill="rgba(61,7,47,0.15)" stroke="#fb7185" stroke-dasharray="3,3"/>

<!-- head / tail markers (竖线 + 标签) -->
<line x1="1000" y1="-8" x2="1000" y2="68" stroke="#22d3ee" stroke-width="2"/>
<text x="1000" y="-14" fill="#22d3ee" font-size="10" text-anchor="middle">head / offset</text>

<!-- consumer cursors (下方小圆 + 标签) -->
<circle cx="720" cy="80" r="6" fill="#a78bfa"/>
<text   x="720" y="100" fill="#a78bfa" font-size="9" text-anchor="middle">consumer-A</text>
```

三要素：① 环形条（用矩形展开）；② head / tail 双竖线标记；③ 多 consumer 的当前位置用 violet 小圆点标注在条下方。

### 三条必写的说明文字

在条下方留三行正文：
1. "命中条件"（什么样的 offset 能续传）；
2. "大小估算公式"（通常是 `T × W` 最慢 consumer 断连时间 × 生产速率）；
3. "failover / epoch 影响"（如 replid2 保留一轮让旧副本续传）。

---

## 版本演进时间线（timeline bar）

用在 § 3.N 版本演进章。画布 `viewBox="0 0 1060 140"`。一条水平主线 + 8 个圆点里程碑 + 每点上下各一行文字（上标版本号，下标日期）。

### 骨架

```svg
<line x1="60" y1="80" x2="1020" y2="80" stroke="#334155" stroke-width="2"/>

<circle cx="200" cy="80" r="7" fill="#0f172a" stroke="#22d3ee" stroke-width="1.5"/>
<text x="200" y="105" fill="#94a3b8" font-family="JetBrains Mono" font-size="9" text-anchor="middle">2022-04</text>
<text x="200" y="63"  fill="#22d3ee" font-family="JetBrains Mono" font-size="9" font-weight="700" text-anchor="middle">7.0</text>
```

### 颜色分代

把 release 分成"早期 / 主线 / 当前"三代，每代一个语义色。典型：

- `slate`（#94a3b8）：最早的、不再主推的旧版。
- `cyan`：引入多线程 / 重大协议变化的里程碑。
- `emerald`：现役稳定版。
- `violet`：架构性改写（独立 event loop、双通道复制等）。
- `amber`：仍在迭代 / pre-GA。

最新 GA 版本圆点 `stroke-width="2"` 加粗以区分。

### 检查表

- [ ] 横轴按时间均匀分布，不按版本号等距？
- [ ] 每个节点上下各一行（版本号 + 日期）？
- [ ] 颜色分代能让读者一眼看出"这个版本属于哪一波演进"？
