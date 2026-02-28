# TheAgentCompany — Distilled & Augmented
### arxiv: 2412.14161 (v3, Sep 2025) | Xu et al., CMU + Duke
### Full-Day Playgroup Session Guide

---

## 🔴 MUST — Always Include

### 🎯 CORE THESIS
**175 real professional tasks** inside a simulated software company reveal that even the best LLM agent (**Gemini 2.5 Pro**) only completes **30.3%** autonomously — simple tasks are solvable but long-horizon, multi-tool, and social tasks remain far beyond reach.

### 💡 TOP INSIGHTS (5)

1. **30% ceiling with best model** — Why it matters: Gemini 2.5 Pro hits 30.3% success / 39.3% partial score at $4.20/task; this is the **hard reality check** for "agents will replace workers" claims.

2. **Social interaction is the killer** — Why it matters: Tasks requiring colleague communication via RocketChat are dramatically harder; agents fail to ask clarifying questions, misparse responses, or loop endlessly — the **communication gap** is wider than the reasoning gap.

3. **O\*NET-grounded task design** — Why it matters: Unlike academic-biased benchmarks, tasks are derived from the US Department of Labor's **O\*NET database** (job population × median salary), making economic implications more credible than prior benchmarks.

4. **Partial credit scoring reveals hidden progress** — Why it matters: The `S_partial = 0.5 × (Result/Total) + 0.5 × S_full` formula means agents get ~39% partial score vs 30% full completion — there's meaningful **partial capability** even in failed tasks.

5. **Open-weights models are 3-5× worse** — Why it matters: Llama 3.1 405B hits 7.4% vs Gemini's 30.3% — the **capability gap between proprietary and open models** is enormous for agent tasks, far larger than on standard NLP benchmarks.

### ⚡ IMMEDIATE TAKEAWAYS

- **Don't benchmark agents on single tools** — real work requires browser + terminal + code + chat orchestration; single-tool benchmarks vastly overstate capability
- **If building agents, prioritize error recovery** — agents loop on failures instead of recovering; this is the #1 engineering improvement available now
- **Social/communication skills are the frontier** — invest in agent ↔ human protocols, not just tool-use; most agent frameworks ignore this entirely
- **Use checkpoint-based evaluation** in your own agent projects — binary pass/fail hides real progress signals
- **Cost matters**: Gemini 2.0 Flash achieves 11.4% at $0.60/task — **5× cheaper** than top models with 1/3 the performance; good enough for some production uses

---

## 🟡 SHOULD — Include Only If Present

### 📦 CODE & CONFIG

**Run the full benchmark locally**
```bash
# Clone and setup (Docker required, ~16GB RAM)
git clone https://github.com/TheAgentCompany/TheAgentCompany
cd TheAgentCompany
# Follow setup instructions to launch:
# - GitLab (source code)
# - Plane (project management)  
# - RocketChat (team messaging)
# - OwnCloud (file sharing)
# All self-hosted via Docker containers
```
⚠️ Requires: Docker, ~16GB RAM, LLM API key (for agent backbone)
💬 Key insight: NPC colleagues and LLM-as-judge evaluators are **always Claude-3.5-Sonnet** regardless of which model you're testing — this is the environment, not the agent

**Partial completion scoring formula**
```python
# S_partial = 0.5 * (checkpoint_points_earned / total_points) + 0.5 * S_full
# Where S_full = 1 only if ALL checkpoints pass, else 0
# This heavily rewards full completion (50% bonus) while still crediting partial progress

def partial_score(checkpoints_earned, total_points, all_passed):
    fractional = checkpoints_earned / total_points
    s_full = 1.0 if all_passed else 0.0
    return 0.5 * fractional + 0.5 * s_full
```
⚠️ Requires: Understanding that scores in the paper combine these two components
💬 Key insight: An agent completing 80% of checkpoints but failing the last one scores only 0.4 — the **binary bonus is massive**

### 📊 DIAGRAMS

#### Architecture — Animated SVG (open in browser for progressive reveal)
![TheAgentCompany Architecture](architecture_animated.svg)

<details><summary>📝 Text fallback (if SVG not rendering)</summary>

