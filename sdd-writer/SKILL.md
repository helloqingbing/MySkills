---
name: sdd-writer
description: Write a software design document (SDD) in the ccmanager dark-theme style — a single self-contained HTML file with six fixed chapters (总览 / 概要设计 / 详细设计 / 测试场景与覆盖度 / AI 辅助工程实践 / 优劣点), a sticky right-side scroll-spy navigation, SVG architecture diagrams on a dotted-grid canvas, card/panel/table/scoreboard components in a slate-blue palette, and a final scoring section with dimension bars. Trigger this skill whenever the user asks for 软件设计文档 / SDD / 架构设计文档 / system design document / technical design doc / 设计说明书, or mentions writing a design doc "in the ccmanager style" / "same style as ccmanager-sdd" / "像 ccmanager 那个文档那样". Also trigger when the user asks to refactor or reformat an existing design document into a structured chaptered form with side navigation and scoring, or to add chapters like 核心不变式 / 测试覆盖度矩阵 / AI 协作章节 / 综合评分 to a doc. Prefer this skill over generic "write docs" responses whenever the user wants a single-file, dark-themed, visually distinctive design document.
---

# SDD Writer — ccmanager-style software design document

这个 skill 生成一种很具体的软件设计文档：**单文件 HTML、暗色主题、六章结构、侧栏滚动导航、SVG 架构图、最终带综合评分**。原型是 `docs/architecture/ccmanager-sdd.html`，整篇 1900 行、自包含、可直接 `open` 于浏览器。

## 什么时候用

读者让你写"设计文档 / SDD / 架构设计 / technical design"，而且愿意接受一个 **HTML 单文件** 作为交付物时用这个 skill。需要交付 Markdown 给 Confluence / GitHub Wiki 的场景**不用**这个 skill。

如果读者只是让你给一张架构图，用 `architecture-diagram` 或 `drawio` skill。本 skill 的核心价值是**把架构图放进一整套标准化的叙事骨架里**。

## 产出形态

一个 HTML 文件，默认文件名 `<project>-sdd.html`，默认路径 `docs/architecture/`。打开后应该具备：

1. 顶部带脉冲绿点的项目标题 + 副标题 + 三项元信息（项目/语言/存储）。
2. 左侧主内容 + 右侧 260px 固定侧栏，宽 ≤1024px 时侧栏隐藏。
3. 六章按固定顺序排列，每章用 `第 N 章` 横幅 + 若干带青色 section-num 药丸的小节。
4. 侧栏当前章节高亮（IntersectionObserver 驱动，脚本已在模板末尾）。
5. 至少一张 SVG 架构图（第 2.1 节），画在 1100×720 的点阵网格画布上。
6. **第 3 章必须内嵌至少 2 张补充 SVG 图**：一张"核心控制流 / IO 路径流程图"（泳道式，展示线程 / 进程边界），以及若干"异步任务时序图"（每个重要异步子系统一张——持久化 fork、复制握手、故障切换、后台 GC 等）。只要系统存在跨线程 / 跨进程 / 跨节点的协作，就必须画；单进程纯同步系统才可豁免。
7. **第 3 章应包含"数据结构内存布局"小节**：对系统里每一种可变尺寸 / 编码多态的核心结构体画**字节条图**（byte-strip），展示一次 malloc 的字段顺序、位域、内嵌区。存储类 / 数据库 / 协议解析器尤其要有。
8. **第 3 章末尾强烈建议设置"§ 3.N 版本演进"章**：按版本时间线 + 四维变更表（结构 / 网络 / 性能 / 新命令 or 新 API）+ 设计总结卡组。让读者一眼看懂"这个系统 3-5 年来在往哪走"。
9. **第 3 章最后一节必须是"§ 3.M 配置参数速查"**：把所有运维要接触的配置（命令行 flag / env var / yaml / .conf）按主题分 7-10 组打表列出，每组一个 `<h3>` + `<table>`，四列："参数 / 默认值 / 说明 / 调优提示"。<span class="tag amber">hot</span> 标签标出"默认值在多数生产环境都要改"的参数。
10. **§ 2.2 核心模块与依赖必须同时包含"模块速览"卡片和"源码目录树"**：前者（2.2.1）用 `card-grid` 列 8-12 张模块卡，每张卡一句话职责；后者（2.2.2）用 `<div class="tree">` 画顶层目录树，按"公有 API → 核心主干 → 存储格式 → 系统抽象 → 扩展 / 工具"层次铺开，每条目带 `← / ·` 注释指明功能与代表类/行数，末尾一段总结"新增能力该放哪"的经验规则。卡片告诉读者"有哪些模块"，目录树告诉读者"文件在哪、改动该落在哪里"——两者互补，缺一不可。
11. 第 4 章测试章、第 6 章优劣点章各有一个"左大分 + 右维度条"的 scoreboard。

