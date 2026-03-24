# Implementation Plan: Decision Simulator

## Overview

Implement the Decision Simulator backend (FastAPI + simulation engine + LLM service) and React/Vite frontend incrementally, wiring all components together at the end.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create `backend/requirements.txt` with fastapi, uvicorn, sqlalchemy, pydantic, transformers, torch, numpy, hypothesis
  - Create `frontend/package.json` with react, vite, axios dependencies
  - Create `backend/app/db.py` with SQLAlchemy engine and session setup for SQLite
  - Create `backend/app/models.py` with the `Decision` ORM model (id, decision_text, structured_json, result_json, created_at)
  - Create `backend/app/schemas.py` with `SimulationRequest` and `SimulationResponse` Pydantic models including field validators
  - _Requirements: 1.1, 1.2, 1.3, 8.1, 8.3_

- [x] 2. Implement LLM Service
  - [x] 2.1 Implement `LLMService` class in `backend/app/services/llm_service.py`
    - Load flan-t5-base model and tokenizer once as module-level singleton
    - Implement `structure_input`: constrained prompt, regex JSON extraction (`re.search(r'\{.*\}', output, re.DOTALL)`), fallback dict on parse failure
    - Implement `generate_explanation`: pass only `best_option` + top 2–3 scenarios to prompt
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.1, 6.2_

  - [x] 2.2 Write property test for LLM structuring always returns valid dict
    - **Property 6: LLM structuring always returns valid dict**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
    - Use `hypothesis` to generate arbitrary non-empty strings as `decision_text`; mock the model to return malformed output; assert returned dict always has `decision`, `options` (≥2), `factors` (≥1) and never raises

- [x] 3. Implement Simulation Engine — scenario generation
  - [x] 3.1 Implement `generate_scenarios` in `backend/app/simulation.py`
    - Return one scenario group per option with 2–3 scenarios each
    - Assign probabilities influenced by `risk_tolerance`; last probability = `1.0 - sum(assigned_probs)` (no independent rounding)
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 Write property test for scenario probability sum invariant
    - **Property 1: Scenario probability sum invariant**
    - **Validates: Requirements 3.2, 3.3**
    - Use `hypothesis` to generate valid `structured_input` dicts and `risk_tolerance` floats in [0.0, 1.0]; assert each option group's probabilities sum to exactly 1.0 and each group has 2–3 scenarios

- [x] 4. Implement Simulation Engine — numerical simulation
  - [x] 4.1 Implement `run_simulation` in `backend/app/simulation.py`
    - Set `np.random.seed(42)` before sampling
    - Apply scenario-aware salary multipliers based on keyword matching in scenario name
    - Scale salary by `(1 + 0.05 * time_horizon)`
    - Produce `risk_score` and `happiness` in [0.0, 1.0] per scenario type
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

  - [x] 4.2 Write property test for simulation output value invariants
    - **Property 7: Simulation output value invariants**
    - **Validates: Requirements 4.2, 4.3, 4.4**
    - Use `hypothesis` to generate valid scenario lists and `time_horizon >= 1`; assert every result has `salary > 0`, `risk_score` in [0.0, 1.0], `happiness` in [0.0, 1.0]

  - [x] 4.3 Write property test for simulation determinism
    - **Property 9: Simulation determinism**
    - **Validates: Requirements 4.1**
    - Call `run_simulation` twice with identical inputs; assert outputs are identical

  - [x] 4.4 Write property test for semantic salary ranges
    - **Property 8: Semantic salary ranges**
    - **Validates: Requirements 4.5, 4.6, 4.7**
    - Use `hypothesis` to generate scenario names containing high-growth / stressful / neutral keywords; assert salary multiplier falls within the correct range for each keyword class

- [x] 5. Implement Simulation Engine — outcome ranking
  - [x] 5.1 Implement `rank_outcomes` in `backend/app/simulation.py`
    - Derive `risk_w = 1.0 - risk_tolerance`
    - Normalize salary dynamically using `min/max` of actual results; use range=1 if all salaries equal
    - Score each scenario: `salary_w * norm_salary + happiness_w * happiness - risk_w * risk_score`
    - Aggregate to option level: `option_score = sum(score * probability)`
    - Return `{best_option, ranked, scenario_results}` with `ranked` sorted non-increasing
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_

  - [x] 5.2 Write property test for ranking non-increasing order
    - **Property 2: Ranking non-increasing order**
    - **Validates: Requirements 5.6, 5.7**
    - Use `hypothesis` to generate non-empty results lists with valid fields; assert `ranked[0].score >= ranked[i].score` for all `i > 0` and `best_option == ranked[0]["option"]`

  - [x] 5.3 Write property test for risk weight derivation
    - **Property 3: Risk weight derivation**
    - **Validates: Requirements 5.1**
    - Use `hypothesis` to generate `risk_tolerance` floats in [0.0, 1.0]; assert `risk_w == 1.0 - risk_tolerance` exactly

  - [x] 5.4 Write property test for dynamic salary normalization
    - **Property 4: Dynamic salary normalization**
    - **Validates: Requirements 5.2, 5.3**
    - Use `hypothesis` to generate results lists with known salary values; assert normalization uses `min/max` of that specific list, not static bounds

  - [x] 5.5 Write property test for probability-weighted option aggregation
    - **Property 5: Probability-weighted option aggregation**
    - **Validates: Requirements 5.5**
    - Use `hypothesis` to generate results with multiple scenarios per option; assert each option's aggregate score equals `sum(score * probability)` for its scenarios

- [x] 6. Checkpoint — Ensure all simulation engine tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement FastAPI endpoint and persistence
  - [x] 7.1 Implement `POST /simulate` in `backend/app/main.py`
    - Orchestrate pipeline: `structure_input` → `generate_scenarios` → `run_simulation` → `rank_outcomes` → `generate_explanation`
    - Persist `decision_text`, `structured_json`, `result_json`, `created_at` to SQLite via SQLAlchemy ORM; log and continue on DB write failure
    - Configure CORS to allow only `localhost` origins
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 8.2, 8.3_

  - [x] 7.2 Write property test for request validation rejects out-of-range inputs
    - **Property 10: Request validation rejects out-of-range inputs**
    - **Validates: Requirements 1.1, 1.2, 1.3**
    - Use `hypothesis` to generate out-of-range `risk` values, `time_horizon < 1`, and empty `decision_text`; assert FastAPI returns HTTP 422 for each

- [x] 8. Implement React frontend
  - [x] 8.1 Implement Page 1 input form in `frontend/src/components/InputForm.jsx`
    - Decision text input, risk slider [0.0, 1.0], time horizon number input, submit button
    - POST to `/simulate` on submit; show loading indicator while awaiting response; show error message on API error
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 8.2 Implement Page 2 results display in `frontend/src/components/ResultsPage.jsx`
    - Render scenarios table, ranked results list, highlighted best option, and explanation text
    - _Requirements: 9.4_

  - [x] 8.3 Wire pages together in `frontend/src/App.jsx`
    - Manage state to switch between input form and results page
    - Pass simulation response from Page 1 to Page 2
    - _Requirements: 9.1, 9.4_

- [x] 9. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- Each task references specific requirements for traceability
- Property tests use the `hypothesis` library and should be placed in `backend/tests/`
- The LLM singleton is loaded at import time — tests that exercise `structure_input` should mock the model to avoid slow cold starts
- `np.random.seed(42)` is set inside `run_simulation`; property tests for determinism should call the function twice and compare outputs directly
