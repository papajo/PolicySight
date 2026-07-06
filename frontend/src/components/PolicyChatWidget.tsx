import React, { useState, useRef, useEffect, useCallback } from "react";
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
import SupportAgentIcon from "@mui/icons-material/SupportAgent";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import GavelIcon from "@mui/icons-material/Gavel";
import { useNavigate } from "react-router-dom";
import api from "../services/api";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  action?: string;
  actionTarget?: string;
}

interface ChatApiResponse {
  reply: string;
  action?: string;
  action_target?: string;
}

interface Props {
  currentPath?: string;
}

const PAGE_INFO: Record<string, { name: string; tagline: string }> = {
  "/": { name: "Home", tagline: "Your insurance command center" },
  "/decoder": { name: "Policy Decoder", tagline: "Understand your SLIP document" },
  "/claims": { name: "Claims Advocate", tagline: "Fight for fair settlements" },
  "/trajectory": { name: "Rate Forecast", tagline: "Predict your next premium" },
  "/lapse": { name: "Lapse Bridge", tagline: "Bridge coverage gaps" },
  "/timeline": { name: "Coverage Timeline", tagline: "Visualize your history" },
  "/scenario": { name: "Scenario Checker", tagline: "Test hypothetical situations" },
  "/intake": { name: "Claim Intake", tagline: "File a claim step by step" },
  "/decision": { name: "Decision Draft", tagline: "Coverage decision analysis" },
  "/audit": { name: "Audit Trail", tagline: "Track all actions" },
  "/edge-cases": { name: "Edge Cases", tagline: "Unusual situations explained" },
  "/cost-estimator": { name: "Cost Estimator", tagline: "Estimate out-of-pocket costs" },
  "/states": { name: "State Rules", tagline: "State-specific requirements" },
  "/feedback": { name: "Feedback", tagline: "Help us improve" },
  "/compare": { name: "Policy Comparison", tagline: "Compare two policies" },
  "/copilot": { name: "Copilot Dashboard", tagline: "Your AI copilot" },
};

const QUICK_ACTIONS: Record<string, string[]> = {
  "/": [
    "What can you do?",
    "How does PolicySight work?",
    "Is my data safe?",
    "Take me to the Policy Decoder",
  ],
  "/decoder": [
    "How do I upload my policy?",
    "What is a SLIP document?",
    "What coverages will you extract?",
    "Explain liability coverage",
  ],
  "/claims": [
    "How do I file a claim?",
    "What are sub-limits?",
    "What is actual cash value?",
    "Help me understand my settlement",
  ],
  "/trajectory": [
    "How is my premium calculated?",
    "What affects my rate?",
    "Should I switch carriers?",
    "Explain the forecast",
  ],
  "/lapse": [
    "What happens if my policy lapses?",
    "Do I need SR-22?",
    "How do I bridge a coverage gap?",
  ],
  "/scenario": [
    "What if I hit a deer?",
    "What if my car is stolen?",
    "What if I'm in a hit-and-run?",
  ],
  "/intake": [
    "What info do I need for a claim?",
    "Walk me through the intake form",
  ],
  "/decision": [
    "How do coverage decisions work?",
    "What does escalation mean?",
  ],
  "/edge-cases": [
    "What about rideshare coverage?",
    "What if someone borrowed my car?",
  ],
  "/cost-estimator": [
    "How do deductibles work?",
    "Estimate my out-of-pocket costs",
  ],
  "/states": [
    "What are my state's minimum limits?",
    "Is my state no-fault?",
  ],
  "/compare": [
    "What should I look for when comparing?",
    "Help me compare two policies",
  ],
};

