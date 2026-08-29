# Handoff: Voxcat 1A — Instrument Panel UI

## Overview

A premium redesign of the Voxcat client (`client/src`). The current UI is a 48px logo bar, a 40px status strip with a 24px pulsing orb and two emoji buttons, and two nested `react-resizable-panels` splits (activity 40 / files 60, then tree 30 / preview 70). This redesign keeps the same information — transcript, tool calls, per-persona output files, file preview — and rearranges it around a **voice instrument** that occupies the centre of a single 92px top rail.

Design goals, as agreed with the designer:

- Voice is the visual centrepiece, not a 24px dot in a strip.
- Transcript is a **timeline**: timestamp gutter, speaker label, tool events inline in the same stream.
- Serif for anything a human said or wrote; monospace for anything the machine labels.
- Violet marks exactly two things: live voice state, and output the agent produced. Nothing else is violet.
- Dark is primary; light theme is a token swap on the same grid.

## About the design files

The files in this bundle are **design references created in HTML** — prototypes of the intended look and behaviour, not production code to copy. The task is to **recreate them in the existing client environment**: React 19 + TypeScript + Vite, `@pipecat-ai/voice-ui-kit`, `@pipecat-ai/client-react`, `react-resizable-panels`, `react-markdown`, and a single global `App.css`. Keep those libraries and that structure; replace the styling and the layout composition.

The prototypes use inline styles because of the tool they were authored in. **Do not port inline styles.** Translate the token table below into `App.css` custom properties and class rules, matching the file's existing convention (`:root { --bg: … }`, section-commented class blocks).

## Fidelity

**High-fidelity.** Colors, type sizes, letter-spacing, rule weights, and paddings in this document are final and should be reproduced exactly. Copy in the prototypes is sample session content — replace with real data bindings, do not ship the strings.

## Target files

| File | Change |
|---|---|
| `client/src/App.css` | Rewrite. New tokens, new layout classes, both themes. |
| `client/src/App.tsx` | Restructure `SessionView` — one 92px rail replaces `.topbar` + `.topbar-connected`; three-column grid replaces the outer `Group`/`Panel` split. |
| `client/src/components/VoiceInstrument.tsx` | **New.** Ring + level meter + state label + elapsed. Replaces `.mini-orb` / `.listening-label`. |
| `client/src/components/ActivityPanel.tsx` | Rewrite as timeline rows (timestamp gutter + body). |
| `client/src/components/ToolResultCard.tsx` | Rewrite — inline event row, not a filled card. |
| `client/src/components/FileExplorer.tsx` | Split into `OutputTree.tsx` and `FilePreview.tsx`; the inner `Group`/`Panel` split goes away (the two panes become two cells of the page grid). |
| `client/src/components/PersonaSelector.tsx` | Rewrite as a list of persona rows for the landing page; the `<select>` disappears. |
| `client/src/hooks/useActivityLog.ts` | No change to the shape of `ActivityEntry`. See "State" for two additions. |
| `client/src/types.ts` | Add `latencyMs?` and `resultKind` (see below). |

`VoiceArea.tsx` is unused by `App.tsx` in the current tree — delete it or leave it; the redesign does not use it.

---

## Design tokens

Both themes. Put these in `App.css` as custom properties on `:root` and `[data-theme="light"]`.

### Dark (default)

