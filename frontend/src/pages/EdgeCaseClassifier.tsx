import React, { useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Button,
  TextField,
  CircularProgress,
  Alert,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import InfoIcon from "@mui/icons-material/Info";
import api from "../services/api";

interface EdgeCaseFlag {
  scenario_type: string;
  severity: string;
  detected: boolean;
  title: string;
  description: string;
  risk: string;
  recommendation: string;
  applies: boolean;
}

interface EdgeCaseResult {
  description: string;
  flags: EdgeCaseFlag[];
  primary_concern: string | null;
  requires_underwriting: boolean;
  requires_supervisor: boolean;
}

const severityColor = (s: string) =>
  s === "high" ? "error" : s === "medium" ? "warning" : "success";

const SUGGESTED_SCENARIOS = [
  "I was delivering food for DoorDash when I got into an accident.",
  "My friend borrowed my car and crashed it. I gave them permission.",
  "My cousin lives with me but isn't on my policy. He caused an accident.",
  "Someone hit my car in a parking lot and drove off.",
  "My car was totaled and I still owe $15,000 on the loan.",
  "I forgot to report an accident from two weeks ago.",
];

interface Props {
  policyText?: string;
  standalone?: boolean;
}

const EdgeCaseClassifier: React.FC<Props> = ({ policyText: propText, standalone }) => {
  const [policyText, setPolicyText] = useState(propText || "");
  const [scenario, setScenario] = useState("");
  const [result, setResult] = useState<EdgeCaseResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCheck = async () => {
    if (!policyText.trim() || !scenario.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.post("/policies/edge-cases", { text: policyText, scenario });
      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to analyze edge cases.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      {standalone && (
        <>
          <Typography variant="h4" gutterBottom>Edge Case Classifier</Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Analyzes messy real-world situations — rideshare, excluded drivers, borrowed vehicles, hit-and-run, late reporting, total loss, and more. Matches your scenario against known edge case patterns and flags risks.
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
        <TextField
          fullWidth
          multiline
          minRows={2}
          maxRows={4}
          label="What happened?"
          placeholder="Describe the situation in detail..."
          value={scenario}
          onChange={(e) => setScenario(e.target.value)}
          sx={{ mb: 2 }}
        />
        <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 2 }}>
          {SUGGESTED_SCENARIOS.map((s, i) => (
            <Chip
              key={i}
              label={s}
              size="small"
              variant="outlined"
              onClick={() => setScenario(s)}
              sx={{ cursor: "pointer", "&:hover": { borderColor: "primary.main" } }}
            />
          ))}
        </Box>
        <Button variant="contained" size="large" fullWidth onClick={handleCheck} disabled={!policyText.trim() || !scenario.trim() || loading}>
          {loading ? <CircularProgress size={24} /> : "Analyze Edge Cases"}
        </Button>
      </Paper>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {result && (
        <Box>
          {result.requires_supervisor && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              <strong>Supervisor review recommended.</strong> High-severity edge cases detected that may affect coverage.
            </Alert>
          )}
          {result.requires_underwriting && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              <strong>Underwriting attention may be needed.</strong> Some scenarios may require policy modification.
            </Alert>
          )}

          {result.flags.filter(f => f.applies).length === 0 && (
            <Alert severity="info" sx={{ mb: 2 }}>No specific edge cases matched. Standard coverage rules apply.</Alert>
          )}

          {result.flags.filter(f => f.applies).map((flag, i) => (
            <Accordion key={i} variant="outlined" sx={{ mb: 1, "&:before": { display: "none" }, borderLeft: 4, borderLeftColor: `${severityColor(flag.severity)}.main` }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1, width: "100%", pr: 2 }}>
                  {flag.severity === "high" ? <WarningAmberIcon color="error" /> : <InfoIcon color={severityColor(flag.severity) as any} />}
                  <Typography sx={{ fontWeight: 600, flexGrow: 1 }}>{flag.title}</Typography>
                  <Chip label={`Scenario #${nextScenarioRef(flag.scenario_type)}`} size="small" variant="outlined" sx={{ fontSize: "0.65rem" }} />
                  <Chip label={flag.severity} size="small" color={severityColor(flag.severity) as any} />
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="body2" sx={{ mb: 1 }}>{flag.description}</Typography>
                <Alert severity="error" sx={{ mb: 1, py: 0.5, "& .MuiAlert-message": { fontSize: "0.85rem" } }}>
                  <strong>Risk:</strong> {flag.risk}
                </Alert>
                <Alert severity="info" sx={{ py: 0.5, "& .MuiAlert-message": { fontSize: "0.85rem" } }}>
                  <strong>Recommendation:</strong> {flag.recommendation}
                </Alert>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      )}
    </Box>
  );
};

const nextScenarioRef = (type: string): number => {
  const refs: Record<string, number> = {
    commercial_delivery: 4, permissive_use: 3, excluded_driver: 9,
    unauthorized_use: 8, hit_and_run: 2, late_notice: 15,
    total_loss: 12, custom_equipment: 11, glass_claim: 14,
    medical_coverage: 13, rental_exposure: 10,
  };
  return refs[type] || 0;
};

export default EdgeCaseClassifier;
