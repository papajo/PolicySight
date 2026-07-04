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
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import QuestionAnswerIcon from "@mui/icons-material/QuestionAnswer";
import SafeFailurePanel from "../components/SafeFailurePanel";
import api from "../services/api";

interface CoverageExplanation {
  coverage_type: string;
  limit: string | null;
  what_is_covered: string;
  what_is_not_covered: string;
  what_needs_review: string;
  confidence: string;
  source_text: string | null;
  citation: string | null;
}

interface CoverageExplanationSet {
  explanations: CoverageExplanation[];
  overall_confidence: string;
  safe_failure_assessment: string;
  safe_failure_required_info: any[];
  safe_failure_next_actions: any[];
}

interface EvidenceAnswer {
  question: string;
  answer: string;
  citations: string[];
  confidence: string;
  is_assumption: boolean;
  missing_info: string[];
}

const confColor = (c: string) =>
  c === "high" ? "success" : c === "medium" ? "warning" : "error";

interface Props {
  policyText: string;
}

const CoverageExplainerPanel: React.FC<Props> = ({ policyText }) => {
  const [explanations, setExplanations] = useState<CoverageExplanationSet | null>(null);
  const [explainLoading, setExplainLoading] = useState(false);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<EvidenceAnswer | null>(null);
  const [askLoading, setAskLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExplain = async () => {
    setExplainLoading(true);
    setError(null);
    try {
      const res = await api.post("/policies/explain", { text: policyText });
      setExplanations(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to generate explanations.");
    } finally {
      setExplainLoading(false);
    }
  };

  const handleAsk = async () => {
    if (!question.trim()) return;
    setAskLoading(true);
    setError(null);
    try {
      const res = await api.post("/policies/ask", { text: policyText, question });
      setAnswer(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to answer question.");
    } finally {
      setAskLoading(false);
    }
  };

  return (
    <Box>
      <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", mb: 3 }}>
        <Button
          variant="contained"
          startIcon={explainLoading ? <CircularProgress size={18} /> : <AutoAwesomeIcon />}
          onClick={handleExplain}
          disabled={explainLoading}
        >
          Explain My Coverage
        </Button>

        <Box sx={{ display: "flex", gap: 1, flexGrow: 1, maxWidth: 500 }}>
          <TextField
            fullWidth
            size="small"
            placeholder="Ask a question about your policy..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAsk()}
          />
          <Button
            variant="outlined"
            startIcon={askLoading ? <CircularProgress size={18} /> : <QuestionAnswerIcon />}
            onClick={handleAsk}
            disabled={askLoading || !question.trim()}
          >
            Ask
          </Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {answer && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Q: {answer.question}
          </Typography>
          <Typography variant="body1" gutterBottom>{answer.answer}</Typography>
          <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mt: 1 }}>
            <Chip label={answer.confidence} size="small" color={confColor(answer.confidence) as any} />
            {answer.is_assumption && <Chip label="Assumption" size="small" color="warning" variant="outlined" />}
          </Box>
          {answer.citations.length > 0 && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Sources:</Typography>
              {answer.citations.map((c, i) => (
                <Typography key={i} variant="caption" color="text.secondary" sx={{ display: "block", fontStyle: "italic" }}>
                  {c}
                </Typography>
              ))}
            </Box>
          )}
          {answer.missing_info.length > 0 && (
            <Box sx={{ mt: 1 }}>
              <Typography variant="caption" color="warning.dark" sx={{ fontWeight: 600 }}>Not found in policy:</Typography>
              {answer.missing_info.map((m, i) => (
                <Typography key={i} variant="caption" color="warning.dark" sx={{ display: "block" }}>
                  {m}
                </Typography>
              ))}
            </Box>
          )}
        </Paper>
      )}

      {explanations && (
        <Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
            <Typography variant="h6">Coverage-by-Coverage Explanation</Typography>
            <Chip label={`Overall confidence: ${explanations.overall_confidence}`} size="small" color={confColor(explanations.overall_confidence) as any} />
          </Box>

          <SafeFailurePanel
            overall_status={explanations.safe_failure_assessment ? "partial" : "determinate"}
            assessment={explanations.safe_failure_assessment}
            required_info={explanations.safe_failure_required_info}
            next_actions={explanations.safe_failure_next_actions}
          />

          {explanations.explanations.map((exp, i) => (
            <Accordion key={i} variant="outlined" sx={{ mb: 1, "&:before": { display: "none" } }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1, width: "100%", pr: 2 }}>
                  <Typography sx={{ fontWeight: 600, flexGrow: 1 }}>{exp.coverage_type}</Typography>
                  <Chip label={exp.limit || "Not found"} size="small" color={exp.limit ? "primary" : "error"} variant="outlined" />
                  <Chip label={exp.confidence} size="small" color={confColor(exp.confidence) as any} />
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>What's covered:</strong> {exp.what_is_covered}
                </Typography>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  <strong>What's not covered:</strong> {exp.what_is_not_covered}
                </Typography>
                {exp.what_needs_review && (
                  <Typography variant="body2" color="warning.dark" sx={{ mb: 1 }}>
                    <strong>Review needed:</strong> {exp.what_needs_review}
                  </Typography>
                )}
                {exp.citation && (
                  <Typography variant="caption" color="text.secondary" sx={{ display: "block", fontStyle: "italic", mt: 1 }}>
                    Source: "{exp.citation}"
                  </Typography>
                )}
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      )}
    </Box>
  );
};

export default CoverageExplainerPanel;