| Token | Value | Used for |
|---|---|---|
| `--bg` | `#0b0b0d` | app background, every pane |
| `--rule` | `rgba(255,255,255,0.09)` | all structural hairlines (rail, column dividers, pane headers) |
| `--rule-soft` | `rgba(255,255,255,0.05)` | between timeline rows |
| `--tint` | `rgba(255,255,255,0.015)` | tool-event row background |
| `--surface` | `rgba(255,255,255,0.03)` | code blocks, inset panels |
| `--surface-border` | `rgba(255,255,255,0.07)` | border of the above |
| `--text` | `#eceaea` | body |
| `--text-strong` | `#f5f4f2` | document titles, hero type |
| `--text-2` | `rgba(255,255,255,0.58)` | tool result body |
| `--text-3` | `rgba(255,255,255,0.42)` | inactive file names |
| `--text-4` | `rgba(255,255,255,0.30)` | mono section labels |
| `--text-5` | `rgba(255,255,255,0.26)` | timestamps |
| `--accent` | `#8b5cf6` | live voice, tool provenance dot, primary button fill |
| `--accent-text` | `#c4b5fd` | violet text (labels, doc section heads) |
| `--accent-rule` | `rgba(139,92,246,0.35)` | left rule of a tool result |
| `--accent-tint` | `rgba(139,92,246,0.08)` | selected file row |
| `--accent-hover` | `#a78bfa` | button hover |
| `--ok` | `#4ade80` | MIC ON dot, `OK` status |
| `--danger` | `#f87171` | denied tool, END hover |

### Light

Same names, swapped values. Structure and sizing are identical.

| Token | Value |
|---|---|
| `--bg` | `#fbfaf8` |
| `--rule` | `rgba(0,0,0,0.10)` |
| `--rule-soft` | `rgba(0,0,0,0.06)` |
| `--tint` | `rgba(109,77,224,0.035)` |
| `--surface` | `#ffffff` |
| `--surface-border` | `rgba(0,0,0,0.07)` |
| `--text` | `#17171a` |
| `--text-strong` | `#17171a` |
| `--text-2` | `rgba(23,23,26,0.65)` |
| `--text-3` | `rgba(23,23,26,0.50)` |
| `--text-4` | `rgba(23,23,26,0.45)` |
| `--text-5` | `rgba(23,23,26,0.32)` |
| `--accent` | `#6d4de0` |
| `--accent-text` | `#5b3fc4` |
| `--accent-rule` | `rgba(109,77,224,0.35)` |
| `--accent-tint` | `rgba(109,77,224,0.07)` |
| `--ok` | `#16a34a` |
| `--danger` | `#dc2626` |

### Typography

Two families, loaded from Google Fonts. Replace the current Inter `@import` in `App.css`:

```css
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;1,6..72,300;1,6..72,400&family=IBM+Plex+Mono:wght@300;400;500&display=swap');
```

- **`'Newsreader', serif`** — utterance text, document body and headings, persona names, big landing type. Weight 300 for display sizes, 400 for body, italic 400 for quotes and the `speaking` placeholder.
- **`'IBM Plex Mono', ui-monospace, monospace`** — everything else: `body` default family, all labels, timestamps, file names, buttons, code, table headers.

Type scale (final values):

| Role | Family | Size | Weight | Letter-spacing | Line-height |
|---|---|---|---|---|---|
| Landing hero | Newsreader | 54px | 300 | — | 1.05 |
| Document title | Newsreader | 28px | 300 | — | 1.2 |
| Persona name | Newsreader | 19px | 400 | — | — |
| Utterance | Newsreader | 17px | 400 | — | 1.55 |
| Document body | Newsreader | 16px | 400 | — | 1.7 |
| Wordmark `VOXCAT` | Mono | 12px | 400 | 0.26em | — |
| Pane header label | Mono | 10px | 400 | 0.18em | — |
| Speaker / tool label | Mono | 10px | 400 | 0.16em | — |
| Doc section label | Mono | 10px | 400 | 0.18em | — |
| Persona / meta label | Mono | 10px | 400 | 0.12em | — |
| Button | Mono | 10px | 400 | 0.14em | — |
| Timestamp | Mono | 10px | 400 | — | — |
| File name | Mono | 11px | 400 | — | — |
| Tool result body | Mono | 12px | 400 | — | 1.65 |
| Code block | Mono | 11px | 400 | — | 1.85 |

All mono labels are uppercase. Uppercase the **content**, not via `text-transform`, where the string is a fixed UI label; use `text-transform: uppercase` for interpolated values like persona keys and file names.

