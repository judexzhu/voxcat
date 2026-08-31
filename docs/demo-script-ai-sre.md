# Voxcat Demo Video Script

**Topic:** AI SRE — exploring how AI changes site reliability engineering
**Persona:** Thinking Partner
**Duration:** ~4-5 minutes
**Tone:** Casual, like showing a colleague something you built over the weekend

---

## COLD OPEN (0:00 - 0:10)

**[Screen: terminal, `voxcat` command running]**

> **Voiceover (you):** "Hi , my name is Jude and I built VOXCAT which is a voice agent that thinks with me. Here is the Architecture. How Let me show you what it looks like."

---

## ACT 1: LAUNCH + PERSONA SELECT (0:10 - 0:30)

**[Screen: browser opens to Voxcat landing page]**

> **Voiceover:** "This is Voxcat. Pick a persona — each one behaves differently and gets its own output folder. I'll use Thinking Partner today."

**Actions to show:**

- Hover over each persona briefly (show descriptions)
- Select **Thinking Partner**
- Point out the file count badge next to the output directory
- Click **START SESSION**

**[Screen: mic permission prompt, then session view loads with CONNECTING state]**

---

## ACT 2: OPENING CONVERSATION (0:30 - 1:15)

**[Screen: session view — voice instrument shows LISTENING]**

> **You (speaking):** "I want to explore the idea of AI SRE — what would it look like if an AI agent handled on-call instead of a human?"

**[Voxcat responds — 2-3 sentences, challenges the premise, asks a clarifying question]**

> **You:** "Good question. Let's say tier-1 incidents only — the ones with known runbooks."

**[Voxcat responds — makes a distinction between automation and AI, suggests the real value is in the ambiguous cases]**

**What the viewer sees:**

- Voice instrument cycling between LISTENING and SPEAKING states
- Audio meter bars reacting to your voice
- Transcript appearing in timeline (read-ahead text before audio finishes)
- Elapsed timer ticking

---

## ACT 3: TRIGGERING TOOLS (1:15 - 2:45)

### Web Search (1:15 - 1:45)

> **You:** "Are there any companies already doing autonomous incident response?"

**[Voxcat says "Let me check" — voice instrument shows WORKING with "WEB_SEARCH" label]**

**What the viewer sees:**

- Tool-start entry in timeline (tinted row, "WEB_SEARCH")
- Tool-result card with 5 results (titles, snippets, clickable URLs)
- Voxcat speaks a summary of what it found

### Deep Analysis (1:45 - 2:15)

> **You:** "Why do most AIOps platforms fail at root cause analysis?"

**[Voxcat says "Let me think about that" — WORKING state with "DEEP_ANALYSIS"]**

**What the viewer sees:**

- Longer tool call (~3-5 seconds)
- Prose result card with left accent border (rendered markdown)
- Voxcat delivers a structured analysis — correlation vs causation, alert fatigue, lack of system topology

### Research (2:15 - 2:45)

> **You:** "Research what Google and Meta are doing with AI in their SRE teams."

**[Voxcat says "Looking into that" — WORKING state with "RESEARCH", takes ~10 seconds]**

**What the viewer sees:**

- Longer wait (mention this is a multi-step tool: search + read sources + synthesize)
- Research report card with Key Findings, Sources
- Voxcat summarizes the highlights

### Text Input Demo (2:45 - 3:30)

> **Voiceover:** "You can also type messages — useful when you don't want to say something out loud."

---

## ACT 4: FILE OUTPUT (3:30 - 3:45)

> **You:** "Save the key takeaways so far as 'ai-sre-exploration.md'."

**[Voxcat calls FILE_WRITE — no confirmation, just saves]**

**What the viewer sees:**

- Tool-result shows "OK" status with file path
- **Output tree auto-refreshes** — new file appears under THINKING-PARTNER folder
- Click the file — **Document Preview** renders the markdown
- Show the rendered headings, bullet points, formatted content

**Actions:**

- Type a message in the text input at bottom of timeline: "add a section about risks of AI-driven rollbacks"
- Hit Enter — message appears in timeline as "YOU"
- Voxcat responds to the typed message, calls FILE_WRITE to update the file
- Document Preview auto-refreshes with new content

---

## ACT 5: SESSION WRAP-UP (3:30 - 4:15)

> **You:** "That's all for today."

**[Voxcat calls SUMMARIZE_SESSION — saves summary silently, confirms]**

**What the viewer sees:**

- Summary file appears in output tree
- Click it — shows Key Ideas, Decisions Made, Action Items, Open Questions

### Quick Feature Flash (3:50 - 4:00)

**[Fast cuts, no narration needed — just show:]**

- Click **TOOLS ONLY** toggle — timeline filters to just tool events
- Click **theme toggle** — switch dark/light
- Click **MUTE** — show mic off state, then unmute with SYNCING indicator
- Click **END** — session ends, transcript saved

---

## CLOSING (4:00 - 4:15)

**[Screen: back to landing page, or output folder showing saved files]**

> **Voiceover:** "Voice in, structured output out. That's Voxcat."

**[Show GitHub URL or install command]**

```
uv tool install git+https://github.com/judexzhu/voxcat
```

---

## PRODUCTION NOTES

### Before Recording

- Have `TAVILY_API_KEY` set (enables web_search, research)
- Clear old output files for clean demo: `rm -rf ~/Documents/voxcat/output/thinking-partner/*`
- Use split mode for better tool reliability and read-ahead text effect
- Test the three tool calls beforehand — make sure they return good results for these queries

### Recording Tips

- Screen record at 1920x1080 or 2560x1440
- Use a good mic — your voice is half the demo
- Don't script Voxcat's responses — let it be natural, that's the point
- If a tool call takes long, don't cut — the wait + WORKING state is part of the UX
- Keep the browser zoom at 100% so UI text is readable

### Fallback Queries

If the AI SRE topic doesn't trigger good tool results, alternatives:

- Web search: "What is PagerDuty Copilot doing with AI incident response 2026"
- Deep analysis: "Compare the trade-offs between human-in-the-loop vs fully autonomous incident remediation"
- Research: "Research autonomous remediation platforms launched in 2025-2026"

### Key Features to Ensure Are Visible

- [ ] Landing page persona selector
- [ ] Voice instrument state changes (LISTENING, SPEAKING, WORKING)
- [ ] Audio meter bars reacting to voice
- [ ] Read-ahead text (text appears before audio finishes)
- [ ] Web search results card
- [ ] Deep analysis prose card
- [ ] Research report card
- [ ] File write + auto-refresh in output tree
- [ ] Document preview with rendered markdown
- [ ] Text input message
- [ ] Session summary
- [ ] Tools-only filter toggle
- [ ] Theme toggle
- [ ] Mute/unmute with SYNCING state
- [ ] End session
