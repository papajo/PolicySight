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
  Chip,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Tabs,
  Tab,
  Tooltip,
} from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import WarningIcon from "@mui/icons-material/Warning";
import ErrorIcon from "@mui/icons-material/Error";
import CoverageExplainerPanel from "./CoverageExplainerPanel";
import ScenarioChecker from "./ScenarioChecker";
import api from "../services/api";

interface CoverageGap {
  field: string;
  detail: string;
  why_it_matters: string;
  potential_consequence: string;
}

interface ParsedPolicy {
  liability_limit: string | null;
  liability_source: string | null;
  liability_confidence: string;
  medical_limit: string | null;
  medical_source: string | null;
  medical_confidence: string;
  property_limit: string | null;
  property_source: string | null;
  property_confidence: string;
  uninsured_motorist_limit: string | null;
  uninsured_motorist_source: string | null;
  uninsured_motorist_confidence: string;
  collision_deductible: string | null;
  collision_deductible_source: string | null;
  comprehensive_deductible: string | null;
  comprehensive_deductible_source: string | null;
  rental_reimbursement: string | null;
  rental_reimbursement_source: string | null;
  roadside_assistance: string | null;
  roadside_assistance_source: string | null;
  loan_lease_payoff: string | null;
  loan_lease_payoff_source: string | null;
  policy_number: string | null;
  named_insured: string | null;
  effective_date: string | null;
  expiration_date: string | null;
  exclusions: string[];
  endorsements: string[];
  coverage_gaps: CoverageGap[];
  missing_fields: string[];
  unclear_fields: string[];
  plain_english_summary: string;
  raw_text: string;
}

const formatApiError = (detail: unknown): string => {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((i) => (typeof i === "string" ? i : i?.msg || JSON.stringify(i))).join(" ");
  if (detail && typeof detail === "object") return JSON.stringify(detail);
  return "Failed to decode policy. Please try again.";
};

const confColor = (c: string) => c === "high" ? "success" : c === "medium" ? "warning" : c === "low" ? "error" : "default";

