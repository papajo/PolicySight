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
  Card,
  CardContent,
} from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CancelIcon from "@mui/icons-material/Cancel";
import WarningIcon from "@mui/icons-material/Warning";
import { FeedbackButtons } from "./FeedbackLoop";
import api from "../services/api";

interface CoverageDetermination {
  coverage_type: string;
  limit: string | null;
  deductible: string | null;
  estimated_payout: string | null;
  applies: boolean;
  confidence: string;
  reasoning: string;
  needs_review: boolean;
  escalation_reason: string | null;
}

interface ValidationItem {
  type: string;
  status: string;
  message: string;
}

interface CoverageDecision {
  claim_summary: string;
  determinations: CoverageDetermination[];
  total_estimated_payout: string | null;
  overall_confidence: string;
  escalation_level: string;
  escalation_reason: string | null;
  next_steps: string[];
  validations?: ValidationItem[];
}

const valSeverity = (s: string) =>
  s === "within_period" || s === "listed" ? "success"
    : s === "not_listed" || s === "before_period" || s === "after_period" ? "warning"
    : "info";

const confColor = (c: string) => c === "high" ? "success" : c === "medium" ? "warning" : "error";
const escColor = (e: string) => e === "auto_adjudicate" ? "success" : e === "supervisor_review" ? "warning" : "error";

const DecisionDraft: React.FC = () => {
  const [policyText, setPolicyText] = useState("");
  const [claimDesc, setClaimDesc] = useState("");
  const [accidentDate, setAccidentDate] = useState("");
  const [accidentVehicle, setAccidentVehicle] = useState("");
  const [result, setResult] = useState<CoverageDecision | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!policyText.trim() || !claimDesc.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.post("/policies/decision", {
        text: policyText,
        claim: claimDesc,
        accident_date: accidentDate || undefined,
        accident_vehicle: accidentVehicle || undefined,
      });
      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to generate decision.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Claim Coverage Decision Draft</Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Enter policy text and describe a claim to generate a structured coverage decision with confidence levels and escalation recommendations.
      </Typography>

      <Paper variant="outlined" sx={{ p: 3, mb: 2 }}>
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
        <TextField
          fullWidth
          multiline
          minRows={2}
          maxRows={4}
          label="Claim Description"
          placeholder="Describe what happened..."
          value={claimDesc}
          onChange={(e) => setClaimDesc(e.target.value)}
          sx={{ mb: 2 }}
        />
        <Box sx={{ display: "flex", gap: 2, mb: 2 }}>
          <TextField
            fullWidth
            size="small"
            label="Accident Date (optional)"
            placeholder="MM/DD/YYYY"
            value={accidentDate}
            onChange={(e) => setAccidentDate(e.target.value)}
          />
          <TextField
            fullWidth
            size="small"
            label="Accident Vehicle (optional)"
            placeholder="e.g. 2018 Ford F-150"
            value={accidentVehicle}
            onChange={(e) => setAccidentVehicle(e.target.value)}
          />
        </Box>
        <Button variant="contained" size="large" fullWidth onClick={handleGenerate} disabled={!policyText.trim() || !claimDesc.trim() || loading}>
          {loading ? <CircularProgress size={24} /> : "Generate Decision"}
        </Button>
      </Paper>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {result && (
        <Box>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1, flexWrap: "wrap" }}>
                <Typography variant="h6">Decision</Typography>
                <Chip label={`Escalation: ${result.escalation_level.replace("_", " ")}`} size="small" color={escColor(result.escalation_level) as any} />
                <Chip label={`Confidence: ${result.overall_confidence}`} size="small" color={confColor(result.overall_confidence) as any} />
              </Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>{result.claim_summary}</Typography>
              {result.total_estimated_payout && (
                <Typography variant="h5" color="primary.main" sx={{ mt: 1 }}>
                  Est. Payout: {result.total_estimated_payout}
                </Typography>
              )}
              <FeedbackButtons action="coverage_decision" details={result.claim_summary} />
            </CardContent>
          </Card>

          {result.escalation_reason && (
            <Alert severity={result.escalation_level === "auto_adjudicate" ? "info" : "warning"} sx={{ mb: 2 }}>
              {result.escalation_reason}
            </Alert>
          )}

          <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>Coverage Determinations</Typography>
            {result.determinations.map((d, i) => (
              <Box key={i} sx={{ py: 1.5, borderBottom: i < result.determinations.length - 1 ? "1px solid #eee" : "none" }}>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap", mb: 0.5 }}>
                  {d.applies ? <CheckCircleIcon color="success" fontSize="small" /> : d.needs_review ? <WarningIcon color="warning" fontSize="small" /> : <CancelIcon color="disabled" fontSize="small" />}
                  <Typography variant="body2" fontWeight={600}>{d.coverage_type}</Typography>
                  <Chip label={d.applies ? "Applies" : "N/A"} size="small" color={d.applies ? "success" : "default"} variant="outlined" />
                  <Chip label={d.confidence} size="small" color={confColor(d.confidence) as any} />
                  {d.needs_review && <Chip label="Needs Review" size="small" color="warning" />}
                </Box>
                <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
                  {d.reasoning}
                </Typography>
                <Box sx={{ display: "flex", gap: 2, mt: 0.3, flexWrap: "wrap" }}>
                  {d.limit && <Typography variant="caption" color="text.secondary">Limit: {d.limit}</Typography>}
                  {d.deductible && <Typography variant="caption" color="text.secondary">Deductible: {d.deductible}</Typography>}
                  {d.estimated_payout && <Typography variant="caption" color="primary.main" fontWeight={600}>Est. Payout: {d.estimated_payout}</Typography>}
                </Box>
                {d.escalation_reason && (
                  <Alert severity="warning" sx={{ mt: 0.5, py: 0, "& .MuiAlert-message": { fontSize: "0.75rem" } }}>
                    {d.escalation_reason}
                  </Alert>
                )}
              </Box>
            ))}
          </Paper>

          {result.validations && result.validations.length > 0 && (
            <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>Claim Validations</Typography>
              {result.validations.map((v, i) => (
                <Alert key={i} severity={valSeverity(v.status) as any} sx={{ mb: i < result.validations!.length - 1 ? 1 : 0 }}>
                  <Typography variant="body2" fontWeight={600}>{v.type.replace("_", " ")}</Typography>
                  <Typography variant="body2">{v.message}</Typography>
                </Alert>
              ))}
            </Paper>
          )}

          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>Next Steps</Typography>
            {result.next_steps.map((step, i) => (
              <Box key={i} sx={{ display: "flex", alignItems: "center", gap: 1, py: 0.5 }}>
                <Typography variant="body2">{i + 1}.</Typography>
                <Typography variant="body2">{step}</Typography>
              </Box>
            ))}
          </Paper>
        </Box>
      )}
    </Box>
  );
};

export default DecisionDraft;
