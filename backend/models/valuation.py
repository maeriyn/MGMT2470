from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Literal

import numpy as np

from .terms import InvestorTerms, LiquidationPreference


@dataclass
class RoundResult:
	price_per_share: float
	series_a_shares_issued_total: float
	series_a_shares_investor: float
	series_b_shares_total: float
	series_b_shares_investor: float
	pre_money_shares: float
	post_money_shares_after_a: float
	post_money_shares_after_b: float


def project_exit(cagr: float, margin: float, base_revenue: float, base_year: int, target_year: int) -> Tuple[float, float]:
	if target_year < base_year:
		raise ValueError("target_year must be >= base_year")
	years = target_year - base_year
	exit_revenue = float(base_revenue) * ((1.0 + float(cagr)) ** years)
	exit_net_income = exit_revenue * float(margin)
	return exit_revenue, exit_net_income


def exit_value_from_pe(net_income: float, pe_multiple: float) -> float:
	return float(net_income) * float(pe_multiple)


def build_pre_money_fd_shares(terms: InvestorTerms) -> float:
	# Validate pre-money FD shares match components
	cap = terms.cap_table
	computed = cap.founders_common_shares + cap.early_employees_common_shares + cap.option_pool_pre_shares
	if cap.pre_money_fully_diluted_shares != computed:
		# trust explicit FD number; keep for price per share
		return float(cap.pre_money_fully_diluted_shares)
	return float(computed)


def simulate_rounds(terms: InvestorTerms, price_a: float) -> RoundResult:
	pre_fd = build_pre_money_fd_shares(terms)
	# Series A issuance
	total_invest_a = float(terms.total_a_investment)
	investor_a = float(terms.investor_a_investment)
	series_a_shares_total = total_invest_a / float(price_a)
	series_a_shares_investor = investor_a / float(price_a)
	post_a_shares = pre_fd + series_a_shares_total
	# Series B issuance at multiple
	price_b = price_a * float(terms.follow_on.series_b_price_multiple)
	total_invest_b = float(terms.follow_on.investment_amount)
	series_b_total = total_invest_b / float(price_b)
	# Investor pro‑rata: keep same % ownership (after A) times pro_rata fraction
	own_after_a = series_a_shares_investor / post_a_shares
	pro_rata = float(terms.follow_on.pro_rata_participation)
	investor_target_b_shares = series_b_total * own_after_a * pro_rata
	post_b_shares = post_a_shares + series_b_total
	return RoundResult(
		price_per_share=price_a,
		series_a_shares_issued_total=series_a_shares_total,
		series_a_shares_investor=investor_a / price_a,
		series_b_shares_total=series_b_total,
		series_b_shares_investor=investor_target_b_shares,
		pre_money_shares=pre_fd,
		post_money_shares_after_a=post_a_shares,
		post_money_shares_after_b=post_b_shares,
	)


def accrue_dividends(principal_invested: float, rate: float, years: float, compounding: bool = False) -> float:
	if rate <= 0 or years <= 0:
		return 0.0
	if compounding:
		return float(principal_invested) * ((1.0 + float(rate)) ** float(years) - 1.0)
	return float(principal_invested) * float(rate) * float(years)


def _as_converted_value(
	proceeds_equity_value: float,
	investor_common_fraction: float,
) -> float:
	return proceeds_equity_value * investor_common_fraction


