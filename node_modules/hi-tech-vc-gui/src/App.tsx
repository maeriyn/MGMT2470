import { useEffect, useMemo, useState } from 'react'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import {
	Box, Container, CssBaseline, Grid2 as Grid, Typography, Paper, Divider
} from '@mui/material'
import { Investor, ValuationResp, computeValuation, listTermVersions } from './api/client'
import ValuationInputs from './components/ValuationInputs'
import ValuationResults from './components/ValuationResults'
import Sensitivity from './components/Sensitivity'
import Waterfall from './components/Waterfall'
import SummaryTable from './components/SummaryTable'

const theme = createTheme({
	palette: {
		mode: 'light',
		primary: { main: '#0b6efd' },
		secondary: { main: '#6c757d' }
	},
	typography: {
		fontFamily: ['Inter', 'Segoe UI', 'Roboto', 'Arial', 'sans-serif'].join(',')
	}
})

export default function App() {
	const [investor, setInvestor] = useState<Investor>('galaxy')
	const [versions, setVersions] = useState<string[]>([])
	const [activeVersion, setActiveVersion] = useState<string | undefined>(undefined)
	const [inputs, setInputs] = useState({
		version: undefined as string | undefined,
		cagr: undefined as number | undefined,
		margin: undefined as number | undefined,
		pe_multiple: undefined as number | undefined,
		exit_horizon_years: undefined as number | undefined,
		follow_on_amount: undefined as number | undefined,
		follow_on_year: undefined as number | undefined,
		series_b_price_multiple: 2.0,
		pro_rata_participation: 1.0,
		target_irr: undefined as number | undefined,
		exit_scenario: 'M&A' as 'M&A' | 'IPO'
	})
	const [valuation, setValuation] = useState<ValuationResp | null>(null)

	useEffect(() => {
		listTermVersions(investor).then((res) => {
			setVersions(res.versions)
			setActiveVersion(res.active)
			setInputs((old) => ({ ...old, version: res.active }))
		})
	}, [investor])

	useEffect(() => {
		const run = async () => {
			const resp = await computeValuation({ investor, ...inputs })
			setValuation(resp)
		}
		run().catch(console.error)
	}, [investor, inputs])

	return (
		<ThemeProvider theme={theme}>
			<CssBaseline />
			<Container maxWidth="xl" sx={{ py: 3 }}>
				<Typography variant="h5" fontWeight={700} gutterBottom>
					Hi‑Tech VC Valuation — Live Model
				</Typography>
				<Grid container spacing={2}>
					<Grid size={{ xs: 12, md: 3 }}>
						<Paper variant="outlined" sx={{ p: 2 }}>
							<ValuationInputs
								investor={investor}
								setInvestor={setInvestor}
								versions={versions}
								activeVersion={activeVersion}
								inputs={inputs}
								setInputs={setInputs}
							/>
						</Paper>
					</Grid>
					<Grid size={{ xs: 12, md: 9 }}>
						<Grid container spacing={2}>
							<Grid size={12}>
								<ValuationResults valuation={valuation} />
							</Grid>
							<Grid size={{ xs: 12, md: 6 }}>
								<Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
									<Sensitivity investor={investor} inputs={inputs} />
								</Paper>
							</Grid>
							<Grid size={{ xs: 12, md: 6 }}>
								<Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
									<Waterfall investor={investor} inputs={inputs} valuation={valuation} />
								</Paper>
							</Grid>
							<Grid size={12}>
								<Paper variant="outlined" sx={{ p: 2 }}>
									<SummaryTable valuation={valuation} />
								</Paper>
							</Grid>
						</Grid>
					</Grid>
				</Grid>
			</Container>
		</ThemeProvider>
	)
}

