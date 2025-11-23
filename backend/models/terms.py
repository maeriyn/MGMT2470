from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Literal

from pydantic import BaseModel, Field


TERMS_ROOT = Path("data/terms")


class FollowOnTerms(BaseModel):
	investment_amount: float = Field(..., description="Total Series B investment dollars injected into company")
	year_offset: int = Field(..., description="Years after Series A when Series B occurs")
	series_b_price_multiple: float = Field(2.0, description="Price_B = multiple * Price_A")
	pro_rata_participation: float = Field(1.0, ge=0.0, le=1.0, description="Fraction of Series A investor's ownership maintained in B via participation")


class Capitalization(BaseModel):
	founders_common_shares: int
	early_employees_common_shares: int
	option_pool_pre_shares: int
	pre_money_fully_diluted_shares: int


class LiquidationPreference(BaseModel):
	multiple: float = Field(..., description="e.g., 2.0 for 2x")
	participating: bool = Field(..., description="If True, participates pro‑rata after pref; if False, non‑participating")
	participation_cap_multiple: Optional[float] = Field(
		None, description="If participating and capped, cap multiple (e.g., 3.0x). None for uncapped."
	)


class Dividends(BaseModel):
	rate: float = Field(..., description="Annual cumulative dividend rate (simple) as decimal, e.g., 0.10")
	payable_on: Literal["liquidity", "ipo_or_sale"] = "liquidity"
	compounding: bool = False


class InvestorTerms(BaseModel):
	investor: Literal["acorn", "galaxy"]
	# Investor's own cash invested at Series A (not the full round if syndicated)
	investor_a_investment: float
	total_a_investment: float
	# Targets and defaults
	target_irr: float
	default_pe_multiple: float
	default_exit_horizon_years: int
	# Financial base
	base_year: int = 2030
	base_revenue: float = 52_000_000.0
	base_net_income: float = 3_450_000.0
	default_margin: float = 0.066  # ~ 3.45 / 52.0
	default_cagr: Optional[float] = None
	# Terms
	cap_table: Capitalization
	preference: LiquidationPreference
	dividends: Dividends
	mandatory_ipo_conversion: bool = True
	follow_on: FollowOnTerms


def _investor_dir(investor: str) -> Path:
	return TERMS_ROOT / investor.lower()


def list_versions(investor: str) -> Dict[str, Path]:
	idir = _investor_dir(investor)
	if not idir.exists():
		return {}
	return {p.stem: p for p in idir.glob("*.json") if p.name != "active.json"}


def get_active_version(investor: str) -> Optional[str]:
	idir = _investor_dir(investor)
	f = idir / "active.json"
	if not f.exists():
		# If only one version exists, assume it's active
		versions = list_versions(investor)
		if len(versions) == 1:
			return next(iter(versions.keys()))
		return None
	import json
	with f.open("r", encoding="utf-8") as fh:
		obj = json.load(fh)
	return obj.get("active")


def set_active_version(investor: str, version_id: str) -> None:
	idir = _investor_dir(investor)
	idir.mkdir(parents=True, exist_ok=True)
	import json
	with (idir / "active.json").open("w", encoding="utf-8") as fh:
		json.dump({"active": version_id}, fh, indent=2)


def load_terms(investor: str, version: Optional[str] = None) -> InvestorTerms:
	investor = investor.lower()
	idir = _investor_dir(investor)
	if version is None:
		version = get_active_version(investor)
	versions = list_versions(investor)
	if not versions:
		raise FileNotFoundError(f"No term versions found for investor '{investor}'. Expected under {idir}")
	if version is None:
		# Pick latest (sorted by name)
		version = sorted(versions.keys())[-1]
	path = idir / f"{version}.json"
	if not path.exists():
		raise FileNotFoundError(f"Terms file not found: {path}")
	import json
	with path.open("r", encoding="utf-8") as fh:
		data = json.load(fh)
	return InvestorTerms.model_validate(data)


def save_new_version(investor: str, version_id: str, data: Dict) -> str:
	investor = investor.lower()
	idir = _investor_dir(investor)
	idir.mkdir(parents=True, exist_ok=True)
	import json
	target = idir / f"{version_id}.json"
	if target.exists():
		raise FileExistsError(f"Version '{version_id}' already exists for investor '{investor}'.")
	with target.open("w", encoding="utf-8") as fh:
		json.dump(data, fh, indent=2)
	return version_id