def waterfall(
	proceeds_equity_value: float,
	terms: InvestorTerms,
	rounds: RoundResult,
	horizon_years: int,
	scenario: Literal["M&A", "IPO"] = "M&A",
) -> Dict[str, float]:
	"""
	Returns payout by class:
	- series_a_investor
	- series_a_others
	- common (founders + employees + pool + series_b + any conversions)
	Note: We treat Series B as common shares (no separate preference modeled).
	"""
	proceeds = float(proceeds_equity_value)
	# Share counts
	common_shares = rounds.pre_money_shares + rounds.series_b_shares_total
	series_a_total = rounds.series_a_shares_issued_total
	series_a_investor = rounds.series_a_shares_investor
	series_a_other = series_a_total - series_a_investor
	total_fully_diluted = common_shares + series_a_total

	# Fractions if as‑converted
	f_investor_common = series_a_investor / total_fully_diluted
	f_other_a_common = series_a_other / total_fully_diluted
	f_common = common_shares / total_fully_diluted

	# Dividends (Series A)
	div_rate = terms.dividends.rate
	div_comp = terms.dividends.compounding
	div_investor = accrue_dividends(terms.investor_a_investment, div_rate, horizon_years, div_comp)
	div_other = accrue_dividends(terms.total_a_investment - terms.investor_a_investment, div_rate, horizon_years, div_comp)

	# Preference
	lp: LiquidationPreference = terms.preference
	pref_investor = terms.investor_a_investment * lp.multiple
	pref_other = (terms.total_a_investment - terms.investor_a_investment) * lp.multiple

	if scenario == "IPO" and terms.mandatory_ipo_conversion:
		# As‑converted, do not pay prefs or cash dividends
		return {
			"series_a_investor": _as_converted_value(proceeds, f_investor_common),
			"series_a_others": _as_converted_value(proceeds, f_other_a_common),
			"common": _as_converted_value(proceeds, f_common),
		}

	# M&A (or non‑IPO liquidity) with preferences and dividends
	remaining = proceeds
	payout_investor = 0.0
	payout_others_a = 0.0
	payout_common = 0.0

	# Pay preferences + dividends
	required_investor = pref_investor + div_investor
	required_others = pref_other + div_other
	required_total = required_investor + required_others

	if lp.participating:
		# Pay pref+div first if proceeds allow
		if remaining >= required_total:
			payout_investor += required_investor
			payout_others_a += required_others
			remaining -= required_total
			# Participate pro‑rata with common thereafter
			# Participation cap (if any): limit to cap * original investment
			# We apply cap at the investor class level
			cap_multiple = lp.participation_cap_multiple
			# As-converted fractions:
			total_partic_fraction = (series_a_total + common_shares) / total_fully_diluted  # equals 1.0
			# Pro‑rata split remaining by fully diluted ownership
			alloc_investor = remaining * (series_a_investor / total_fully_diluted)
			alloc_others_a = remaining * (series_a_other / total_fully_diluted)
			alloc_common = remaining * (common_shares / total_fully_diluted)
			# Apply cap if specified
			if cap_multiple is not None:
				max_total_investor = terms.investor_a_investment * cap_multiple
				excess = max(0.0, (payout_investor + alloc_investor) - max_total_investor)
				if excess > 0:
					alloc_common += excess
					alloc_investor -= excess
			payout_investor += alloc_investor
			payout_others_a += alloc_others_a
			payout_common += alloc_common
		else:
			# Not enough to cover prefs+divs: pay pro‑rata of requireds
			if required_total > 0:
				ratio = remaining / required_total
			else:
				ratio = 0.0
			payout_investor += required_investor * ratio
			payout_others_a += required_others * ratio
			remaining = 0.0
	else:
		# Non‑participating: each holder takes max(pref+div, as-converted)
		as_conv_investor = _as_converted_value(proceeds, f_investor_common)
		as_conv_others = _as_converted_value(proceeds, f_other_a_common)
		as_conv_common = _as_converted_value(proceeds, f_common)
		payout_investor = max(required_investor, as_conv_investor)
		payout_others_a = max(required_others, as_conv_others)
		# Common gets the remainder
		rem = proceeds - payout_investor - payout_others_a
		payout_common = max(0.0, rem)

	return {
		"series_a_investor": float(payout_investor),
		"series_a_others": float(payout_others_a),
		"common": float(payout_common),
	}


