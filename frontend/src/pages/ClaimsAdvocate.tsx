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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider,
} from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import api from "../services/api";

interface ClaimValuation {
  total_claim_amount: number;
  carrier_offer: number;
  estimated_payout: number;
  sub_limit_breakdown: Record<string, number>;
  verdict: string;
  confidence_score: number;
}

const ClaimsAdvocate: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [description, setDescription] = useState("");
  const [carrierOffer, setCarrierOffer] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ClaimValuation | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const handleSubmit = async () => {
    if (!file || !description) return;

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("description", description);
      formData.append("carrier_offer", carrierOffer || "0");
      const response = await api.post("/claims/advocate", formData);
      setResult(response.data);
    } catch (err: any) {
      setError(err.message || (typeof err.response?.data?.detail === 'string' ? err.response.data.detail : 'An unexpected error occurred'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Claims Advocate
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Upload accident photos and describe the incident. We'll compare your
        policy limits against the carrier's offer.
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
            mb: 2,
            "&:hover": { borderColor: "primary.main" },
          }}
          onClick={() => document.getElementById("claim-upload")?.click()}
        >
          <input
            id="claim-upload"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg"
            hidden
            onChange={handleFileChange}
          />
          <CloudUploadIcon sx={{ fontSize: 48, color: "primary.main", mb: 1 }} />
          <Typography variant="h6">
            {file ? file.name : "Upload accident photo or police report"}
          </Typography>
        </Box>

        <TextField
          fullWidth
          multiline
          rows={4}
          label="Describe the accident"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          sx={{ mb: 2 }}
        />

        <TextField
          fullWidth
          label="Carrier's offer amount ($)"
          type="number"
          value={carrierOffer}
          onChange={(e) => setCarrierOffer(e.target.value)}
          sx={{ mb: 2 }}
        />

        <Button
          variant="contained"
          size="large"
          fullWidth
          onClick={handleSubmit}
          disabled={!file || !description || loading}
        >
          {loading ? <CircularProgress size={24} /> : "Analyze My Claim"}
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
              Claim Valuation Report
            </Typography>

            <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Category</TableCell>
                    <TableCell align="right">Amount</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  <TableRow>
                    <TableCell>Total Claim Amount</TableCell>
                    <TableCell align="right">
                      ${result.total_claim_amount.toLocaleString()}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>Carrier Offer</TableCell>
                    <TableCell align="right" sx={{ color: "error.main" }}>
                      ${result.carrier_offer.toLocaleString()}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell sx={{ fontWeight: "bold" }}>
                      Estimated Payout
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: "bold", color: "success.main" }}>
                      ${result.estimated_payout.toLocaleString()}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </TableContainer>

            <Typography variant="h6" gutterBottom>
              Sub-Limit Breakdown
            </Typography>
            <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Coverage Type</TableCell>
                    <TableCell align="right">Limit</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.entries(result.sub_limit_breakdown).map(([key, value]) => (
                    <TableRow key={key}>
                      <TableCell>{key}</TableCell>
                      <TableCell align="right">${value.toLocaleString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Verdict
            </Typography>
            <Alert severity={result.estimated_payout > result.carrier_offer ? "warning" : "success"}>
              {result.verdict}
            </Alert>

            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Confidence Score: {(result.confidence_score * 100).toFixed(0)}%
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default ClaimsAdvocate;