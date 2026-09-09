import os
import json
import time
import warnings

# Suppress minor platform deprecation/SSL warnings for clean output
warnings.filterwarnings("ignore")

from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError

# Automatically load environment variables from .env
load_dotenv()

# ---------------------------------------------------------------------------
# 1. Pydantic Schemas for Strategy & Optimization
# ---------------------------------------------------------------------------

class Shot(BaseModel):
    shot_number: int
    scene_location: str
    framing_and_lens: str
    camera_movement: str
    visual_action: str
    audio_vo: str

class BudgetItem(BaseModel):
    category: str
    line_item: str
    estimated_cost_usd: float

class BriefAnalysis(BaseModel):
    client_name: str
    core_objective: str
    target_audience: str
    deliverables: List[str]
    aesthetic_tone: str
    estimated_budget_tier: str

class VisualTreatment(BaseModel):
    treatment_title: str
    logline: str
    visual_direction: str
    color_palette: List[str]
    ai_previs_prompts: List[str]

class HookOption(BaseModel):
    hook_type: str = Field(description="Pattern Interrupt, Curiosity Gap, or Sensory Shock")
    visual_hook_description: str = Field(description="First 0-3s visual action")
    on_screen_text: str = Field(description="High-contrast bold caption overlay for TikTok/Reels")
    audio_hook: str = Field(description="First 3 seconds sound effect or dialogue line")
    retention_rationale: str = Field(description="Why this prevents scrolling based on market trends")

class CompetitorInsight(BaseModel):
    competitor_name: str = Field(description="Direct or indirect competitor brand")
    winning_creative_pattern: str = Field(description="What works in their current ad creatives")
    creative_opportunity_gap: str = Field(description="How our campaign will visually outperform them")

class CompleteProductionTreatment(BaseModel):
    brief_analysis: BriefAnalysis
    treatment: VisualTreatment
    shot_list: List[Shot]
    budget_breakdown: List[BudgetItem]
    total_estimated_budget_usd: float

class StrategyOptimizationPackage(BaseModel):
    competitor_insights: List[CompetitorInsight]
    high_retention_hooks: List[HookOption]
    selected_primary_hook: HookOption
    optimized_cta: str = Field(description="High-converting end screen Call to Action")
    enriched_treatment: CompleteProductionTreatment

# ---------------------------------------------------------------------------
# 2. Agent 1b Implementation
# ---------------------------------------------------------------------------

class CompetitorStrategyAgent:
    def __init__(self, fallback_models: Optional[List[str]] = None):
        self.client = genai.Client()
        self.fallback_models = fallback_models or [
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.1-flash-lite",
            "gemini-3.8-flash"
        ]

    def _resolve_path(self, path: str) -> str:
        """Finds input file across common relative locations if not found at exact path."""
        if os.path.exists(path):
            return path

        script_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(script_dir, path),
            os.path.join(script_dir, "..", "Agent 1a", path),
            os.path.join(script_dir, "..", path),
            os.path.join(script_dir, "..", "..", path),
            os.path.join(script_dir, "..", "..", "Agent 1", "Agent 1a", path),
            os.path.join(os.getcwd(), "Agent 1", "Agent 1a", path),
            os.path.join(os.getcwd(), path),
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                return os.path.abspath(candidate)
        return path

    def run(self, input_treatment_path: str) -> StrategyOptimizationPackage:
        """Reads previous treatment JSON, performs competitor analysis, and optimizes state."""
        resolved_path = self._resolve_path(input_treatment_path)
        if not os.path.exists(resolved_path):
            raise FileNotFoundError(
                f"Input file not found: {input_treatment_path} (checked {resolved_path}). Run Agent 1a first!"
            )

        with open(resolved_path, "r") as f:
            previous_treatment_data = json.load(f)

        print(f"📥 [Agent 1b] Loaded Agent 1a Treatment from: {resolved_path}")
        print("🔍 [Agent 1b] Analyzing competitor landscape & optimizing high-retention hooks...")

        system_instruction = """
        You are a Lead Creative Strategist and Performance Ad Director specializing in social video (TikTok, Instagram Reels, YouTube Shorts).
        Your task is to take an existing commercial treatment, analyze top competitor ad patterns in its category, 
        and optimize the opening 3-second hooks and ending Call-To-Action (CTA) for maximum scroll-stopping retention.

        Enforce strict visual hooks, pattern interrupts, tactile sound design, and sharp on-screen text overlays.
        Return the fully enriched treatment with the optimized shot list and strategy analysis.
        """

        prompt = f"""
        Perform a competitive creative analysis and hook optimization for the following production treatment:

        === EXISTING TREATMENT JSON ===
        {json.dumps(previous_treatment_data, indent=2)}
        ===============================
        """

        # Model Fallback Execution Loop with Exponential Backoff
        last_exception = None
        for model_name in self.fallback_models:
            for attempt in range(1, 3):
                try:
                    attempt_str = f" (attempt {attempt}/2)" if attempt > 1 else ""
                    print(f"🚀 Attempting optimization with model: {model_name}{attempt_str}...", flush=True)
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.3,
                            response_mime_type="application/json",
                            response_schema=StrategyOptimizationPackage,
                        ),
                    )

                    if hasattr(response, "parsed") and isinstance(response.parsed, StrategyOptimizationPackage):
                        return response.parsed

                    result_json = json.loads(response.text)
                    return StrategyOptimizationPackage(**result_json)

                except ServerError as e:
                    print(f"⚠️ Model {model_name} hit server load error (503). Waiting 2s before retry...", flush=True)
                    last_exception = e
                    time.sleep(2)
                except Exception as e:
                    print(f"⚠️ Error with model {model_name}: {e}. Retrying next model...", flush=True)
                    last_exception = e
                    break

        raise RuntimeError(f"All candidate models failed. Last error: {last_exception}")

