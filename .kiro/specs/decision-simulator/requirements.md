# Requirements Document

## Introduction

The Decision Simulator is a local MVP that accepts a natural language decision from the user, structures it via a locally-run LLM (flan-t5-base), generates probabilistic scenarios per option, runs Monte Carlo-style simulations, ranks outcomes by user-defined weights, and returns a natural language explanation. All processing is local — no external API calls. The system is composed of a React/Vite frontend, a FastAPI backend, and SQLite persistence.

## Glossary

- **System**: The Decision Simulator application as a whole
- **API**: The FastAPI backend service
- **LLM_Service**: The component wrapping the flan-t5-base HuggingFace model
- **Simulation_Engine**: The component responsible for scenario generation, simulation, and ranking
- **Frontend**: The React/Vite single-page application
- **SimulationRequest**: The Pydantic model representing a validated incoming request
- **SimulationResponse**: The Pydantic model representing the full simulation result returned to the client
- **decision_text**: The raw natural language decision string provided by the user
- **risk_tolerance**: A float in [0.0, 1.0] representing the user's willingness to accept risk
- **time_horizon**: A positive integer representing the number of years to simulate
- **scenario**: A named probabilistic outcome for a given option
- **option**: One of the choices extracted from the user's decision
- **risk_w**: The derived risk penalty weight, equal to `1.0 - risk_tolerance`
- **option_score**: The probability-weighted aggregate score for an option across all its scenarios

---

## Requirements

### Requirement 1: Request Validation

**User Story:** As a user, I want the system to validate my inputs before processing, so that I receive clear feedback when my request is malformed.

#### Acceptance Criteria

1. IF `decision_text` is an empty string, THEN THE API SHALL reject the request with HTTP 422 and a descriptive validation error.
2. IF `risk` is less than 0.0 or greater than 1.0, THEN THE API SHALL reject the request with HTTP 422 and a descriptive validation error.
3. IF `time_horizon` is less than 1, THEN THE API SHALL reject the request with HTTP 422 and a descriptive validation error.
4. WHEN a valid `SimulationRequest` is received, THE API SHALL proceed with the simulation pipeline without modification to the input values.

---

### Requirement 2: LLM Input Structuring

**User Story:** As a developer, I want the LLM service to reliably extract structured data from free-form decision text, so that the simulation pipeline always has valid input to work with.

#### Acceptance Criteria

1. WHEN `structure_input` is called with a non-empty `decision_text`, THE LLM_Service SHALL return a dict containing the keys `decision`, `options`, and `factors`.
2. THE LLM_Service SHALL ensure the returned `options` list contains at least 2 elements.
3. THE LLM_Service SHALL ensure the returned `factors` list contains at least 1 element.
4. IF the LLM output cannot be parsed as valid JSON or is missing required keys, THEN THE LLM_Service SHALL return a fallback dict `{"decision": decision_text, "options": ["proceed", "do not proceed"], "factors": ["risk", "reward"]}` without raising an exception.
5. THE LLM_Service SHALL load the flan-t5-base model and tokenizer exactly once as a module-level singleton, so that subsequent calls do not incur model reload overhead.

---

### Requirement 3: Scenario Generation

**User Story:** As a user, I want the system to generate plausible scenarios for each decision option, so that I can understand the range of possible outcomes.

#### Acceptance Criteria

1. WHEN `generate_scenarios` is called with a valid `structured_input` and `risk_tolerance`, THE Simulation_Engine SHALL return exactly one scenario group per option in `structured_input["options"]`.
2. THE Simulation_Engine SHALL generate between 2 and 3 scenarios per option.
3. FOR each option group, THE Simulation_Engine SHALL assign scenario probabilities such that their sum equals exactly 1.0, computed by setting the last probability to `1.0 - sum(assigned_probs)`.
4. WHERE `risk_tolerance` is higher, THE Simulation_Engine SHALL produce a higher-variance probability distribution across scenarios for that option.

---

### Requirement 4: Numerical Simulation

**User Story:** As a user, I want the simulation to produce deterministic, semantically meaningful outcome metrics, so that results are reproducible and interpretable.

#### Acceptance Criteria

