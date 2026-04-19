# Visualization skeletons

Each visualization serves a specific analytical question. Pick what answers it — do not visualize for decoration.

---

## 1 · Lineage tree (学派谱系) — ASCII

**Fits**: 5–15 papers with clear school affiliations.

```
                     实证史学
                     ┌───┴───┐
                   陈寅恪   钱穆
                     │       │
           ┌─────────┼───────┘
           │         │
         王 1985   李 1992
                     │
        新文化史 ─ 影响 ─→ 赵 2001
                          │
                     ← 批判 ──── 后殖民 ──→ 周 2015
                                            │
                                        刘 2020
```

---

## 2 · Lineage scatter — SVG

**Fits**: 15+ papers or messy citation graphs. Axes: 史观 spectrum (evidentialist ↔ interpretive) × temporal or scope.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600"
     font-family="Source Han Serif SC, Songti, Georgia, serif">
  <rect width="800" height="600" fill="#FAFAF7"/>

  <!-- axis frame -->
  <g stroke="#888" stroke-width="0.4" fill="none">
    <line x1="80" y1="540" x2="760" y2="540"/>
    <line x1="80" y1="60" x2="80" y2="540"/>
  </g>

  <!-- axis labels -->
  <g font-size="11" fill="#444">
    <text x="80" y="560" text-anchor="start">评证</text>
    <text x="760" y="560" text-anchor="end">诠释</text>
    <text x="60" y="60" text-anchor="end">近年</text>
    <text x="60" y="540" text-anchor="end">早年</text>
  </g>

  <!-- scatter points (one per paper — customize) -->
  <g font-size="11" fill="#111">
    <circle cx="200" cy="500" r="3"/>
    <text x="210" y="504">王 1985</text>

    <circle cx="260" cy="430" r="3"/>
    <text x="270" y="434">李 1992</text>

    <circle cx="520" cy="320" r="3"/>
    <text x="530" y="324">赵 2001</text>

    <circle cx="620" cy="180" r="3"/>
    <text x="630" y="184">周 2015</text>

    <circle cx="680" cy="120" r="3"/>
    <text x="690" y="124">刘 2020</text>
  </g>

  <!-- caption -->
  <text x="400" y="30" font-size="13" fill="#111" text-anchor="middle">
    {Corpus} · 学派谱系
  </text>
</svg>
```

Strip color. One weight of line. Labels small and close.

---

## 3 · Coverage grid (时空覆盖) — ASCII

**Fits**: papers mapped across time × space. Density via glyph (`·` thin, `●` concentrated).

```
空间 ↓ / 时间 →   1840-60   1860-95   1895-11   1911-27   1927-49
─────────────────────────────────────────────────────────────────
京畿               ●●         ●●●       ●●●●●     ●●●       ●●
江南               ●          ●●        ●●●       ●         ●
两广               ·          ●         ●●        ●         ·
西南               ·          ·         ●         ·         ·
海外华人           ·          ·         ●         ●         ●
─────────────────────────────────────────────────────────────────
                                                 ↑
                                   corpus over-represents 京畿 1895-1911
```

---

## 4 · Coverage map — SVG

**Fits**: for finer spatial granularity or when time axis is long.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 500"
     font-family="Source Han Serif SC, Songti, serif">
  <rect width="900" height="500" fill="#FAFAF7"/>

  <!-- grid lines (subtle) -->
  <g stroke="#DDD" stroke-width="0.3" fill="none">
    <!-- vertical time bands -->
    <line x1="160" y1="40" x2="160" y2="440"/>
    <line x1="320" y1="40" x2="320" y2="440"/>
    <line x1="480" y1="40" x2="480" y2="440"/>
    <line x1="640" y1="40" x2="640" y2="440"/>
    <line x1="800" y1="40" x2="800" y2="440"/>
    <!-- horizontal region bands -->
    <line x1="80" y1="100" x2="860" y2="100"/>
    <line x1="80" y1="160" x2="860" y2="160"/>
    <line x1="80" y1="220" x2="860" y2="220"/>
    <line x1="80" y1="280" x2="860" y2="280"/>
    <line x1="80" y1="340" x2="860" y2="340"/>
  </g>

  <!-- time labels -->
  <g font-size="10" fill="#555" text-anchor="middle">
    <text x="160" y="465">1840</text>
    <text x="320" y="465">1880</text>
    <text x="480" y="465">1920</text>
    <text x="640" y="465">1960</text>
    <text x="800" y="465">2000</text>
  </g>

  <!-- region labels -->
  <g font-size="10" fill="#555" text-anchor="end">
    <text x="70" y="75">京畿</text>
    <text x="70" y="135">江南</text>
    <text x="70" y="195">两广</text>
    <text x="70" y="255">西南</text>
    <text x="70" y="315">海外</text>
  </g>

  <!-- density markers (one per paper — size encodes weight) -->
  <g fill="#111">
    <circle cx="400" cy="70" r="3"/>
    <circle cx="420" cy="72" r="4"/>
    <circle cx="460" cy="68" r="3"/>
    <!-- add more per corpus -->
  </g>

  <!-- caption -->
  <text x="450" y="25" font-size="13" fill="#111" text-anchor="middle">
    {Corpus} · 时空覆盖
  </text>
</svg>
```