```
┌─────────────────────────────────────────────────────────────┐
│                    🤖 AGENT                                  │
│              OpenHands CodeAct / OWL RolePlay                │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              LOCAL WORKSPACE (Docker Sandbox)                 │
├──────────────────┬──────────────────┬───────────────────────┤
│   🌐 Browser     │   ⌨️ Terminal    │     📁 File I/O       │
│   (Playwright)   │   (Bash/Code)    │     (Read/Write)      │
└────────┬─────────┴──────────────────┴───────────────────────┘
         │ Browser navigates to ▼
┌────────┴────────────────────────────────────────────────────┐
│                    INTRANET (Docker)                          │
├──────────┬──────────┬──────────────┬────────────────────────┤
│  GitLab  │  Plane   │  RocketChat  │      OwnCloud          │
│  (Code)  │  (PM)    │  (Chat)      │      (Docs)            │
└──────────┴──────────┴──────┬───────┴────────────────────────┘
                             │
                             ▼
              ┌──────────────────────────┐
              │  👥 SIMULATED COLLEAGUES  │ ⚠️ Always Claude 3.5
              │  Claude 3.5 Sonnet NPCs  │    Sonnet backbone
              │  (via Sotopia platform)  │    (not agent under test)
              └──────────────────────────┘
─ ─ ─ ─ ─ ─ ─ ─ ─ EVALUATION LAYER ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
  ✅ Deterministic       🧑‍⚖️ LLM-as-Judge      ──►  S_partial
  (Python evaluators)    (Claude 3.5 Sonnet)      (0.5·frac + 0.5·full)
```
</details>

#### Performance Tiers — Animated SVG (bars grow to show relative scale)
![Model Performance Tiers](performance_animated.svg)

<details><summary>📝 Text fallback (if SVG not rendering)</summary>

```
MODEL PERFORMANCE — Success Rate (175 tasks)
═══════════════════════════════════════════════════════

TIER 1 (24-30%) ████████████████████████████████████████
  Gemini 2.5 Pro    ████████████████████████████████ 30.3%  $4.20
  Claude 3.7 Sonnet ███████████████████████████      26.3%  $4.10
  Claude 3.5 Sonnet ████████████████████████         24.0%  $6.30
                    ─── ~3× GAP ──────────────────────────

TIER 2 (7-11%)  ████████████
  Gemini 2.0 Flash  ████████████   11.4%  💰$0.60 (best value!)
  GPT-4o            █████████      8.6%   $1.30
  Llama 3.1 405B    ████████       7.4%   (open-weights)
                    ─── 2-5× GAP ─────────────────────────

TIER 3 (1-6%)   ██████
  Qwen 2.5 72B     ██████         5.7%   (open-weights)
  OWL RolePlay      ████           4.0%   (multi-agent — hurts!)
  Amazon Nova Pro   ██             1.7%
```
</details>

### 📈 DATA & BENCHMARKS

| What | Value | Significance |
|------|-------|--------------|
| **Best success rate** | Gemini 2.5 Pro: **30.3%** | Ceiling for autonomous task completion |
| **Best partial score** | Gemini 2.5 Pro: **39.3%** | ~9% hidden partial progress beyond full completion |
| **Claude 3.7 Sonnet** | 26.3% success / 36.4% partial | Strong #2, close to Gemini |
| **Claude 3.5 Sonnet** | 24.0% / 34.4% | Original SOTA at v1 publication |
| **GPT-4o** | 8.6% / 16.7% | Surprisingly weak — half the steps but worse |
| **Gemini 2.0 Flash** | 11.4% / 19.0% at **$0.60** | Best cost-efficiency ratio by far |
| **Llama 3.1 405B** | 7.4% / 14.1% | Best open-weights model |
| **Qwen 2.5 72B** | 5.7% / 11.8% | Open-weights competitive with Llama 70B |
| **OWL RolePlay (GPT-4o + o3-mini)** | 4.0% / 11.3% | Multi-agent framework, underperforms single-agent |
| **Total tasks** | 175 | Across SDE, PM, finance, HR, data science |
| **Avg steps (best)** | 27.2 | ~27 LLM calls per task even for top model |
| **Avg cost (best)** | $4.20/task | Non-trivial at scale |
| **Construction effort** | 3,000 person-hours | 20 people × 2+ months; some tasks >10hrs each |
| **Agent framework** | OpenHands CodeAct v0.14.2/v0.28.1 + OWL RolePlay | Browser + terminal + code execution |

### 🏗️ THE SIMULATED COMPANY (Environment Detail)