### Geometry

- **Radius: 0 everywhere.** No rounded corners except the voice ring and status dots, which are circles. This is the single strongest departure from the current UI — remove every `border-radius: 6/8/10/24px`.
- Hairlines are always exactly `1px solid var(--rule)`.
- Structural heights: top rail **92px**, pane header **13px vertical padding** (≈40px tall), output-tree footer **12px vertical padding**.
- Column widths: `1fr 244px 1fr`.
- No shadows anywhere except the voice dot glow (below). Delete `box-shadow: 0 0 40px…` from the connect button.

---

## Screens

### 1. Landing (`LandingPage` in `App.tsx`)

64px header rail: `VOXCAT` wordmark left; right side two mono 10px/0.12em labels — `GEMINI LIVE · SMALLWEBRTC` and `PAST SESSIONS` (the latter interactive, hover to `--text`).

Body is a two-column grid, `1fr 1fr`, divided by a vertical hairline, both columns vertically centred with 72px horizontal padding.

**Left column** (gap 40px):
- Newsreader 54px/300, line-height 1.05: “Think out loud.” / “Keep the notes.” (two lines, `<br>`).
- Mono 12px, line-height 1.9, letter-spacing 0.03em, `--text-3`, max-width 400px: the one-line explanation of what the product does.
- Three spec rows, max-width 400px, each `grid-template-columns: 78px 1fr`, gap 12px, `padding-top: 12px`, `border-top: 1px solid var(--rule)`. Left cell mono 10px/0.12em `--text-4`; right cell mono 11px `--text-2`. Rows: `LATENCY` / ~300 ms speech to speech · `TOOLS` / websearch · file read / write · MCP, read-only · `OUTPUT` / markdown, on your disk.

**Right column** (gap 26px):
- Mono 10px/0.18em `--text-4`: `SELECT PERSONA`.
- Persona list: a `1px` bordered box whose children are separated by `1px` gaps filled by `--rule` (`display:flex; flex-direction:column; gap:1px; background: var(--rule); border: 1px solid var(--rule)`), so every row divider is a hairline with no double borders.
- Each row: `grid-template-columns: 1fr auto`, align-items center, gap 16px, padding 18px 20px. Left cell: a 5×5px square (`--accent` when selected, `rgba(255,255,255,0.2)` otherwise) + Newsreader 19px name; below it mono 11px/1.6 `--text-3` description. Right cell: mono 10px/0.12em `SELECTED` in `--accent-text` when selected, and mono 10px `--text-5` showing `<output dir> · <file count>`.
- Unselected row background `--bg`, hover `rgba(255,255,255,0.03)`. Selected row background `--accent-tint` at 0.09 alpha.
- Footer row: primary button — mono 11px/0.16em, padding 14px 26px, background `--accent`, color `--bg`, weight 500, no radius, hover `--accent-hover`; beside it mono 10px `--text-5` `MICROPHONE REQUIRED`.

Persona descriptions (from `config.yaml` instructions, one line each — these are final copy): Thinking Partner “Probing questions, challenged assumptions, two sentences at a time.” · Devil's Advocate “Takes the opposite side of whatever you just said.” · Note Taker “Stays quiet, writes down what you say.” · SRE Assistant “Cases, KCS and Jira, read-only. Summarises findings.”

File counts come from `/api/files/tree`; fetch it on the landing page too, so the counts are real before a session starts.

### 2. Session (`SessionView`)

`display:flex; flex-direction:column; height:100vh`. Two children: the rail, then the grid.

#### 2a. Top rail — 92px, `grid-template-columns: 300px 1fr 300px`, bottom hairline

