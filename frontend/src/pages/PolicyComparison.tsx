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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import RemoveIcon from "@mui/icons-material/Remove";
import api from "../services/api";

interface FieldDiff {
  field: string;
  label: string;
  policy_a_value: string | null;
  policy_b_value: string | null;
  change_type: string;
}

interface ComparisonResult {
  policy_a_label: string;
  policy_b_label: string;
  diffs: FieldDiff[];
  improvements: string[];
  reductions: string[];
  gaps_bridged: string[];
  overall_assessment: string;
}

const changeIcon = (t: string) => {
  if (t === "improved") return <ArrowUpwardIcon fontSize="small" color="success" />;
  if (t === "reduced") return <ArrowDownwardIcon fontSize="small" color="error" />;
  if (t === "added") return <Chip label="ADDED" size="small" color="success" variant="outlined" />;
  if (t === "removed") return <Chip label="REMOVED" size="small" color="error" variant="outlined" />;
  return <RemoveIcon fontSize="small" color="disabled" />;
};

const PolicyComparison: React.FC = () => {
  const [policyA, setPolicyA] = useState("");
  const [policyB, setPolicyB] = useState("");
  const [labelA, setLabelA] = useState("Current Policy");
  const [labelB, setLabelB] = useState("New Policy");
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCompare = async () => {
    if (!policyA.trim() || !policyB.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.post("/policies/compare", {
        policy_a_text: policyA,
        policy_b_text: policyB,
        label_a: labelA,
        label_b: labelB,
      });
      setResult(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to compare policies.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Policy Comparison Tool</Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Compare two policies side-by-side. Paste declarations text from both policies to see improvements, reductions, and bridged gaps.
      </Typography>

      <Paper variant="outlined" sx={{ p: 3, mb: 2 }}>
        <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
          <Box sx={{ flex: 1, minWidth: 250 }}>
            <TextField
              fullWidth
              size="small"
              label="Label A"
              value={labelA}
              onChange={(e) => setLabelA(e.target.value)}
              sx={{ mb: 1 }}
            />
            <TextField
              fullWidth
              multiline
              minRows={4}
              maxRows={8}
              placeholder="Paste policy A text..."
              value={policyA}
              onChange={(e) => setPolicyA(e.target.value)}
            />
          </Box>
          <Box sx={{ flex: 1, minWidth: 250 }}>
            <TextField
              fullWidth
              size="small"
              label="Label B"
              value={labelB}
              onChange={(e) => setLabelB(e.target.value)}
              sx={{ mb: 1 }}
            />
            <TextField
              fullWidth
              multiline
              minRows={4}
              maxRows={8}
              placeholder="Paste policy B text..."
              value={policyB}
              onChange={(e) => setPolicyB(e.target.value)}
            />
          </Box>
        </Box>
        <Button variant="contained" size="large" fullWidth sx={{ mt: 2 }} onClick={handleCompare} disabled={!policyA.trim() || !policyB.trim() || loading}>
          {loading ? <CircularProgress size={24} /> : "Compare Policies"}
        </Button>
      </Paper>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {result && (
        <Box>
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>{result.overall_assessment}</Typography>
              <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
                <Chip icon={<ArrowUpwardIcon />} label={`${result.improvements.length} Improvements`} color="success" variant="outlined" />
                <Chip icon={<ArrowDownwardIcon />} label={`${result.reductions.length} Reductions`} color="error" variant="outlined" />
                {result.gaps_bridged.length > 0 && <Chip label={`${result.gaps_bridged.length} Gaps Bridged`} color="info" variant="outlined" />}
              </Box>
            </CardContent>
          </Card>

          <TableContainer component={Paper} variant="outlined" sx={{ mb: 2 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ fontWeight: 600 }}>Coverage</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>{result.policy_a_label}</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>{result.policy_b_label}</TableCell>
                  <TableCell sx={{ fontWeight: 600 }}>Change</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {result.diffs.map((d, i) => (
                  <TableRow key={i} hover sx={d.change_type === "improved" ? { bgcolor: "rgba(76,175,80,0.04)" } : d.change_type === "reduced" ? { bgcolor: "rgba(244,67,54,0.04)" } : undefined}>
                    <TableCell>
                      <Typography variant="body2" fontWeight={500}>{d.label}</Typography>
                    </TableCell>
                    <TableCell>
                      {d.policy_a_value ? (
                        <Chip label={d.policy_a_value} size="small" variant="outlined" />
                      ) : (
                        <Typography variant="caption" color="text.disabled">—</Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      {d.policy_b_value ? (
                        <Chip label={d.policy_b_value} size="small" variant="outlined" color={d.change_type === "improved" ? "success" : d.change_type === "reduced" ? "error" : "default"} />
                      ) : (
                        <Typography variant="caption" color="text.disabled">—</Typography>
                      )}
                    </TableCell>
                    <TableCell>{changeIcon(d.change_type)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {result.improvements.length > 0 && (
            <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle1" fontWeight={600} color="success.main" gutterBottom>Improvements</Typography>
              {result.improvements.map((imp, i) => (
                <Typography key={i} variant="body2" sx={{ mb: 0.5 }}>+ {imp}</Typography>
              ))}
            </Paper>
          )}

          {result.reductions.length > 0 && (
            <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle1" fontWeight={600} color="error.main" gutterBottom>Reductions</Typography>
              {result.reductions.map((red, i) => (
                <Typography key={i} variant="body2" sx={{ mb: 0.5 }}>− {red}</Typography>
              ))}
            </Paper>
          )}

          {result.gaps_bridged.length > 0 && (
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle1" fontWeight={600} color="info.main" gutterBottom>Gaps Bridged</Typography>
              {result.gaps_bridged.map((gap, i) => (
                <Typography key={i} variant="body2" sx={{ mb: 0.5 }}>✓ {gap}</Typography>
              ))}
            </Paper>
          )}
        </Box>
      )}
    </Box>
  );
};

export default PolicyComparison;
