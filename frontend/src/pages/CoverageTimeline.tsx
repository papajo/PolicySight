import React, { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Alert,
  Chip,
  CircularProgress,
  Card,
  CardContent,
} from "@mui/material";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import api from "../services/api";

interface PolicyPeriod {
  policy_number: string;
  carrier: string;
  effective_date: string;
  expiration_date: string | null;
  coverage_types: string[];
  status: string;
}

interface CoverageEvent {
  date: string;
  event_type: string;
  label: string;
  policy_number?: string;
}

interface TimelineResult {
  periods: PolicyPeriod[];
  events: CoverageEvent[];
  gaps: { from: string; to: string; days: number; severity: string }[];
  has_active_coverage: boolean;
  days_until_lapse: number | null;
}

const formatDate = (d: string) => {
  const [y, m, day] = d.split("-");
  return `${m}/${day}/${y}`;
};

const severityColor = (s: string) =>
  s === "high" ? "error" : s === "medium" ? "warning" : "success";

const CoverageTimeline: React.FC = () => {
  const [data, setData] = useState<TimelineResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/timeline").then((res) => {
      setData(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <Box sx={{ textAlign: "center", py: 4 }}><CircularProgress /></Box>;

  if (!data) return <Alert severity="info">No timeline data available.</Alert>;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Coverage Timeline</Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Track your coverage periods, spot gaps, and see when your next lapse could occur.
      </Typography>

      <Box sx={{ display: "flex", gap: 2, mb: 3, flexWrap: "wrap" }}>
        <Card variant="outlined" sx={{ flex: 1, minWidth: 180 }}>
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary">Status</Typography>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              {data.has_active_coverage ? (
                <><CheckCircleIcon color="success" /><Typography variant="h6">Active</Typography></>
              ) : (
                <><ErrorIcon color="error" /><Typography variant="h6">No Active Coverage</Typography></>
              )}
            </Box>
          </CardContent>
        </Card>
        {data.days_until_lapse !== null && (
          <Card variant="outlined" sx={{ flex: 1, minWidth: 180 }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary">Days Until Lapse</Typography>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 0.5 }}>
                <WarningAmberIcon color={data.days_until_lapse < 30 ? "warning" : "success"} />
                <Typography variant="h6">{data.days_until_lapse} days</Typography>
              </Box>
            </CardContent>
          </Card>
        )}
        <Card variant="outlined" sx={{ flex: 1, minWidth: 180 }}>
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary">Policies</Typography>
            <Typography variant="h6">{data.periods.length}</Typography>
          </CardContent>
        </Card>
        <Card variant="outlined" sx={{ flex: 1, minWidth: 180 }}>
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary">Gaps Detected</Typography>
            <Typography variant="h6" color={data.gaps.length > 0 ? "error.main" : "success.main"}>
              {data.gaps.length}
            </Typography>
          </CardContent>
        </Card>
      </Box>

      <Paper variant="outlined" sx={{ p: 3, mb: 3 }}>
        <Box sx={{ position: "relative", py: 2 }}>
          {data.events.map((event, i) => {
            const colorMap: Record<string, string> = {
              start: "#4caf50",
              end: "#f44336",
              gap_start: "#ff9800",
              gap_end: "#ff9800",
            };
            return (
              <Box key={i} sx={{ display: "flex", alignItems: "flex-start", mb: 2, position: "relative" }}>
                <Box
                  sx={{
                    width: 14,
                    height: 14,
                    borderRadius: "50%",
                    bgcolor: colorMap[event.event_type] || "#999",
                    flexShrink: 0,
                    mt: 0.5,
                    mr: 2,
                    zIndex: 1,
                    border: "2px solid white",
                    boxShadow: "0 0 0 1px #e0e0e0",
                  }}
                />
                <Box sx={{ flex: 1 }}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap" }}>
                    <Typography variant="body2" color="text.secondary" sx={{ fontFamily: "monospace" }}>
                      {formatDate(event.date)}
                    </Typography>
                    <Chip
                      label={event.event_type.replace("_", " ")}
                      size="small"
                      color={colorMap[event.event_type] === "#4caf50" ? "success" : colorMap[event.event_type] === "#f44336" ? "error" : "warning"}
                      variant="outlined"
                    />
                  </Box>
                  <Typography variant="body2" sx={{ mt: 0.3 }}>{event.label}</Typography>
                </Box>
              </Box>
            );
          })}
        </Box>
      </Paper>

      {data.gaps.length > 0 && (
        <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>Coverage Gaps</Typography>
          {data.gaps.map((gap, i) => (
            <Card key={i} variant="outlined" sx={{ mb: 1.5, p: 1.5, borderColor: gap.severity === "high" ? "error.main" : "warning.main" }}>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <Box>
                  <Typography variant="body2">
                    {formatDate(gap.from)} → {formatDate(gap.to)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {gap.days} day{gap.days !== 1 ? "s" : ""} without coverage
                  </Typography>
                </Box>
                <Chip label={gap.severity} size="small" color={severityColor(gap.severity) as any} />
              </Box>
            </Card>
          ))}
        </Paper>
      )}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>Policy History</Typography>
        {data.periods.map((p, i) => (
          <Box key={i} sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", py: 1, borderBottom: i < data.periods.length - 1 ? "1px solid #eee" : "none" }}>
            <Box>
              <Typography variant="body2" fontWeight={600}>{p.carrier} — {p.policy_number}</Typography>
              <Typography variant="caption" color="text.secondary">
                {formatDate(p.effective_date)} → {p.expiration_date ? formatDate(p.expiration_date) : "Ongoing"}
              </Typography>
              <Box sx={{ display: "flex", gap: 0.5, mt: 0.5, flexWrap: "wrap" }}>
                {p.coverage_types.map((ct, j) => (
                  <Chip key={j} label={ct} size="small" variant="outlined" sx={{ fontSize: "0.65rem" }} />
                ))}
              </Box>
            </Box>
            <Chip
              label={p.status}
              size="small"
              color={p.status === "active" ? "success" : p.status === "expired" ? "default" : "info"}
            />
          </Box>
        ))}
      </Paper>
    </Box>
  );
};

export default CoverageTimeline;
