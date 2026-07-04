import React, { useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Button,
  TextField,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Slider,
  FormControlLabel,
  Switch,
} from "@mui/material";
import api from "../services/api";

interface CostLineItem {
  category: string;
  estimated_cost: number;
  covered_by_insurance: number;
  out_of_pocket: number;
  detail: string;
}

interface CostEstimate {
  total_out_of_pocket: number;
  total_covered: number;
  deductible: number;
  line_items: CostLineItem[];
  breakdown_summary: string;
  recommendations: string[];
  max_exposure: number;
}

interface Props {
  policyText?: string;
  standalone?: boolean;
}

const CostEstimator: React.FC<Props> = ({ policyText: propText, standalone }) => {
  const [policyText, setPolicyText] = useState(propText || "");
  const [damageEstimate, setDamageEstimate] = useState(5000);
  const [hasInjuries, setHasInjuries] = useState(false);
  const [needsRentalDays, setNeedsRentalDays] = useState(14);
  const [result, setResult] = useState<CostEstimate | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleEstimate = async () => {
    if (!policyText.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.post("/policies/estimate-costs", {
        text: policyText,
        damage_estimate: damageEstimate,
        has_injuries: hasInjuries,
        needs_rental_days: needsRentalDays,
      });
      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to estimate costs.");
    } finally {
      setLoading(false);
    }
  };

  const fmt = (n: number) => `$${n.toLocaleString("en-US", { minimumFractionDigits: 0 })}`;

  return (
    <Box>
      {standalone && (
        <>
          <Typography variant="h4" gutterBottom>Out-of-Pocket Cost Estimator</Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Estimate what you'll pay out of pocket based on your policy limits, deductibles, and rental coverage. Adjust the sliders to match your situation.
          </Typography>
        </>
      )}

      <Paper variant="outlined" sx={{ p: 3, mb: 2 }}>
        {!propText && (
          <TextField
            fullWidth
            multiline
            minRows={3}
            maxRows={6}
            label="Policy Text"
            placeholder="Paste your policy declarations text..."
            value={policyText}
            onChange={(e) => setPolicyText(e.target.value)}
            sx={{ mb: 2 }}
          />
        )}

        <Typography variant="subtitle2" gutterBottom>Estimated repair/replacement cost: <strong>{fmt(damageEstimate)}</strong></Typography>
        <Slider
          value={damageEstimate}
          onChange={(_, v) => setDamageEstimate(v as number)}
          min={500}
          max={50000}
          step={500}
          valueLabelDisplay="auto"
          valueLabelFormat={(v) => fmt(v)}
          sx={{ mb: 2 }}
        />

        <Typography variant="subtitle2" gutterBottom>Rental car needed: <strong>{needsRentalDays} days</strong></Typography>
        <Slider
          value={needsRentalDays}
          onChange={(_, v) => setNeedsRentalDays(v as number)}
          min={0}
          max={30}
          step={1}
          valueLabelDisplay="auto"
          sx={{ mb: 2 }}
        />

        <FormControlLabel
          control={<Switch checked={hasInjuries} onChange={(e) => setHasInjuries(e.target.checked)} />}
          label="Injuries / medical expenses involved"
          sx={{ mb: 2, display: "block" }}
        />

        <Button variant="contained" size="large" fullWidth onClick={handleEstimate} disabled={!policyText.trim() || loading}>
          {loading ? <CircularProgress size={24} /> : "Estimate My Costs"}
        </Button>
      </Paper>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {result && (
        <Box>
          <Box sx={{ display: "flex", gap: 2, mb: 2, flexWrap: "wrap" }}>
            <Card variant="outlined" sx={{ flex: 1, minWidth: 150, borderColor: "error.main" }}>
              <CardContent>
                <Typography variant="subtitle2" color="error.main">Out-of-Pocket</Typography>
                <Typography variant="h5" color="error.main">{fmt(result.total_out_of_pocket)}</Typography>
              </CardContent>
            </Card>
            <Card variant="outlined" sx={{ flex: 1, minWidth: 150, borderColor: "success.main" }}>
              <CardContent>
                <Typography variant="subtitle2" color="success.main">Insurance Covers</Typography>
                <Typography variant="h5" color="success.main">{fmt(result.total_covered)}</Typography>
              </CardContent>
            </Card>
            <Card variant="outlined" sx={{ flex: 1, minWidth: 150, borderColor: "warning.main" }}>
              <CardContent>
                <Typography variant="subtitle2" color="warning.main">Max Exposure</Typography>
                <Typography variant="h5" color="warning.main">{fmt(result.max_exposure)}</Typography>
              </CardContent>
            </Card>
          </Box>

          <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
            <Typography variant="body1" sx={{ fontStyle: "italic", color: "text.secondary", mb: 1 }}>
              {result.breakdown_summary}
            </Typography>
            {result.deductible > 0 && (
              <Typography variant="body2" color="text.secondary">
                Deductible applies: <strong>{fmt(result.deductible)}</strong>
              </Typography>
            )}
          </Paper>

          <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>Cost Breakdown</Typography>
            {result.line_items.map((item, i) => (
              <Box key={i} sx={{ py: 1.5, borderBottom: i < result.line_items.length - 1 ? "1px solid #eee" : "none" }}>
                <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
                  <Typography variant="body2" fontWeight={600}>{item.category}</Typography>
                  <Typography variant="body2">{fmt(item.estimated_cost)}</Typography>
                </Box>
                <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
                  <Typography variant="caption" color="success.main">Covered: {fmt(item.covered_by_insurance)}</Typography>
                  <Typography variant="caption" color="error.main">OOP: {fmt(item.out_of_pocket)}</Typography>
                </Box>
                <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.3 }}>
                  {item.detail}
                </Typography>
              </Box>
            ))}
          </Paper>

          {result.recommendations.length > 0 && (
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>Recommendations</Typography>
              {result.recommendations.map((r, i) => (
                <Alert key={i} severity="info" sx={{ mb: 1, py: 0.5, "& .MuiAlert-message": { fontSize: "0.85rem" } }}>
                  {r}
                </Alert>
              ))}
            </Paper>
          )}
        </Box>
      )}
    </Box>
  );
};

export default CostEstimator;