const PolicyChatWidget: React.FC<Props> = ({ currentPath }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [initialized, setInitialized] = useState(false);

  const path = currentPath || "/";
  const pageInfo = PAGE_INFO[path] || PAGE_INFO["/"];
  const quickActions = QUICK_ACTIONS[path] || QUICK_ACTIONS["/"];

  // Initialize welcome message when opened or path changes
  useEffect(() => {
    if (open && !initialized) {
      const welcomeMsg: ChatMessage = {
        role: "assistant",
        content: getWelcomeMessage(path),
      };
      setMessages([welcomeMsg]);
      setInitialized(true);
    }
  }, [open, initialized, path]);

  // Reset when path changes (if widget is open)
  useEffect(() => {
    if (open) {
      const welcomeMsg: ChatMessage = {
        role: "assistant",
        content: getWelcomeMessage(path),
      };
      setMessages([welcomeMsg]);
      setInitialized(true);
      setQuestion("");
    }
  }, [path]);

  // Scroll to bottom on new messages
  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  // Focus input when opened
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [open]);

  function getWelcomeMessage(routePath: string): string {
    const info = PAGE_INFO[routePath] || PAGE_INFO["/"];
    if (routePath === "/") {
      return (
        `Hi there! I'm **PolicySight Assistant**, your AI insurance guide.\n\n` +
        `I can help you understand your policy, navigate claims, compare rates, ` +
        `and answer questions about auto insurance.\n\n` +
        `I see you're on the **${info.name}** page. How can I help you today?`
      );
    }
    return (
      `Hi! I'm **PolicySight Assistant**. I see you're on the **${info.name}** page — ${info.tagline}.\n\n` +
      `I can help explain concepts, guide you through features, or answer insurance questions. ` +
      `What would you like to know?`
    );
  }

  const handleAsk = useCallback(async (q?: string) => {
    const text = q || question;
    if (!text.trim()) return;

    setQuestion("");
    setLoading(true);
    const userMsg: ChatMessage = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const res = await api.post("/chat", {
        messages: [...messages, userMsg].map((m) => ({ role: m.role, content: m.content })),
        context: { page: path },
      });
      const data: ChatApiResponse = res.data;
      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: data.reply,
        action: data.action,
        actionTarget: data.action_target,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || "Unknown error";
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `I couldn't process that. ${detail}` },
      ]);
    } finally {
      setLoading(false);
    }
  }, [question, messages, path]);

  const handleNavigate = (route: string) => {
    navigate(route);
    setOpen(false);
  };

  const handleActionClick = (msg: ChatMessage) => {
    if (msg.action === "navigate" && msg.actionTarget) {
      handleNavigate(msg.actionTarget);
    }
  };

  const toggleOpen = () => {
    setOpen((prev) => !prev);
    if (!open) {
      setInitialized(false);
    }
  };

  return (
    <>
      {/* ── FAB Toggle Button ── */}
      <Zoom in={!open}>
        <Fab
          color="primary"
          aria-label="Open chat assistant"
          sx={{
            position: "fixed",
            bottom: { xs: 16, sm: 24 },
            right: { xs: 16, sm: 24 },
            zIndex: 1300,
            boxShadow: "0 4px 20px rgba(26,35,126,0.4)",
            "&:hover": {
              transform: "scale(1.05)",
              boxShadow: "0 6px 24px rgba(26,35,126,0.5)",
            },
            transition: "all 0.2s ease-in-out",
          }}
          onClick={toggleOpen}
        >
          <ChatIcon />
        </Fab>
      </Zoom>

      {/* ── Chat Panel ── */}
      <Collapse
        in={open}
        orientation="horizontal"
        sx={{
          position: "fixed",
          bottom: { xs: 16, sm: 24 },
          right: { xs: 16, sm: 24 },
          zIndex: 1300,
        }}
      >
        <Paper
          elevation={12}
          sx={{
            width: isMobile ? "calc(100vw - 32px)" : 400,
            height: isMobile ? "calc(100vh - 80px)" : 620,
            maxWidth: isMobile ? 400 : 400,
            display: "flex",
            flexDirection: "column",
            borderRadius: isMobile ? 2 : 3,
            overflow: "hidden",
            border: "1px solid",
            borderColor: "divider",
          }}
        >
          {/* ═══ Header ═══ */}
          <Box
            sx={{
              bgcolor: "primary.main",
              color: "white",
              p: 2,
              display: "flex",
              alignItems: "center",
              gap: 1.5,
            }}
          >
            <Box
              sx={{
                width: 36,
                height: 36,
                borderRadius: "50%",
                bgcolor: "rgba(255,255,255,0.15)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <GavelIcon fontSize="small" />
            </Box>
            <Box sx={{ flex: 1 }}>
              <Typography variant="subtitle2" fontWeight={700}>
                PolicySight Assistant
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.85 }}>
                {pageInfo.name} — {pageInfo.tagline}
              </Typography>
            </Box>
            <IconButton size="small" sx={{ color: "white" }} onClick={toggleOpen}>
              <CloseIcon />
            </IconButton>
          </Box>

          {/* ═══ Messages ═══ */}
          <Box
            ref={listRef}
            sx={{
              flex: 1,
              overflowY: "auto",
              p: 2,
              display: "flex",
              flexDirection: "column",
              gap: 2,
              bgcolor: "grey.50",
            }}
          >
            {messages.map((msg, i) => (
              <Box
                key={i}
                sx={{
                  display: "flex",
                  flexDirection: msg.role === "user" ? "row-reverse" : "row",
                  gap: 1,
                  alignItems: "flex-start",
                }}
              >
                {/* Avatar */}
                <Box
                  sx={{
                    width: 28,
                    height: 28,
                    borderRadius: "50%",
                    bgcolor: msg.role === "user" ? "primary.main" : "grey.200",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                    mt: 0.5,
                  }}
                >
                  {msg.role === "user" ? (
                    <PersonIcon sx={{ fontSize: 16, color: "white" }} />
                  ) : (
                    <SmartToyIcon sx={{ fontSize: 16, color: "text.secondary" }} />
                  )}
                </Box>

                {/* Bubble */}
                <Box sx={{ maxWidth: "80%" }}>
                  <Paper
                    elevation={0}
                    sx={{
                      px: 1.5,
                      py: 1,
                      bgcolor: msg.role === "user" ? "primary.main" : "white",
                      color: msg.role === "user" ? "white" : "text.primary",
                      borderRadius: 2,
                      border: msg.role === "assistant" ? "1px solid" : "none",
                      borderColor: "divider",
                    }}
                  >
                    <Typography
                      variant="body2"
                      sx={{
                        whiteSpace: "pre-line",
                        "& strong": { fontWeight: 600 },
                        lineHeight: 1.5,
                      }}
                    >
                      {msg.content}
                    </Typography>
                  </Paper>

                  {/* Action button */}
                  {msg.action === "navigate" && msg.actionTarget && (
                    <Button
                      size="small"
                      endIcon={<OpenInNewIcon sx={{ fontSize: "0.8rem" }} />}
                      onClick={() => handleActionClick(msg)}
                      sx={{
                        mt: 0.5,
                        textTransform: "none",
                        fontSize: "0.7rem",
                        color: "primary.main",
                      }}
                    >
                      Go to {PAGE_INFO[msg.actionTarget]?.name || msg.actionTarget}
                    </Button>
                  )}
                </Box>
              </Box>
            ))}

            {/* Loading indicator */}
            {loading && (
              <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
                <CircularProgress size={14} />
                <Typography variant="caption" color="text.secondary">
                  Thinking...
                </Typography>
              </Box>
            )}
          </Box>

          {/* ═══ Quick Actions ═══ */}
          {messages.length <= 2 && (
            <Box
              sx={{
                px: 2,
                pb: 1,
                display: "flex",
                gap: 0.5,
                flexWrap: "wrap",
              }}
            >
              {quickActions.map((action) => (
                <Chip
                  key={action}
                  label={action}
                  size="small"
                  variant="outlined"
                  onClick={() => handleAsk(action)}
                  sx={{
                    fontSize: "0.65rem",
                    cursor: "pointer",
                    borderColor: "primary.light",
                    color: "primary.main",
                    "&:hover": {
                      bgcolor: "primary.main",
                      color: "white",
                    },
                  }}
                />
              ))}
            </Box>
          )}

          {/* ═══ Input ═══ */}
          <Box
            sx={{
              p: 1.5,
              borderTop: 1,
              borderColor: "divider",
              display: "flex",
              gap: 1,
              bgcolor: "white",
            }}
          >
            <TextField
              inputRef={inputRef}
              fullWidth
              size="small"
              placeholder={`Ask about ${pageInfo.name.toLowerCase()}...`}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !loading && handleAsk()}
              disabled={loading}
              sx={{
                "& .MuiOutlinedInput-root": {
                  borderRadius: 3,
                  bgcolor: "grey.50",
                },
              }}
            />
            <IconButton
              color="primary"
              onClick={() => handleAsk()}
              disabled={!question.trim() || loading}
              sx={{
                bgcolor: "primary.main",
                color: "white",
                "&:hover": { bgcolor: "primary.dark" },
                "&.Mui-disabled": {
                  bgcolor: "grey.300",
                  color: "grey.500",
                },
              }}
            >
              <SendIcon fontSize="small" />
            </IconButton>
          </Box>

          {/* ═══ Footer ═══ */}
          <Box
            sx={{
              px: 2,
              pb: 1.5,
              display: "flex",
              flexDirection: "column",
              gap: 0.5,
            }}
          >
            <Button
              size="small"
              startIcon={<SupportAgentIcon />}
              variant="text"
              color="inherit"
              sx={{
                textTransform: "none",
                fontSize: "0.65rem",
                color: "text.secondary",
                justifyContent: "flex-start",
              }}
              onClick={() => {
                setMessages((prev) => [
                  ...prev,
                  {
                    role: "assistant",
                    content:
                      "For complex claim decisions or specific legal advice, I recommend consulting a licensed insurance agent or claims adjuster. You can also contact your carrier directly for definitive answers about your policy.",
                  },
                ]);
              }}
            >
              Talk to a human
            </Button>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontSize: "0.6rem", lineHeight: 1.3 }}
            >
              By messaging, you agree that this chat may be monitored and used
              to improve PolicySight. AI responses are informational only and do
              not constitute insurance advice.
            </Typography>
          </Box>
        </Paper>
      </Collapse>
    </>
  );
};

export default PolicyChatWidget;
