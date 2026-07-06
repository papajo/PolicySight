import React, { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
} from "@mui/material";
import GavelIcon from "@mui/icons-material/Gavel";
import { useNavigate } from "react-router-dom";
import { SignIn, useAuth } from "@clerk/clerk-react";
import api from "../services/api";

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

/**
 * Login page with dual auth support:
 * - If Clerk is configured (VITE_CLERK_PUBLISHABLE_KEY set): renders Clerk's <SignIn> component
 * - If Clerk is not configured: falls back to local JWT login/register forms
 */
const Login: React.FC = () => {
  const navigate = useNavigate();
  const clerkKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || "";

  // Clerk hooks (only active when Clerk is configured)
  const { isSignedIn, getToken } = useAuth();
  const [clerkLoading, setClerkLoading] = useState(false);

  // Local auth state
  const [tab, setTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Login form
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  // Register form
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const regRole = "user";

  // When Clerk signs in, exchange the token for our backend JWT
  useEffect(() => {
    if (clerkKey && isSignedIn && !localStorage.getItem("auth_token")) {
      exchangeClerkToken();
    }
  }, [isSignedIn, clerkKey]);

  const exchangeClerkToken = async () => {
    setClerkLoading(true);
    try {
      const clerkToken = await getToken();
      if (!clerkToken) {
        setError("Failed to get Clerk session token");
        return;
      }

      const response = await api.post("/auth/clerk-session", {
        clerk_token: clerkToken,
      });

      localStorage.setItem("auth_token", response.data.access_token);
      localStorage.setItem("user_email", response.data.email);
      localStorage.setItem("user_id", String(response.data.user_id));
      navigate("/");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Clerk session exchange failed");
    } finally {
      setClerkLoading(false);
    }
  };

  const handleLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post("/auth/login", {
        email: loginEmail,
        password: loginPassword,
      });
      localStorage.setItem("auth_token", response.data.access_token);
      localStorage.setItem("user_email", response.data.email);
      localStorage.setItem("user_id", String(response.data.user_id));
      navigate("/");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post("/auth/register", {
        email: regEmail,
        password: regPassword,
        role: regRole,
      });
      localStorage.setItem("auth_token", response.data.access_token);
      localStorage.setItem("user_email", response.data.email);
      localStorage.setItem("user_id", String(response.data.user_id));
      navigate("/");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: "80vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Paper sx={{ p: 4, maxWidth: clerkKey ? 480 : 440, width: "100%" }}>
        <Box sx={{ textAlign: "center", mb: 3 }}>
          <GavelIcon sx={{ fontSize: 48, color: "primary.main", mb: 1 }} />
          <Typography variant="h4" fontWeight={700}>
            PolicySight
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Your Policy, Decoded. Your Claim, Defended.
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {clerkLoading && (
          <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
            <CircularProgress />
            <Typography sx={{ ml: 2 }}>Signing in with Clerk...</Typography>
          </Box>
        )}

        {/* ── Clerk Auth Mode ── */}
        {clerkKey && !clerkLoading && (
          <SignIn
            routing="hash"
            signUpUrl="#/sign-up"
            appearance={{
              variables: { colorPrimary: "#1a237e" },
              elements: {
                card: {
                  boxShadow: "none",
                  border: "1px solid #e0e0e0",
                },
              },
            }}
            afterSignInUrl="/"
          />
        )}

        {/* ── Local Auth Mode (development fallback) ── */}
        {!clerkKey && (
          <>
            <Tabs value={tab} onChange={(_, v) => setTab(v)} centered>
              <Tab label="Login" />
              <Tab label="Register" />
            </Tabs>

            <TabPanel value={tab} index={0}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                sx={{ mb: 2 }}
              />
              <Button
                fullWidth
                variant="contained"
                size="large"
                onClick={handleLogin}
                disabled={!loginEmail || !loginPassword || loading}
              >
                {loading ? <CircularProgress size={24} /> : "Login"}
              </Button>
            </TabPanel>

            <TabPanel value={tab} index={1}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={regEmail}
                onChange={(e) => setRegEmail(e.target.value)}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={regPassword}
                onChange={(e) => setRegPassword(e.target.value)}
                sx={{ mb: 2 }}
              />
              <Button
                fullWidth
                variant="contained"
                size="large"
                onClick={handleRegister}
                disabled={!regEmail || !regPassword || loading}
              >
                {loading ? <CircularProgress size={24} /> : "Create Account"}
              </Button>
            </TabPanel>
          </>
        )}

        {clerkKey && (
          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 2, textAlign: "center" }}>
            Powered by Clerk — secure, hosted authentication
          </Typography>
        )}
      </Paper>
    </Box>
  );
};

export default Login;
