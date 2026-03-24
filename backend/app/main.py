"""FastAPI application — POST /simulate endpoint."""

import json
import logging
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.db import Base, SessionLocal, engine
from backend.app.models import Decision
from backend.app.schemas import SimulationRequest, SimulationResponse
from backend.app.services.llm_service import LLMService
from backend.app.simulation import generate_scenarios, rank_outcomes, run_simulation

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="Decision Simulator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:5173",
        "http://127.0.0.1",
        "http://127.0.0.1:5173",
        "https://himanshu-nakrani.github.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create DB tables on startup
Base.metadata.create_all(bind=engine)

# Module-level LLM singleton — loaded once to avoid cold-start overhead per request
llm = LLMService()

# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@app.post("/simulate", response_model=SimulationResponse)
async def simulate(request: SimulationRequest) -> SimulationResponse:
    # 1. Structure the free-form decision text
    structured = llm.structure_input(request.decision_text)

    # 2. Generate probabilistic scenarios per option
    scenarios = generate_scenarios(structured, request.risk)

    # 3. Run Monte Carlo-style numerical simulation
    results = run_simulation(scenarios, request.time_horizon)

    # 4. Rank options by weighted score
    weights = {"salary_w": 0.4, "happiness_w": 0.4}
    ranking = rank_outcomes(results, weights, request.risk)

    # 5. Build explanation from top 3 scenarios
    top_scenarios = ranking["scenario_results"][:3]
    explanation = llm.generate_explanation(structured, ranking["best_option"], top_scenarios)

    # 6. Assemble response dict for persistence
    response_dict = {
        "structured_input": structured,
        "scenarios": scenarios,
        "results": ranking["scenario_results"],
        "best_option": ranking["best_option"],
        "explanation": explanation,
    }

    # 7. Persist to SQLite — log and continue on failure
    db = SessionLocal()
    try:
        record = Decision(
            decision_text=request.decision_text,
            structured_json=json.dumps(structured),
            result_json=json.dumps(response_dict),
            created_at=datetime.now(timezone.utc),
        )
        db.add(record)
        db.commit()
    except Exception as exc:
        logger.error("DB write failed, continuing without persistence: %s", exc)
        db.rollback()
    finally:
        db.close()

    return SimulationResponse(
        structured_input=structured,
        scenarios=scenarios,
        results=ranking["scenario_results"],
        best_option=ranking["best_option"],
        explanation=explanation,
    )
