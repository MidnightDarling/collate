# constellatio · viewer spec

美学、技术规范、Latin 约定。做暗夜星图 viewer 时读这一份。
散文例子见 `example-may-fourth.md`;canonical HTML 见 `example-may-fourth.html`。

---

## 什么时候做星图

散文分析是完整交付物。星图可选,只在以下条件同时满足时做:

- 现象有 3+ 种读法,分歧可以在同一组事件上做视觉比较 — 同样的点,
  不同的连法、不同的明暗。
- 视觉叠加本身能揭示散文需要绕弯才能说的东西 — 三代的选择叠在一起,
  共同的沉默或共同的强调一目了然。
- 读者有时间坐下来看。星图不适合做缩略图或幻灯片嵌入。

不做的情况:

- 只有两种读法且只是互相矛盾 — 散文够了,没有第三种读法让眼睛做三角。
- 结论是"无法归结" — 把 aporia 画成图只会显得整洁,替你撒谎。
- 图会给散文中诚实地留有余地的判断加上虚假的确定性。

散文单独是完整交付物。星图单独不是。

## 三张图

| 图 | 内容 |
|----|------|
| **FIG I · Stellae Fixae** | 每个读法都必须包括的事实。一个场、所有标记全亮。底图。 |
| **FIG II · Constellationes Temporum** | 每种读法一个面板;同样的坐标,不同的连法和明暗。暖金色 = 肯定面板,冷银色 = 批评面板。 |
| **FIG III · Cartographia Comparata** | 所有连线淡淡叠加;标记压暗;跨时代反复出现的关切画成唯一的实心光晕。 |

FIG III 下方有一组小型标题文章(`.grav-grid`),每个跨时代关切一篇。
这些是图例说明,不是散文分析 — 保持简短。

通常 **2-3 个**跨时代关切光晕。超过三个通常是在凑数;只有一个也行,
但不要为了构图对称而发明第二个。

散文段落与 HTML 区域的对应:

| 散文段 | HTML 区域 |
|--------|-----------|
| 现象 | `<header class="hero">` |
| 不可压缩面 | `<section class="chart-wrap">` (FIG I) |
| 每代读法的诊断 | `<section class="duo-wrap">` (FIG II) |
| 屏幕属性 / 变迁追踪 | `<section class="overlay-wrap">` (FIG III) + `.grav-grid` |

星图没有"诊断"区域。读法即诊断、屏幕属性、变迁追踪 — 这些思考工作
只在散文里。

## 美学立场

**深空,不是书页。**

星图活在夜里。页面是天空,不是纸张。星点坐在近黑底色上。连线是细淡的
笔触;跨时代关切是暖金光晕;各代读法染暖或冷。奶油色墨水在暗底上读起来
像星光,不像印刷。

这是刻意的。kaozheng / chunqiu / real-thesis 处理散文,用纸页风格。
constellatio 处理的是跨时代的判断叠加,暗夜天空编码的就是这种横向、
档案式、多时代的工作形态。

### 不是什么

