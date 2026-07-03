import React, { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Chip,
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
} from "@mui/material";
import api from "../services/api";

interface AuditEntry {
  id: number;
  timestamp: string;
  action: string;
  resource: string;
  user: string;
  details: string;
  severity: string;
}

interface AuditSummary {
  total_entries: number;
  by_action: Record<string, number>;
  by_severity: Record<string, number>;
}

const severityColor = (s: string) =>
  s === "error" ? "error" : s === "warning" ? "warning" : "info";

const AuditTrail: React.FC = () => {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [summary, setSummary] = useState<AuditSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/audit/log"),
      api.get("/audit/summary"),
    ]).then(([logRes, sumRes]) => {
      setEntries(logRes.data);
      setSummary(sumRes.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <Box sx={{ textAlign: "center", py: 4 }}><CircularProgress /></Box>;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Audit Trail</Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Chronological log of all system actions. Every policy decode, explanation, scenario check, decision, and claim intake is recorded.
      </Typography>

      {summary && (
        <Box sx={{ display: "flex", gap: 2, mb: 3, flexWrap: "wrap" }}>
          <Card variant="outlined" sx={{ flex: 1, minWidth: 120 }}>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary">Total Entries</Typography>
              <Typography variant="h5">{summary.total_entries}</Typography>
            </CardContent>
          </Card>
          {Object.entries(summary.by_action).slice(0, 6).map(([action, count]) => (
            <Card key={action} variant="outlined" sx={{ flex: 1, minWidth: 100 }}>
              <CardContent>
                <Typography variant="caption" color="text.secondary" sx={{ textTransform: "capitalize" }}>
                  {action.replace(/_/g, " ")}
                </Typography>
                <Typography variant="h6">{count}</Typography>
              </CardContent>
            </Card>
          ))}
        </Box>
      )}

      <TableContainer component={Paper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 600 }}>Time</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Action</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Resource</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Details</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Severity</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {entries.map((entry) => (
              <TableRow key={entry.id} hover sx={entry.severity === "error" ? { bgcolor: "rgba(211,47,47,0.04)" } : undefined}>
                <TableCell sx={{ fontFamily: "monospace", fontSize: "0.75rem", whiteSpace: "nowrap" }}>
                  {new Date(entry.timestamp).toLocaleString()}
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ textTransform: "capitalize" }}>
                    {entry.action.replace(/_/g, " ")}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip label={entry.resource} size="small" variant="outlined" />
                </TableCell>
                <TableCell>
                  <Typography variant="body2" sx={{ maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {entry.details}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip label={entry.severity} size="small" color={severityColor(entry.severity) as any} variant="outlined" />
                </TableCell>
              </TableRow>
            ))}
            {entries.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <Typography variant="body2" color="text.secondary">No audit entries yet.</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default AuditTrail;
