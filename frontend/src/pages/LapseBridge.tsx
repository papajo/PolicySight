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
  Divider,
  Chip,
} from "@mui/material";
import ShieldIcon from "@mui/icons-material/Shield";
import WarningIcon from "@mui/icons-material/Warning";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import api from "../services/api";

const LapseBridge: React.FC = () => {
  const userId = parseInt(localStorage.getItem("user_id") || "0", 10);
  const [carrier, setCarrier] = useState("");
  const [renewalDate, setRenewalDate] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRegister = async () => {
    if (!carrier) return;

    setLoading(true);
    setError(null);

    try {
      const response = await api.post("/lapse/register", null, {
        params: {
          user_id: userId,
          current_carrier: carrier,
          renewal_date: renewalDate || null,
        },
      });
      setStatus(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to register. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleCheckStatus = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.get(`/lapse/status/${userId}`, {
        params: {
          current_carrier: carrier || undefined,
          renewal_date: renewalDate || undefined,
        },
      });
      setStatus(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to check status.");
    } finally {
      setLoading(false);
    }
  };

  const coverageStatus = status?.coverage_status;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Lapse Bridge
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Never let your coverage lapse. We monitor your renewal window and
        automatically bridge the gap if needed.
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
          <ShieldIcon sx={{ fontSize: 40, color: "error.main" }} />
          <Typography variant="h6">Register for Bridge Protection</Typography>
        </Box>

        <TextField
          fullWidth
          label="Current Carrier"
          value={carrier}
          onChange={(e) => setCarrier(e.target.value)}
          sx={{ mb: 2 }}
        />
        <TextField
          fullWidth
          label="Renewal Date (optional)"
          type="date"
          value={renewalDate}
          onChange={(e) => setRenewalDate(e.target.value)}
          InputLabelProps={{ shrink: true }}
          sx={{ mb: 2 }}
        />

        <Box sx={{ display: "flex", gap: 2 }}>
          <Button
            variant="contained"
            size="large"
            onClick={handleRegister}
            disabled={!carrier || loading}
          >
            {loading ? <CircularProgress size={24} /> : "Register Bridge"}
          </Button>
          <Button
            variant="outlined"
            size="large"
            onClick={handleCheckStatus}
            disabled={loading}
          >
            Check Status
          </Button>
        </Box>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {status && (
        <Card>
          <CardContent>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
              {coverageStatus?.is_covered ? (
                <CheckCircleIcon sx={{ color: "success.main", fontSize: 32 }} />
              ) : (
                <WarningIcon sx={{ color: "error.main", fontSize: 32 }} />
              )}
              <Typography variant="h5">
                {coverageStatus?.is_covered ? "Covered" : "Lapse Detected"}
              </Typography>
              <Chip
                label={status.bridge_needed ? "Bridge Needed" : "Protected"}
                color={status.bridge_needed ? "warning" : "success"}
                size="small"
              />
            </Box>

            <Divider sx={{ my: 2 }} />

            <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}>
              <Paper variant="outlined" sx={{ p: 2, textAlign: "center" }}>
                <Typography variant="body2" color="text.secondary">
                  Days Until Lapse
                </Typography>
                <Typography variant="h5" color={coverageStatus?.days_until_lapse <= 7 ? "error" : "text.primary"}>
                  {coverageStatus?.days_until_lapse ?? "N/A"}
                </Typography>
              </Paper>
              <Paper variant="outlined" sx={{ p: 2, textAlign: "center" }}>
                <Typography variant="body2" color="text.secondary">
                  Bridge Active
                </Typography>
                <Typography variant="h5" color={coverageStatus?.bridge_active ? "success.main" : "text.secondary"}>
                  {coverageStatus?.bridge_active ? "Yes" : "No"}
                </Typography>
              </Paper>
            </Box>

            {status.bridge_product && (
              <Box sx={{ mt: 2, p: 2, bgcolor: "action.hover", borderRadius: 1 }}>
                <Typography variant="subtitle1" gutterBottom fontWeight={700}>
                  Recommended Bridge Product
                </Typography>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                  <Chip label={status.bridge_product.product_type.replace("_", " ").toUpperCase()} color="primary" size="small" />
                  <Typography variant="h6">{status.bridge_product.name}</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  {status.bridge_product.description}
                </Typography>
                <Divider sx={{ my: 1 }} />
                <Box sx={{ display: "flex", gap: 3, alignItems: "baseline" }}>
                  <Box>
                    <Typography variant="h4" color="error.main">
                      ${status.bridge_product.total_cost.toFixed(2)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {status.bridge_product.term_days} days at ${status.bridge_product.daily_rate.toFixed(2)}/day
                    </Typography>
                  </Box>
                </Box>
                <Paper variant="outlined" sx={{ p: 1.5, mt: 1, bgcolor: "background.default" }}>
                  <Typography variant="caption" color="text.secondary">
                    {status.bridge_product.selection_rationale}
                  </Typography>
                </Paper>
              </Box>
            )}

            {status.alert && (
              <Alert
                severity={coverageStatus?.is_covered ? "info" : "error"}
                sx={{ mt: 2 }}
              >
                <Typography
                  variant="body2"
                  sx={{ whiteSpace: "pre-wrap" }}
                  dangerouslySetInnerHTML={{
                    __html: status.alert.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>"),
                  }}
                />
              </Alert>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default LapseBridge;
