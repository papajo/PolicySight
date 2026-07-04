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
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import api from "../services/api";

interface DashboardData {
  claims_count: number;
  intakes: any[];
  audits: any[];
  decisions: number;
  feedback_accuracy: number;
  edge_cases: any[];
}

const CopilotDashboard: React.FC = () => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/claims/intake/list").catch(() => ({ data: [] })),
      api.get("/audit/log?limit=20").catch(() => ({ data: [] })),
      api.get("/feedback/summary").catch(() => ({ data: {} })),
    ]).then(([intakesRes, auditRes, fbRes]) => {
      setData({
        claims_count: (intakesRes.data || []).length,
        intakes: intakesRes.data || [],
        audits: auditRes.data || [],
        decisions: ((auditRes.data || []).filter((e: any) => e.action === "coverage_decision")).length,
        feedback_accuracy: fbRes.data?.accuracy_rate || 0,
        edge_cases: (auditRes.data || []).filter((e: any) => e.action === "edge_case_check"),
      });
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <Box sx={{ textAlign: "center", py: 4 }}><CircularProgress /></Box>;

  const totalActions = data?.audits.length || 0;
  const edgeCasesWithFlags = data?.edge_cases.filter((e: any) => e.details?.includes("flags")).length || 0;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Adjuster Copilot Dashboard</Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Professional dashboard with consolidated claims, coverage decisions, risk flags, and AI reasoning. All actions are audited.
      </Typography>

      <Box sx={{ display: "flex", gap: 2, mb: 3, flexWrap: "wrap" }}>
        <Card variant="outlined" sx={{ flex: 1, minWidth: 140, borderTop: 3, borderTopColor: "primary.main" }}>
          <CardContent>
            <Typography variant="h5">{data?.claims_count || 0}</Typography>
            <Typography variant="caption" color="text.secondary">Claims Filed</Typography>
          </CardContent>
        </Card>
        <Card variant="outlined" sx={{ flex: 1, minWidth: 140, borderTop: 3, borderTopColor: "success.main" }}>
          <CardContent>
            <Typography variant="h5">{data?.decisions || 0}</Typography>
            <Typography variant="caption" color="text.secondary">Decisions</Typography>
          </CardContent>
        </Card>
        <Card variant="outlined" sx={{ flex: 1, minWidth: 140, borderTop: 3, borderTopColor: "warning.main" }}>
          <CardContent>
            <Typography variant="h5">{edgeCasesWithFlags}</Typography>
            <Typography variant="caption" color="text.secondary">Edge Cases Flagged</Typography>
          </CardContent>
        </Card>
        <Card variant="outlined" sx={{ flex: 1, minWidth: 140, borderTop: 3, borderTopColor: "info.main" }}>
          <CardContent>
            <Typography variant="h5">{totalActions}</Typography>
            <Typography variant="caption" color="text.secondary">Audit Events</Typography>
          </CardContent>
        </Card>
        <Card variant="outlined" sx={{ flex: 1, minWidth: 140, borderTop: 3, borderTopColor: data?.feedback_accuracy && data.feedback_accuracy >= 80 ? "success.main" : "warning.main" }}>
          <CardContent>
            <Typography variant="h5" color={data?.feedback_accuracy && data.feedback_accuracy >= 80 ? "success.main" : "warning.main"}>
              {data?.feedback_accuracy || 0}%
            </Typography>
            <Typography variant="caption" color="text.secondary">Accuracy Rate</Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Recent Claims */}
      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle1" fontWeight={600} gutterBottom>
          Recent Claims
          {data && <Chip label={`${data.intakes.length} total`} size="small" sx={{ ml: 1 }} />}
        </Typography>
        {data?.intakes && data.intakes.length > 0 ? (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 600 }}>Date</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Location</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Description</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Damages</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.intakes.slice(0, 10).map((intake: any, i: number) => (
                  <TableRow key={i} hover>
                    <TableCell sx={{ fontSize: "0.8rem" }}>{intake.date_of_loss}</TableCell>
                    <TableCell sx={{ fontSize: "0.8rem" }}>{intake.location}</TableCell>
                    <TableCell sx={{ fontSize: "0.8rem", maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {intake.description}
                    </TableCell>
                    <TableCell>
                      {(intake.damages || []).map((d: any, j: number) => (
                        <Chip key={j} label={d.type} size="small" variant="outlined" sx={{ mr: 0.5, fontSize: "0.65rem" }} />
                      ))}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: "center" }}>
            No claims filed yet.
          </Typography>
        )}
      </Paper>

      {/* Edge Case Flags */}
      {data?.edge_cases && data.edge_cases.filter((e: any) => e.details?.includes("flags")).length > 0 && (
        <Paper variant="outlined" sx={{ p: 2, mb: 2, borderLeft: 4, borderLeftColor: "warning.main" }}>
          <Typography variant="subtitle1" fontWeight={600} gutterBottom>
            <WarningAmberIcon color="warning" sx={{ mr: 0.5, verticalAlign: "middle" }} />
            Edge Cases Requiring Attention
          </Typography>
          {data.edge_cases.filter((e: any) => e.details?.includes("flags")).map((e: any, i: number) => (
            <Alert key={i} severity="warning" sx={{ mb: 1, py: 0.5, "& .MuiAlert-message": { fontSize: "0.85rem" } }}>
              {e.details}
            </Alert>
          ))}
        </Paper>
      )}

      {/* Recent Audit Events */}
      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle1" fontWeight={600} gutterBottom>
          Recent Activity
          {data && <Chip label={`${data.audits.length} events`} size="small" sx={{ ml: 1 }} />}
        </Typography>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>Time</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Action</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Details</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {data?.audits.slice(0, 10).map((entry: any, i: number) => (
                <TableRow key={i} hover>
                  <TableCell sx={{ fontFamily: "monospace", fontSize: "0.7rem", whiteSpace: "nowrap" }}>
                    {new Date(entry.timestamp).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ textTransform: "capitalize", fontSize: "0.8rem" }}>
                      {entry.action.replace(/_/g, " ")}
                    </Typography>
                  </TableCell>
                  <TableCell sx={{ fontSize: "0.8rem", maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {entry.details}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
};

export default CopilotDashboard;