| Component | Tool | Real-world Equivalent |
|-----------|------|-----------------------|
| Code & repos | **GitLab** (self-hosted) | GitHub |
| Project mgmt | **Plane** | Jira / Linear |
| Communication | **RocketChat** | Slack |
| Documents | **OwnCloud** | Google Drive / SharePoint |
| NPC Colleagues | **Sotopia** platform + Claude 3.5 Sonnet | Your actual coworkers |

All services run via **Docker containers** — fully reproducible, no external dependencies. Environment data populated with real-world software project data + manually curated mock data.

### 🎯 TASK CATEGORIES

The 175 tasks span real professional work motivated by O\*NET job categories:

| Category | Focus | Example Task |
|----------|-------|--------------|
| **SDE** (Software Dev) | Code, CI/CD, repos | "Clone JanusGraph repo, build binary, launch server with HTTP endpoint" |
| **PM** (Project Mgmt) | Sprints, boards, tracking | "Create sprint board and assign tasks from backlog" |
| **Finance/Admin** | Expense reports, analysis | "Process Q3 expense reports, contact David Wong to resolve ambiguities" |
| **Data Science** | Analysis, visualization | "Analyze dataset and produce visualization report" |
| **HR/Other** | Onboarding, DevOps, QA | "Set up monitoring dashboard for service Y" |

### 📊 BENCHMARK COMPARISON MATRIX

| Feature | TheAgentCompany | SWE-bench | WebArena | GAIA | OSWorld |
|---------|:-:|:-:|:-:|:-:|:-:|
| Multi-tool orchestration | ✅ | ❌ | ❌ | Partial | Partial |
| Social/communication tasks | ✅ | ❌ | ❌ | ❌ | ❌ |
| Checkpoint partial credit | ✅ | ❌ | ❌ | ❌ | ✅ |
| Self-hosted/reproducible | ✅ | ✅ | ✅ | ❌ | ✅ |
| O\*NET labor market grounding | ✅ | ❌ | ❌ | ❌ | ❌ |
| Long-horizon tasks | ✅ | ✅ | ❌ | ✅ | Partial |
| Code + Web + Chat combined | ✅ | Code only | Web only | Mixed | OS only |

**Key differentiator**: TheAgentCompany is the **only benchmark combining code, project management, communication, and social interaction** in a unified realistic environment.

---

## 🟢 COULD — Include If Notably Valuable

- **🧠 Mental Model**: **The Integration Tax** — Agent intelligence ≠ agent capability. The gap between "can reason about the task" and "can orchestrate across 4 web tools + terminal + chat to complete it" is the dominant bottleneck. Raw IQ is necessary but not sufficient; **executive function** (planning, switching, error recovery) is the binding constraint.

- **🧠 Mental Model**: **O\*NET-grounded evaluation** — By rooting task selection in the US Department of Labor's job/task database weighted by employment × salary, this benchmark makes the first credible attempt at connecting agent benchmarks to **labor market economic analysis**. This methodology (not just the results) is worth replicating.

- **📌 Quotable**: The paper cautions against drawing conclusions about full job automation, noting they measure certain **tasks within jobs**, not whole jobs — and emphasize the need for further labor analysis by professionals.

- **🐛 Gotcha**: **GPT-4o's low step count (14.6) masks early surrender** — it gives up faster rather than exploring, inflating its efficiency but tanking its success rate. Step count alone is misleading.

- **🐛 Gotcha**: **NPC backbone bias** — All simulated colleagues run on Claude 3.5 Sonnet regardless of which model is being tested. Claude agents may have a subtle communication advantage when talking to Claude-backed NPCs. The paper acknowledges this but doesn't measure the effect.

- **🐛 Gotcha**: **Gemini 2.0 Flash averages 40 steps** — the highest of any model — because it gets stuck in loops and aimless exploration, yet still achieves 11.4% through sheer volume of attempts.

- **🐛 Gotcha**: **OWL RolePlay multi-agent (4.0%) underperforms single-agent OpenHands (8.6%)** both using GPT-4o — multi-agent coordination overhead can actually hurt on this benchmark.

- **❓ Follow-up**: Would a **specialist multi-agent architecture** (one agent per tool: GitLab, Plane, RocketChat) with a coordinator outperform the generalist? OWL's poor result suggests naive multi-agent doesn't help, but better orchestration might.