const PolicyDecoder: React.FC = () => {
  const [tab, setTab] = useState(0);
  const [file, setFile] = useState<File | null>(null);
  const [pastedText, setPastedText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ParsedPolicy | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await api.post("/policies/decode", formData);
      setResult(response.data);
    } catch (err: any) {
      setError(formatApiError(err.response?.data?.detail));
    } finally {
      setLoading(false);
    }
  };

  const handlePasteDecode = async () => {
    if (!pastedText.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const response = await api.post("/policies/decode-text", { text: pastedText });
      setResult(response.data);
    } catch (err: any) {
      setError(formatApiError(err.response?.data?.detail));
    } finally {
      setLoading(false);
    }
  };

  const CoverageRow = ({ label, value, source, confidence }: { label: string; value: string | null; source?: string | null; confidence?: string }) => (
    <Box sx={{ mb: 1.5 }}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap" }}>
        <Typography variant="body2" fontWeight={600}>{label}:</Typography>
        {value ? (
          <>
            <Chip label={value} size="small" color="primary" variant="outlined" />
            {confidence && <Chip label={confidence} size="small" color={confColor(confidence) as any} variant="filled" />}
          </>
        ) : (
          <Chip label="Not found" size="small" color="error" variant="outlined" />
        )}
      </Box>
      {source && (
        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.3, fontStyle: "italic", wordBreak: "break-word" }}>
          Source: "{source.slice(0, 200)}"
        </Typography>
      )}
    </Box>
  );

  const SectionCard = ({ title, children }: { title: string; children: React.ReactNode }) => (
    <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
      <Typography variant="subtitle1" fontWeight={600} gutterBottom>{title}</Typography>
      {children}
    </Paper>
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Policy Coverage Parser</Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Upload a declarations page or paste your policy text for a structured breakdown of limits, exclusions, and gaps — with source citations for every field.
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Tabs value={tab} onChange={(_, v) => { setTab(v); setResult(null); setError(null); }} centered sx={{ mb: 2 }}>
          <Tab label="Upload File" />
          <Tab label="Paste Text" />
        </Tabs>

        {tab === 0 && (
          <>
            <Box
              sx={{ border: "2px dashed", borderColor: file ? "primary.main" : "grey.300", borderRadius: 2, p: 4, textAlign: "center", cursor: "pointer", "&:hover": { borderColor: "primary.main" } }}
              onClick={() => document.getElementById("slip-upload")?.click()}
            >
              <input id="slip-upload" type="file" accept=".pdf,.png,.jpg,.jpeg" hidden onChange={handleFileChange} />
              <CloudUploadIcon sx={{ fontSize: 48, color: "primary.main", mb: 1 }} />
              <Typography variant="h6">{file ? file.name : "Drop your SLIP document here or click to browse"}</Typography>
              <Typography variant="body2" color="text.secondary">Supports PDF, PNG, JPG</Typography>
            </Box>
            <Button variant="contained" size="large" fullWidth sx={{ mt: 2 }} onClick={handleUpload} disabled={!file || loading}>
              {loading ? <CircularProgress size={24} /> : "Decode My Policy"}
            </Button>
          </>
        )}

        {tab === 1 && (
          <>
            <TextField fullWidth multiline minRows={6} maxRows={12} placeholder="Paste your insurance policy declarations page text here..." value={pastedText} onChange={(e) => setPastedText(e.target.value)} sx={{ mb: 2 }} />
            <Button variant="contained" size="large" fullWidth onClick={handlePasteDecode} disabled={!pastedText.trim() || loading}>
              {loading ? <CircularProgress size={24} /> : "Analyze Policy Text"}
            </Button>
          </>
        )}
      </Paper>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {result && (
        <Box>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                <CheckCircleIcon color="success" />
                <Typography variant="h5">Policy Analysis Complete</Typography>
              </Box>
              <Typography variant="body1" paragraph sx={{ fontStyle: "italic", color: "text.secondary" }}>
                {result.plain_english_summary}
              </Typography>

              {result.policy_number && <Typography variant="caption" color="text.secondary">Policy #{result.policy_number}</Typography>}
              {(result.effective_date || result.expiration_date) && (
                <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
                  Period: {result.effective_date || "?"} → {result.expiration_date || "?"}
                </Typography>
              )}
            </CardContent>
          </Card>

          <SectionCard title="Coverage Limits">
            <CoverageRow label="Liability" value={result.liability_limit} source={result.liability_source} confidence={result.liability_confidence} />
            <CoverageRow label="Medical Payments" value={result.medical_limit} source={result.medical_source} confidence={result.medical_confidence} />
            <CoverageRow label="Property Damage" value={result.property_limit} source={result.property_source} confidence={result.property_confidence} />
            <CoverageRow label="UM/UIM" value={result.uninsured_motorist_limit} source={result.uninsured_motorist_source} confidence={result.uninsured_motorist_confidence} />
            <CoverageRow label="Collision Deductible" value={result.collision_deductible} source={result.collision_deductible_source} />
            <CoverageRow label="Comprehensive Deductible" value={result.comprehensive_deductible} source={result.comprehensive_deductible_source} />
            <CoverageRow label="Rental Reimbursement" value={result.rental_reimbursement} source={result.rental_reimbursement_source} />
            <CoverageRow label="Roadside Assistance" value={result.roadside_assistance} source={result.roadside_assistance_source} />
            <CoverageRow label="Loan/Lease Payoff" value={result.loan_lease_payoff} source={result.loan_lease_payoff_source} />
          </SectionCard>

          {(result.missing_fields.length > 0 || result.unclear_fields.length > 0) && (
            <SectionCard title="Missing & Unclear Fields">
              {result.missing_fields.map((f, i) => (
                <Box key={i} sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
                  <ErrorIcon color="error" fontSize="small" />
                  <Typography variant="body2">{f}</Typography>
                </Box>
              ))}
              {result.unclear_fields.map((f, i) => (
                <Box key={i} sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
                  <WarningIcon color="warning" fontSize="small" />
                  <Typography variant="body2">{f}</Typography>
                </Box>
              ))}
            </SectionCard>
          )}

          {result.coverage_gaps.length > 0 && (
            <SectionCard title="Coverage Gaps">
              {result.coverage_gaps.map((gap, i) => (
                <Card key={i} variant="outlined" sx={{ mb: 1.5, p: 1.5 }}>
                  <Typography variant="subtitle2" color="error.main" gutterBottom>{gap.field.replace("_", " ")}</Typography>
                  <Typography variant="body2" gutterBottom>{gap.detail}</Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
                    <strong>Why it matters:</strong> {gap.why_it_matters}
                  </Typography>
                  <Typography variant="caption" color="warning.dark" sx={{ display: "block" }}>
                    <strong>Risk:</strong> {gap.potential_consequence}
                  </Typography>
                </Card>
              ))}
            </SectionCard>
          )}

          {(result.exclusions.length > 0 || result.endorsements.length > 0) && (
            <SectionCard title="Exclusions & Endorsements">
              {result.exclusions.map((e, i) => (
                <Typography key={i} variant="body2" color="error.main" sx={{ mb: 0.5 }}>🚫 {e}</Typography>
              ))}
              {result.endorsements.map((e, i) => (
                <Typography key={i} variant="body2" color="info.main" sx={{ mb: 0.5 }}>📝 {e}</Typography>
              ))}
            </SectionCard>
          )}

          <Divider sx={{ my: 3 }} />
          <Typography variant="h6" gutterBottom>Coverage Analysis</Typography>
          <CoverageExplainerPanel policyText={result.raw_text} />

          <Divider sx={{ my: 3 }} />
          <Typography variant="h6" gutterBottom>Check a Scenario</Typography>
          <ScenarioChecker policyText={result.raw_text} />

          {result.raw_text && (
            <SectionCard title="Source Text">
              <Typography variant="caption" color="text.secondary" sx={{ whiteSpace: "pre-wrap", wordBreak: "break-word", fontSize: "0.7rem" }}>
                {result.raw_text.slice(0, 3000)}
                {result.raw_text.length > 3000 && "\n...[truncated]"}
              </Typography>
            </SectionCard>
          )}
        </Box>
      )}
    </Box>
  );
};

export default PolicyDecoder;
