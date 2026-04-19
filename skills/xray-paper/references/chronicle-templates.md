# Chronicle shapes — a sampler

Each historical argument moves through time differently. Pick the shape that matches what the paper says about time — continuity, rupture, convergence, divergence, cycle, inheritance.

---

## 1 · Vertical axis (传统编年)

The oldest shape. Year at the left, event at the right. Compact, clean succession.

**Use when**: single-thread chronology, straightforward continuity or rupture.

```
1895 ┬─ 马关割台
     │
1898 ┼─ 戊戌变法 · 百日而终
     │
1905 ┼─ 废科举 · 革命派崛起
     │
1911 ┼─ 辛亥 · 帝制覆
     │
1915 ┴─ 新文化运动 · 知识界转向
```

---

## 2 · River (parallel streams)

Multiple strands — court / society / intellectual / economy — flow in parallel, converging and diverging across time.

**Use when**: social-political history with multi-domain resonance; papers arguing about how forces interlock.

```
年份     朝廷              士人                 地方
─────────────────────────────────────────────────────────
1860  ～洋务运动～～～      经世致用兴       ～太平天国乱
              ＼             │                ／
1895  ──── 割台 ──────→  维新思潮  ────  民变频仍
                  ＼         │              ／
1900  ────── 庚子之变 ──→  留日潮  ────── 新军兴
                              │              │
1911  ─────────────→    革命党 ←──── 各省响应
```

---

## 3 · Branching tree

A single origin fanning into consequences.

**Use when**: intellectual history, concept seeding divergent schools, one event producing multiple institutional descendants.

```
                    1902
               梁启超《新民说》
                     │
           ┌─────────┼─────────┐
           │         │         │
        孙中山     陈独秀     章太炎
      "民族主义"  "新文化"   "国故整理"
           │         │         │
         革命党   《新青年》   国粹派
```

---

## 4 · Parallel lanes (comparative)

Two or more cases side-by-side.

**Use when**: comparative history (中日 / 中西 / 中印), for showing divergence in apparently shared conditions.

```
           中国                  日本
           ────                  ────
1850  ─── 鸦片战争 ... 停滞      黑船 ... 震动
1860  ─── 洋务 (器不及道)        维新酝酿
1868  ─── ——                   明治维新
1895  ─── 割台 (败)             胜
1905  ─── 废科举                日俄战胜
1911  ─── 辛亥                  大正德谟克拉西
```

---

## 5 · Circular (cyclic)

Dynastic cycle, periodic revival.

**Use when**: longue durée arguments about repeating structure.

```
            盛世
          ╱      ╲
      中兴          衰乱
       │            │
        ╲          ╱
         ←─ 易代 ─→
              │
          新朝初建
```

---

## 6 · Sparse points on a long line

For papers arguing discontinuity — long silences punctuated by rare moments.

**Use when**: the paper emphasizes rupture; most of the timeline is background, the argument lives in a few dots.

```
|─────────────|─|──────────────────────|──|────────────|
1368         1398 1402                1644 1661       1683
            朱允炆  永乐                崇祯 郑成功      施琅
            建文  靖难                  亡   台澎       台归
             │
             ↑ 死因千年未明 — 本文考辨于此
```

---

## SVG skeleton — river form

For chronicles with more than 6 points or multiple lanes, SVG renders better.