## 工作流程

### 第 1 步 · 定位并读取资料

先摸清楚要写哪个系统的 SDD。通常需要：

- 项目根目录（用 `pwd` 或读者给出）。
- 核心源码入口（`main.go` / `app.py` / `src/index.ts`）。
- 已有文档（`README.md`、`CLAUDE.md`、`docs/`）。
- 测试目录，判断覆盖度。
- 最近 10-20 条 git log，用于第 5.5 节的证据。
- **固定代码版本快照**（必须）：跑一次 `git rev-parse --short HEAD`（取 commit hash）、`git log -1 --format=%ci`（取 commit date）、以及项目版本文件（`src/version.h` / `package.json` / `Cargo.toml` / `VERSION`）的值。这三个值写进 header meta-line 与 § 3.8 版本演进章，让读者知道"这份文档是基于哪个 snapshot 写的"，避免文档与源码随时间漂移时无法判断对错。

不要猜。信息不够就问读者，或者让 Explore agent 先跑一遍。

### 第 2 步 · 复制模板 & 填写 header

```bash
cp ~/.claude/skills/sdd-writer/assets/template.html <project>/docs/architecture/<project>-sdd.html
```

然后替换 header 占位符：`{{PROJECT_NAME}}` / `{{SUBTITLE}}` / `{{PROJECT_SLUG}}` / `{{LANG}}` / `{{STORAGE}}` / `{{VERSION}}` / `{{COMMIT_SHORT}}` / `{{COMMIT_DATE}}`。subtitle 用 ` · ` 分隔 3-5 个关键词，像技术标语那样。

**防漂移规则**：所有"引用特定行号 / 特定 PR / 特定结构体"的描述，都默认以 `{{COMMIT_SHORT}}` 为准。正文里提到"见 <code>src/foo.c:123</code>"时，心里就要记住"在 COMMIT_SHORT 时该行是 XXX 函数"——之后 rebase 后行号会飘，但有 header 的 commit 标识，读者能自己对应回去。

### 第 3 步 · 按章节顺序写内容

章节顺序 **不要调整**。每章的"该写什么、长度、推荐组件"详见 `references/chapters.md`。写之前先过一遍 playbook。

常见失误：
- 1.3 核心不变式写成"实现细节"——它应该是**能被后面所有章节回指**的系统性事实。
- 3.x 贴大段代码——每块 `<pre>` 控制在 30 行以内，给签名和核心循环。
- 4.2 场景矩阵打分失衡——全 9+ 失去参考意义，要让 5-6 分的弱项真实出现。
- 6.3 综合评分没有支撑——每一维打分都应该能在 6.1/6.2 找到对应条目。

### 第 4 步 · 画架构图与流程/时序图

**至少产出三类 SVG**（都画在同一套点阵网格 + 四色连线 + LEGEND 的风格里）：

1. **§ 2.1 分层架构图** — 必须画。系统的四层全景快照。画布 1100×720。
2. **§ 3.x 控制流 / IO 路径流程图** — 必须画至少一张。用**泳道**表达线程 / 进程 / 节点边界（例如 KERNEL / IO THREAD / MAIN THREAD / BIO THREAD），把一条典型请求从进到出的每一步按编号 ①②③… 标出，让读者一眼看清"谁在哪一步做了什么"。插入位置通常是"网络 / 事件循环 / 请求处理"那节的末尾，配 `<h3>N.x.y 控制流</h3>` 小节引出。
3. **§ 3.x 异步任务时序图** — 只要系统有任何异步协作（fork 子进程、主从复制、消息队列、后台 GC、选举、双写、外部回调）就必须为每一个画一张。用 UML 风格的生命线（actor 头 + 虚线 lifeline + 带箭头的消息），把"阻塞窗口、并发活动、心跳、失败分支"全部画出来。插入位置在对应模块小节的末尾。

判断"要不要多画一张"的唯一标准：**读者看完文字后仍要问"谁先谁后？阻塞在哪？哪里可以并行？"** — 只要会问，就要画。

SVG 的画布规格、配色语义、节点/连线/分组框/图例、泳道与时序图的标准写法，全部在 `references/svg-diagram.md`。点阵网格 + 统一语义色 + 右下 LEGEND 是这套视觉的签名，每张图都要带，别偷懒省略。

