import { useEffect } from 'react'
import {
	Box, Button, Divider, FormControl, InputLabel, MenuItem, Select, SelectChangeEvent, Stack, TextField, ToggleButton, ToggleButtonGroup, Typography
} from '@mui/material'
import { Investor, activateTermVersion, createTermVersion, listTermVersions, getTermSheet } from '../api/client'
import { useState } from 'react'

export default function ValuationInputs({
	investor,
	setInvestor,
	versions,
	activeVersion,
	inputs,
	setInputs
}: {
	investor: Investor
	setInvestor: (v: Investor) => void
	versions: string[]
	activeVersion?: string
	inputs: any
	setInputs: (f: any) => void
}) {
	const [newVerId, setNewVerId] = useState('')
	const [newVerJson, setNewVerJson] = useState('')
	const [termDefaults, setTermDefaults] = useState<any>(null)

	useEffect(() => {
		if (activeVersion) {
			getTermSheet(investor, activeVersion).then(setTermDefaults).catch(console.error)
		}
	}, [investor, activeVersion])

	const handleInvestor = (_: any, v: Investor) => {
		if (v) setInvestor(v)
	}
	const handleVersion = (e: SelectChangeEvent) => {
		setInputs({ ...inputs, version: e.target.value })
	}
	const handleCreateVersion = async () => {
		try {
			const dataObj = JSON.parse(newVerJson)
			await createTermVersion(investor, newVerId, dataObj)
			await activateTermVersion(investor, newVerId)
			const res = await listTermVersions(investor)
			setInputs({ ...inputs, version: newVerId })
			alert(`Version ${newVerId} created and activated`)
		} catch (e: any) {
			alert(`Failed to create version: ${e?.message || e}`)
		}
	}

	return (
		<Stack spacing={2}>
			<Typography variant="subtitle1" fontWeight={700}>Investor</Typography>
			<ToggleButtonGroup value={investor} exclusive onChange={handleInvestor} size="small">
				<ToggleButton value="galaxy">Galaxy</ToggleButton>
				<ToggleButton value="acorn">Acorn</ToggleButton>
			</ToggleButtonGroup>

			<FormControl fullWidth size="small">
				<InputLabel id="ver">Version</InputLabel>
				<Select labelId="ver" label="Version" value={inputs.version || activeVersion || ''} onChange={handleVersion}>
					{versions.map(v => <MenuItem key={v} value={v}>{v}</MenuItem>)}
				</Select>
			</FormControl>
			<TextField size="small" label="New Version ID" value={newVerId} onChange={e => setNewVerId(e.target.value)} />
			<TextField size="small" label="New Version JSON" multiline minRows={3} value={newVerJson} onChange={e => setNewVerJson(e.target.value)} />
			<Button variant="outlined" size="small" onClick={handleCreateVersion} disabled={!newVerId || !newVerJson}>Create + Activate</Button>

			<Divider />
			<Typography variant="subtitle1" fontWeight={700}>Key Assumptions</Typography>
			<TextField 
				size="small" 
				label="CAGR" 
				type="number" 
				value={inputs.cagr ?? ''} 
				onChange={e => setInputs({ ...inputs, cagr: e.target.value === '' ? undefined : Number(e.target.value) })} 
				helperText={termDefaults ? `Term default: ${termDefaults.default_cagr ?? 0}` : "e.g., 0.25 for 25%"} 
			/>
			<TextField 
				size="small" 
				label="Net Margin" 
				type="number" 
				value={inputs.margin ?? ''} 
				onChange={e => setInputs({ ...inputs, margin: e.target.value === '' ? undefined : Number(e.target.value) })} 
				helperText={termDefaults ? `Term default: ${termDefaults.default_margin}` : "e.g., 0.15 for 15%"} 
			/>
			<TextField 
				size="small" 
				label="Exit P/E (optional)" 
				type="number" 
				value={inputs.pe_multiple ?? ''} 
				onChange={e => setInputs({ ...inputs, pe_multiple: e.target.value === '' ? undefined : Number(e.target.value) })} 
				helperText={termDefaults ? `Term default: ${termDefaults.default_pe_multiple}` : ""} 
			/>
			<TextField 
				size="small" 
				label="Exit Horizon (yrs, optional)" 
				type="number" 
				value={inputs.exit_horizon_years ?? ''} 
				onChange={e => setInputs({ ...inputs, exit_horizon_years: e.target.value === '' ? undefined : Number(e.target.value) })} 
				helperText={termDefaults ? `Term default: ${termDefaults.default_exit_horizon_years} years` : ""} 
			/>
			<TextField 
				size="small" 
				label="Target IRR (optional)" 
				type="number" 
				value={inputs.target_irr ?? ''} 
				onChange={e => setInputs({ ...inputs, target_irr: e.target.value === '' ? undefined : Number(e.target.value) })} 
				helperText={termDefaults ? `Term default: ${termDefaults.target_irr}` : ""} 
			/>

			<Divider />
			<Typography variant="subtitle1" fontWeight={700}>Follow‑On Round</Typography>
			<TextField 
				size="small" 
				label="Follow‑On Amount ($)" 
				type="number" 
				value={inputs.follow_on_amount ?? ''} 
				onChange={e => setInputs({ ...inputs, follow_on_amount: e.target.value === '' ? undefined : Number(e.target.value) })} 
				helperText={termDefaults ? `Term default: $${(termDefaults.follow_on?.investment_amount || 0).toLocaleString()}` : ""} 
			/>
			<TextField 
				size="small" 
				label="Follow‑On Year Offset" 
				type="number" 
				value={inputs.follow_on_year ?? ''} 
				onChange={e => setInputs({ ...inputs, follow_on_year: e.target.value === '' ? undefined : Number(e.target.value) })} 
				helperText={termDefaults ? `Term default: Year ${termDefaults.follow_on?.year_offset}` : ""} 
			/>
			<TextField 
				size="small" 
				label="Series B Price Multiple" 
				type="number" 
				value={inputs.series_b_price_multiple} 
				onChange={e => setInputs({ ...inputs, series_b_price_multiple: Number(e.target.value) })} 
				helperText={termDefaults ? `Term default: ${termDefaults.follow_on?.series_b_price_multiple}x` : ""} 
			/>
			<TextField 
				size="small" 
				label="Pro‑Rata Participation (0‑1)" 
				type="number" 
				value={inputs.pro_rata_participation} 
				onChange={e => setInputs({ ...inputs, pro_rata_participation: Number(e.target.value) })} 
				helperText={termDefaults ? `Term default: ${termDefaults.follow_on?.pro_rata_participation}` : ""} 
			/>

			<Divider />
			<Typography variant="subtitle1" fontWeight={700}>Exit Scenario</Typography>
			<ToggleButtonGroup value={inputs.exit_scenario} exclusive onChange={(_, v) => setInputs({ ...inputs, exit_scenario: v })} size="small">
				<ToggleButton value="M&A">M&amp;A</ToggleButton>
				<ToggleButton value="IPO">IPO</ToggleButton>
			</ToggleButtonGroup>
		</Stack>
	)
}

