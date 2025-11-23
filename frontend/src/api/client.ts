import axios from 'axios'

const baseURL = (import.meta as any).env?.VITE_API_BASE || 'http://localhost:8000'

export const api = axios.create({
	baseURL
})

export type Investor = 'acorn' | 'galaxy'

export interface ValuationReq {
	investor: Investor
	version?: string
	cagr?: number
	margin?: number
	pe_multiple?: number
	exit_horizon_years?: number
	follow_on_amount?: number
	follow_on_year?: number
	series_b_price_multiple?: number
	pro_rata_participation?: number
	target_irr?: number
	exit_scenario?: 'M&A' | 'IPO'
}

export interface ValuationResp {
	investor: string
	version: string
	pre_money_valuation: number
	price_per_share: number
	post_money_after_a: number
	investor_ownership_post_a: number
	investor_exit_cash: number
	exit_equity_value: number
	inputs_used: Record<string, number>
}

export async function computeValuation(req: ValuationReq) {
	const { data } = await api.post<ValuationResp>('/api/valuation', req)
	return data
}

export interface WaterfallReq {
	investor: Investor
	version?: string
	exit_equity_value: number
	exit_horizon_years?: number
	exit_scenario?: 'M&A' | 'IPO'
	price_per_share?: number
	cagr?: number
	margin?: number
	pe_multiple?: number
}

export interface WaterfallResp {
	investor: string
	version: string
	payouts: Record<string, number>
	price_per_share: number
	notes?: string
}

export async function computeWaterfall(req: WaterfallReq) {
	const { data } = await api.post<WaterfallResp>('/api/waterfall', req)
	return data
}

export async function listTermVersions(investor: Investor) {
	const { data } = await api.get(`/api/terms/${investor}`)
	return data as { investor: Investor; active?: string; versions: string[] }
}

export async function getTermSheet(investor: Investor, version: string) {
	const { data } = await api.get(`/api/terms/${investor}/${version}`)
	return data
}

export async function createTermVersion(investor: Investor, version_id: string, dataObj: any) {
	const { data } = await api.post(`/api/terms/${investor}`, { version_id, data: dataObj })
	return data
}

export async function activateTermVersion(investor: Investor, version_id: string) {
	const { data } = await api.post(`/api/terms/${investor}/activate`, { version_id })
	return data
}

