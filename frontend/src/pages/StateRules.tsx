import React, { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Chip,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import api from "../services/api";

interface StateRule {
  state: string;
  state_name: string;
  is_no_fault: boolean;
  requires_pip: boolean;
  pip_min_limit: string | null;
  requires_um_uim: boolean;
  um_uim_min_limit: string | null;
  glass_deductible_rule: string;
  notes: string[];
}

const StateRules: React.FC = () => {
  const [states, setStates] = useState<{ code: string; name: string }[]>([]);
  const [selectedRule, setSelectedRule] = useState<StateRule | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/states").then((res) => {
      setStates(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const loadState = async (code: string) => {
    try {
      const res = await api.get(`/states/${code}`);
      setSelectedRule(res.data);
    } catch {
      setSelectedRule(null);
    }
  };

  if (loading) return <Box sx={{ textAlign: "center", py: 4 }}><CircularProgress /></Box>;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>State-Specific Insurance Rules</Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Insurance rules vary by state. Select a state to see its specific requirements for PIP, UM/UIM, no-fault status, and more.
      </Typography>

      <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle1" fontWeight={600} gutterBottom>Available States</Typography>
        <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap" }}>
          {states.map((s) => (
            <Chip
              key={s.code}
              label={`${s.code} — ${s.name}`}
              variant="outlined"
              onClick={() => loadState(s.code)}
              sx={{ cursor: "pointer", "&:hover": { borderColor: "primary.main" } }}
            />
          ))}
        </Box>
      </Paper>

      {selectedRule && (
        <Box>
          <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
            <Typography variant="h6" gutterBottom>{selectedRule.state} — {selectedRule.state_name}</Typography>
            <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 2 }}>
              <Chip label={selectedRule.is_no_fault ? "No-Fault State" : "Tort State"} size="small" color={selectedRule.is_no_fault ? "info" : "default"} />
              {selectedRule.requires_pip && <Chip label={`Requires PIP (min ${selectedRule.pip_min_limit})`} size="small" color="primary" />}
              {selectedRule.requires_um_uim && <Chip label={`Requires UM/UIM (min ${selectedRule.um_uim_min_limit})`} size="small" color="warning" />}
              <Chip label={`Glass: ${selectedRule.glass_deductible_rule.replace("_", " ")}`} size="small" variant="outlined" />
            </Box>
          </Paper>

          <Accordion variant="outlined" defaultExpanded>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography fontWeight={600}>State Notes & Requirements</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {selectedRule.notes.map((note, i) => (
                <Alert key={i} severity="info" sx={{ mb: 1, py: 0.5, "& .MuiAlert-message": { fontSize: "0.85rem" } }}>
                  {note}
                </Alert>
              ))}
            </AccordionDetails>
          </Accordion>

          <Accordion variant="outlined" sx={{ mt: 1 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography fontWeight={600}>Rule Details</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Rule</TableCell>
                      <TableCell>Value</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow><TableCell>No-Fault</TableCell><TableCell>{selectedRule.is_no_fault ? "Yes" : "No"}</TableCell></TableRow>
                    <TableRow><TableCell>Requires PIP</TableCell><TableCell>{selectedRule.requires_pip ? `Yes (min ${selectedRule.pip_min_limit})` : "No"}</TableCell></TableRow>
                    <TableRow><TableCell>Requires UM/UIM</TableCell><TableCell>{selectedRule.requires_um_uim ? `Yes (min ${selectedRule.um_uim_min_limit})` : "No"}</TableCell></TableRow>
                    <TableRow><TableCell>Glass Deductible Rule</TableCell><TableCell>{selectedRule.glass_deductible_rule.replace("_", " ")}</TableCell></TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </AccordionDetails>
          </Accordion>
        </Box>
      )}

      {!selectedRule && !loading && (
        <Alert severity="info">Click a state above to view its insurance rules.</Alert>
      )}
    </Box>
  );
};

export default StateRules;