- **❓ Follow-up**: How would **RAG-augmented agents** perform? Many failures stem from agents not knowing where to find information in the company intranet. A retrieval layer over company docs could unlock significant gains.

- **❓ Follow-up**: What's the **human baseline** completion time and accuracy? The paper establishes agent performance but doesn't run controlled human studies.

- **❓ Follow-up**: Could **better prompting or scaffolding** (e.g., chain-of-thought plans, tool-use schemas) close the gap without changing the underlying model? The paper only tests default OpenHands prompts.

---

## 💡 PLAYGROUP DISCUSSION PROMPTS

1. **The 30% ceiling** — What architectural changes could push this significantly higher? Is ReAct/CodeAct the right paradigm, or do we need fundamentally different agent designs?

2. **Social skills gap** — How would you design an agent that can effectively communicate with coworkers? What's missing from current approaches? How does the Sotopia NPC framework shape the difficulty?

3. **Multi-agent potential** — OWL RolePlay's 4% vs OpenHands' 8.6% (both GPT-4o) suggests naive multi-agent hurts. What would an *effective* multi-agent architecture look like for this benchmark?

4. **Practical implications** — At 30%, where does this say we should/shouldn't deploy agents in real companies today? What's the ROI at $4.20/task?

5. **Connection to your work** — How do RAG-based knowledge retrieval and multi-agent orchestration connect to the gaps exposed here? Could better knowledge agents help with the "ambiguous requirements" failure mode?

6. **Evaluation methodology** — Is the `0.5 × fractional + 0.5 × S_full` formula the right way to measure? Does the 50% binary bonus distort the picture?

7. **Cost economics** — Gemini Flash at $0.60 vs Gemini Pro at $4.20 — is 11% vs 30% worth 7× the cost? When does each make sense?

---

## 🛠️ HANDS-ON SESSION PLAN

### Morning: Understand & Explore (2-3 hrs)

**Quick orientation (20 min)**
- Walk through this distilled doc as a group

**Repo exploration (30 min)**
- Browse [github.com/TheAgentCompany/TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany)
- Examine 3-4 task JSONs across different categories
- Look at the Docker Compose setup — understand the infrastructure

**Deep-dive: Evaluation design (30 min)**
- Study the partial scoring formula and checkpoint design
- Is this the right way to measure agent capability?

**Leaderboard check (20 min)**
- Review [the-agent-company.com](https://the-agent-company.com) for any newer results since v3

**Discussion round 1 (30 min)**
- What makes these tasks hard for agents but easy for humans?
- Where are the failure modes?

### Afternoon: Analyze, Design & Connect (3 hrs)

**Failure analysis exercise (60 min)**
- Pick 3 tasks where the best agent fails
- Hypothesize why using the common failure patterns from §7.3
- Design an improved agent architecture targeting those specific failures

**Social tasks deep-dive (45 min)**
- Study the Sotopia/NPC colleague system
- How would you design better agent ↔ human communication protocols?
- Can your multi-agent orchestration research inform this?

**Connection to your work (45 min)**
- How do RAG agents and knowledge retrieval connect to the gaps?
- Could document intelligence (your Docling/PDF extraction work) help agents navigate OwnCloud?
- Multi-agent orchestration: what would you do differently than OWL RolePlay?

**Wrap-up & action items (30 min)**
- Key takeaways
- What to build next
- Follow-up resources and experiments

---

## 📚 KEY REFERENCES

| Resource | Link |
|----------|------|
| **Paper** | [arxiv.org/abs/2412.14161](https://arxiv.org/abs/2412.14161) |
| **Website** | [the-agent-company.com](https://the-agent-company.com) |
| **Code** | [github.com/TheAgentCompany/TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany) |
| **Experiments** | [github.com/TheAgentCompany/experiments](https://github.com/TheAgentCompany/experiments) |
| **OpenHands agent** | [github.com/All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands) |
| **Sotopia (NPC framework)** | Referenced in paper for simulated colleagues |
| **O\*NET database** | US Dept of Labor job/task database used for task selection |

---

*Distilled using content-distiller MoSCoW framework, augmented with playgroup session planning*
*Source: Xu et al., "TheAgentCompany: Benchmarking LLM Agents on Consequential Real World Tasks", v3 Sep 2025*
*Prepared for playgroup session — Feb 2026*
