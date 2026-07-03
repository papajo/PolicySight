import React, { useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Button,
  TextField,
  CircularProgress,
  Chip,
  Snackbar,
} from "@mui/material";
import ThumbUpIcon from "@mui/icons-material/ThumbUp";
import ThumbDownIcon from "@mui/icons-material/ThumbDown";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";
import api from "../services/api";

const ratingMeta = {
  correct: { label: "Correct", color: "success", icon: ThumbUpIcon },
  incorrect: { label: "Incorrect", color: "error", icon: ThumbDownIcon },
  incomplete: { label: "Incomplete", color: "warning", icon: HelpOutlineIcon },
  unclear: { label: "Unclear", color: "info", icon: VisibilityOffIcon },
};

interface FeedbackEntry {
  id: number;
  timestamp: string;
  action: string;
  rating: string;
  comment: string;
}

interface Props {
  action: string;
  details?: string;
  onFeedbackSubmitted?: () => void;
}

const FeedbackButtons: React.FC<Props> = ({ action, details, onFeedbackSubmitted }) => {
  const [selected, setSelected] = useState<string | null>(null);
  const [comment, setComment] = useState("");
  const [showComment, setShowComment] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [snackbar, setSnackbar] = useState("");

  const submitRating = async (rating: string) => {
    setSelected(rating);
    setSubmitting(true);
    try {
      await api.post("/feedback", { action, rating, comment, details: details || "" });
      setSnackbar(`Feedback recorded: ${rating}`);
      setShowComment(false);
      setComment("");
      onFeedbackSubmitted?.();
    } catch {
      setSnackbar("Failed to submit feedback.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box sx={{ mt: 1 }}>
      <Box sx={{ display: "flex", gap: 0.5, alignItems: "center" }}>
        <Typography variant="caption" color="text.secondary" sx={{ mr: 0.5 }}>
          Rate this:
        </Typography>
        {(Object.entries(ratingMeta) as [string, typeof ratingMeta.correct][]).map(([key, meta]) => {
          const Icon = meta.icon;
          return (
            <Chip
              key={key}
              icon={<Icon fontSize="small" />}
              label={meta.label}
              size="small"
              variant={selected === key ? "filled" : "outlined"}
              color={selected === key ? (meta.color as any) : "default"}
              onClick={() => !submitting && submitRating(key)}
              sx={{ cursor: "pointer", fontSize: "0.7rem" }}
            />
          );
        })}
        {selected && !showComment && (
          <Button size="small" sx={{ fontSize: "0.7rem", minWidth: "auto", ml: 0.5 }} onClick={() => setShowComment(true)}>
            Add comment
          </Button>
        )}
      </Box>
      {showComment && selected && (
        <Box sx={{ display: "flex", gap: 1, mt: 0.5 }}>
          <TextField
            size="small"
            placeholder="Optional feedback..."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            sx={{ flex: 1, "& input": { fontSize: "0.8rem" } }}
          />
          <Button size="small" variant="contained" onClick={() => { setShowComment(false); setSnackbar("Comment saved."); }}>
            Save
          </Button>
        </Box>
      )}
      <Snackbar open={!!snackbar} autoHideDuration={3000} onClose={() => setSnackbar("")} message={snackbar} />
    </Box>
  );
};

const FeedbackDashboard: React.FC = () => {
  const [entries, setEntries] = useState<FeedbackEntry[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  React.useEffect(() => {
    Promise.all([
      api.get("/feedback"),
      api.get("/feedback/summary"),
    ]).then(([eRes, sRes]) => {
      setEntries(eRes.data);
      setSummary(sRes.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <Box sx={{ textAlign: "center", py: 4 }}><CircularProgress /></Box>;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>Feedback & Model Quality</Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Track user ratings of AI responses. Every decode, explanation, scenario check, and decision can be rated.
      </Typography>

      {summary && (
        <Box sx={{ display: "flex", gap: 2, mb: 3, flexWrap: "wrap" }}>
          <Paper variant="outlined" sx={{ p: 2, flex: 1, minWidth: 120, textAlign: "center" }}>
            <Typography variant="h5">{summary.total}</Typography>
            <Typography variant="caption" color="text.secondary">Total Ratings</Typography>
          </Paper>
          <Paper variant="outlined" sx={{ p: 2, flex: 1, minWidth: 120, textAlign: "center" }}>
            <Typography variant="h5" color="success.main">{summary.accuracy_rate}%</Typography>
            <Typography variant="caption" color="text.secondary">Accuracy Rate</Typography>
          </Paper>
          {(Object.entries(summary.by_rating) as [string, number][]).map(([rating, count]) => (
            <Paper key={rating} variant="outlined" sx={{ p: 2, flex: 1, minWidth: 80, textAlign: "center" }}>
              <Typography variant="h6" sx={{ textTransform: "capitalize" }}>{count}</Typography>
              <Typography variant="caption" color="text.secondary" sx={{ textTransform: "capitalize" }}>{rating}</Typography>
            </Paper>
          ))}
        </Box>
      )}

      <Paper variant="outlined">
        {entries.length === 0 && (
          <Box sx={{ p: 4, textAlign: "center" }}>
            <Typography variant="body2" color="text.secondary">No feedback recorded yet. Rate results from any page to see them here.</Typography>
          </Box>
        )}
        {entries.map((e) => (
          <Box key={e.id} sx={{ p: 2, borderBottom: "1px solid #eee", display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <Box>
              <Box sx={{ display: "flex", gap: 1, alignItems: "center", mb: 0.5 }}>
                <Chip label={e.rating} size="small" color={(ratingMeta as any)[e.rating]?.color || "default"} />
                <Typography variant="caption" color="text.secondary">{e.action}</Typography>
              </Box>
              {e.comment && <Typography variant="body2" color="text.secondary">{e.comment}</Typography>}
            </Box>
            <Typography variant="caption" color="text.secondary">
              {new Date(e.timestamp).toLocaleString()}
            </Typography>
          </Box>
        ))}
      </Paper>
    </Box>
  );
};

export { FeedbackButtons, FeedbackDashboard };
export default FeedbackDashboard;
