import React, { useState, useEffect } from "react";
import { Routes, Route, Link, useNavigate, useLocation } from "react-router-dom";
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Button,
  CssBaseline,
  Chip,
  Avatar,
  Menu,
  MenuItem,
  IconButton,
} from "@mui/material";
import GavelIcon from "@mui/icons-material/Gavel";
import LogoutIcon from "@mui/icons-material/Logout";
import PolicyDecoder from "./pages/PolicyDecoder";
import ClaimsAdvocate from "./pages/ClaimsAdvocate";
import Trajectory from "./pages/Trajectory";
import Login from "./pages/Login";
import Home from "./pages/Home";
import LapseBridge from "./pages/LapseBridge";
import CoverageTimeline from "./pages/CoverageTimeline";

const App: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem("auth_token"));
  const [userEmail, setUserEmail] = useState<string | null>(localStorage.getItem("user_email"));
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    setIsAuthenticated(!!token);
    setUserEmail(localStorage.getItem("user_email"));
  }, [location.pathname]);

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user_email");
    localStorage.removeItem("user_id");
    setIsAuthenticated(false);
    setUserEmail(null);
    navigate("/login");
  };

  return (
    <>
      <CssBaseline />
      <AppBar position="sticky" elevation={1}>
        <Toolbar>
          <GavelIcon sx={{ mr: 1 }} />
          <Typography
            variant="h6"
            component={Link}
            to="/"
            sx={{
              textDecoration: "none",
              color: "inherit",
              fontWeight: 700,
              letterSpacing: 1,
              mr: 3,
            }}
          >
            PolicySight
          </Typography>

          {isAuthenticated && (
            <Box sx={{ display: "flex", gap: 1, flexGrow: 1 }}>
              <Button color="inherit" component={Link} to="/">
                Home
              </Button>
              <Button color="inherit" component={Link} to="/decoder">
                Decoder
              </Button>
              <Button color="inherit" component={Link} to="/claims">
                Claims
              </Button>
              <Button color="inherit" component={Link} to="/trajectory">
                Forecast
              </Button>
              <Button color="inherit" component={Link} to="/lapse">
                Lapse Bridge
              </Button>
              <Button color="inherit" component={Link} to="/timeline">
                Timeline
              </Button>
            </Box>
          )}

          {!isAuthenticated && (
            <Box sx={{ flexGrow: 1 }} />
          )}

          {isAuthenticated ? (
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <Chip
                avatar={<Avatar>{userEmail?.[0]?.toUpperCase() || "U"}</Avatar>}
                label={userEmail || "User"}
                variant="outlined"
                size="small"
                sx={{ color: "white", borderColor: "rgba(255,255,255,0.5)" }}
              />
              <IconButton color="inherit" onClick={handleLogout} size="small">
                <LogoutIcon />
              </IconButton>
            </Box>
          ) : (
            <Button color="inherit" component={Link} to="/login">
              Login
            </Button>
          )}
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Routes>
          <Route path="/" element={isAuthenticated ? <Home /> : <Login />} />
          <Route path="/login" element={<Login />} />
          <Route
            path="/decoder"
            element={isAuthenticated ? <PolicyDecoder /> : <Login />}
          />
          <Route
            path="/claims"
            element={isAuthenticated ? <ClaimsAdvocate /> : <Login />}
          />
          <Route
            path="/trajectory"
            element={isAuthenticated ? <Trajectory /> : <Login />}
          />
          <Route
            path="/lapse"
            element={isAuthenticated ? <LapseBridge /> : <Login />}
          />
          <Route
            path="/timeline"
            element={isAuthenticated ? <CoverageTimeline /> : <Login />}
          />
        </Routes>
      </Container>

      <Box
        component="footer"
        sx={{
          py: 3,
          mt: "auto",
          backgroundColor: "background.paper",
          textAlign: "center",
        }}
      >
        <Typography variant="body2" color="text.secondary">
          PolicySight — Your Policy, Decoded. Your Claim, Defended.
        </Typography>
      </Box>
    </>
  );
};

export default App;