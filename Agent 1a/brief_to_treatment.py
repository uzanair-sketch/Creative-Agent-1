import os
import json
import warnings
from typing import List, Optional, Union
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from google.genai.errors import ServerError

# Suppress minor platform deprecation/SSL warnings for clean output
warnings.filterwarnings("ignore")

# Automatically load environment variables from .env file
load_dotenv()

# ---------------------------------------------------------------------------
# 1. Structured Data Schemas (Pydantic Models)
# ---------------------------------------------------------------------------

class BriefAnalysis(BaseModel):
    client_name: str = Field(description="Name of the brand or client")
    core_objective: str = Field(description="Primary commercial or creative goal")
    target_audience: str = Field(description="Demographics and psychographics")
    deliverables: List[str] = Field(description="List of video deliverables (e.g., 1x 30s hero, 3x 15s social)")
    aesthetic_tone: str = Field(description="Visual and narrative style description")
    estimated_budget_tier: str = Field(description="Budget tier: Micro (<$5k), Mid ($5k-$20k), High ($20k+)")

class VisualTreatment(BaseModel):
    treatment_title: str = Field(description="Working title of the project concept")
    logline: str = Field(description="A 1-2 sentence core creative narrative summary")
    visual_direction: str = Field(description="Detailed direction on lighting, camera, textures, and grading")
    color_palette: List[str] = Field(description="Key HEX or descriptive color codes")
    ai_previs_prompts: List[str] = Field(
        description="High-fidelity generative image prompts for Midjourney/Flux/Krea (including aspect ratios, lighting, camera model)"
    )

class Shot(BaseModel):
    shot_number: int = Field(description="Sequential shot number")
    scene_location: str = Field(description="INT/EXT location description")
    framing_and_lens: str = Field(description="Camera angle and lens choice (e.g., MCU 85mm f/1.8, Anamorphic Wide)")
    camera_movement: str = Field(description="Camera movement (e.g., Static, Steadicam Push-In, Handheld)")
    visual_action: str = Field(description="What happens on screen")
    audio_vo: str = Field(description="Voiceover, dialogue, or sound design cues")

class BudgetItem(BaseModel):
    category: str = Field(description="Phase: Pre-Production, Crew, Equipment, Post-Production, AI Rendering")
    line_item: str = Field(description="Description of item or role")
    estimated_cost_usd: float = Field(description="Estimated cost in USD")

class CompleteProductionTreatment(BaseModel):
    brief_analysis: BriefAnalysis
    treatment: VisualTreatment
    shot_list: List[Shot]
    budget_breakdown: List[BudgetItem]
    total_estimated_budget_usd: float

# ---------------------------------------------------------------------------
# 2. Agent Implementation Class
# ---------------------------------------------------------------------------

class BriefToTreatmentAgent:
    def __init__(
        self,
        model_name: Optional[str] = None,
        fallback_models: Optional[List[str]] = None
    ):
        """Initialize the agent with Google GenAI SDK and fallback support."""
        self.client = genai.Client()
        primary = model_name or os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
        self.candidate_models = [primary] + (fallback_models or ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.8-flash"])
        # Deduplicate while preserving order
        self.candidate_models = list(dict.fromkeys(self.candidate_models))

    def run(self, raw_brief_text: str) -> CompleteProductionTreatment:
        """Executes the agent workflow to convert raw brief into full treatment."""
        system_instruction = """
        You are an elite Creative Director and Commercial Producer working at a top visual production agency.
        Your job is to transform raw client briefs into actionable, high-end commercial video treatments, 
        generative image prompts for pre-visualization (Midjourney v6 / Flux style), production-ready shot lists, 
        and line-item budget estimates.

        Be hyper-specific in your visual choices (mention specific camera focal lengths, lighting setups, 
        color palettes, and realistic commercial pricing).
        """

        prompt = f"""
        Process the following raw client brief and produce a complete commercial video production package:

        === CLIENT BRIEF ===
        {raw_brief_text}
        ====================
        """

        last_error = None
        for model in self.candidate_models:
            print(f"🤖 [Brief-To-Treatment Agent] Analyzing brief with {model}...", flush=True)
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.4,
                        response_mime_type="application/json",
                        response_schema=CompleteProductionTreatment,
                    ),
                )

                if hasattr(response, "parsed") and isinstance(response.parsed, CompleteProductionTreatment):
                    return response.parsed
                result_json = json.loads(response.text)
                return CompleteProductionTreatment(**result_json)

            except ServerError as e:
                print(f"⚠️ High demand / server error on {model}: {e}. Retrying with next candidate...", flush=True)
                last_error = e
                continue
            except Exception as e:
                # Other errors (e.g. schema/client)
                raise e

        if last_error:
            raise last_error

