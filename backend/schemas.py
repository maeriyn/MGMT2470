from __future__ import annotations

from typing import Literal, Optional, Dict, List
from pydantic import BaseModel, Field


class ValuationRequest(BaseModel):
	investor: Literal["acorn", "galaxy"]
	version: Optional[str] = None
	# Scenario inputs
	cagr: Optional[float] = None
	margin: Optional[float] = None
	pe_multiple: Optional[float] = None
	exit_horizon_years: Optional[int] = None
	# Follow-on round overrides
	follow_on_amount: Optional[float] = None
	follow_on_year: Optional[int] = None
	series_b_price_multiple: Optional[float] = None
	pro_rata_participation: Optional[float] = None
	# Anti-dilution toggle (placeholder)
	anti_dilution_on: bool = False
	# Target IRR override
	target_irr: Optional[float] = None
	# Scenario selection for exit
	exit_scenario: Literal["M&A", "IPO"] = "M&A"


class ValuationResponse(BaseModel):
	investor: str
	version: str
	pre_money_valuation: float
	price_per_share: float
	post_money_after_a: float
	investor_ownership_post_a: float
	investor_exit_cash: float
	exit_equity_value: float
	inputs_used: Dict[str, float]


class WaterfallRequest(BaseModel):
	investor: Literal["acorn", "galaxy"]
	version: Optional[str] = None
	exit_equity_value: float
	exit_horizon_years: Optional[int] = None
	exit_scenario: Literal["M&A", "IPO"] = "M&A"
	# Price per share to evaluate at (if known); if not provided, compute using implied VC method solution
	price_per_share: Optional[float] = None
	# Optional overrides matching valuation inputs
	cagr: Optional[float] = None
	margin: Optional[float] = None
	pe_multiple: Optional[float] = None


class WaterfallResponse(BaseModel):
	investor: str
	version: str
	payouts: Dict[str, float]
	price_per_share: float
	notes: Optional[str] = None


class TermVersionCreate(BaseModel):
	data: Dict
	version_id: str = Field(..., description="e.g., v2")



