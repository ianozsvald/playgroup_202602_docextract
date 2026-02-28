#!/usr/bin/env python3
"""
playground.py — Generate an interactive HTML analysis playground for model extraction results.

Usage: uv run python playground.py
Output: playground.html  (open in any browser, fully self-contained)
"""

import json
from pathlib import Path

DATA_DIR = Path("data")
EXPECTED_FILE = DATA_DIR / "playgroup_dev_expected.tsv"
OUTPUT_FILE = Path("which-models-extracted-playground.html")

FIELDS = [
    "charity_number",
    "charity_name",
    "report_date",
    "income_annually_in_british_pounds",
    "spending_annually_in_british_pounds",
    "address__postcode",
    "address__post_town",
    "address__street_line",
]

FIELD_LABELS = {
    "charity_number": "Charity No.",
    "charity_name": "Charity Name",
    "report_date": "Report Date",
    "income_annually_in_british_pounds": "Income (£)",
    "spending_annually_in_british_pounds": "Spending (£)",
    "address__postcode": "Postcode",
    "address__post_town": "Post Town",
    "address__street_line": "Street Line",
}

FIELD_GROUPS = {
    "identity": ["charity_number", "charity_name", "report_date"],
    "financial": ["income_annually_in_british_pounds", "spending_annually_in_british_pounds"],
    "address": ["address__postcode", "address__post_town", "address__street_line"],
}


def load_model_meta() -> dict:
    """Read tier, pricing and modality info from config_models.py's VALUE_MODELS."""
    try:
        from config_models import VALUE_MODELS
    except ImportError:
        return {}
    meta = {}
    for short_name, cfg in VALUE_MODELS.items():
        if not isinstance(cfg, dict):
            continue
        raw_tier = cfg.get("tier", "unknown")
        # normalise underscore tiers → hyphen for display consistency
        tier = raw_tier.replace("_", "-")
        meta[short_name] = {
            "tier":       tier,
            "price_in":   cfg.get("price_in"),
            "price_out":  cfg.get("price_out"),
            "multimodal": cfg.get("multimodal", False),
            "modalities": cfg.get("modalities", []),
            "ctx":        cfg.get("ctx"),
            "notes":      cfg.get("notes", ""),
        }
    return meta


# ── Parsing ──────────────────────────────────────────────────────────────────

def _parse_kv_parts(parts: list[str], target: dict) -> None:
    for part in parts:
        if "=" in part:
            key, _, val = part.partition("=")
            target[key.strip()] = val.strip()


def parse_tsv(filepath: Path) -> list[dict]:
    """Parse extracted TSV, handling:
    - Blank lines  → empty document row {} (model skipped that doc)
    - Error lines  → {'__error__': True}
    - Continuation → first token has no '=', merged into previous row
    - Normal lines → new document row
    """
    rows = []
    pending: dict | None = None
    try:
        lines = filepath.read_text(encoding="utf-8").split("\n")
        # strip trailing blank lines so they don't create phantom empty rows
        while lines and not lines[-1].strip():
            lines.pop()

        for raw in lines:
            line = raw.strip()

            if not line:
                # blank = explicitly skipped document
                if pending is not None:
                    rows.append(pending)
                    pending = None
                rows.append({})
                continue

            parts = line.split("\t")
            first = parts[0]

            if first.startswith("error="):
                if pending is not None:
                    rows.append(pending)
                    pending = None
                rows.append({"__error__": True})
                continue

            if "=" not in first:
                # continuation line (model put a newline inside a field value)
                if pending is not None:
                    _parse_kv_parts(parts, pending)
                continue

            # new document row
            if pending is not None:
                rows.append(pending)
            pending = {}
            _parse_kv_parts(parts, pending)

    except Exception:
        pass

    if pending is not None:
        rows.append(pending)
    return rows


# ── Scoring ───────────────────────────────────────────────────────────────────

