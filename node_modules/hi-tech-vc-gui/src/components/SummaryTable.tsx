import { Box, Divider, Grid2 as Grid, Typography } from '@mui/material'
import { ValuationResp } from '../api/client'

export default function SummaryTable({ valuation }: { valuation: ValuationResp | null }) {
	const currency = (n: number) => n.toLocaleString(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
	const pct = (x: number) => (x * 100).toFixed(1) + '%'
	return (
		<Box>
			<Typography variant="h6" fontWeight={700} gutterBottom>Founders’ Summary (Selected Investor)</Typography>
			{!valuation ? (
				<Typography variant="body2">Awaiting results…</Typography>
			) : (
				<Grid container spacing={1}>
					<Grid size={4}><Typography variant="body2" fontWeight={700}>Investor</Typography></Grid>
					<Grid size={8}><Typography variant="body2">{valuation.investor.toUpperCase()} — {valuation.version}</Typography></Grid>
					<Grid size={4}><Typography variant="body2" fontWeight={700}>Pre‑Money Valuation</Typography></Grid>
					<Grid size={8}><Typography variant="body2">{currency(valuation.pre_money_valuation)}</Typography></Grid>
					<Grid size={4}><Typography variant="body2" fontWeight={700}>Price per Share</Typography></Grid>
					<Grid size={8}><Typography variant="body2">{currency(valuation.price_per_share)}</Typography></Grid>
					<Grid size={4}><Typography variant="body2" fontWeight={700}>Post‑Money (A)</Typography></Grid>
					<Grid size={8}><Typography variant="body2">{currency(valuation.post_money_after_a)}</Typography></Grid>
					<Grid size={4}><Typography variant="body2" fontWeight={700}>Investor Ownership (post A)</Typography></Grid>
					<Grid size={8}><Typography variant="body2">{pct(valuation.investor_ownership_post_a)}</Typography></Grid>
				</Grid>
			)}
			<Divider sx={{ mt: 2 }} />
		</Box>
	)
}