- **Left cell** (padding 0 24px, centred column, gap 7px): `VOXCAT` wordmark; under it a row, gap 8px — persona label (mono 10px/0.12em `--text-4`, uppercase), a `·` in `rgba(255,255,255,0.2)`, and the persona's output directory (mono 10px/0.06em `--text-5`).
- **Centre cell** — the voice instrument. Left and right hairline borders, so it reads as an instrument bay. Contents centred, gap 22px: the ring, the level meter, then a two-line status block (min-width 104px, gap 5px): state label mono 10px/0.16em `--accent-text`, and mono 10px/0.08em `--text-4` `MM:SS ELAPSED`.
- **Right cell** (padding 0 24px, justify flex-end, gap 8px): a mic indicator (5px circle `--ok` + mono 10px/0.1em `MIC ON`, margin-right 6px), then `MUTE` and `END` buttons — mono 10px/0.14em, padding 8px 13px, transparent background, `1px solid rgba(255,255,255,0.14)`, color `--text-2`. `MUTE` hover: border `rgba(255,255,255,0.34)`, color `--text`. `END` hover: border `rgba(239,68,68,0.5)`, color `--danger`. Both replace the emoji `ctrl-btn`s.

#### 2b. Body — `grid-template-columns: 1fr 244px 1fr`, `overflow:hidden`

Middle column carries left and right hairlines. Each column is `flex-direction: column` with a fixed header and a scrolling body.

Pane header: `display:flex; align-items:center; justify-content:space-between; padding:13px 24px` (18px in the tree, 28px in the document), bottom hairline, `flex-shrink:0`. Left label mono 10px/0.18em `--text-4`. Right side meta mono 10px/0.1em `--text-5`, interactive items hover to `--text`.

Scroll containers: `overflow-y:auto`, custom scrollbar `width:3px`, thumb `rgba(255,255,255,0.12)`, radius 2px. Drop the 4px/5px scrollbar variants in the current CSS for this one.

**Column 1 — Timeline.** Header: `TIMELINE` · `<n> EVENTS` and a `TOOLS ONLY` filter toggle. Rows are `display:grid; grid-template-columns: 68px 1fr; gap:16px; padding:14px 24px; border-bottom:1px solid var(--rule-soft)`.

- Timestamp cell: mono 10px `--text-5`, `padding-top:4px` to sit on the first text baseline. Format `HH:MM:SS` from `entry.timestamp`.
- Utterance body: column, gap 6px — speaker label (mono 10px/0.16em; `YOU` in `rgba(255,255,255,0.48)`, `VOXCAT` in `--accent-text`) then Newsreader 17px/1.55 `--text`. **Note the change from the current UI:** the user is no longer green. Green is reserved for the mic-live dot.
- Tool event row: same grid, plus `background: var(--tint)`. Body column gap 10px. Header line: 5×5px `--accent` square, tool name mono 10px/0.16em `--accent-text` uppercase, then mono 10px `--text-5` meta (`1.2s · 2 RESULTS`), and a right-aligned `COLLAPSE` affordance. Result body: `border-left: 1px solid var(--accent-rule); padding-left: 14px`, children mono 12px/1.65 `--text-2`, with the result title in `--text`.
- Cancelled event: same row, no tint, 5×5px **outlined** square (`1px solid rgba(255,255,255,0.25)`), name and `CANCELLED` both `--text-4` / `rgba(255,255,255,0.24)`.
- Streaming bot turn: speaker label, then Newsreader 17px **italic** at `rgba(236,234,234,0.55)` reading `speaking`, beside a 60×1px track with a 25%-wide `--accent` bar animated by `vxSweep` (see Animations).

Keep the existing auto-scroll-on-new-entry behaviour, but replace `scrollIntoView` with `el.scrollTop = el.scrollHeight` on the scroll container — `scrollIntoView` on a nested pane can scroll the whole page.

**Column 2 — Output** (244px). Header `OUTPUT` + `↻` refresh. Body `padding: 10px 0`.

