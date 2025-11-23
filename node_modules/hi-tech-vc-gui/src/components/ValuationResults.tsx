import { Box, Stack, Typography } from '@mui/material'
import { ValuationResp } from '../api/client'

export default function ValuationResults({ valuation }: { valuation: ValuationResp | null }) {
	if (!valuation) {
		return <Typography variant="body2">Computing valuation…</Typography>
	}
	const currency = (n: number) => n.toLocaleString(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
	const pct = (x: number) => (x * 100).toFixed(2) + '%'
	return (
		<Stack spacing={1} component={Box} sx={{ p: 2 }} >
			<Typography variant="h6" fontWeight={700}>VC Method Results</Typography>
			<Typography variant="body2">Investor: {valuation.investor.toUpperCase()} — Version: {valuation.version}</Typography>
			<Typography>Exit Equity Value: {currency(valuation.exit_equity_value)}</Typography>
			<Typography>Implied Pre‑Money Valuation: {currency(valuation.pre_money_valuation)}</Typography>
			<Typography>Price per Share: {currency(valuation.price_per_share)}</Typography>
			<Typography>Post‑Money (after A): {currency(valuation.post_money_after_a)}</Typography>
			<Typography>Investor Ownership (post A): {pct(valuation.investor_ownership_post_a)}</Typography>
			<Typography>Investor Exit Cash (at target IRR): {currency(valuation.investor_exit_cash)}</Typography>
		</Stack>
	)
}


