import React, { useState } from "react";
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

const Login: React.FC = () => {
  const navigate = useNavigate();
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
      <Paper sx={{ p: 4, maxWidth: 440, width: "100%" }}>
        <Box sx={{ textAlign: "center", mb: 3 }}>
          <GavelIcon sx={{ fontSize: 48, color: "primary.main", mb: 1 }} />
          <Typography variant="h4" fontWeight={700}>
            PolicySight
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Your Policy, Decoded. Your Claim, Defended.
          </Typography>
        </Box>

        <Tabs value={tab} onChange={(_, v) => setTab(v)} centered>
          <Tab label="Login" />
          <Tab label="Register" />
        </Tabs>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

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
      </Paper>
    </Box>
  );
};

export default Login;