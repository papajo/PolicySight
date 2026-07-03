import React, { useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Button,
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
} from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import WarningIcon from "@mui/icons-material/Warning";
import api from "../services/api";

interface ParsedPolicy {
  liability_limit: string | null;
  medical_limit: string | null;
  property_limit: string | null;
  uninsured_motorist_limit: string | null;
  deductible: string | null;
  coverage_gaps: string[];
  plain_english_summary: string;
}

const formatApiError = (detail: unknown): string => {
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }

        if (item && typeof item === "object" && "msg" in item && typeof item.msg === "string") {
          return item.msg;
        }

        return JSON.stringify(item);
      })
      .join(" ");
  }

  if (detail && typeof detail === "object") {
    return JSON.stringify(detail);
  }

  return "Failed to decode policy. Please try again.";
};

const PolicyDecoder: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
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

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Policy Decoder
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Upload your Summary of Liability Insurance Policy (SLIP) and get a
        plain-English breakdown of your coverage.
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Box
          sx={{
            border: "2px dashed",
            borderColor: file ? "primary.main" : "grey.300",
            borderRadius: 2,
            p: 4,
            textAlign: "center",
            cursor: "pointer",
            "&:hover": { borderColor: "primary.main" },
          }}
          onClick={() => document.getElementById("slip-upload")?.click()}
        >
          <input
            id="slip-upload"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            hidden
            onChange={handleFileChange}
          />
          <CloudUploadIcon sx={{ fontSize: 48, color: "primary.main", mb: 1 }} />
          <Typography variant="h6">
            {file ? file.name : "Drop your SLIP document here or click to browse"}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Supports PDF, PNG, JPG
          </Typography>
        </Box>

        <Button
          variant="contained"
          size="large"
          fullWidth
          sx={{ mt: 2 }}
          onClick={handleUpload}
          disabled={!file || loading}
        >
          {loading ? <CircularProgress size={24} /> : "Decode My Policy"}
        </Button>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {result && (
        <Card>
          <CardContent>
            <Typography variant="h5" gutterBottom>
              Your Policy Breakdown
            </Typography>

            <Typography variant="body1" paragraph sx={{ fontStyle: "italic", color: "text.secondary" }}>
              {result.plain_english_summary}
            </Typography>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Coverage Limits
            </Typography>

            <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1, mb: 2 }}>
              <Chip label={`Liability: ${result.liability_limit ?? "Not found"}`} variant="outlined" color="primary" />
              <Chip label={`Medical: ${result.medical_limit ?? "Not found"}`} variant="outlined" color="primary" />
              <Chip label={`Property: ${result.property_limit ?? "Not found"}`} variant="outlined" color="primary" />
              <Chip label={`Uninsured Motorist: ${result.uninsured_motorist_limit ?? "Not found"}`} variant="outlined" color="primary" />
              <Chip label={`Deductible: ${result.deductible ?? "Not found"}`} variant="outlined" color="secondary" />
            </Box>

            {result.coverage_gaps.length > 0 && (
              <>
                <Divider sx={{ my: 2 }} />
                <Typography variant="h6" gutterBottom color="warning.dark">
                  Coverage Gaps Detected
                </Typography>
                <List dense>
                  {result.coverage_gaps.map((gap, i) => (
                    <ListItem key={i}>
                      <ListItemIcon>
                        <WarningIcon color="warning" />
                      </ListItemIcon>
                      <ListItemText primary={gap} />
                    </ListItem>
                  ))}
                </List>
              </>
            )}

            <Divider sx={{ my: 2 }} />
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <CheckCircleIcon color="success" />
              <Typography variant="body2" color="success.main">
                Analysis complete. Your policy has been decoded.
              </Typography>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default PolicyDecoder;
