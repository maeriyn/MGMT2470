from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
	ValuationRequest,
	ValuationResponse,
	WaterfallRequest,
	WaterfallResponse,
	TermVersionCreate,
)
from .models.terms import load_terms, list_versions, save_new_version, set_active_version, get_active_version
from .models.valuation import (
	project_exit,
	exit_value_from_pe,
	build_pre_money_fd_shares,
	simulate_rounds,
	solve_premoney_for_target_irr,
	investor_proceeds_and_irr,
)

app = FastAPI(title="Hi-Tech VC Valuation API", version="1.0.0")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


def _apply_overrides(terms, req: ValuationRequest):
	# Override basic levers if provided
	if req.follow_on_amount is not None:
		terms.follow_on.investment_amount = float(req.follow_on_amount)
	if req.follow_on_year is not None:
		terms.follow_on.year_offset = int(req.follow_on_year)
	if req.series_b_price_multiple is not None:
		terms.follow_on.series_b_price_multiple = float(req.series_b_price_multiple)
	if req.pro_rata_participation is not None:
		terms.follow_on.pro_rata_participation = float(req.pro_rata_participation)
	return terms


@app.post("/api/valuation", response_model=ValuationResponse)
def api_valuation(req: ValuationRequest) -> ValuationResponse:
	try:
		terms = load_terms(req.investor, version=req.version)
	except FileNotFoundError as e:
		raise HTTPException(status_code=404, detail=str(e))

	terms = _apply_overrides(terms, req)
	exit_years = int(req.exit_horizon_years or terms.default_exit_horizon_years)
	margin = float(req.margin if req.margin is not None else terms.default_margin)
	pe = float(req.pe_multiple if req.pe_multiple is not None else terms.default_pe_multiple)
	target_irr = float(req.target_irr if req.target_irr is not None else terms.target_irr)

	# Compute default CAGR if none provided
	cagr = float(req.cagr if req.cagr is not None else (terms.default_cagr if terms.default_cagr is not None else 0.0))
	exit_rev, exit_ni = project_exit(cagr, margin, terms.base_revenue, terms.base_year, terms.base_year + exit_years)
	exit_equity = exit_value_from_pe(exit_ni, pe)

	# Solve VC method for pre-money valuation
	pre_money, price_per_share, investor_exit = solve_premoney_for_target_irr(
		terms, exit_equity, exit_years, target_irr, scenario=req.exit_scenario
	)

	pre_fd = build_pre_money_fd_shares(terms)
	rounds = simulate_rounds(terms, price_per_share)
	post_money_after_a = pre_money + terms.total_a_investment
	investor_ownership_post_a = rounds.series_a_shares_investor / rounds.post_money_shares_after_a

	version_used = req.version or (get_active_version(req.investor) or "v1")
	return ValuationResponse(
		investor=terms.investor,
		version=version_used,
		pre_money_valuation=pre_money,
		price_per_share=price_per_share,
		post_money_after_a=post_money_after_a,
		investor_ownership_post_a=investor_ownership_post_a,
		investor_exit_cash=investor_exit,
		exit_equity_value=exit_equity,
		inputs_used={
			"cagr": cagr,
			"margin": margin,
			"pe_multiple": pe,
			"target_irr": target_irr,
			"exit_horizon_years": float(exit_years),
		},
	)


@app.post("/api/waterfall", response_model=WaterfallResponse)
def api_waterfall(req: WaterfallRequest) -> WaterfallResponse:
	try:
		terms = load_terms(req.investor, version=req.version)
	except FileNotFoundError as e:
		raise HTTPException(status_code=404, detail=str(e))

	exit_years = int(req.exit_horizon_years or terms.default_exit_horizon_years)
	margin = float(req.margin if req.margin is not None else terms.default_margin)
	pe = float(req.pe_multiple if req.pe_multiple is not None else terms.default_pe_multiple)
	# choose price per share
	if req.price_per_share is not None:
		price_a = float(req.price_per_share)
	else:
		# get implied price from VC method using investor IRR target
		exit_rev, exit_ni = project_exit(
			terms.default_cagr or 0.0, margin, terms.base_revenue, terms.base_year, terms.base_year + exit_years
		)
		exit_equity = exit_value_from_pe(exit_ni, pe)
		pre_money, price_a, _ = solve_premoney_for_target_irr(terms, exit_equity, exit_years, terms.target_irr, scenario=req.exit_scenario)

	_, irr = investor_proceeds_and_irr(terms, price_a, float(req.exit_equity_value), exit_years, scenario=req.exit_scenario)
	from .models.valuation import simulate_rounds, waterfall as wf
	rounds = simulate_rounds(terms, price_a)
	payouts = wf(float(req.exit_equity_value), terms, rounds, exit_years, scenario=req.exit_scenario)

	version_used = req.version or (get_active_version(req.investor) or "v1")
	return WaterfallResponse(
		investor=terms.investor,
		version=version_used,
		payouts=payouts,
		price_per_share=price_a,
		notes=None,
	)


@app.get("/api/terms/{investor}")
def api_terms_list(investor: str):
	versions = list_versions(investor)
	active = get_active_version(investor)
	return {
		"investor": investor,
		"active": active,
		"versions": sorted(list(versions.keys())),
	}


@app.get("/api/terms/{investor}/{version}")
def api_terms_get(investor: str, version: str):
	try:
		terms = load_terms(investor, version=version)
	except FileNotFoundError as e:
		raise HTTPException(status_code=404, detail=str(e))
	return terms.model_dump()


@app.post("/api/terms/{investor}")
def api_terms_create(investor: str, body: TermVersionCreate):
	try:
		version_id = save_new_version(investor, body.version_id, body.data)
	except FileExistsError as e:
		raise HTTPException(status_code=400, detail=str(e))
	return {"investor": investor, "version": version_id}


@app.post("/api/terms/{investor}/activate")
def api_terms_activate(investor: str, body: dict):
	version_id = body.get("version_id")
	if not version_id:
		raise HTTPException(status_code=400, detail="version_id required")
	versions = list_versions(investor)
	if version_id not in versions:
		raise HTTPException(status_code=404, detail=f"Version '{version_id}' not found")
	set_active_version(investor, version_id)
	return {"investor": investor, "active": version_id}