### 第 5 步 · 维护侧栏

模板末尾的 `<aside class="side-nav">` 已经预置好六章的锚链接。**改 section 结构时同步改侧栏**：

- section 的 `id` 保持 stable ID（`ov-*` / `hld-*` / `dd-*` / `ts-*` / `ai-*` / `pros/cons/scoring/verdict`）。
- 新增 3.x 模块小节 → 在侧栏第 3 章的 `<ul>` 里加一个 `<li>`，`nav-num` 填 3.N。
- 页面末尾 scroll-spy 的 JS 不用动。它会自动做三件事：① 为所有有 id 的 section 建 IntersectionObserver；② <strong>从正文扫每个 section 的 `<h3>`</strong>，动态生成侧栏的三级子列表 `<ul class="sub">`；③ 当前 section 激活时把它的 li 加 `.sec-active` 自动展开子列表，离开则折叠。

**三级导航的约束**（写正文时要守住这几条）：

- <strong>h3 必须是 section 的直接子元素</strong>（`section > h3`）。不要把 h3 套进 `<div>`、`<details>` 等容器里，否则 scroll-spy 的 `:scope > h3` 抓不到。
- h3 文本开头用 `N.N.N 标题` 格式（三级编号 + 空格 + 标题）。脚本会用正则 `^(\d+(?:\.\d+)+)\s+(.*)$` 拆成"编号 + 标签"分别渲染。编号不写也能跑，但侧栏就只剩标题。
- h3 的 `id` 不必手写，脚本会按 `<section-id>-h3-<N>` 兜底。但如果你想让外链稳定，**手动给关键 h3 写 id** 更可靠（例如 `id="dd-object-layout"`）。
- h3 数量建议控制在每节 3–10 条；超过 10 条考虑拆成更多 h2。侧栏展开高度上限 `max-height: 60rem`，再多会截断。

### 第 6 步 · 打开检查

```bash
# Linux / macOS
xdg-open <path>.html 2>/dev/null || open <path>.html
```

检查项：
- 侧栏滚动 spy 随滚动正确高亮？
- 1024px 以下侧栏是否隐藏（用浏览器 DevTools 缩窗口试）？
- 架构图里没有网格从矩形透出（每个 rect 要先铺 `#0f172a` 实底再覆语义色）？
- 所有 `{{...}}` 占位符是否都替换完了？可以 `grep -n "{{" <path>.html` 确认。
- **离线可读**：文件里没有任何 `http://` / `https://` 资源依赖（字体、CDN、图标）。`grep -n "https://" <path>.html` 只该返回文档性 URL（如作者个人主页），不该有 `link rel="stylesheet"` 类外链。模板已改为纯系统字 fallback。
- **SVG 可达性**：每张 `<svg>` 都有 `role="img"` + `<title>` + `<desc>`——`grep -c 'role="img"'` 应等于 `grep -c '<svg viewBox'`。
- **源码版本钉死**：header meta-line 含源码版本 + commit short + 日期。事实类断言（文件行数、结构体字段、函数名、PR 号）都能映射回 header 上的 commit。

## 参考文件（按需读取）

- `assets/template.html` — 完整骨架，直接 `cp` 后编辑。所有 CSS、侧栏、scroll-spy JS 全齐。
- `references/chapters.md` — 六章写作 playbook，填内容前读。
- `references/components.md` — 组件速查（card / panel / table / scoreboard / callout / pill / tag），抄 HTML 用。
- `references/svg-diagram.md` — SVG 架构图的画布、配色、节点、连线、图例配方。

## 风格底线（Why matters）

这套文档的识别度来自**几个不妥协的细节**，如果丢掉其中之一就不再是 ccmanager 风格：

1. **section-num 药丸**：每个 h2 小节标题都必须带 `<span class="section-num">N.N</span>`。这是视觉 DNA。
2. **JetBrains Mono 用于所有技术字**：章节号、代码、表头、侧栏编号、大分值。与 Inter 正文形成对比。
3. **暗蓝色渐变背景**：两束 radial-gradient（青色 + 紫色）打在 `#020617` 深蓝上。不要换成纯黑或白底。
4. **网格 SVG 画布**：所有架构图都要带点阵网格 pattern。这是"技术感"的来源。
5. **评分维度条**：scoreboard 的右侧是强语义组件——它让读者秒懂"这个系统在哪里强、在哪里弱"。不要用饼图或雷达图替换。

保留这五点，其他内容随项目自由调整。