def score_model(expected_rows: list, extracted_rows: list) -> dict:
    per_field = {f: {"correct": 0, "missing": 0, "wrong": 0} for f in FIELDS}
    per_doc = []
    total_correct = 0
    total_expected = 0

    for row_idx, expected_row in enumerate(expected_rows):
        extracted_row = extracted_rows[row_idx] if row_idx < len(extracted_rows) else {}
        is_error = bool(extracted_row.get("__error__"))

        doc = {"correct": 0, "total": 0, "accuracy": 0.0, "is_error": is_error, "fields": {}}

        for field, expected_val in expected_row.items():
            if field.startswith("__"):
                continue
            doc["total"] += 1
            total_expected += 1

            if is_error or field not in extracted_row:
                per_field.setdefault(field, {"correct": 0, "missing": 0, "wrong": 0})["missing"] += 1
                doc["fields"][field] = {"expected": expected_val, "got": None, "status": "missing"}
            elif extracted_row[field] == expected_val:
                per_field.setdefault(field, {"correct": 0, "missing": 0, "wrong": 0})["correct"] += 1
                doc["correct"] += 1
                total_correct += 1
                doc["fields"][field] = {"expected": expected_val, "got": extracted_row[field], "status": "correct"}
            else:
                per_field.setdefault(field, {"correct": 0, "missing": 0, "wrong": 0})["wrong"] += 1
                doc["fields"][field] = {"expected": expected_val, "got": extracted_row[field], "status": "wrong"}

        doc["accuracy"] = doc["correct"] / doc["total"] if doc["total"] > 0 else 0.0
        per_doc.append(doc)

    return {
        "total_correct": total_correct,
        "total_expected": total_expected,
        "accuracy": total_correct / total_expected if total_expected > 0 else 0.0,
        "per_field": per_field,
        "per_doc": per_doc,
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    expected_rows = parse_tsv(EXPECTED_FILE)

    doc_names = []
    for i, row in enumerate(expected_rows):
        name = row.get("charity_name", f"Document {i + 1}").replace("_", " ")
        doc_names.append(name)

    model_meta = load_model_meta()
    models_data = {}
    for model_file in sorted(DATA_DIR.glob("playgroup_dev_extracted__*.tsv")):
        model_name = model_file.stem.replace("playgroup_dev_extracted__", "")
        extracted_rows = parse_tsv(model_file)
        scores = score_model(expected_rows, extracted_rows)
        models_data[model_name] = scores
        mm_tag = "MM" if model_meta.get(model_name, {}).get("multimodal") else "text"
        print(f"  {model_name:35s}  {mm_tag:<6}  {scores['accuracy']:5.1%}  ({scores['total_correct']}/{scores['total_expected']})")
    payload = {
        "models": models_data,
        "fields": FIELDS,
        "field_labels": FIELD_LABELS,
        "field_groups": FIELD_GROUPS,
        "model_meta": model_meta,
        "doc_names": doc_names,
        "expected": expected_rows,
    }

    html = HTML_TEMPLATE.replace("/*__DATA__*/null", json.dumps(payload))
    OUTPUT_FILE.write_text(html)
    print(f"\nWrote {OUTPUT_FILE}  —  open in your browser")


# ── HTML Template ─────────────────────────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Model Extraction Playground</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<style>
:root{
  --bg:#f8fafc;--surface:#fff;--surface2:#f1f5f9;--border:#e2e8f0;
  --text:#0f172a;--muted:#64748b;--accent:#6366f1;
  --green:#10b981;--yellow:#f59e0b;--orange:#f97316;--red:#ef4444;--blue:#3b82f6;
  --correct:#10b981;--wrong:#f97316;--missing:#ef4444;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,sans-serif;background:var(--bg);color:var(--text);font-size:14px;line-height:1.5}
header{background:var(--accent);color:#fff;padding:18px 28px}
header h1{font-size:22px;font-weight:700}
header p{font-size:13px;opacity:.85;margin-top:2px}
.tabs{display:flex;gap:2px;background:var(--surface2);padding:8px 28px 0;border-bottom:1px solid var(--border);overflow-x:auto}
.tab-btn{padding:8px 16px;border:none;background:transparent;cursor:pointer;font-size:13px;font-weight:500;color:var(--muted);border-radius:6px 6px 0 0;white-space:nowrap;transition:all .15s}
.tab-btn.active{background:var(--surface);color:var(--accent);border-bottom:2px solid var(--accent);margin-bottom:-1px}
.tab-btn:hover:not(.active){background:var(--surface);color:var(--text)}
.tab-panel{display:none;padding:24px 28px}
.tab-panel.active{display:block}
.stats-bar{display:flex;gap:16px;margin-bottom:24px;flex-wrap:wrap}
.stat-card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:14px 20px;min-width:140px}
.stat-card .val{font-size:26px;font-weight:700;color:var(--accent)}
.stat-card .lbl{font-size:12px;color:var(--muted);margin-top:2px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px;margin-bottom:20px}
.card h2{font-size:15px;font-weight:600;margin-bottom:14px;color:var(--text)}
.card h3{font-size:13px;font-weight:600;margin-bottom:10px;color:var(--muted)}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;padding:8px 10px;background:var(--surface2);border-bottom:1px solid var(--border);font-weight:600;white-space:nowrap}
td{padding:7px 10px;border-bottom:1px solid var(--border)}
tr:last-child td{border-bottom:none}
tr:hover td{background:var(--surface2)}
.badge{display:inline-block;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600}
.badge-green{background:#dcfce7;color:#166534}
.badge-blue{background:#dbeafe;color:#1e40af}
.badge-yellow{background:#fef9c3;color:#854d0e}
.badge-orange{background:#ffedd5;color:#9a3412}
.badge-red{background:#fee2e2;color:#991b1b}
.badge-gray{background:#f1f5f9;color:#475569}
.heatmap{overflow-x:auto}
.heatmap table td,.heatmap table th{padding:5px 6px;text-align:center;font-size:12px;white-space:nowrap}
.heatmap table th{font-size:11px;background:var(--surface2)}
.hm-cell{border-radius:4px;width:48px;height:28px;display:flex;align-items:center;justify-content:center;font-weight:600;font-size:11px;color:#fff;cursor:default}
.chart-wrap{position:relative;height:340px}
.chart-wrap-lg{position:relative;height:460px}
.chart-wrap-sm{position:relative;height:240px}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media(max-width:768px){.two-col{grid-template-columns:1fr}}
select,button.ctrl{padding:6px 12px;border:1px solid var(--border);border-radius:6px;background:var(--surface);font-size:13px;cursor:pointer}
.ctrl-row{display:flex;gap:10px;align-items:center;margin-bottom:16px;flex-wrap:wrap}
.diff-table td{font-family:monospace;font-size:12px}
.diff-correct{background:#dcfce7}
.diff-wrong{background:#ffedd5}
.diff-missing{background:#fee2e2}
.insight{background:var(--surface2);border-left:3px solid var(--accent);padding:10px 14px;border-radius:0 6px 6px 0;margin-bottom:10px;font-size:13px}
.insight strong{color:var(--accent)}
.insight-warn{border-color:var(--orange)}
.insight-warn strong{color:var(--orange)}
.insight-tip{border-color:var(--green)}
.insight-tip strong{color:var(--green)}
.rank-bar-wrap{background:var(--surface2);border-radius:4px;height:18px;overflow:hidden;min-width:120px}
.rank-bar{height:100%;border-radius:4px;transition:width .4s ease}
.sort-btn{background:none;border:none;cursor:pointer;font-size:12px;color:var(--muted);padding:0 4px}
.sort-btn.asc::after{content:" ▲"}
.sort-btn.desc::after{content:" ▼"}
.legend{display:flex;gap:14px;margin-bottom:12px;flex-wrap:wrap}
.legend-item{display:flex;align-items:center;gap:5px;font-size:12px}
.legend-dot{width:12px;height:12px;border-radius:50%}
</style>
</head>
<body>

<header>
  <h1>Model Extraction Playground</h1>
  <p>Interactive analysis of LLM performance on charity document data extraction</p>
</header>

<div class="tabs">
  <button class="tab-btn active" onclick="switchTab('rankings')">Rankings</button>
  <button class="tab-btn" onclick="switchTab('field-heatmap')">Field Heatmap</button>
  <button class="tab-btn" onclick="switchTab('doc-analysis')">Document Analysis</button>
  <button class="tab-btn" onclick="switchTab('errors')">Error Breakdown</button>
  <button class="tab-btn" onclick="switchTab('deepdive')">Deep Dive</button>
  <button class="tab-btn" onclick="switchTab('recommendations')">Recommendations</button>
</div>

<!-- ═══════════════════════════════ RANKINGS ═══════════════════════════════ -->
<div id="tab-rankings" class="tab-panel active">
  <div class="stats-bar" id="stats-bar"></div>
  <div class="two-col">
    <div class="card" style="min-width:0">
      <h2>Model Leaderboard</h2>
      <div class="ctrl-row">
        <label>Sort by:
          <select id="rank-sort" onchange="renderRankTable()">
            <option value="accuracy">Overall Accuracy</option>
            <option value="correct">Correct Extractions</option>
            <option value="wrong">Wrong (fewest)</option>
            <option value="missing">Missing (fewest)</option>
          </select>
        </label>
        <label>Filter:
          <select id="rank-filter" onchange="renderRankTable()">
            <option value="all">All Models</option>
            <option value="active">Functional Only</option>
            <option value="free">Free tier only</option>
            <option value="ultra-cheap">≤ Ultra-cheap</option>
            <option value="great-value">≤ Great Value</option>
          </select>
        </label>
      </div>
      <div id="rank-table-wrap" style="overflow-x:auto"></div>
    </div>
    <div class="card" style="min-width:0">
      <h2>Accuracy Overview</h2>
      <div class="chart-wrap"><canvas id="chart-accuracy"></canvas></div>
    </div>
  </div>
</div>

<!-- ════════════════════════════ FIELD HEATMAP ════════════════════════════ -->
<div id="tab-field-heatmap" class="tab-panel">
  <div class="card">
    <h2>Field-Level Accuracy Heatmap</h2>
    <p style="font-size:12px;color:var(--muted);margin-bottom:14px">Each cell shows how accurately a model extracted that field across all 11 documents. Click a cell for details.</p>
    <div class="ctrl-row">
      <label>Show:
        <select id="hm-filter" onchange="renderFieldHeatmap()">
          <option value="all">All models</option>
          <option value="active">Functional only</option>
        </select>
      </label>
    </div>
    <div class="heatmap" id="field-heatmap"></div>
  </div>
  <div class="two-col">
    <div class="card">
      <h2>Best Model per Field</h2>
      <div id="best-per-field"></div>
    </div>
    <div class="card">
      <h2>Field Difficulty Ranking</h2>
      <p style="font-size:12px;color:var(--muted);margin-bottom:12px">Average accuracy across all functional models</p>
      <div class="chart-wrap-sm"><canvas id="chart-field-diff"></canvas></div>
    </div>
  </div>
</div>

<!-- ══════════════════════════ DOCUMENT ANALYSIS ══════════════════════════ -->
<div id="tab-doc-analysis" class="tab-panel">
  <div class="card">
    <h2>Document × Model Accuracy Heatmap</h2>
    <p style="font-size:12px;color:var(--muted);margin-bottom:14px">Each cell shows accuracy for a specific document/model pair.</p>
    <div class="ctrl-row">
      <label>Models:
        <select id="doc-hm-filter" onchange="renderDocHeatmap()">
          <option value="active">Functional only</option>
          <option value="all">All</option>
        </select>
      </label>
    </div>
    <div class="heatmap" id="doc-heatmap"></div>
  </div>
  <div class="card">
    <h2>Document Difficulty (avg accuracy across functional models)</h2>
    <div class="chart-wrap-sm"><canvas id="chart-doc-diff"></canvas></div>
  </div>
</div>

<!-- ══════════════════════════ ERROR BREAKDOWN ════════════════════════════ -->
<div id="tab-errors" class="tab-panel">
  <div class="card">
    <h2>Error Category Breakdown per Model</h2>
    <div class="legend">
      <div class="legend-item"><div class="legend-dot" style="background:var(--correct)"></div>Correct</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--wrong)"></div>Wrong value</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--missing)"></div>Missing</div>
    </div>
    <div class="chart-wrap-lg"><canvas id="chart-errors"></canvas></div>
  </div>
  <div class="card">
    <h2>Common Error Patterns</h2>
    <div id="error-patterns"></div>
  </div>
</div>

<!-- ═════════════════════════════ DEEP DIVE ═══════════════════════════════ -->
<div id="tab-deepdive" class="tab-panel">
  <div class="card">
    <h2>Per-Document Field Comparison</h2>
    <div class="ctrl-row">
      <label>Model:
        <select id="dd-model" onchange="renderDeepDive()"></select>
      </label>
      <label>Document:
        <select id="dd-doc" onchange="renderDeepDive()"></select>
      </label>
    </div>
    <div id="dd-output"></div>
  </div>
</div>

<!-- ══════════════════════════ RECOMMENDATIONS ════════════════════════════ -->
<div id="tab-recommendations" class="tab-panel">
  <div class="card">
    <h2>Decision Helper</h2>
    <div class="ctrl-row">
      <label>Use case:
        <select id="rec-usecase" onchange="renderRecommendations()">
          <option value="all">All fields — full extraction</option>
          <option value="identity">Identity fields only (number, name, date)</option>
          <option value="financial">Financial fields only (income, spending)</option>
          <option value="address">Address fields only (postcode, town, street)</option>
        </select>
      </label>
      <label>Budget:
        <select id="rec-budget" onchange="renderRecommendations()">
          <option value="any">Any cost</option>
          <option value="free">Free only</option>
          <option value="ultra-cheap">≤ Ultra-cheap</option>
          <option value="great-value">≤ Great Value</option>
          <option value="premium">All (incl. Premium)</option>
        </select>
      </label>
    </div>
    <div id="rec-output"></div>
  </div>
  <div class="card">
    <h2>Key Insights</h2>
    <div id="insights"></div>
  </div>
  <div class="card">
    <h2>Improvement Suggestions</h2>
    <div id="improvements"></div>
  </div>
</div>

<script>
const RAW = /*__DATA__*/null;

// ── Helpers ───────────────────────────────────────────────────────────────

function pct(n){ return (n*100).toFixed(1)+'%' }
function hsl(v){ // 0→red, 0.5→yellow, 1→green
  const h = v < 0.5 ? v*120 : 60 + (v-0.5)*120;
  return `hsl(${h.toFixed(0)},70%,42%)`
}
function bgAlpha(v){ // for cell backgrounds
  const h = v < 0.5 ? v*120 : 60 + (v-0.5)*120;
  return `hsla(${h.toFixed(0)},70%,42%,${(0.15 + v*0.75).toFixed(2)})`
}
function tier(v){
  if(v>=0.8) return {cls:'badge-green',label:'Excellent'}
  if(v>=0.6) return {cls:'badge-blue',label:'Good'}
  if(v>=0.4) return {cls:'badge-yellow',label:'Fair'}
  if(v>=0.1) return {cls:'badge-orange',label:'Poor'}
  return {cls:'badge-red',label:'Failed'}
}
function isActive(m){
  return RAW.models[m].accuracy > 0
}
function activeModels(){
  return Object.keys(RAW.models).filter(isActive)
}
function allModels(){
  return Object.keys(RAW.models)
}
const TIER_ORDER = ['free','ultra-cheap','great-value','premium']
function tierLabel(t){
  return {'free':'Free','ultra-cheap':'Ultra-cheap','great-value':'Great Value','premium':'Premium'}[t]||t
}
function tierBadgeCls(t){
  return {'free':'badge-gray','ultra-cheap':'badge-blue','great-value':'badge-green','premium':'badge-yellow'}[t]||'badge-gray'
}
function costTierBadge(m){
  const t = RAW.model_meta?.[m]?.tier || 'unknown'
  return `<span class="badge ${tierBadgeCls(t)}">${tierLabel(t)}</span>`
}

// ── Tab switching ─────────────────────────────────────────────────────────

const initialized = new Set()
function switchTab(id){
  document.querySelectorAll('.tab-btn').forEach((b,i)=>{
    b.classList.toggle('active', b.getAttribute('onclick').includes("'"+id+"'"))
  })
  document.querySelectorAll('.tab-panel').forEach(p=>{
    p.classList.toggle('active', p.id === 'tab-'+id)
  })
  if(!initialized.has(id)){
    initialized.add(id)
    if(id==='rankings') renderRankings()
    if(id==='field-heatmap') renderFieldHeatmap(), renderBestPerField(), renderFieldDifficulty()
    if(id==='doc-analysis') renderDocHeatmap(), renderDocDifficulty()
    if(id==='errors') renderErrorChart(), renderErrorPatterns()
    if(id==='deepdive') initDeepDive()
    if(id==='recommendations') renderRecommendations(), renderInsights(), renderImprovements()
  }
}

// ── ① Rankings ────────────────────────────────────────────────────────────

let chartAccuracy = null

function renderRankings(){
  // Stats bar
  const mods = allModels()
  const active = activeModels()
  const totalFields = Object.values(RAW.models[active[0]]?.per_field||{}).reduce((s,f)=>s+f.correct+f.missing+f.wrong,0)
  document.getElementById('stats-bar').innerHTML = `
    <div class="stat-card"><div class="val">${mods.length}</div><div class="lbl">Models tested</div></div>
    <div class="stat-card"><div class="val">${active.length}</div><div class="lbl">Functional models</div></div>
    <div class="stat-card"><div class="val">${RAW.doc_names.length}</div><div class="lbl">Documents</div></div>
    <div class="stat-card"><div class="val">${RAW.fields.length}</div><div class="lbl">Fields per document</div></div>
    <div class="stat-card"><div class="val">${mods.length - active.length}</div><div class="lbl">Rate-limited / failed</div></div>
  `
  renderRankTable()
  renderAccuracyChart()
}

function rankRows(){
  const sort = document.getElementById('rank-sort').value
  const filter = document.getElementById('rank-filter').value
  const tierBudgets = {'free':['free'],'ultra-cheap':['free','ultra-cheap'],'great-value':['free','ultra-cheap','great-value']}
  let models = allModels()
  if(filter==='active') models = activeModels()
  else if(tierBudgets[filter]) models = models.filter(m=>tierBudgets[filter].includes(RAW.model_meta?.[m]?.tier))
  return models.map(m=>{
    const d = RAW.models[m]
    let correct=0,wrong=0,missing=0
    for(const f of Object.values(d.per_field)){
      correct+=f.correct; wrong+=f.wrong; missing+=f.missing
    }
    return {m, acc:d.accuracy, correct, wrong, missing, total:d.total_expected}
  }).sort((a,b)=>{
    if(sort==='accuracy') return b.acc - a.acc
    if(sort==='correct') return b.correct - a.correct
    if(sort==='wrong') return a.wrong - b.wrong
    if(sort==='missing') return a.missing - b.missing
    return 0
  })
}

function renderRankTable(){
  const rows = rankRows()
  const best = rows[0]?.acc || 1
  let html = `<table><thead><tr>
    <th>#</th><th>Model</th><th>Accuracy</th><th>Score bar</th>
    <th>Correct</th><th>Wrong</th><th>Missing</th><th>Perf.</th><th>Cost</th>
  </tr></thead><tbody>`
  rows.forEach((r,i)=>{
    const t = tier(r.acc)
    html += `<tr>
      <td style="color:var(--muted)">${i+1}</td>
      <td><strong>${r.m}</strong></td>
      <td><strong style="color:${hsl(r.acc)}">${pct(r.acc)}</strong></td>
      <td>
        <div class="rank-bar-wrap">
          <div class="rank-bar" style="width:${(r.acc/Math.max(best,0.01)*100).toFixed(1)}%;background:${hsl(r.acc)}"></div>
        </div>
      </td>
      <td style="color:var(--correct)">${r.correct}</td>
      <td style="color:var(--wrong)">${r.wrong}</td>
      <td style="color:var(--missing)">${r.missing}</td>
      <td><span class="badge ${t.cls}">${t.label}</span></td>
      <td>${costTierBadge(r.m)}</td>
    </tr>`
  })
  html += '</tbody></table>'
  document.getElementById('rank-table-wrap').innerHTML = html
}

function renderAccuracyChart(){
  const rows = rankRows()
  const ctx = document.getElementById('chart-accuracy').getContext('2d')
  if(chartAccuracy) chartAccuracy.destroy()
  chartAccuracy = new Chart(ctx, {
    type:'bar',
    data:{
      labels: rows.map(r=>r.m),
      datasets:[{
        label:'Accuracy',
        data: rows.map(r=>+(r.acc*100).toFixed(1)),
        backgroundColor: rows.map(r=>bgAlpha(r.acc)),
        borderColor: rows.map(r=>hsl(r.acc)),
        borderWidth:1,
        borderRadius:4,
      }]
    },
    options:{
      indexAxis:'y',
      responsive:true,
      maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>`${ctx.parsed.x.toFixed(1)}%`}}},
      scales:{
        x:{min:0,max:100,ticks:{callback:v=>v+'%'},grid:{color:'#e2e8f0'}},
        y:{ticks:{font:{size:11}}}
      }
    }
  })
}

// ── ② Field Heatmap ───────────────────────────────────────────────────────

function renderFieldHeatmap(){
  const filter = document.getElementById('hm-filter').value
  const models = filter==='active' ? activeModels() : allModels()
  const fields = RAW.fields
  const labels = RAW.field_labels

  let html = '<table><thead><tr><th>Model</th>'
  for(const f of fields) html += `<th title="${f}">${labels[f]}</th>`
  html += '</tr></thead><tbody>'

  for(const m of models){
    html += `<tr><td style="font-size:12px;font-weight:600;white-space:nowrap">${m}</td>`
    const pf = RAW.models[m].per_field
    for(const f of fields){
      const fd = pf[f] || {correct:0,missing:0,wrong:0}
      const total = fd.correct + fd.missing + fd.wrong
      const acc = total > 0 ? fd.correct/total : 0
      const txt = total > 0 ? pct(acc) : '—'
      const tooltip = `Correct: ${fd.correct}, Wrong: ${fd.wrong}, Missing: ${fd.missing}`
      html += `<td title="${tooltip}">
        <div class="hm-cell" style="background:${total>0?bgAlpha(acc):'#f1f5f9'};color:${total>0?hsl(acc):'#94a3b8'}">${txt}</div>
      </td>`
    }
    html += '</tr>'
  }
  html += '</tbody></table>'
  document.getElementById('field-heatmap').innerHTML = html
}

function renderBestPerField(){
  const models = activeModels()
  const fields = RAW.fields
  let html = '<table><thead><tr><th>Field</th><th>Best Model</th><th>Accuracy</th><th>Runner-up</th></tr></thead><tbody>'
  for(const f of fields){
    const scores = models.map(m=>{
      const fd = RAW.models[m].per_field[f] || {correct:0,missing:0,wrong:0}
      const total = fd.correct+fd.missing+fd.wrong
      return {m, acc: total>0 ? fd.correct/total : 0}
    }).sort((a,b)=>b.acc-a.acc)
    const best = scores[0]
    const runner = scores[1]
    html += `<tr>
      <td>${RAW.field_labels[f]}</td>
      <td><strong>${best.m}</strong></td>
      <td style="color:${hsl(best.acc)};font-weight:600">${pct(best.acc)}</td>
      <td style="color:var(--muted)">${runner?`${runner.m} (${pct(runner.acc)})`:'—'}</td>
    </tr>`
  }
  html += '</tbody></table>'
  document.getElementById('best-per-field').innerHTML = html
}

let chartFieldDiff = null
function renderFieldDifficulty(){
  const models = activeModels()
  const fields = RAW.fields
  const avgAcc = fields.map(f=>{
    const accs = models.map(m=>{
      const fd = RAW.models[m].per_field[f]||{correct:0,missing:0,wrong:0}
      const total = fd.correct+fd.missing+fd.wrong
      return total>0 ? fd.correct/total : 0
    })
    return {f, avg: accs.reduce((s,v)=>s+v,0)/accs.length}
  }).sort((a,b)=>a.avg-b.avg)

  const ctx = document.getElementById('chart-field-diff').getContext('2d')
  if(chartFieldDiff) chartFieldDiff.destroy()
  chartFieldDiff = new Chart(ctx,{
    type:'bar',
    data:{
      labels: avgAcc.map(x=>RAW.field_labels[x.f]),
      datasets:[{
        label:'Avg accuracy',
        data: avgAcc.map(x=>+(x.avg*100).toFixed(1)),
        backgroundColor: avgAcc.map(x=>bgAlpha(x.avg)),
        borderColor: avgAcc.map(x=>hsl(x.avg)),
        borderWidth:1, borderRadius:4
      }]
    },
    options:{
      indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`${c.parsed.x.toFixed(1)}%`}}},
      scales:{
        x:{min:0,max:100,ticks:{callback:v=>v+'%'},grid:{color:'#e2e8f0'}},
        y:{ticks:{font:{size:11}}}
      }
    }
  })
}

// ── ③ Document Analysis ───────────────────────────────────────────────────

function renderDocHeatmap(){
  const filter = document.getElementById('doc-hm-filter').value
  const models = filter==='active' ? activeModels() : allModels()
  const docs = RAW.doc_names

  let html = '<table><thead><tr><th>Document</th>'
  for(const m of models) html += `<th style="writing-mode:vertical-lr;transform:rotate(180deg);height:80px;font-size:10px">${m}</th>`
  html += '</tr></thead><tbody>'

  for(let di=0; di<docs.length; di++){
    html += `<tr><td style="font-size:12px;max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${docs[di]}">${docs[di]}</td>`
    for(const m of models){
      const pd = RAW.models[m].per_doc[di]
      if(!pd){html += `<td><div class="hm-cell" style="background:#f1f5f9;color:#94a3b8">—</div></td>`;continue}
      const acc = pd.accuracy
      const txt = pd.is_error ? 'ERR' : pct(acc)
      const tooltip = pd.is_error ? 'Rate limit error' : `${pd.correct}/${pd.total}`
      html += `<td title="${tooltip}"><div class="hm-cell" style="background:${pd.is_error?'#fee2e2':bgAlpha(acc)};color:${pd.is_error?'#991b1b':hsl(acc)}">${txt}</div></td>`
    }
    html += '</tr>'
  }
  html += '</tbody></table>'
  document.getElementById('doc-heatmap').innerHTML = html
}

let chartDocDiff = null
function renderDocDifficulty(){
  const models = activeModels()
  const docs = RAW.doc_names
  const avgs = docs.map((name,di)=>{
    const accs = models.map(m=>{
      const pd = RAW.models[m].per_doc[di]
      return (pd && !pd.is_error) ? pd.accuracy : 0
    })
    return {name, avg: accs.reduce((s,v)=>s+v,0)/accs.length}
  })
  const sorted = [...avgs].sort((a,b)=>a.avg-b.avg)
  const ctx = document.getElementById('chart-doc-diff').getContext('2d')
  if(chartDocDiff) chartDocDiff.destroy()
  chartDocDiff = new Chart(ctx,{
    type:'bar',
    data:{
      labels: sorted.map(x=>x.name.length>30?x.name.slice(0,28)+'…':x.name),
      datasets:[{
        label:'Avg accuracy',
        data: sorted.map(x=>+(x.avg*100).toFixed(1)),
        backgroundColor: sorted.map(x=>bgAlpha(x.avg)),
        borderColor: sorted.map(x=>hsl(x.avg)),
        borderWidth:1, borderRadius:4
      }]
    },
    options:{
      indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`${c.parsed.x.toFixed(1)}%`}}},
      scales:{
        x:{min:0,max:100,ticks:{callback:v=>v+'%'},grid:{color:'#e2e8f0'}},
        y:{ticks:{font:{size:10}}}
      }
    }
  })
}

// ── ④ Error Breakdown ─────────────────────────────────────────────────────

let chartErrors = null
function renderErrorChart(){
  const models = Object.keys(RAW.models).sort((a,b)=>{
    const da = RAW.models[a], db = RAW.models[b]
    let ca=0,cb=0
    for(const f of Object.values(da.per_field)) ca+=f.correct
    for(const f of Object.values(db.per_field)) cb+=f.correct
    return cb-ca
  })

  const corrects=[], wrongs=[], missings=[], totals=[]
  for(const m of models){
    let c=0,w=0,ms=0
    for(const f of Object.values(RAW.models[m].per_field)){c+=f.correct;w+=f.wrong;ms+=f.missing}
    corrects.push(c); wrongs.push(w); missings.push(ms)
    totals.push(c+w+ms)
  }

  const ctx = document.getElementById('chart-errors').getContext('2d')
  if(chartErrors) chartErrors.destroy()
  chartErrors = new Chart(ctx,{
    type:'bar',
    data:{
      labels: models,
      datasets:[
        {label:'Correct', data:corrects.map((c,i)=>totals[i]>0?(c/totals[i]*100).toFixed(1):0), backgroundColor:'rgba(16,185,129,0.7)', borderRadius:4},
        {label:'Wrong value', data:wrongs.map((w,i)=>totals[i]>0?(w/totals[i]*100).toFixed(1):0), backgroundColor:'rgba(249,115,22,0.7)'},
        {label:'Missing', data:missings.map((ms,i)=>totals[i]>0?(ms/totals[i]*100).toFixed(1):0), backgroundColor:'rgba(239,68,68,0.7)'},
      ]
    },
    options:{
      responsive:true, maintainAspectRatio:false,
      plugins:{tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${c.parsed.y}%`}}},
      scales:{
        x:{stacked:true,ticks:{font:{size:10},maxRotation:45}},
        y:{stacked:true,max:100,ticks:{callback:v=>v+'%'},grid:{color:'#e2e8f0'}}
      }
    }
  })
}

function renderErrorPatterns(){
  const models = activeModels()
  // Find fields that are consistently wrong (high wrong rate vs missing)
  const fieldStats = RAW.fields.map(f=>{
    let totalWrong=0, totalMissing=0, totalCorrect=0
    for(const m of models){
      const fd = RAW.models[m].per_field[f]||{correct:0,wrong:0,missing:0}
      totalWrong+=fd.wrong; totalMissing+=fd.missing; totalCorrect+=fd.correct
    }
    const total = totalWrong+totalMissing+totalCorrect
    return {f, wrongRate:totalWrong/total, missingRate:totalMissing/total, correctRate:totalCorrect/total}
  })

  let html = ''
  const highWrong = fieldStats.filter(x=>x.wrongRate>0.15).sort((a,b)=>b.wrongRate-a.wrongRate)
  const highMissing = fieldStats.filter(x=>x.missingRate>0.3).sort((a,b)=>b.missingRate-a.missingRate)

  if(highWrong.length){
    html += '<h3 style="margin-bottom:8px">Fields with frequent wrong values (model extracts but gets wrong)</h3>'
    html += '<table><thead><tr><th>Field</th><th>Wrong rate</th><th>Likely cause</th></tr></thead><tbody>'
    const causes = {
      'income_annually_in_british_pounds':'Decimal precision, year mismatch, or format (e.g. .39 vs .00)',
      'spending_annually_in_british_pounds':'Same as income',
      'charity_name':'Capitalisation, punctuation, or abbreviation differences',
      'address__street_line':'Multi-line addresses joined differently',
    }
    for(const x of highWrong){
      html+=`<tr><td>${RAW.field_labels[x.f]}</td><td style="color:var(--orange);font-weight:600">${pct(x.wrongRate)}</td><td style="color:var(--muted)">${causes[x.f]||'Formatting/normalisation mismatch'}</td></tr>`
    }
    html += '</tbody></table>'
  }
  if(highMissing.length){
    html += '<h3 style="margin:16px 0 8px">Fields frequently omitted entirely</h3>'
    html += '<table><thead><tr><th>Field</th><th>Missing rate</th></tr></thead><tbody>'
    for(const x of highMissing){
      html+=`<tr><td>${RAW.field_labels[x.f]}</td><td style="color:var(--red);font-weight:600">${pct(x.missingRate)}</td></tr>`
    }
    html += '</tbody></table>'
  }
  if(!html) html = '<p style="color:var(--muted)">No significant error patterns detected.</p>'
  document.getElementById('error-patterns').innerHTML = html
}

// ── ⑤ Deep Dive ───────────────────────────────────────────────────────────

function initDeepDive(){
  const modelSel = document.getElementById('dd-model')
  const docSel = document.getElementById('dd-doc')
  for(const m of Object.keys(RAW.models)){
    const opt = document.createElement('option'); opt.value=m; opt.text=m
    modelSel.appendChild(opt)
  }
  for(let i=0;i<RAW.doc_names.length;i++){
    const opt = document.createElement('option'); opt.value=i; opt.text=`${i+1}. ${RAW.doc_names[i]}`
    docSel.appendChild(opt)
  }
  renderDeepDive()
}

function renderDeepDive(){
  const m = document.getElementById('dd-model').value
  const di = parseInt(document.getElementById('dd-doc').value||'0')
  if(!m){document.getElementById('dd-output').innerHTML='<p style="color:var(--muted)">Select a model above.</p>';return}
  const pd = RAW.models[m]?.per_doc[di]
  const expected = RAW.expected[di]

  let html = ''
  if(pd?.is_error){
    html = `<div class="insight insight-warn"><strong>Rate limit error</strong> — This model returned an API error for this document. No extraction was attempted.</div>`
  } else {
    const acc = pd?.accuracy||0
    html = `<div style="margin-bottom:12px">
      <span class="badge ${tier(acc).cls}">${tier(acc).label}</span>
      <strong style="margin-left:8px;color:${hsl(acc)}">${pct(acc)} accuracy</strong>
      <span style="color:var(--muted);margin-left:8px">${pd?.correct||0} of ${pd?.total||0} fields correct</span>
    </div>`
    html += `<table class="diff-table"><thead><tr>
      <th>Field</th><th>Expected</th><th>Extracted</th><th>Status</th>
    </tr></thead><tbody>`
    for(const f of RAW.fields){
      if(!(f in (expected||{}))) continue
      const fs = pd?.fields[f]
      const status = fs?.status || 'missing'
      const got = fs?.got ?? '—'
      const exp = fs?.expected ?? expected[f]
      html += `<tr class="diff-${status}">
        <td style="font-weight:600">${RAW.field_labels[f]}</td>
        <td>${exp?.replace(/_/g,' ')||'—'}</td>
        <td>${got===null?'<em style="color:var(--muted)">not extracted</em>':(got?.replace(/_/g,' ')||'—')}</td>
        <td><span class="badge ${status==='correct'?'badge-green':status==='wrong'?'badge-orange':'badge-red'}">${status}</span></td>
      </tr>`
    }
    html += '</tbody></table>'
  }
  document.getElementById('dd-output').innerHTML = html
}

// ── ⑥ Recommendations ─────────────────────────────────────────────────────

function renderRecommendations(){
  const usecase = document.getElementById('rec-usecase').value
  const budget  = document.getElementById('rec-budget').value
  const relevantFields = usecase==='all' ? RAW.fields : RAW.field_groups[usecase]
  const budgetTiers = {'free':['free'],'ultra-cheap':['free','ultra-cheap'],'great-value':['free','ultra-cheap','great-value'],'premium':TIER_ORDER}
  const allowed = budget==='any' ? null : budgetTiers[budget]
  const models = activeModels().filter(m=> !allowed || allowed.includes(RAW.model_meta?.[m]?.tier))

  const scores = models.map(m=>{
    let correct=0, total=0
    for(const f of relevantFields){
      const fd = RAW.models[m].per_field[f]||{correct:0,wrong:0,missing:0}
      correct+=fd.correct; total+=fd.correct+fd.wrong+fd.missing
    }
    return {m, acc: total>0?correct/total:0, correct, total}
  }).sort((a,b)=>b.acc-a.acc)

  let budgetNote = budget==='any' ? '' : ` <span style="color:var(--muted)">(budget: ${tierLabel(budget)} and below)</span>`
  let html = `<p style="font-size:12px;color:var(--muted);margin-bottom:14px">Ranking models by accuracy on: <strong>${relevantFields.map(f=>RAW.field_labels[f]).join(', ')}</strong>${budgetNote}</p>`
  if(!models.length){html+='<p style="color:var(--muted)">No functional models match this budget filter.</p>'; document.getElementById('rec-output').innerHTML=html; return}
  html += '<table><thead><tr><th>#</th><th>Model</th><th>Accuracy on selected fields</th><th>Correct</th><th>Perf.</th><th>Cost</th></tr></thead><tbody>'
  scores.forEach((r,i)=>{
    const t = tier(r.acc)
    html += `<tr>
      <td style="color:var(--muted)">${i+1}</td>
      <td><strong>${r.m}</strong></td>
      <td>
        <span style="color:${hsl(r.acc)};font-weight:700">${pct(r.acc)}</span>
        <div class="rank-bar-wrap" style="margin-top:3px;width:120px">
          <div class="rank-bar" style="width:${(r.acc*100).toFixed(1)}%;background:${hsl(r.acc)}"></div>
        </div>
      </td>
      <td style="color:var(--muted)">${r.correct}/${r.total}</td>
      <td><span class="badge ${t.cls}">${t.label}</span></td>
      <td>${costTierBadge(r.m)}</td>
    </tr>`
  })
  html += '</tbody></table>'

  if(scores.length){
    const top = scores[0]
    const bestFree = scores.find(r=>(RAW.model_meta?.[r.m]?.tier)==='free')
    html += `<div class="insight insight-tip" style="margin-top:16px">
      <strong>Recommended:</strong> <strong>${top.m}</strong> (${costTierBadge(top.m)}) achieves ${pct(top.acc)} on the selected fields.
      ${scores[1] && scores[1].m!==top.m?`Runner-up: <strong>${scores[1].m}</strong> at ${pct(scores[1].acc)}.`:''}
    </div>`
    if(bestFree && bestFree.m!==top.m){
      html += `<div class="insight" style="margin-top:8px"><strong>Best free option:</strong> <strong>${bestFree.m}</strong> at ${pct(bestFree.acc)}.</div>`
    }
  }

  document.getElementById('rec-output').innerHTML = html
}

function renderInsights(){
  const models = activeModels()
  const allM = allModels()
  const failedModels = allM.filter(m=>!isActive(m))
  const fields = RAW.fields

  // Best overall
  const sorted = models.map(m=>({m,acc:RAW.models[m].accuracy})).sort((a,b)=>b.acc-a.acc)
  const best = sorted[0], second = sorted[1]

  // Hardest field (lowest avg across active models)
  const fieldAvg = fields.map(f=>{
    const accs = models.map(m=>{const fd=RAW.models[m].per_field[f]||{correct:0,wrong:0,missing:0};const t=fd.correct+fd.wrong+fd.missing;return t>0?fd.correct/t:0})
    return {f, avg:accs.reduce((s,v)=>s+v,0)/accs.length}
  })
  const hardest = fieldAvg.sort((a,b)=>a.avg-b.avg)[0]
  const easiest = [...fieldAvg].sort((a,b)=>b.avg-a.avg)[0]

  // Financial consistency — std dev of income/spending accuracy
  const financialConsistency = models.map(m=>{
    const inc = RAW.models[m].per_field['income_annually_in_british_pounds']||{correct:0,wrong:0,missing:0}
    const sp = RAW.models[m].per_field['spending_annually_in_british_pounds']||{correct:0,wrong:0,missing:0}
    const t1=inc.correct+inc.wrong+inc.missing, t2=sp.correct+sp.wrong+sp.missing
    const a1=t1>0?inc.correct/t1:0, a2=t2>0?sp.correct/t2:0
    return {m, financialAcc:(a1+a2)/2}
  }).sort((a,b)=>b.financialAcc-a.financialAcc)

  let html = ''
  html += `<div class="insight insight-tip"><strong>Top performer:</strong> ${best.m} leads with ${pct(best.acc)} overall accuracy. ${second?`${second.m} follows at ${pct(second.acc)}.`:''}</div>`
  html += `<div class="insight"><strong>Hardest field:</strong> "${RAW.field_labels[hardest.f]}" averages only ${pct(hardest.avg)} accuracy across functional models — indicating consistent extraction difficulty.</div>`
  html += `<div class="insight insight-tip"><strong>Easiest field:</strong> "${RAW.field_labels[easiest.f]}" is most reliably extracted at ${pct(easiest.avg)} average accuracy.</div>`
  html += `<div class="insight"><strong>Financial data leader:</strong> ${financialConsistency[0].m} is best for income/spending extraction at ${pct(financialConsistency[0].financialAcc)} combined accuracy.</div>`
  if(failedModels.length){
    html += `<div class="insight insight-warn"><strong>Rate-limited models (${failedModels.length}):</strong> ${failedModels.join(', ')} — all returned API errors (429). Results are invalid; retry with a paid key or lower throughput.</div>`
  }

  // Check if any model is better on smaller tasks
  const smallModelBest = models.filter(m=>m.includes('7b')||m.includes('8b'))
  if(smallModelBest.length){
    const bestSmall = smallModelBest.map(m=>({m,acc:RAW.models[m].accuracy})).sort((a,b)=>b.acc-a.acc)[0]
    if(bestSmall.acc > 0.5){
      html += `<div class="insight insight-tip"><strong>Small model worth noting:</strong> ${bestSmall.m} achieves ${pct(bestSmall.acc)} — a cost-effective option for high-throughput pipelines.</div>`
    }
  }

  document.getElementById('insights').innerHTML = html
}

function renderImprovements(){
  const models = activeModels()
  const fields = RAW.fields

  // Find patterns in wrong values
  const streetWrong = models.reduce((s,m)=>{const fd=RAW.models[m].per_field['address__street_line']||{wrong:0};return s+fd.wrong},0)
  const incomeWrong = models.reduce((s,m)=>{const fd=RAW.models[m].per_field['income_annually_in_british_pounds']||{wrong:0};return s+fd.wrong},0)
  const nameWrong = models.reduce((s,m)=>{const fd=RAW.models[m].per_field['charity_name']||{wrong:0};return s+fd.wrong},0)

  let html = ''
  html += `<div class="insight insight-tip"><strong>Prompt: normalise numbers</strong> — Income and spending show high "wrong" rates due to decimal/rounding differences (e.g. <code>122836.39</code> vs <code>122836.00</code>). Add explicit instruction: <em>"Round amounts to 2 decimal places. Use the exact figure from the accounts, not a rounded total."</em></div>`
  html += `<div class="insight insight-tip"><strong>Prompt: canonical charity name</strong> — Charity names vary in case and punctuation. Instruct: <em>"Use the official registered name exactly as shown on the document header."</em></div>`
  html += `<div class="insight insight-tip"><strong>Prompt: street line normalisation</strong> — Multi-line addresses are collapsed inconsistently. Instruct: <em>"Join multiple address lines with a single space. Omit building names unless the street number is absent."</em></div>`
  html += `<div class="insight"><strong>Consider few-shot examples</strong> — Models that got 100% on some docs but 0% on others are likely sensitive to document format variations. Adding 1-2 in-context examples from different document layouts will reduce variance.</div>`
  html += `<div class="insight"><strong>Post-processing</strong> — Apply deterministic cleaning after extraction: uppercase postcodes, strip trailing/leading whitespace, normalise decimal places. This can close the gap between "wrong" and "correct" for formatting-only errors.</div>`
  html += `<div class="insight insight-warn"><strong>Re-test rate-limited models</strong> — Several models (llama-3.3-70b, mistral-small-free, command-r-plus, qwen-coder-32b) returned errors. These results are invalid. Run them again with proper rate limiting or paid API keys before drawing conclusions.</div>`

  document.getElementById('improvements').innerHTML = html
}

// ── Boot ─────────────────────────────────────────────────────────────────────

window.addEventListener('DOMContentLoaded', ()=>{
  initialized.add('rankings')
  renderRankings()
})
</script>
</body>
</html>"""

if __name__ == "__main__":
    main()
