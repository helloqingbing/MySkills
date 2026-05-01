# 组件速查（Components Cookbook）

所有组件的 CSS 都在 `assets/template.html` 的 `<style>` 块里定义好了。这里只列出 HTML 结构与使用场景，直接复制即可。

## 章节骨架

每个章节（chapter）对应一个"第 N 章"的大号横幅 + 若干 section。小节（section）必有 `id`，供右侧 side-nav 锚定。

```html
<div class="chapter">
  <div class="chapter-head">
    <span class="chapter-num">第 3 章</span>
    <h2>详细设计</h2>
  </div>

  <section id="dd-cm">
    <h2><span class="section-num">3.1</span>ClusterManager</h2>
    <h3>3.1.1 数据结构</h3>
    <p>...</p>
  </section>
</div>
```

- `section-num` 是那个高亮的青色小药丸，是这套文档的视觉签名。**每个 h2 小节标题都必须带**。
- 三级标题 `<h3>` 不带药丸，内文直接用 `3.1.1 数据结构` 的文字编号即可。侧栏 scroll-spy 会**自动**把 `section > h3` 抓出来注入为三级子条目（见 SKILL.md 第 5 步的三级导航约束）——所以 h3 必须是 section 的<strong>直接子元素</strong>，且开头写 `N.N.N 标题` 的编号格式。

## 两栏面板（In Scope / Out of Scope）

```html
<div class="two-col">
  <div class="panel">
    <h4 style="margin-top:0; color:var(--emerald)">In Scope（本系统负责）</h4>
    <ul><li>...</li></ul>
  </div>
  <div class="panel">
    <h4 style="margin-top:0; color:var(--rose)">Out of Scope（本系统不负责）</h4>
    <ul><li>...</li></ul>
  </div>
</div>
```

## 卡片网格（card-grid）

默认 3 列自适应，最小宽度 260px。强制 1 列（行排列）用 `style="grid-template-columns: 1fr"`。

```html
<div class="card-grid">
  <div class="card" style="--accent: var(--emerald)">
    <div class="card-title">Ownership 唯一性</div>
    <div class="card-desc">...</div>
  </div>
</div>
```

`--accent` 变量控制左侧 3px 色条，推荐配色：
- `var(--emerald)` 绿：正向主线、强项、数据面
- `var(--cyan)` 青：网络 / IO / 并发
- `var(--violet)` 紫：存储 / CAS / 写入
- `var(--amber)` 黄：警示 / 阈值 / 评审
- `var(--orange)` 橙：事件 / 异步
- `var(--rose)` 玫瑰：劣势 / 失败路径

需要大号数字（metric 卡）时加 `<div class="card-metric">9.2</div>` 在标题和描述之间。

## 表格

**始终**把表格包在 `<div class="panel" style="padding:0">` 里，这样圆角和边框由 panel 提供，table 只负责排版。

```html
<div class="panel" style="padding:0">
  <table>
    <thead><tr><th>#</th><th>场景</th><th style="text-align:right">评分</th></tr></thead>
    <tbody>
      <tr><td>1</td><td class="scene">集群 Hash 分配</td><td class="score">9.0</td></tr>
    </tbody>
  </table>
</div>
```

表格 td class 配色约定：
- `scene` / `path` 紫色（模块名、场景名、代码路径）
- `method` 绿色右对齐（HTTP 方法、函数签名）
- `key` 琥珀色（配置 key、术语）
- `score` 右对齐绿色；加 `.mid` 变琥珀，加 `.low` 变玫瑰
- `ok` 绿 / `no` 玫瑰

## Callout（引用块）

```html
<div class="callout emerald"><strong>核心优势：</strong>...</div>
<div class="callout amber"><strong>注意：</strong>...</div>
<div class="callout rose"><strong>严重风险：</strong>...</div>
<div class="callout"><strong>补充：</strong>默认青色</div>
```

## Pill（小徽章）

用于周期/一次性标记、HTTP 方法：