- Group header per persona: `padding: 9px 18px`, mono 10px/0.14em `--text-4`, `display:flex; justify-content:space-between`, count on the right in `--text-5`. No chevrons and no expand/collapse — all groups are always open. This is a deliberate simplification of the current tree; the folder toggle state in `FileExplorer` can go.
- File row: `padding: 8px 18px 8px 24px`, mono 11px `--text-3`, single line with ellipsis, hover color `--text` + background `rgba(255,255,255,0.03)`.
- Selected file row: `padding-left: 22px`, `border-left: 2px solid var(--accent)`, `background: var(--accent-tint)`, color `--text`.
- Empty group: Newsreader 12px italic `rgba(255,255,255,0.24)`, text `empty`, padding `6px 18px 6px 24px`.
- Footer, `flex-shrink:0`, top hairline, `padding:12px 18px`, mono 10px/0.1em `--text-5`: `<n> FILES · <n> ROOTS`.

**Column 3 — Document.** Header shows the filename uppercase (mono 10px/0.12em `--text-2`), and on the right relative mtime + a `RAW` toggle. Body `padding: 30px 28px`.

`react-markdown` element mapping — override these components rather than styling by descendant selector:

| Markdown | Rendering |
|---|---|
| `h1` | Newsreader 28px/300, line-height 1.2, `--text-strong`; followed by a mono 10px/0.12em `--text-4` metadata line, then 18px padding and a bottom hairline |
| `h2` | mono 10px/0.18em `--accent-text`, margin `24px 0 9px` |
| `h3` | mono 10px/0.16em `--text-4`, margin `18px 0 8px` |
| `p` | Newsreader 16px/1.7 `rgba(236,234,234,0.85)` |
| `ul`/`ol` | no bullets — each `li` is `grid-template-columns: 18px 1fr`, gap 8px; ordered lists show a zero-padded index (`01`) in `--text-4`, unordered a 5×5 square; item text mono 12px/1.65 `--text-2` |
| `blockquote` | `border-left: 1px solid rgba(139,92,246,0.5); padding-left: 16px; margin: 24px 0`, Newsreader 16px italic `rgba(255,255,255,0.55)` |
| `pre` | `padding:14px 16px; background: var(--surface); border:1px solid var(--surface-border)`, mono 11px/1.85 `--text-2`, no radius |
| `code` (inline) | mono 12px `--accent-text`, no background pill |
| `table` | outer `1px solid var(--rule)`; header row mono 10px/0.12em `--text-4` with a bottom hairline; cells mono 12px `--text-2`, `padding:10px 14px`, vertical hairline between columns |
| `hr` | `1px solid var(--rule)` |
| `a` | `--accent-text`, `border-bottom: 1px solid rgba(167,139,250,0.4)`; hover both to `#c4b5fd` |

Empty state, when no file is selected: Newsreader 16px italic `--text-4`, centred — not the current 13px sans “Select a file to preview”.

### 3. Voice instrument states (`VoiceInstrument.tsx`)

One component, driven by a `state` prop: `'connecting' | 'listening' | 'speaking' | 'muted' | 'working' | 'ended'`. Geometry is constant across states — 38px ring, meter, two-line label — so the rail never reflows.

