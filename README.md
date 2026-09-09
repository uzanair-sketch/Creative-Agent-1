# Creative Agent 1: Autonomous Commercial Treatment & Strategy Pipeline

An AI-powered multi-agent creative commercial production pipeline built with the Google GenAI SDK and Pydantic structured schemas.

---

## 🏗️ Architecture & Modules

Creative Agent 1 consists of two specialized sub-agents working sequentially:

```
                          ┌───────────────────────────┐
                          │     Client Video Brief    │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ Agent 1a: Brief-To-Treatment Generator (Agent 1a/brief_to_treatment.py)       │
│ • Converts unstructured briefs into cinematic visual treatments               │
│ • Generates camera framing, lighting, color palette, and shot lists           │
│ • Builds line-item production budgets and outputs DOCX/HTML/JSON              │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │ (output/treatment_output.json)
                                        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│ Agent 1b: Competitor Strategy & Hook Optimizer (Agent 1b/competitor_strategy) │
│ • Analyzes category competitor ad patterns and creative opportunity gaps      │
│ • Generates high-retention 0-3s hooks (Pattern Interrupt, Sensory Shock, etc.) │
│ • Optimizes ending Call-To-Action (CTA)                                       │
│ • Enriches master treatment state for Agent 2 (Pre-Vis Storyboard Generator)  │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```
.
├── Agent 1a/
│   ├── brief_to_treatment.py   # Agent 1a: Brief to treatment generator
│   ├── create_docx.py          # Professional DOCX document generator
│   ├── output/                 # Treatment documents, JSON state, and exports
│   └── requirements.txt        # Agent 1a specific dependencies
├── Agent 1b/
│   ├── competitor_strategy_agent.py # Agent 1b: Competitor & Hook Optimizer
│   └── output/                 # Enriched treatment state & strategy report
├── .gitignore
├── README.md
└── requirements.txt
```

---

## 🚀 Getting Started

### 1. Prerequisites & Installation

```bash
git clone https://github.com/uzanair-sketch/Creative-Agent-1.git
cd Creative-Agent-1
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the root:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Running the Pipeline

#### Step 1: Run Agent 1a (Treatment Generator)
```bash
python "Agent 1a/brief_to_treatment.py"
```
Produces `output/treatment_output.json`, `output/treatment.docx`, and `output/treatment.html`.

#### Step 2: Run Agent 1b (Competitor Strategy & Hook Optimization)
```bash
python "Agent 1b/competitor_strategy_agent.py"
```
Reads the treatment state, analyzes competitors, formulates scroll-stopping hooks, and outputs:
- `output/strategy_report.md` (Human-readable strategy analysis)
- `output/strategy_report.json` (Structured strategy data)
- `output/treatment_output.json` (Enriched master state ready for Agent 2)

---

## ⚡ Robust Multi-Model Fallback

Both agents leverage intelligent model fallback to guarantee 99.9% pipeline uptime against server demand spikes:
`gemini-3.6-flash` ➔ `gemini-3.5-flash` ➔ `gemini-3.1-flash-lite` ➔ `gemini-3.8-flash`