1. WHEN `run_simulation` is called, THE Simulation_Engine SHALL set `numpy.random.seed(42)` before any sampling to ensure deterministic output.
2. FOR all simulation results, THE Simulation_Engine SHALL produce a `salary` value greater than 0.
3. FOR all simulation results, THE Simulation_Engine SHALL produce a `risk_score` value in the range [0.0, 1.0].
4. FOR all simulation results, THE Simulation_Engine SHALL produce a `happiness` value in the range [0.0, 1.0].
5. WHEN a scenario name contains "high growth", "promotion", or "success", THE Simulation_Engine SHALL apply a salary multiplier sampled from [1.3, 2.0].
6. WHEN a scenario name contains "stressful", "risk", or "struggle", THE Simulation_Engine SHALL apply a salary multiplier sampled from [0.8, 1.1].
7. WHEN a scenario name matches neither high-growth nor stressful keywords, THE Simulation_Engine SHALL apply a neutral salary multiplier sampled from [1.0, 1.4].
8. THE Simulation_Engine SHALL scale salary by the factor `(1 + 0.05 * time_horizon)` to reflect time-based growth.

---

### Requirement 5: Outcome Ranking

**User Story:** As a user, I want the system to rank decision options by a weighted score that reflects my risk preference, so that the recommended option aligns with my priorities.

#### Acceptance Criteria

1. WHEN `rank_outcomes` is called, THE Simulation_Engine SHALL derive `risk_w` as `1.0 - risk_tolerance`.
2. THE Simulation_Engine SHALL normalize salary values dynamically using the minimum and maximum salary values present in the actual simulation results.
3. IF all simulated salaries are equal, THEN THE Simulation_Engine SHALL use a salary range of 1 to avoid division by zero.
4. THE Simulation_Engine SHALL compute each scenario's score as `salary_w * norm_salary + happiness_w * happiness - risk_w * risk_score`.
5. THE Simulation_Engine SHALL compute each option's aggregate score as `sum(scenario_score * scenario_probability)` across all scenarios for that option.
6. THE Simulation_Engine SHALL return a `ranked` list of options sorted in non-increasing order of aggregate score.
7. THE Simulation_Engine SHALL set `best_option` to the option with the highest aggregate score, equal to `ranked[0]["option"]`.
8. THE Simulation_Engine SHALL include scenario-level results sorted by score in the response for UI display.

---

### Requirement 6: Explanation Generation

**User Story:** As a user, I want a natural language explanation of the recommended option, so that I can understand the reasoning behind the simulation result.

#### Acceptance Criteria

1. WHEN `generate_explanation` is called, THE LLM_Service SHALL produce a plain text explanation string describing why `best_option` is recommended.
2. THE LLM_Service SHALL pass only `best_option` and the top 2–3 ranked scenarios to the explanation prompt, not the full results list.

---

### Requirement 7: Simulation API Endpoint

**User Story:** As a frontend developer, I want a single POST endpoint that runs the full simulation pipeline, so that the frontend can retrieve all results in one request.

#### Acceptance Criteria

1. THE API SHALL expose a `POST /simulate` endpoint accepting a `SimulationRequest` body.
2. WHEN a valid request is received, THE API SHALL orchestrate the pipeline in order: `structure_input` → `generate_scenarios` → `run_simulation` → `rank_outcomes` → `generate_explanation`.
3. THE API SHALL return a `SimulationResponse` containing `structured_input`, `scenarios`, `results`, `best_option`, and `explanation`.
4. THE API SHALL persist the `decision_text`, `structured_json`, `result_json`, and `created_at` timestamp to the SQLite `decisions` table after each successful simulation.
5. IF the SQLite write fails, THEN THE API SHALL log the error and still return the `SimulationResponse` to the client without raising an HTTP error.
6. THE API SHALL configure CORS to allow requests only from `localhost` origins.

---

### Requirement 8: Data Persistence

**User Story:** As a developer, I want each simulation run to be stored in SQLite, so that results are available for future reference.

#### Acceptance Criteria

1. THE System SHALL maintain a `decisions` table with columns: `id` (primary key, autoincrement), `decision_text`, `structured_json`, `result_json`, and `created_at` (UTC timestamp).
2. WHEN a simulation completes successfully, THE System SHALL insert one record into the `decisions` table containing the full request and response data.
3. THE System SHALL use SQLAlchemy ORM for all database interactions to prevent SQL injection.

---

### Requirement 9: React Frontend

**User Story:** As a user, I want a simple two-page web interface to submit decisions and view results, so that I can interact with the simulator without using the API directly.

#### Acceptance Criteria

1. THE Frontend SHALL render Page 1 with a decision text input field, a risk slider with range [0.0, 1.0], and a time horizon number input.
2. WHEN the user submits the form, THE Frontend SHALL POST the input values to `/simulate` and display a loading indicator while awaiting the response.
3. IF the API returns an error, THEN THE Frontend SHALL display a user-readable error message.
4. WHEN the response is received, THE Frontend SHALL render Page 2 displaying the scenarios table, ranked results, highlighted best option, and explanation text.
