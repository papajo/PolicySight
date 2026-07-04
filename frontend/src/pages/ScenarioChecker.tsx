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
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import { FeedbackButtons } from "./FeedbackLoop";
import api from "../services/api";

interface CoverageResult {
  coverage: string;
  covered: boolean;
  deductible: string | null;
  details: string;
}

interface ScenarioResult {
  scenario: string;
  summary: string;
  coverages: CoverageResult[];
  deductible: string | null;
  limitations: string[];
  is_covered: boolean;
  confidence: string;
  citations: string[];
}

const confColor = (c: string) =>
  c === "high" ? "success" : c === "medium" ? "warning" : "error";

const SUGGESTED_SCENARIOS = [
  "I hit a deer on the highway and damaged my front bumper.",
  "Someone rear-ended me at a stoplight. I have their info.",
  "A hailstorm damaged my roof and hood.",
  "My car was broken into and the stereo was stolen.",
  "I need a rental car while my car is in the shop.",
  "I caused an accident and the other driver is injured.",
];

interface Props {
  policyText?: string;
  standalone?: boolean;
}

const ScenarioChecker: React.FC<Props> = ({ policyText: propText, standalone }) => {
  const [policyText, setPolicyText] = useState(propText || "");
  const [scenario, setScenario] = useState("");
  const [result, setResult] = useState<ScenarioResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCheck = async () => {
    if (!policyText.trim() || !scenario.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.post("/policies/scenario", { text: policyText, scenario });
      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to check scenario.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      {standalone && (
        <>
          <Typography variant="h4" gutterBottom>Coverage Scenario Checker</Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            Describe what happened and we'll check which coverages from your policy apply.
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
            placeholder="Paste your policy declarations text here..."
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
          placeholder="Describe the incident..."
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

        <Button
          variant="contained"
          size="large"
          fullWidth
          onClick={handleCheck}
          disabled={!policyText.trim() || !scenario.trim() || loading}
        >
          {loading ? <CircularProgress size={24} /> : "Check Coverage"}
        </Button>
      </Paper>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {result && (
        <Box>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                {result.is_covered ? <CheckCircleIcon color="success" /> : <CancelIcon color="error" />}
                <Typography variant="h6">
                  {result.is_covered ? "Coverage May Apply" : "No Coverage Found"}
                </Typography>
                <Chip label={result.confidence} size="small" color={confColor(result.confidence) as any} />
              </Box>
              <Typography variant="body1" sx={{ fontStyle: "italic", color: "text.secondary" }}>
                {result.summary}
              </Typography>
              <FeedbackButtons action="scenario_check" details={result.summary} />
            </CardContent>
          </Card>

          {result.deductible && (
            <Alert severity="info" sx={{ mb: 2 }}>
              Applicable deductible: <strong>{result.deductible}</strong>
            </Alert>
          )}

          <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
            <Typography variant="subtitle1" fontWeight={600} gutterBottom>Coverage Breakdown</Typography>
            {result.coverages.map((c, i) => (
              <Box key={i} sx={{ display: "flex", alignItems: "flex-start", gap: 1.5, py: 1.5, borderBottom: i < result.coverages.length - 1 ? "1px solid #eee" : "none" }}>
                {c.covered ? (
                  <CheckCircleIcon color="success" fontSize="small" sx={{ mt: 0.3 }} />
                ) : (
                  <HelpOutlineIcon color="disabled" fontSize="small" sx={{ mt: 0.3 }} />
                )}
                <Box sx={{ flex: 1 }}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap" }}>
                    <Typography variant="body2" fontWeight={600}>{c.coverage}</Typography>
                    <Chip label={c.covered ? "Applies" : "Not detected"} size="small" color={c.covered ? "success" : "default"} variant="outlined" />
                    {c.deductible && <Chip label={`Deductible: ${c.deductible}`} size="small" variant="outlined" />}
                  </Box>
                  <Typography variant="caption" color="text.secondary">{c.details}</Typography>
                </Box>
              </Box>
            ))}
          </Paper>

          {result.limitations.length > 0 && (
            <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle2" color="warning.dark" gutterBottom>Limitations</Typography>
              {result.limitations.map((l, i) => (
                <Typography key={i} variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>{l}</Typography>
              ))}
            </Paper>
          )}

          {result.citations.length > 0 && (
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle2" gutterBottom>Sources</Typography>
              {result.citations.map((c, i) => (
                <Typography key={i} variant="caption" color="text.secondary" sx={{ display: "block", fontStyle: "italic" }}>
                  {c}
                </Typography>
              ))}
            </Paper>
          )}
        </Box>
      )}
    </Box>
  );
};

export default ScenarioChecker;