- 不是信息图。没有坐标轴、图例框、tooltip。读者要读,不是 hover。
- 不是对称的。读法确实偏心聚集;不要为了视觉平衡把标记往中间拉。
- 不是暖色调。底色近黑(#050812),暖金和冷银只作语义编码,不作氛围。
- 不是动画。星图是静态的。时代切换可以做交互;过渡和悬停效果不要。
- 不是极简。三张图、完整 SVG 线条、多个光晕、逐面板标记 — 画满,不省笔。

## 字体

| 角色 | 字族 | 字重 | 用途 |
|------|------|------|------|
| Hero / 层名 | Cinzel | 400-700 | 全大写 Latin 标题、层名、跨时代关切名 |
| Body Latin | Bodoni Moda | 400-600, italic | 英文叙述、时代标签、技术子标签 |
| Body 中文 | Noto Serif SC | 300-500 | 中文叙述、主阅读文本、星点注释 |
| Mono / meta | IBM Plex Mono | 300-400 | 坐标标签、FIG 序号、页脚 |

Cinzel 是石刻寄存器。Bodoni Moda italic 是百科全书寄存器 — 中立权威,
略带冷感。Noto Serif SC 让中文材料与 Latin 平权;中文不得降级为小号
注释字重。IBM Plex Mono 是测量 / 制图寄存器。

```html
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500;600;700&family=Bodoni+Moda:ital,opsz,wght@0,6..96,400;0,6..96,500;0,6..96,600;1,6..96,400;1,6..96,500;1,6..96,600&family=IBM+Plex+Mono:wght@300;400&family=Noto+Serif+SC:wght@300;400;500&display=swap" rel="stylesheet">
```

## 色板

语义轴:**肯定 ↔ 批评**。肯定当下现象的时代读法偏暖金;批评的偏冷银。
不变事实保持中性奶油。跨时代关切取偏暖奶油金光晕 — 它们是不变的,
不属于某一代。

```css
:root {
  /* 天空底色 */
  --bg-deep: #050812;  --bg-mid: #0A1228;  --bg-glow: #1A2547;
  /* 奶油墨水(星光) */
  --ink-1: #F4EDE0;  --ink-2: #C9C2B4;  --ink-3: #807A6E;  --ink-4: #4A4636;
  /* 肯定寄存器(暖金) */
  --gold: #E8C685;  --gold-soft: #C9A56A;
  /* 批评寄存器(冷银) */
  --silver: #B8C8E8;  --silver-soft: #8FA3C9;
  /* 线条 */
  --line-1: rgba(244,237,224,0.06);  --line-2: rgba(244,237,224,0.14);
}
```

不加额外强调色。暖和冷坐在同一张图上,让眼睛感受分歧 — 这就够了。

## 星图几何

- **星点** = 柔和径向渐变(`star-warm` 或 `cool-star`)+ 2-3.4px 实心
  奶油核心。标签在右侧 12px(或 `anchor="end"` 在左),Bodoni Moda
  italic 在上,Noto Serif SC 在下。
- **坐标全文档固定。** 同一个星点在 FIG I / II / III 的 `(x, y)` 相同。
  这种一致性让三图递进可读。移动标记来"让某一层好看"= 破坏图表。
- **亮度编码时代注意力,不编码绝对重要性。** 亮(radius 11-14, opacity
  0.7-0.85)= 这代在连这个星。暗(radius 6, opacity 0.6, `dim-star`)=
  这代拒绝连。同坐标,不同亮度。
- **连线。** 0.5-1.4px。暖金实线,冷银虚线(`stroke-dasharray="2 4"`)。
  图案 + 颜色一起携带信号 — 不要只靠颜色。
- **Terra Incognita**(每代拒绝触碰的区域)= 对角线条纹 `<pattern>`
  叠加,40-80% opacity,Cinzel UPPER 11px 标题。
- **跨时代关切光晕** 只出现在 FIG III。每个 = 三层径向渐变(外圈
  80-92px 50% opacity,中圈 44-46px 85%,核心 6px 实心奶油)。名称
  Cinzel UPPER 20-22px 在上;Latin gloss + 中文 gloss 在下。
- **SVG 手工绘制。** 不用 D3、Canvas、图表库。图足够小,手工布局强制
  对每个标记的位置做编辑判断。
- **渐变定义复用。** 每个 figure 定义一次 `<radialGradient>`:
  `star-warm`、`cool-star`、`dim-star`、`dim-star-c`、`nebula`、
  `grav-glow`、`revocatio-glow`。
- **每个面板的盲区。** FIG II 的每个面板标出该时代拒绝进入的区域。
  对角条纹 `<pattern>` 叠加,低 opacity,Cinzel UPPER 11px 标题,
  用 `--silver-soft` 或 `--gold-soft`。

## 间距

```css
:root {
  --letter-cinzel: 0.18em;  --letter-mono: 0.34em;
  --letter-bodoni: 0.02em;  --letter-noto: 0;
}
```

- 外容器:`max-width: 1480px; padding: 84px 6vw 60px;`
- 段间距:`padding: 0 6vw 80px;`
- 图间垂直间隔 60-84px。不要过度动画。
- Cinzel hero 字距 0.05em,层名字距 0.18-0.22em。图需要呼吸;不要拥挤。

## 字体层级

| 元素 | 字族 | 大小 | 字距 | 大小写 |
|------|------|------|------|--------|
| 现象 hero | Cinzel 500 | clamp(50px,8.4vw,116px) | 0.05em | UPPER |
| 副标题 | Bodoni Moda italic 400 | clamp(20px,2.4vw,32px) | n/a | 句首大写 |
| 层标签 (FIG I) | IBM Plex Mono 300 | 10px | 0.34em | UPPER |
| 层名 (Stellae Fixae) | Bodoni Moda italic 500 | 22px | 0.02em | 标题 |
| 面板名 (Illuminatio) | Bodoni Moda italic 500 | 32px | 0.02em | 标题 |
| 面板 meta (MCMLXXX) | IBM Plex Mono 300 | 10px | 0.34em | UPPER |
| 星点 Latin 标签 | Bodoni Moda italic 500 | 11-15px | 0 | 标题 |
| 星点中文标签 | Noto Serif SC 400 | 9-10px | 0 | n/a |
| 关切名 | Cinzel 500 | 20-22px | 0.22em | UPPER |
| 关切 Latin gloss | Bodoni Moda italic 500 | 11.5px | 0.02em | 句首大写 |
| 正文中文 | Noto Serif SC 400 | 13-14.5px | 0 | n/a |

层级反映视觉阅读顺序:层框架 → 时代框架 → 单个标记。

## Latin 约定

Latin 用作寄存器标记,不用作学识展示。它提供工作语言无法提供的结构距离 —
说"这是框架,不是主张"。

**为什么用 Latin:** 命名层跨越各代读法。工作语言会倾向它共享词汇的那种
读法。一旦一个层被叫做"基础读法"或"基本立场",它就已经站队了。Latin
死到足以中立;它不跟任何二十世纪的读法对齐。Latin 是框架。现象、星点、
时代名、关切描述 — 全部留在它们被思考时使用的语言里。

### 命名表

| 术语 | 用途 | 说明 |
|------|------|------|
| Stellae fixae | 每个读法都包含的星 | 来自天体力学。最稳定的层名。 |
| Constellationes temporum | 逐时代星座 | "各时代的星座"。每代画自己的。 |
| Cartographia comparata | 叠加层 | "比较制图" — 图之图。 |
| Polaris caveat | 反对虚假综合的警告 | 英文 + Latin,刻意双语;双语镜像警告本身。 |
| Gravitas | 引力核心 | 仅在引力是道德/政治重量时用;结构空缺用 "gravity"。 |

可选次级术语(少用):Stellae mobiles(移动星)、Stellae deficientes
(缺失星)、Aporia(希腊词,非 Latin,但古典且恰当 — 结论为"无法
解决"时保留)。

模式:`名词(+ 古典修饰词)`,有古典或中世纪 Latin 考证。两词短语优先;
一词可以;三词是上限。

### 避免

- **新造词。** 无考证术语 → 退回英文。发明 Latin 来填空格恰好是这个
  约定要防的失败模式。
- **呼格/祈使句式。** `Audi!` `Ecce!` — 永远不。Latin 在这里是冷的。
- **过度修饰。** 不能一行白话翻译 → 不用。
- **纯 Latin 输出。** 读者是中文历史学者。每个 Latin 层名首次出现时
  附白话 gloss。
- **伪 Latin 学术词。** `Constellatio quantica`、`Hermeneutica meta`
  — 闻到 19 世纪期刊分类法或 20 世纪大陆理论穿长袍的味道,就删。

> "如果一个 Latinist 会皱眉,重写。"

四个检查点:能否读出声;白话 gloss 是否比 Latin 更难写(是 → Latin
在做错误的工作);中文翻译是否别扭;术语排除了什么(层名应该让某些读法
不可说 — 让所有读法通过 = 不是层)。

## 从散文到星图 — 工作流

1. **从 canonical 例子开始。** `cp references/example-may-fourth.html
   <new>.html`。HTML 脚手架、SVG defs、CSS 已编码以上所有规范。
2. **替换现象名** — hero 里的 `.title`、`.subtitle`、`.coords-prose`、
   `.stats`。
3. **标记不可压缩事实** — FIG I。7-12 个标记。按事物本身定位,不按
   说法定位。坐标合理,让眼睛自然分组相关项。
4. **替换每个面板** — FIG II。每种读法一个面板。设 `.warm` 或 `.cool`
   class。更新时代标签、连线集、盲区标题。`.pane-stance` 是单句图表
   标题 — 永远不是分析段落。分析在散文里。
5. **渲染 FIG III 叠加** — 用散文识别出的跨时代关切做光晕。把各代的
   实际标记压暗作为背景;每个光晕放在它所捕捉的标记聚类的质心。
6. **替换 `.grav-grid` 标题** — 每个关切一篇 `<article>`。罗马数字、
   Latin 名、中文 gloss、一句标题。图例,不是分析 — 保持简短。
7. **测试。** 1280px(笔记本)和 768px(平板)。`@media (max-width:
   980px)` 把双栏和 grav-grid 折成单栏。

## 星图是什么、不是什么

- **不是海报。** 安静的器具,不需要标语或装饰。
- **不是散文的替代。** 散文做分析工作;星图和散文一起交付,永远不代替。
- **不是 skill 的应用。** 应用 skill 是散文里的思考行为。星图是散文
  已经分析过的读法的可视化。如果发现自己在标题空间里"应用 skill",
  就是把思考工作泄漏进标签空间了 — 推回散文。

## skill 名称

`constellatio`(第三变格名词,*constellatio, -onis, f.*)见于晚期
Latin 天文学("星的共聚")。是这个 skill 中唯一作为独立标识使用的
Latin 术语;其余 Latin 短语均附 gloss。skill 名携带寄存器;图的内部
标签不需要重复它。