```html
<span class="pill periodic">PERIODIC · 2s</span>
<span class="pill onetime">ONE-TIME</span>
<span class="pill get">GET</span>
<span class="pill post">POST</span>
```

## Tag（分类标签）

用于覆盖度刻度、状态分类，比 pill 更"轻"：

```html
<span class="tag green">9-10 端到端</span>
<span class="tag cyan">7-8 主路径</span>
<span class="tag amber">5-6 单元级</span>
<span class="tag rose">&lt;5 不足</span>
```

## 评分板（scoreboard）

左侧大分 + 右侧维度条，第 4 章和第 6 章各用一次。

```html
<div class="scoreboard">
  <div class="overall-score">
    <div class="overall-label">综合评分</div>
    <div class="overall-value">8.6</div>
    <div class="overall-denom">/ 10.0</div>
    <div class="grade-badge">A · 生产就绪</div>
  </div>
  <div class="dim-grid">
    <div class="dim-row">
      <div class="dim-name">架构合理性</div>
      <div class="dim-bar-outer"><div class="dim-bar-inner" style="width:90%"></div></div>
      <div class="dim-score">9.0</div>
    </div>
    <!-- 重复 dim-row -->
  </div>
</div>
```

- `dim-bar-inner` 的 `width` 填 `score × 10 %`。
- 第 4 章（测试）推荐维度：场景广度 / 时序并发断言 / 幂等恢复 / 故障边界 / e2e 集成 / 性能基线。
- 第 6 章（综合）推荐维度：架构合理性 / 可扩展性 / 可靠性 / 可观测性 / 可维护性 / AI 工程协作。

## 代码块

```html
<pre><code>go test ./...</code></pre>
```

不要在 `<pre>` 前加缩进——`white-space: pre` 会把缩进渲染出来。

## 目录树（tree）

```html
<div class="panel">
  <div class="tree">
<span class="dir">ccmanager/</span>
├── <span class="dir">internal/</span>
│   ├── framework/   <span class="note">← 三引擎</span>
│   └── domain/
└── main.go
  </div>
</div>
```

## 头部 header

整篇文档只有一个 header，位于 `<main>` 顶部：

```html
<header class="header">
  <div class="header-row">
    <div class="pulse-dot"></div>
    <h1>CCManager 软件设计文档</h1>
  </div>
  <div class="subtitle">Redis / RedKV 双数据面控制平面 · 事件驱动</div>
  <div class="meta-line">
    <span>项目：<strong>ccmanager</strong></span>
    <span>语言：<strong>Go 1.22</strong></span>
    <span>存储：<strong>etcd v3</strong></span>
  </div>
</header>
```

subtitle 用 `·` 分隔要点，给人"技术标语"的感觉。meta-line 是三项固定信息，可按项目调整 label。

## Rowspan 分组表（版本演进 / 命令速查必用）

"同一主题下多条命令 / API" 的场景，用 `rowspan` 合并主题列，避免重复读。每组之间加 `<tr>` 的背景色变化可选。

```html
<div class="panel" style="padding:0">
  <table>
    <thead><tr><th>主题</th><th>命令</th><th>引入版本</th><th>说明</th></tr></thead>
    <tbody>
      <tr>
        <td class="scene" rowspan="3">Hash Field Expiration</td>
        <td class="key">HEXPIRE key sec FIELDS n f1..</td>
        <td>7.4</td>
        <td>按字段设秒级 TTL</td>
      </tr>
      <tr><td class="key">HPEXPIRE ...</td><td>7.4</td><td>毫秒</td></tr>
      <tr><td class="key">HEXPIREAT ...</td><td>7.4</td><td>绝对时间</td></tr>
    </tbody>
  </table>
</div>
```

规则：
- `rowspan` 的 `<td>` 一定放 `class="scene"`（紫色）或 `class="key"`（琥珀），语义最强。
- 合并数 ≥ 3 才划算；只有 2 行时不要合并。
- 建议按主题分组的表用在 § 3.N 版本演进 / 新命令速查 / 策略选型这三类场景。
