import React from "react";
import {
  Box,
  Typography,
  Paper,
  Chip,
  Alert,
  List,
  ListItem,
  ListItemText,
  Divider,
} from "@mui/material";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import ErrorIcon from "@mui/icons-material/Error";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";

interface RequiredInfo {
  field: string;
  label: string;
  reason: string;
  how_to_find: string;
}

interface NextAction {
  action: string;
  detail: string;
  priority: string;
}

interface Props {
  overall_status: string;
  assessment: string;
  required_info: RequiredInfo[];
  next_actions: NextAction[];
}

const severityMap: Record<string, "error" | "warning" | "info"> = {
  indeterminate: "error",
  partial: "warning",
  determinate: "info",
};

const SafeFailurePanel: React.FC<Props> = ({ overall_status, assessment, required_info, next_actions }) => {
  if (!overall_status || overall_status === "determinate") return null;

  const severity = severityMap[overall_status] || "warning";

  return (
    <Paper
      variant="outlined"
      sx={{
        p: 2,
        mb: 2,
        borderLeft: 4,
        borderLeftColor: severity === "error" ? "error.main" : severity === "warning" ? "warning.main" : "info.main",
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
        {severity === "error" ? <ErrorIcon color="error" /> : <WarningAmberIcon color="warning" />}
        <Typography variant="subtitle1" fontWeight={600}>
          {overall_status === "indeterminate" ? "Cannot Provide Reliable Analysis" : "Partially Complete Analysis"}
        </Typography>
        <Chip
          label={overall_status}
          size="small"
          color={severity}
          variant="outlined"
          sx={{ ml: "auto" }}
        />
      </Box>

      <Alert severity={severity} sx={{ mb: 1.5, "& .MuiAlert-message": { fontSize: "0.875rem" } }}>
        {assessment}
      </Alert>

      {required_info.length > 0 && (
        <Box sx={{ mb: 1.5 }}>
          <Typography variant="subtitle2" fontWeight={600} gutterBottom sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
            <HelpOutlineIcon fontSize="small" color="action" />
            Required Information
          </Typography>
          <List dense disablePadding>
            {required_info.map((info, i) => (
              <ListItem key={i} sx={{ px: 0, py: 0.3 }}>
                <ListItemText
                  primary={
                    <Typography variant="body2" fontWeight={500}>
                      {info.label}
                    </Typography>
                  }
                  secondary={
                    <>
                      <Typography variant="caption" color="text.secondary" display="block">
                        {info.reason}
                      </Typography>
                      <Typography variant="caption" color="primary.main" display="block" sx={{ mt: 0.2 }}>
                        Where to find: {info.how_to_find}
                      </Typography>
                    </>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Box>
      )}

      {required_info.length > 0 && <Divider sx={{ mb: 1.5 }} />}

      {next_actions.length > 0 && (
        <Box>
          <Typography variant="subtitle2" fontWeight={600} gutterBottom sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
            <ArrowForwardIcon fontSize="small" color="action" />
            Recommended Next Steps
          </Typography>
          {next_actions.map((action, i) => (
            <Box
              key={i}
              sx={{
                display: "flex",
                alignItems: "flex-start",
                gap: 1,
                py: 0.5,
              }}
            >
              <Typography variant="body2" color="text.secondary" sx={{ minWidth: 20 }}>{i + 1}.</Typography>
              <Box sx={{ flex: 1 }}>
                <Typography variant="body2" fontWeight={500}>{action.action}</Typography>
                <Typography variant="caption" color="text.secondary">{action.detail}</Typography>
              </Box>
              <Chip
                label={action.priority}
                size="small"
                color={action.priority === "high" ? "error" : action.priority === "medium" ? "warning" : "default"}
                variant="outlined"
                sx={{ ml: 1, fontSize: "0.65rem" }}
              />
            </Box>
          ))}
        </Box>
      )}
    </Paper>
  );
};

export default SafeFailurePanel;