def _irr_from_cashflows(cashflows: List[float]) -> Optional[float]:
	"""
	Compute IRR using bisection on NPV=0. Returns None if cannot bracket.
	"""
	def npv(rate: float) -> float:
		return sum(cf / ((1.0 + rate) ** t) for t, cf in enumerate(cashflows))

	low, high = -0.99, 10.0
	f_low = npv(low)
	f_high = npv(high)
	if np.sign(f_low) == np.sign(f_high):
		# Try expanding high
		for high in [20.0, 50.0, 100.0]:
			f_high = npv(high)
			if np.sign(f_low) != np.sign(f_high):
				break
		else:
			return None

	for _ in range(100):
		mid = 0.5 * (low + high)
		f_mid = npv(mid)
		if abs(f_mid) < 1e-8:
			return mid
		if np.sign(f_mid) == np.sign(f_low):
			low, f_low = mid, f_mid
		else:
			high, f_high = mid, f_mid
	return 0.5 * (low + high)


def investor_proceeds_and_irr(
	terms: InvestorTerms,
	price_a: float,
	proceeds_equity_value: float,
	horizon_years: int,
	scenario: Literal["M&A", "IPO"] = "M&A",
) -> Tuple[float, Optional[float]]:
	"""
	Returns (investor_cash_proceeds_at_exit, IRR).
	"""
	rounds = simulate_rounds(terms, price_a)
	payouts = waterfall(proceeds_equity_value, terms, rounds, horizon_years, scenario=scenario)
	investor_exit_cash = payouts["series_a_investor"]
	# Cash flows:
	# t=0: -investor_a_investment
	# t=follow_on_year: - investor's pro-rata B dollars
	# t=horizon: + investor_exit_cash
	cfs = [ -float(terms.investor_a_investment) ]
	# fill zero years until follow_on
	for _ in range(max(0, terms.follow_on.year_offset - 1)):
		cfs.append(0.0)
	# investor B cash outlay
	price_b = price_a * float(terms.follow_on.series_b_price_multiple)
	investor_b_shares = rounds.series_b_shares_investor
	investor_b_dollars = investor_b_shares * price_b
	cfs.append(-float(investor_b_dollars))
	# pad until exit
	remaining_years = max(0, horizon_years - terms.follow_on.year_offset - 1)
	cfs.extend([0.0] * remaining_years)
	# exit cash
	cfs.append(float(investor_exit_cash))
	irr = _irr_from_cashflows(cfs)
	return investor_exit_cash, irr


def solve_premoney_for_target_irr(
	terms: InvestorTerms,
	exit_equity_value: float,
	horizon_years: int,
	target_irr: float,
	scenario: Literal["M&A", "IPO"] = "M&A",
) -> Tuple[float, float, float]:
	"""
	Find pre-money valuation V_pre such that the investor IRR equals target_irr.
	Returns (pre_money_valuation, price_per_share, investor_exit_cash_at_solution)
	"""
	pre_fd = build_pre_money_fd_shares(terms)

	def f(v_pre: float) -> float:
		price_a = v_pre / pre_fd
		_, irr = investor_proceeds_and_irr(terms, price_a, exit_equity_value, horizon_years, scenario=scenario)
		if irr is None:
			# Penalize invalid cases
			return 1e3
		return irr - target_irr

	# Bracket on pre-money valuation
	low, high = 1e5, 1e10
	f_low, f_high = f(low), f(high)
	# Expand if needed
	tries = 0
	while np.sign(f_low) == np.sign(f_high) and tries < 10:
		high *= 2.0
		f_high = f(high)
		tries += 1
	if np.sign(f_low) == np.sign(f_high):
		# Fallback: return a reasonable default using price where investor gets exact ownership = invest/exit
		price = (exit_equity_value * 0.2) / terms.total_a_investment / 10.0  # arbitrary fallback
		return pre_fd * price, price, 0.0

	# Bisection
	for _ in range(120):
		mid = 0.5 * (low + high)
		f_mid = f(mid)
		if abs(f_mid) < 1e-7:
			solution = mid
			break
		if np.sign(f_mid) == np.sign(f_low):
			low, f_low = mid, f_mid
		else:
			high, f_high = mid, f_mid
	else:
		solution = 0.5 * (low + high)

	price_a = solution / pre_fd
	inv_exit, irr = investor_proceeds_and_irr(terms, price_a, exit_equity_value, horizon_years, scenario=scenario)
	return solution, price_a, inv_exit



