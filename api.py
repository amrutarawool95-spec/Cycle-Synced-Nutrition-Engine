"""Run:  uvicorn api:app --reload   then open http://127.0.0.1:8000/docs"""
from typing import Dict, Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field
from phase_engine import recommend

app = FastAPI(title="Cycle-synced nutrition (exploratory prototype)")

class Req(BaseModel):
    genotypes: Dict[str, str] = Field(example={"rs1801282": "CG"})
    fasting_insulin_uIU_mL: Optional[float] = None
    cycle_day: Optional[int] = Field(None, ge=1, le=60)
    cycle_length: Optional[int] = None

@app.post("/recommend")
def rec(r: Req):
    return recommend(r.genotypes, r.fasting_insulin_uIU_mL, r.cycle_day, r.cycle_length)
  