| State | Ring | Meter | Label |
|---|---|---|---|
| `connecting` | 38px circle, `1px solid rgba(167,139,250,0.4)`, `vxHalo 1.6s`; inner 9px dot `rgba(139,92,246,0.6)`, no glow | 180×1px track, 22%-wide `--accent` bar, `vxSweep 1.4s linear infinite` | `CONNECTING` / `NEGOTIATING WEBRTC` |
| `listening` | same ring at 0.45 alpha, `vxHalo 3s`; 9px `--accent` dot, `box-shadow: 0 0 12px rgba(139,92,246,0.85)`, `vxBreathe 3s` | 32 bars, 24px tall, 2px wide, 3px gap, `vxWave 1.6s` staggered | `LISTENING` / `08:41 ELAPSED` |
| `speaking` | filled halo `rgba(139,92,246,0.18)` `vxHalo 1.9s` + `1px solid rgba(167,139,250,0.6)` ring; 14px dot, glow `0 0 18px`, `vxBreathe 1.9s` | same bars, 30px tall, `vxWave 0.9s` | `SPEAKING` / elapsed |
| `muted` | 38px `1px solid rgba(255,255,255,0.14)`, no animation; an 11×1px bar rotated −45° inside | bars frozen at `scaleY(0.14)`, color `rgba(255,255,255,0.14)` | `MUTED` / `MIC OFF · SESSION LIVE` |
| `working` | 38px `1px solid var(--rule-strong)`; 9px `--accent` dot, `vxBreathe 1.1s` | 5px square + tool name mono 10px/0.16em `--accent-text` + flexible 1px track with `vxSweep 1.2s` | `WORKING` / `TOOL CALL IN FLIGHT` |
| `ended` | 38px `1px solid rgba(255,255,255,0.12)`; 10×1px bar inside | none | `SESSION ENDED` / `08:41 · TRANSCRIPT SAVED TO <dir>/` |

Map to Pipecat state: `transportState` of `connecting`/`authenticating`/`initializing` → `connecting`; `isMicEnabled === false` → `muted`; bot audio playing → `speaking`; a `tool-start` with no matching `tool-result` → `working`; otherwise `listening`.

The `ended` state replaces the current full-screen red `Disconnected` label and the 1200ms `window.location.reload()`. Keep the session frame on screen, swap the instrument to `ended`, and put a `NEW SESSION` button in the right cell of the rail (same button style as `MUTE`). The transcript and the document stay readable after the call ends — that is the point of ending this way rather than reloading.

**Level meter, ideally real.** The prototype animates the bars on a fixed CSS keyframe because it has no audio. In the app, drive bar heights from an `AnalyserNode` on the local mic stream (listening/muted) or the bot output track (speaking): `requestAnimationFrame`, `getByteFrequencyData`, map 32 buckets to `scaleY(0.14 → 1)`. Fall back to the CSS keyframe if no analyser is available. Bars must be `transform`-animated only, never `height` — 32 elements animating layout at 60fps is a real cost.

### 4. Tool results (`ToolResultCard.tsx`)

Four presentations, chosen from the shape of `result` — the same branches `resultToMarkdown` already discriminates. Rather than flattening everything to markdown, return a `resultKind` and render structurally:

- **`results` array** → header line, then one block per result: title mono 12px `--text`, snippet mono 11px/1.6 `--text-3`, source mono 10px `--text-5`. Inside the `--accent-rule` left border.
- **`analysis` / `report` / `content` string** → prose. Newsreader 15px/1.7 `rgba(236,234,234,0.8)` inside the left border. Prose the agent wrote gets the serif; keep this distinction, it is what makes the timeline readable.
- **`status` / `error` / `cancelled`** → a single row, no body: provenance square, tool name, subject (path or message) mono 11px `--text-3`, and a right-aligned outcome chip mono 10px/0.1em — `OK` in `--ok`, `DENIED` in `--danger` (square and tool name also `--danger`), `CANCELLED` in `rgba(255,255,255,0.24)` with an outlined square.
- **fallback** → raw JSON in the `pre` treatment, `max-height: 150px`, scrollable, with a `COPY` affordance in the header line.

No filled card, no violet pill badge, no 10px uppercase chip on a tinted background — the current `.tool-name` and `.tool-result` treatments both go away. Provenance is carried by the 5px square and the left rule.

---

## Interactions & behaviour