# ---------------------------------------------------------------------------
# 3. Execution & Example Usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Example Raw Client Brief
    sample_brief = """
    We are 'Solstice Coffee Co.', an artisanal cold brew brand launching a new nitro canned cold brew.
    Goal: Create a high-energy 30-second commercial for Instagram/TikTok and YouTube pre-roll.
    Tone: Dark, sleek, tactile, cinematic—think Apple commercial meets high-end mixology. 
    Deep shadows, macro close-ups of condensation, rich espresso swirls, liquid motion, matte black metal cans.
    Deliverables: 1x 30s hero cut (16:9), 2x 15s vertical social cuts (9:16).
    Target Audience: Urban young professionals, coffee snobs, 22-38 years old.
    Budget context: Mid-tier agency pitch budget around $12,000 to $15,000 USD.
    """

    agent = BriefToTreatmentAgent()
    output = agent.run(sample_brief)

    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)

    # 1. Save raw JSON artifact
    json_path = "output/treatment_output.json"
    with open(json_path, "w") as f:
        json.dump(output.model_dump(), f, indent=2)

    # 2. Save formatted Markdown document for easy IDE review
    md_path = "output/treatment.md"
    
    shot_rows = "\n".join([
        f"| {s.shot_number} | {s.scene_location} | {s.framing_and_lens} | {s.camera_movement} | {s.visual_action} | {s.audio_vo} |"
        for s in output.shot_list
    ])
    
    budget_rows = "\n".join([
        f"| {b.category} | {b.line_item} | ${b.estimated_cost_usd:,.2f} |"
        for b in output.budget_breakdown
    ])

    prompts = "\n".join([f"- `{p}`" for p in output.treatment.ai_previs_prompts])

    markdown_content = f"""# Commercial Treatment: {output.treatment.treatment_title}

**Client:** {output.brief_analysis.client_name}  
**Objective:** {output.brief_analysis.core_objective}  
**Target Audience:** {output.brief_analysis.target_audience}  
**Aesthetic Tone:** {output.brief_analysis.aesthetic_tone}  

---

## 1. Creative Concept & Logline

> **Logline:** {output.treatment.logline}

**Visual Direction:**  
{output.treatment.visual_direction}

---

## 2. Pre-Visualization Prompts (Midjourney / Flux)

{prompts}

---

## 3. Shot List

| Shot # | Location | Framing & Lens | Movement | Action | Audio / VO |
| :--- | :--- | :--- | :--- | :--- | :--- |
{shot_rows}

---

## 4. Production Budget Estimate

| Category | Line Item | Estimated Cost (USD) |
| :--- | :--- | :--- |
{budget_rows}

### **Total Estimated Budget:** ${output.total_estimated_budget_usd:,.2f}
"""

    with open(md_path, "w") as f:
        f.write(markdown_content)

    # 3. Save formatted DOCX for Google Docs review
    docx_path = "output/treatment.docx"
    try:
        from create_docx import create_treatment_docx
        create_treatment_docx(json_path, docx_path)
    except Exception as e:
        print(f"Warning: Could not create DOCX: {e}")

    print(f"\n✅ Deliverables generated successfully:")
    print(f" - JSON Data: {json_path}")
    print(f" - Markdown Treatment: {md_path}")
    print(f" - Google Docs / Word File: {docx_path}")