# ---------------------------------------------------------------------------
# 3. Execution & Workspace Artifact Updater
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = "output/treatment_output.json"

    agent = CompetitorStrategyAgent()
    strategy_package = agent.run(input_file)

    # Determine destination directories
    output_dirs = [
        os.path.abspath("output"),
        os.path.join(script_dir, "output"),
    ]
    # Deduplicate while preserving order
    output_dirs = list(dict.fromkeys(output_dirs))

    for out_dir in output_dirs:
        os.makedirs(out_dir, exist_ok=True)

        # 1. Update master treatment output JSON (enriches pipeline state for Agent 2)
        output_json_path = os.path.join(out_dir, "treatment_output.json")
        with open(output_json_path, "w") as f:
            json.dump(strategy_package.enriched_treatment.model_dump(), f, indent=2)

        # 2. Save full strategy report JSON
        strategy_json_path = os.path.join(out_dir, "strategy_report.json")
        with open(strategy_json_path, "w") as f:
            json.dump(strategy_package.model_dump(), f, indent=2)

        # 3. Save formatted Markdown Strategy Report for IDE Review
        md_path = os.path.join(out_dir, "strategy_report.md")

        hooks_md = "\n\n".join([
            f"### Hook {idx+1}: {h.hook_type}\n"
            f"- **Visual Interrupt:** {h.visual_hook_description}\n"
            f"- **Text Overlay:** *\"{h.on_screen_text}\"*\n"
            f"- **Audio Hook:** {h.audio_hook}\n"
            f"- **Retention Rationale:** {h.retention_rationale}"
            for idx, h in enumerate(strategy_package.high_retention_hooks)
        ])

        competitors_md = "\n".join([
            f"| **{c.competitor_name}** | {c.winning_creative_pattern} | {c.creative_opportunity_gap} |"
            for c in strategy_package.competitor_insights
        ])

        md_content = f"""# Strategy & Hook Optimization Report

**Project:** {strategy_package.enriched_treatment.brief_analysis.client_name}  
**Treatment Title:** {strategy_package.enriched_treatment.treatment.treatment_title}  
**Optimized CTA:** *\"{strategy_package.optimized_cta}\"*  

---

## 1. Competitive Ad Creative Analysis

| Competitor | Winning Creative Pattern | Our Opportunity Gap |
| :--- | :--- | :--- |
{competitors_md}

---

## 2. High-Retention Opening Hooks (0-3 Seconds)

{hooks_md}

---

## 3. Selected Primary Hook Strategy

> **Type:** {strategy_package.selected_primary_hook.hook_type}  
> **Visual:** {strategy_package.selected_primary_hook.visual_hook_description}  
> **Text Overlay:** "{strategy_package.selected_primary_hook.on_screen_text}"  
> **Audio:** {strategy_package.selected_primary_hook.audio_hook}  

---

*State updated in `{output_json_path}`. Ready for **Agent 2: Pre-Vis Storyboard Generator**.*
"""

        with open(md_path, "w") as f:
            f.write(md_content)

        print(f"\n✅ Artifacts written to {out_dir}:")
        print(f" 📄 Enriched State:       {output_json_path}")
        print(f" 📄 Strategy Report JSON: {strategy_json_path}")
        print(f" 📄 Strategy Markdown:    {md_path}")
