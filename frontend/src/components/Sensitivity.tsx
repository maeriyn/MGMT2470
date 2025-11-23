import { useEffect, useMemo, useState } from 'react'
import { Box, Stack, Typography } from '@mui/material'
import { Investor, ValuationReq, ValuationResp, computeValuation } from '../api/client'

export default function Sensitivity({ investor, inputs }: { investor: Investor, inputs: any }) {
	const [rows, setRows] = useState<Array<{ label: string, value: number }>>([])
	useEffect(() => {
		const run = async () => {
			const sweepIRR = [0.3, 0.4, 0.5, 0.6, 0.7]
			const out: Array<{ label: string, value: number }> = []
			for (const irr of sweepIRR) {
				const req: ValuationReq = { investor, ...inputs, target_irr: irr }
				const resp: ValuationResp = await computeValuation(req)
				out.push({ label: `${Math.round(irr * 100)}% IRR`, value: resp.pre_money_valuation })
			}
			setRows(out)
		}
		run().catch(console.error)
	}, [investor, inputs])

	const currency = (n: number) => n.toLocaleString(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
	return (
		<Stack spacing={1}>
			<Typography variant="h6" fontWeight={700}>Sensitivity (Pre‑Money vs Target IRR)</Typography>
			{rows.map(r => (
				<Box key={r.label} sx={{ display: 'flex', justifyContent: 'space-between' }}>
					<Typography variant="body2">{r.label}</Typography>
					<Typography variant="body2">{currency(r.value)}</Typography>
				</Box>
			))}
		</Stack>
	)
}