- **Resizable panels.** Both `Group`/`Panel` splits are replaced by a CSS grid. If resizing must be kept, wrap only columns 1 and 3 and style the `Separator` as a 1px `--rule` line with a 5px transparent hit area, hover `--accent`. Do not reintroduce the `· · ·` glyph or the 5px filled bar.
- **Hover.** Only three hover treatments exist: text lifts to `--text`, a row gains `rgba(255,255,255,0.03)`, a button's border lifts to 0.34 alpha. Nothing scales, nothing translates, nothing gains a shadow. Remove `transform: translateY(-1px)` from the primary button.
- **Timeline filter.** `TOOLS ONLY` toggles out `user`/`bot` entries.
- **Tool result collapse.** `COLLAPSE` on a tool event hides its body, leaving the header line. Default expanded; collapse all but the last when the timeline exceeds ~40 entries.
- **Refresh.** `↻` in the output header re-fetches `/api/files/tree`, as now.
- **File selection.** Unchanged: `GET /api/files/<name>?persona=<p>` into the document column.
- **Theme.** `data-theme="light"` on `<html>`, default from `prefers-color-scheme`, user override in `localStorage`. Both palettes above are complete; no other change is needed.

### Animations

```css
@keyframes vxWave    { 0%,100% { transform: scaleY(0.16); } 50% { transform: scaleY(1); } }
@keyframes vxBreathe { 0%,100% { transform: scale(1); opacity: .85; } 50% { transform: scale(1.06); opacity: 1; } }
@keyframes vxHalo    { 0%,100% { opacity: .30; transform: scale(1); } 50% { opacity: .62; transform: scale(1.14); } }
@keyframes vxSweep   { 0% { transform: translateX(-100%); } 100% { transform: translateX(400%); } }
```

Bar stagger: `animation-delay: (i % 9) * 0.13s`. Wrap all four in `@media (prefers-reduced-motion: reduce)` and hold them at their rest frame — a 32-bar meter pulsing is exactly what that media query is for.

## State

Everything needed already exists in `useActivityLog` and the Pipecat hooks, plus:

- `voiceState` — derived, per the mapping table above.
- `elapsed` — seconds since connect, formatted `MM:SS`. One interval at the `SessionView` level, not per component.
- `toolsOnly: boolean`, `collapsed: Set<toolCallId>` — timeline view state.
- `theme: 'dark' | 'light'`.
- `types.ts`: add `latencyMs?: number` to `tool-result` (the meta line shows `1.2s`; if the server doesn't send it, compute it as the delta from the matching `tool-start`), and `resultKind?: 'results' | 'prose' | 'status' | 'raw'` if you decide the classification server-side rather than in the card.

Tool events pair by `toolCallId`, which the entry type already carries — use it to render one row per call (header from `tool-start`, body from `tool-result`) instead of two separate entries as now.

## Assets

None. No icons, no images, no SVG. Every mark in this design is a `div`: 5×5px squares, circles via `border-radius: 50%`, 1px rules, and `↻` / `→` as text characters. The emoji in the current UI (`🎤`, `🔇`, `✕`, `⚙️`, `▾`, `▸`) are all removed and replaced by mono word labels or geometric marks.

Fonts load from Google Fonts. If the client must work offline, self-host Newsreader and IBM Plex Mono (both OFL) and swap the `@import` for `@font-face`.

## Files in this bundle

| File | What it is |
|---|---|
| `Voxcat 1A Instrument.dc.html` | The design. Session dark, session light, landing, six voice states, four tool-result treatments. Open in a browser. |
| `Voxcat Current UI.dc.html` | Recreation of the current build, for before/after comparison. |
| `Voxcat Premium Explorations.dc.html` | The three directions explored; 1A is the one chosen. Useful only as context. |

Open the design file and read the values off the running page where this document is ambiguous — it is the source of truth for anything not written down here.

## Suggested order

1. `App.css` — tokens, both themes, fonts, radius purge, keyframes.
2. `VoiceInstrument.tsx` with the CSS-keyframe meter; wire it into the new 92px rail.
3. Replace the outer split with the three-column grid; move the tree and preview out of `FileExplorer` into the grid cells.
4. `ActivityPanel` timeline rows, then `ToolResultCard`'s four treatments.
5. Landing page persona rows.
6. Real audio analyser on the meter; `ended` state instead of reload.
7. Theme toggle.
