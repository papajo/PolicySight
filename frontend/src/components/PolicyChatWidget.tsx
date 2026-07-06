import React, { useState, useRef, useEffect } from "react";
import {
  Box,
  Typography,
  Paper,
  TextField,
  IconButton,
  Button,
  Chip,
  CircularProgress,
  Collapse,
  Fab,
  Zoom,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import ChatIcon from "@mui/icons-material/Chat";
import CloseIcon from "@mui/icons-material/Close";
import SendIcon from "@mui/icons-material/Send";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import PersonIcon from "@mui/icons-material/Person";
import SourceIcon from "@mui/icons-material/Source";
import SupportAgentIcon from "@mui/icons-material/SupportAgent";
import api from "../services/api";

interface EvidenceAnswer {
  question: string;
  answer: string;
  citations: string[];
  confidence: string;
  is_assumption: boolean;
  missing_info: string[];
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  answer?: EvidenceAnswer;
}

const confColor = (c: string) =>
  c === "high" ? "success" : c === "medium" ? "warning" : "error";

const SUGGESTED = [
  "Am I covered?",
  "What\u2019s my deductible?",
  "Explain my exclusions",
  "Do I have rental car coverage?",
  "What should I do after an accident?",
  "Is theft covered?",
  "Is flood damage covered?",
  "What if I hit another car?",
  "What if someone hit me?",
  "What if the driver was uninsured?",
];

interface Props {
  policyText?: string;
}

const PolicyChatWidget: React.FC<Props> = ({ policyText: externalText }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const [open, setOpen] = useState(false);
  const [policyText, setPolicyText] = useState(externalText || "");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Hi, I can help explain your policy in plain English. I\u2019ll look for the relevant policy sections and show where the answer came from.",
    },
  ]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);
  const [showSources, setShowSources] = useState<Record<number, boolean>>({});

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const handleAsk = async (q?: string) => {
    const text = q || question;
    if (!text.trim() || !policyText.trim()) return;
    setQuestion("");
    setLoading(true);
    const userMsg: ChatMessage = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    try {
      const res = await api.post("/policies/ask", { text: policyText, question: text });
      const data: EvidenceAnswer = res.data;
      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: data.answer,
        answer: data,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || "Unknown error";
      console.error("ChatWidget ask error:", detail, err);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `I couldn\u2019t answer that. ${detail}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const toggleSources = (idx: number) => {
    setShowSources((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const needsPolicy = !policyText.trim();

  return (
    <>
      <Zoom in={!open}>
        <Fab
          color="primary"
          sx={{
            position: "fixed",
            bottom: { xs: 16, sm: 24 },
            right: { xs: 16, sm: 24 },
            zIndex: 1300,
          }}
          onClick={() => setOpen(true)}
        >
          <ChatIcon />
        </Fab>
      </Zoom>

      <Collapse in={open} orientation="horizontal" sx={{ position: "fixed", bottom: { xs: 16, sm: 24 }, right: { xs: 16, sm: 24 }, zIndex: 1300 }}>
        <Paper
          elevation={8}
          sx={{
            width: isMobile ? "calc(100vw - 32px)" : 380,
            height: isMobile ? "calc(100vh - 80px)" : 600,
            maxWidth: isMobile ? 400 : 380,
            display: "flex",
            flexDirection: "column",
            borderRadius: isMobile ? 2 : 3,
            overflow: "hidden",
          }}
        >
          {/* Header */}
          <Box sx={{ bgcolor: "primary.main", color: "white", p: 2, display: "flex", alignItems: "center", gap: 1 }}>
            <SmartToyIcon />
            <Box sx={{ flex: 1 }}>
              <Typography variant="subtitle2" fontWeight={600}>PolicySight Assistant</Typography>
              <Typography variant="caption" sx={{ opacity: 0.9 }}>
                {needsPolicy ? "No policy loaded" : "Using your uploaded policy"}
              </Typography>
            </Box>
            <IconButton size="small" sx={{ color: "white" }} onClick={() => setOpen(false)}>
              <CloseIcon />
            </IconButton>
          </Box>

          {/* Policy paste area if no external text */}
          {needsPolicy && (
            <Box sx={{ p: 1.5, borderBottom: 1, borderColor: "divider" }}>
              <TextField
                fullWidth
                size="small"
                multiline
                minRows={2}
                maxRows={4}
                placeholder="Paste your policy text to get started..."
                value={policyText}
                onChange={(e) => setPolicyText(e.target.value)}
              />
            </Box>
          )}

          {/* Messages */}
          <Box
            ref={listRef}
            sx={{ flex: 1, overflowY: "auto", p: 1.5, display: "flex", flexDirection: "column", gap: 1.5 }}
          >
            {messages.map((msg, i) => (
              <Box key={i} sx={{ display: "flex", flexDirection: msg.role === "user" ? "row-reverse" : "row", gap: 1 }}>
                <Box
                  sx={{
                    maxWidth: "80%",
                    bgcolor: msg.role === "user" ? "primary.main" : "grey.100",
                    color: msg.role === "user" ? "white" : "text.primary",
                    borderRadius: 2,
                    px: 1.5,
                    py: 1,
                  }}
                >
                  <Typography variant="body2">{msg.content}</Typography>

                  {msg.answer && (
                    <Box sx={{ mt: 1 }}>
                      <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap", mb: 0.5 }}>
                        <Chip label={msg.answer.confidence} size="small" color={confColor(msg.answer.confidence) as any} />
                        {msg.answer.is_assumption && <Chip label="Assumption" size="small" color="warning" variant="outlined" />}
                      </Box>

                      {msg.answer.citations.length > 0 && (
                        <>
                          <Button
                            size="small"
                            startIcon={<SourceIcon />}
                            onClick={() => toggleSources(i)}
                            sx={{ textTransform: "none", fontSize: "0.7rem", p: 0, minWidth: 0 }}
                          >
                            {showSources[i] ? "Hide" : "Show"} sources ({msg.answer.citations.length})
                          </Button>
                          <Collapse in={showSources[i]}>
                            {msg.answer.citations.map((c, j) => (
                              <Typography key={j} variant="caption" color="text.secondary" sx={{ display: "block", fontStyle: "italic", fontSize: "0.65rem", mt: 0.3 }}>
                                {c}
                              </Typography>
                            ))}
                          </Collapse>
                        </>
                      )}

                      {msg.answer.missing_info.length > 0 && (
                        <Typography variant="caption" color="warning.dark" sx={{ display: "block", mt: 0.5, fontSize: "0.65rem" }}>
                          Not found: {msg.answer.missing_info.join(", ")}
                        </Typography>
                      )}
                    </Box>
                  )}
                </Box>
                <Box sx={{ mt: 0.5 }}>
                  {msg.role === "user" ? <PersonIcon fontSize="small" color="primary" /> : <SmartToyIcon fontSize="small" color="disabled" />}
                </Box>
              </Box>
            ))}

            {loading && (
              <Box sx={{ display: "flex", gap: 1 }}>
                <CircularProgress size={16} />
                <Typography variant="caption" color="text.secondary">Checking your policy...</Typography>
              </Box>
            )}
          </Box>

          {/* Suggested questions */}
          <Box sx={{ px: 1.5, pb: 0.5, display: "flex", gap: 0.5, flexWrap: "wrap" }}>
            {SUGGESTED.slice(0, 4).map((s) => (
              <Chip
                key={s}
                label={s}
                size="small"
                variant="outlined"
                onClick={() => handleAsk(s)}
                sx={{ fontSize: "0.65rem", cursor: "pointer" }}
              />
            ))}
          </Box>

          {/* Input */}
          <Box sx={{ p: 1.5, borderTop: 1, borderColor: "divider", display: "flex", gap: 1 }}>
            <TextField
              fullWidth
              size="small"
              placeholder="Ask about your policy..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !loading && handleAsk()}
              disabled={loading || needsPolicy}
            />
            <IconButton color="primary" onClick={() => handleAsk()} disabled={!question.trim() || loading || needsPolicy}>
              <SendIcon />
            </IconButton>
          </Box>

          {/* Talk to a human */}
          <Box sx={{ px: 1.5, pb: 1, textAlign: "center" }}>
            <Button
              size="small"
              startIcon={<SupportAgentIcon />}
              variant="text"
              color="warning"
              sx={{ textTransform: "none", fontSize: "0.7rem" }}
              href="#"
              onClick={(e) => {
                e.preventDefault();
                setMessages((prev) => [...prev, {
                  role: "assistant",
                  content: "A human review is recommended for complex claim decisions. Contact your insurance agent or a licensed claims adjuster for a definitive answer.",
                }]);
              }}
            >
              Talk to a human
            </Button>
          </Box>
        </Paper>
      </Collapse>
    </>
  );
};

export default PolicyChatWidget;
