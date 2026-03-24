from pydantic import BaseModel, field_validator


class SimulationRequest(BaseModel):
    decision_text: str
    risk: float
    time_horizon: int

    @field_validator("decision_text")
    @classmethod
    def decision_text_must_be_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("decision_text must not be empty")
        return v

    @field_validator("risk")
    @classmethod
    def risk_must_be_in_range(cls, v: float) -> float:
        if v < 0.0 or v > 1.0:
            raise ValueError("risk must be between 0.0 and 1.0")
        return v

    @field_validator("time_horizon")
    @classmethod
    def time_horizon_must_be_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("time_horizon must be >= 1")
        return v


class SimulationResponse(BaseModel):
    structured_input: dict
    scenarios: list[dict]
    results: list[dict]
    best_option: str
    explanation: str
