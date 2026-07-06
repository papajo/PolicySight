import React, { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Alert,
  CircularProgress,
} from "@mui/material";
import GavelIcon from "@mui/icons-material/Gavel";
import { useNavigate } from "react-router-dom";
import { SignIn, useAuth } from "@clerk/clerk-react";
import api from "../services/api";

/**
 * Clerk-powered login page.
 * Only rendered inside <ClerkProvider> when VITE_CLERK_PUBLISHABLE_KEY is set.
 */
const ClerkLogin: React.FC = () => {
  const navigate = useNavigate();
  const { isSignedIn, getToken } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // When Clerk signs in, exchange the token for our backend JWT
  useEffect(() => {
    if (isSignedIn && !localStorage.getItem("auth_token")) {
      exchangeClerkToken();
    }
  }, [isSignedIn]);

  const exchangeClerkToken = async () => {
    setLoading(true);
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
      <Paper sx={{ p: 4, maxWidth: 480, width: "100%" }}>
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

        {loading && (
          <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
            <CircularProgress />
            <Typography sx={{ ml: 2 }}>Signing in with Clerk...</Typography>
          </Box>
        )}

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

        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 2, textAlign: "center" }}>
          Powered by Clerk — secure, hosted authentication
        </Typography>
      </Paper>
    </Box>
  );
};

export default ClerkLogin;