---

## 5 · Concept constellation — SVG

**Fits**: visualizing how papers cluster around contested concepts. Concepts as large nodes, papers as small crosses near the concept-face they embrace.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600"
     font-family="Source Han Serif SC, Songti, serif">
  <rect width="600" height="600" fill="#FAFAF7"/>

  <!-- concept nodes (larger circles) -->
  <g fill="#111" font-size="13">
    <circle cx="200" cy="200" r="7"/>
    <text x="215" y="205">近代性</text>

    <circle cx="420" cy="200" r="7"/>
    <text x="435" y="205">传统</text>

    <circle cx="300" cy="420" r="7"/>
    <text x="315" y="425">本土</text>
  </g>

  <!-- paper markers as small crosses near their preferred concept -->
  <g stroke="#333" stroke-width="0.8" fill="none">
    <!-- near 近代性 -->
    <path d="M180,240 l5,0 M182.5,237.5 l0,5"/>
    <path d="M210,260 l5,0 M212.5,257.5 l0,5"/>
    <!-- near 传统 -->
    <path d="M440,240 l5,0 M442.5,237.5 l0,5"/>
    <!-- between 本土 and 近代性 -->
    <path d="M250,320 l5,0 M252.5,317.5 l0,5"/>
  </g>

  <!-- tiny paper labels -->
  <g font-size="9" fill="#555">
    <text x="190" y="256">王 1985</text>
    <text x="220" y="276">李 1992</text>
    <text x="450" y="256">陈 2010</text>
    <text x="260" y="336">周 2015</text>
  </g>

  <!-- caption -->
  <text x="300" y="30" font-size="13" fill="#111" text-anchor="middle">
    {Corpus} · 概念争议
  </text>
</svg>
```

---

## 6 · Methodological rose — ASCII

```
              考据 (12)
                 *
               * * *
             * * * * *
     跨学科 (2)  *  计量 (1)
          * * * * * *
         *     *     *
   概念史 (3)  *   口述 (0)
         *     *     *
          * * * * * *
         *           *
     微观 (4)    比较 (5)
               * * *
                 *
```

(Count of papers per method. Visual hierarchy via ring distance.)

---

## 7 · Methodological rose — SVG

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500"
     font-family="Source Han Serif SC, Songti, serif">
  <rect width="500" height="500" fill="#FAFAF7"/>

  <!-- reference rings -->
  <g stroke="#DDD" stroke-width="0.4" fill="none">
    <circle cx="250" cy="250" r="60"/>
    <circle cx="250" cy="250" r="120"/>
    <circle cx="250" cy="250" r="180"/>
  </g>

  <!-- axis lines (7 methods, 7 spokes) -->
  <g stroke="#BBB" stroke-width="0.4">
    <line x1="250" y1="250" x2="250" y2="70"/>
    <line x1="250" y1="250" x2="410" y2="170"/>
    <line x1="250" y1="250" x2="410" y2="330"/>
    <line x1="250" y1="250" x2="250" y2="430"/>
    <line x1="250" y1="250" x2="90" y2="330"/>
    <line x1="250" y1="250" x2="90" y2="170"/>
    <line x1="250" y1="250" x2="250" y2="250"/>
  </g>

  <!-- data polygon (customize per corpus; counts normalized to 180) -->
  <polygon points="250,130  370,200  370,300  250,370  130,300  130,200"
           fill="#111" fill-opacity="0.1" stroke="#111" stroke-width="0.8"/>

  <!-- method labels -->
  <g font-size="11" fill="#111" text-anchor="middle">
    <text x="250" y="60">考据</text>
    <text x="420" y="165">计量</text>
    <text x="420" y="340">口述</text>
    <text x="250" y="450">比较</text>
    <text x="80" y="340">微观</text>
    <text x="80" y="165">概念史</text>
  </g>

  <!-- caption -->
  <text x="250" y="25" font-size="13" fill="#111" text-anchor="middle">
    {Corpus} · 方法论分布
  </text>
</svg>
```

---

## Design notes

- **Achromatic first**. `#FAFAF7` ground, `#111` ink, `#555` metadata, `#DDD` reference lines.
- **One line weight** for structure; half-weight for annotation.
- **Generous margins**. Let whitespace carry hierarchy.
- **No chart junk**: no gridlines beyond what data needs, no legends unless unavoidable, no 3-D, no shadows, no gradients.
- **Color only** when the argument requires visual distinction between rival camps. If used, two colors maximum, one neutral (slate / charcoal) and one warm (terra / rust).
- **Obsidian embed**: use `![[filename.svg]]` — the file goes in the sibling `{map-name}/` folder, referenced from the main Markdown.

---

## When not to visualize

Not every section needs a diagram. If a table carries the information more honestly, keep the table. A visualization must show the reader something the table did not — a gap, a density, a proximity. Otherwise it is ornament.