**Aesthetic**: achromatic (`#FAFAF7` ground / `#111` ink / `#666` metadata), one or two line weights, generous margins, no chart junk.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 400"
     font-family="Source Han Serif SC, Songti, Georgia, serif">
  <rect width="800" height="400" fill="#FAFAF7"/>

  <!-- time axis -->
  <g stroke="#1A1A1A" stroke-width="0.6" fill="none">
    <line x1="80" y1="370" x2="760" y2="370"/>
  </g>

  <!-- year markers -->
  <g font-size="11" fill="#333" text-anchor="middle">
    <text x="80" y="390">1860</text>
    <text x="250" y="390">1880</text>
    <text x="420" y="390">1900</text>
    <text x="590" y="390">1920</text>
    <text x="760" y="390">1940</text>
  </g>

  <!-- lanes (replace paths per paper) -->
  <g stroke="#111" stroke-width="0.8" fill="none">
    <!-- lane 1: court -->
    <path d="M80,100 Q300,100 400,130 T760,160"/>
    <!-- lane 2: intellectual -->
    <path d="M80,210 Q300,210 400,190 T760,180"/>
    <!-- lane 3: society -->
    <path d="M80,320 Q300,320 400,300 T760,280"/>
  </g>

  <!-- lane labels -->
  <g font-size="11" fill="#444" text-anchor="end">
    <text x="70" y="105">朝廷</text>
    <text x="70" y="215">士人</text>
    <text x="70" y="325">地方</text>
  </g>

  <!-- event annotations — add per paper -->
  <g font-size="10" fill="#111">
    <circle cx="250" cy="100" r="2.5"/>
    <text x="254" y="94">洋务始</text>

    <circle cx="420" cy="130" r="2.5"/>
    <text x="424" y="124">割台</text>

    <circle cx="590" cy="160" r="2.5"/>
    <text x="594" y="154">辛亥</text>
  </g>

  <!-- caption -->
  <text x="400" y="25" font-size="13" fill="#111" text-anchor="middle">
    {Paper title} · 1860–1940
  </text>
</svg>
```

Customize per paper. Strip color. Keep the ink thin. Let whitespace do the work.

---

## SVG skeleton — vertical axis

For clean succession, stylish but unornamented.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 700"
     font-family="Source Han Serif SC, Songti, Georgia, serif">
  <rect width="600" height="700" fill="#FAFAF7"/>

  <!-- central axis -->
  <line x1="200" y1="60" x2="200" y2="660" stroke="#111" stroke-width="0.6"/>

  <!-- year-event pairs (add as needed) -->
  <g font-size="13" fill="#111">
    <circle cx="200" cy="120" r="3"/>
    <text x="180" y="124" text-anchor="end">1895</text>
    <text x="220" y="124">马关割台</text>

    <circle cx="200" cy="240" r="3"/>
    <text x="180" y="244" text-anchor="end">1898</text>
    <text x="220" y="244">戊戌变法</text>

    <circle cx="200" cy="360" r="3"/>
    <text x="180" y="364" text-anchor="end">1905</text>
    <text x="220" y="364">废科举</text>

    <circle cx="200" cy="480" r="3"/>
    <text x="180" y="484" text-anchor="end">1911</text>
    <text x="220" y="484">辛亥</text>

    <circle cx="200" cy="600" r="3"/>
    <text x="180" y="604" text-anchor="end">1915</text>
    <text x="220" y="604">新文化运动</text>
  </g>

  <!-- caption -->
  <text x="300" y="40" font-size="14" fill="#111" text-anchor="middle">
    {Chronicle title}
  </text>
</svg>
```

---

## HTML — for interactive chronicles (rare)

Reserve HTML for timelines that need toggling between lanes, or hover annotations. Most cases SVG or ASCII suffice. If warranted:

- Single self-contained `.html` file in `<ws>/analysis/xray/`
- All CSS inline (no external sheets — must work standalone when opened)
- No JavaScript unless interactivity is essential
- Obsidian embeds HTML iframes — `<iframe src="{stem}_chronicle.html" width="100%" height="600"></iframe>`

---

## Design notes

- **Achromatic first**. Color only when the paper's argument demands a chromatic distinction (e.g., two rival camps that must be distinguished visually).
- **One line weight** for structure; half-weight for annotation.
- **Generous margins**. Let whitespace carry hierarchy.
- **No chart junk**: no gridlines beyond what data needs, no legends unless unavoidable, no 3-D, no shadows, no gradients.
- **The chronicle is a reading device**, not a decoration. A reader should learn something from looking at it that the prose did not already state.

---

## When the paper has no timeline

If the paper is synchronic — a structural argument about one moment, no temporal depth — skip the chronicle entirely and write one line in the report:

> 论文为共时结构分析，无年代纪。

A forced chronicle on a synchronic paper is dishonest ink.
