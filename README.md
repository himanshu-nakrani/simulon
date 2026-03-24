---
title: Decision Simulator API
emoji: 🔮
colorFrom: purple
colorTo: indigo
sdk: docker
pinned: false
---

# Decision Simulator API

FastAPI backend for the Decision Simulator. Accepts a natural language decision and returns probabilistic scenario simulations using flan-t5-base.

## Endpoint

`POST /simulate`

```json
{
  "decision_text": "Should I switch jobs?",
  "risk": 0.6,
  "time_horizon": 3
}
```
