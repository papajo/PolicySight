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
} from "@mui/material";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import api from "../services/api";

interface ForecastResult {
  current_rate: number;
  forecasted_rate: number;
  peer_average: number;
  recommendation: string;
  savings_amount: number;
  confidence: number;
}

const Trajectory: React.FC = () => {
  const [currentRate, setCurrentRate] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ForecastResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const userId = parseInt(localStorage.getItem("user_id") || "0", 10);

  const handleForecast = async () => {
    if (!currentRate) return;

    setLoading(true);
    setError(null);

    try {
      const response = await api.get("/rates/forecast", {
        params: {
          user_id: userId,
          current_rate: parseFloat(currentRate),
        },
      });
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to generate forecast. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Rate Trajectory
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        See what your insurance premium will be next year and compare against
        market averages.
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
          <TrendingUpIcon sx={{ fontSize: 40, color: "primary.main" }} />
          <Typography variant="h6">Enter your current monthly premium</Typography>
        </Box>

        <TextField
          fullWidth
          label="Current monthly premium ($)"
          type="number"
          value={currentRate}
          onChange={(e) => setCurrentRate(e.target.value)}
          sx={{ mb: 2 }}
        />

        <Button
          variant="contained"
          size="large"
          fullWidth
          onClick={handleForecast}
          disabled={!currentRate || loading}
        >
          {loading ? <CircularProgress size={24} /> : "Forecast My Rate"}
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
              Rate Forecast
            </Typography>

            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr 1fr",
                gap: 2,
                mb: 3,
              }}
            >
              <Paper variant="outlined" sx={{ p: 2, textAlign: "center" }}>
                <Typography variant="body2" color="text.secondary">
                  Current Rate
                </Typography>
                <Typography variant="h5" color="primary">
                  ${result.current_rate.toFixed(2)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  per month
                </Typography>
              </Paper>

              <Paper variant="outlined" sx={{ p: 2, textAlign: "center" }}>
                <Typography variant="body2" color="text.secondary">
                  Forecasted Rate
                </Typography>
                <Typography variant="h5" color="error">
                  ${result.forecasted_rate.toFixed(2)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  per month (next year)
                </Typography>
              </Paper>

              <Paper variant="outlined" sx={{ p: 2, textAlign: "center" }}>
                <Typography variant="body2" color="text.secondary">
                  Peer Average
                </Typography>
                <Typography variant="h5" color="success.main">
                  ${result.peer_average.toFixed(2)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  per month (market)
                </Typography>
              </Paper>
            </Box>

            <Divider sx={{ my: 2 }} />

            <Box sx={{ textAlign: "center" }}>
              <Typography variant="h6" gutterBottom>
                Recommendation:{" "}
                <Typography
                  component="span"
                  color={result.recommendation === "Switch" ? "success.main" : "warning.main"}
                  variant="h6"
                >
                  {result.recommendation}
                </Typography>
              </Typography>

              {result.recommendation === "Switch" && (
                <Alert severity="success" sx={{ mt: 1 }}>
                  You could save ${result.savings_amount.toFixed(2)}/month by switching carriers.
                </Alert>
              )}

              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Confidence: {(result.confidence * 100).toFixed(0)}%
              </Typography>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default Trajectory;