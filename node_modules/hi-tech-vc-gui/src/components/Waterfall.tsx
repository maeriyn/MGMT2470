import { useEffect, useState } from 'react'
import { Box, Slider, Stack, ToggleButton, ToggleButtonGroup, Typography } from '@mui/material'
import { Investor, ValuationResp, WaterfallReq, WaterfallResp, computeWaterfall } from '../api/client'

export default function Waterfall({ investor, inputs, valuation }: { investor: Investor, inputs: any, valuation: ValuationResp | null }) {
	const [scenario, setScenario] = useState<'M&A' | 'IPO'>(inputs.exit_scenario)
	const [exitValue, setExitValue] = useState<number>(valuation?.exit_equity_value || 200_000_000)
	const [resp, setResp] = useState<WaterfallResp | null>(null)

	useEffect(() => {
		setScenario(inputs.exit_scenario)
	}, [inputs.exit_scenario])

	useEffect(() => {
		if (!valuation) return
		const run = async () => {
			const req: WaterfallReq = {
				investor,
				version: inputs.version,
				exit_equity_value: exitValue,
				exit_scenario: scenario,
				price_per_share: valuation.price_per_share
			}
			const r = await computeWaterfall(req)
			setResp(r)
		}
		run().catch(console.error)
	}, [investor, inputs.version, scenario, exitValue, valuation?.price_per_share])

	const currency = (n: number) => n.toLocaleString(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
	const total = (resp ? Object.values(resp.payouts).reduce((a, b) => a + b, 0) : 0)

	return (
		<Stack spacing={1}>
			<Typography variant="h6" fontWeight={700}>Waterfall</Typography>
			<ToggleButtonGroup value={scenario} exclusive onChange={(_, v) => v && setScenario(v)} size="small" sx={{ mb: 1 }}>
				<ToggleButton value="M&A">M&amp;A</ToggleButton>
				<ToggleButton value="IPO">IPO</ToggleButton>
			</ToggleButtonGroup>
			<Typography variant="body2">Exit Equity Value: {currency(exitValue)}</Typography>
			<Slider min={25_000_000} max={1_000_000_000} step={5_000_000} value={exitValue} onChange={(_, v) => setExitValue(v as number)} />
			{resp && (
				<Box>
					{Object.entries(resp.payouts).map(([k, v]) => (
						<Box key={k} sx={{ display: 'flex', justifyContent: 'space-between' }}>
							<Typography variant="body2">{k}</Typography>
							<Typography variant="body2">{currency(v)}</Typography>
						</Box>
					))}
					<Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
						<Typography variant="body2" fontWeight={700}>Total</Typography>
						<Typography variant="body2" fontWeight={700}>{currency(total)}</Typography>
					</Box>
				</Box>
			)}
		</Stack>
	)
}


