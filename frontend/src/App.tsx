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
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  useMediaQuery,
  useTheme,
  Divider,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import GavelIcon from "@mui/icons-material/Gavel";
import LogoutIcon from "@mui/icons-material/Logout";
import HomeIcon from "@mui/icons-material/Home";
import PolicyIcon from "@mui/icons-material/Description";
import GavelOutlinedIcon from "@mui/icons-material/GavelOutlined";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import ShieldIcon from "@mui/icons-material/Shield";
import TimelineIcon from "@mui/icons-material/Timeline";
import ScienceIcon from "@mui/icons-material/Science";
import InputIcon from "@mui/icons-material/Input";
import BalanceIcon from "@mui/icons-material/Balance";
import AssessmentIcon from "@mui/icons-material/Assessment";
import BugReportIcon from "@mui/icons-material/BugReport";
import AttachMoneyIcon from "@mui/icons-material/AttachMoney";
import MapIcon from "@mui/icons-material/Map";
import FeedbackIcon from "@mui/icons-material/Feedback";
import CompareIcon from "@mui/icons-material/Compare";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import PolicyDecoder from "./pages/PolicyDecoder";
import ClaimsAdvocate from "./pages/ClaimsAdvocate";
import Trajectory from "./pages/Trajectory";
import Login from "./pages/Login";
import Home from "./pages/Home";
import LapseBridge from "./pages/LapseBridge";
import CoverageTimeline from "./pages/CoverageTimeline";
import ScenarioChecker from "./pages/ScenarioChecker";
import ClaimIntakeForm from "./pages/ClaimIntake";
import DecisionDraft from "./pages/DecisionDraft";
import AuditTrail from "./pages/AuditTrail";
import EdgeCaseClassifier from "./pages/EdgeCaseClassifier";
import CostEstimator from "./pages/CostEstimator";
import StateRules from "./pages/StateRules";
import FeedbackDashboard from "./pages/FeedbackLoop";
import PolicyComparison from "./pages/PolicyComparison";
import CopilotDashboard from "./pages/CopilotDashboard";
import PolicyChatWidget from "./components/PolicyChatWidget";

const NAV_ITEMS = [
  { label: "Home", path: "/", icon: <HomeIcon /> },
  { label: "Decoder", path: "/decoder", icon: <PolicyIcon /> },
  { label: "Claims", path: "/claims", icon: <GavelOutlinedIcon /> },
  { label: "Forecast", path: "/trajectory", icon: <TrendingUpIcon /> },
  { label: "Lapse Bridge", path: "/lapse", icon: <ShieldIcon /> },
  { label: "Timeline", path: "/timeline", icon: <TimelineIcon /> },
  { label: "Scenarios", path: "/scenario", icon: <ScienceIcon /> },
  { label: "Claim Intake", path: "/intake", icon: <InputIcon /> },
  { label: "Decisions", path: "/decision", icon: <BalanceIcon /> },
  { label: "Audit", path: "/audit", icon: <AssessmentIcon /> },
  { label: "Edge Cases", path: "/edge-cases", icon: <BugReportIcon /> },
  { label: "Cost Estimator", path: "/cost-estimator", icon: <AttachMoneyIcon /> },
  { label: "State Rules", path: "/states", icon: <MapIcon /> },
  { label: "Feedback", path: "/feedback", icon: <FeedbackIcon /> },
  { label: "Compare", path: "/compare", icon: <CompareIcon /> },
  { label: "Copilot", path: "/copilot", icon: <SmartToyIcon /> },
];

const App: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem("auth_token"));
  const [userEmail, setUserEmail] = useState<string | null>(localStorage.getItem("user_email"));
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    setIsAuthenticated(!!token);
    setUserEmail(localStorage.getItem("user_email"));
  }, [location.pathname]);

  // Close drawer on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("user_email");
    localStorage.removeItem("user_id");
    setIsAuthenticated(false);
    setUserEmail(null);
    navigate("/login");
  };

  const drawerWidth = 260;

  const drawerContent = (
    <Box sx={{ width: drawerWidth }}>
      <Box sx={{ p: 2, display: "flex", alignItems: "center", gap: 1 }}>
        <GavelIcon color="primary" />
        <Typography variant="h6" fontWeight={700} color="primary.main">
          PolicySight
        </Typography>
      </Box>
      <Divider />
      <List>
        {NAV_ITEMS.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              component={Link}
              to={item.path}
              selected={location.pathname === item.path}
              sx={{
                py: 1.2,
                "&.Mui-selected": {
                  backgroundColor: "primary.main",
                  color: "white",
                  "&:hover": { backgroundColor: "primary.dark" },
                  "& .MuiListItemIcon-root": { color: "white" },
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      {isAuthenticated && (
        <>
          <Divider />
          <Box sx={{ p: 2 }}>
            <Chip
              avatar={<Avatar sx={{ width: 28, height: 28 }}>{userEmail?.[0]?.toUpperCase() || "U"}</Avatar>}
              label={userEmail || "User"}
              variant="outlined"
              size="small"
              sx={{ maxWidth: "100%" }}
            />
            <Button
              fullWidth
              startIcon={<LogoutIcon />}
              onClick={handleLogout}
              sx={{ mt: 1.5, justifyContent: "flex-start" }}
              color="error"
            >
              Logout
            </Button>
          </Box>
        </>
      )}
    </Box>
  );

  return (
    <>
      <CssBaseline />
      <AppBar position="sticky" elevation={1}>
        <Toolbar>
          {isAuthenticated && (
            <IconButton
              color="inherit"
              edge="start"
              onClick={() => setMobileOpen(!mobileOpen)}
              sx={{ mr: 1 }}
            >
              <MenuIcon />
            </IconButton>
          )}
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
              mr: 2,
              fontSize: { xs: "0.95rem", sm: "1.1rem" },
            }}
          >
            PolicySight
          </Typography>

          {/* Desktop nav */}
          {isAuthenticated && !isMobile && (
            <Box sx={{ display: "flex", gap: 0, flexGrow: 1, flexWrap: "wrap" }}>
              {NAV_ITEMS.map((item) => (
                <Button
                  key={item.path}
                  color="inherit"
                  component={Link}
                  to={item.path}
                  sx={{
                    fontSize: "0.7rem",
                    minWidth: "auto",
                    px: 0.8,
                    py: 0.8,
                    whiteSpace: "nowrap",
                    fontWeight: location.pathname === item.path ? 700 : 400,
                    borderBottom: location.pathname === item.path ? "2px solid white" : "2px solid transparent",
                  }}
                >
                  {item.label}
                </Button>
              ))}
            </Box>
          )}

          {isAuthenticated && isMobile && <Box sx={{ flexGrow: 1 }} />}
          {!isAuthenticated && <Box sx={{ flexGrow: 1 }} />}

          {isAuthenticated ? (
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              {!isMobile && (
                <Chip
                  avatar={<Avatar>{userEmail?.[0]?.toUpperCase() || "U"}</Avatar>}
                  label={userEmail || "User"}
                  variant="outlined"
                  size="small"
                  sx={{ color: "white", borderColor: "rgba(255,255,255,0.5)" }}
                />
              )}
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

      {/* Mobile Drawer */}
      {isAuthenticated && (
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: "block", md: "none" },
            "& .MuiDrawer-paper": { boxSizing: "border-box", width: drawerWidth },
          }}
        >
          {drawerContent}
        </Drawer>
      )}

      <Container maxWidth="lg" sx={{ mt: { xs: 2, sm: 4 }, mb: { xs: 2, sm: 4 }, px: { xs: 1.5, sm: 3 } }}>
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
          <Route
            path="/scenario"
            element={isAuthenticated ? <ScenarioChecker standalone /> : <Login />}
          />
          <Route
            path="/intake"
            element={isAuthenticated ? <ClaimIntakeForm /> : <Login />}
          />
          <Route
            path="/decision"
            element={isAuthenticated ? <DecisionDraft /> : <Login />}
          />
          <Route
            path="/audit"
            element={isAuthenticated ? <AuditTrail /> : <Login />}
          />
          <Route
            path="/edge-cases"
            element={isAuthenticated ? <EdgeCaseClassifier standalone /> : <Login />}
          />
          <Route
            path="/cost-estimator"
            element={isAuthenticated ? <CostEstimator standalone /> : <Login />}
          />
          <Route
            path="/states"
            element={isAuthenticated ? <StateRules /> : <Login />}
          />
          <Route
            path="/feedback"
            element={isAuthenticated ? <FeedbackDashboard /> : <Login />}
          />
          <Route
            path="/compare"
            element={isAuthenticated ? <PolicyComparison /> : <Login />}
          />
          <Route
            path="/copilot"
            element={isAuthenticated ? <CopilotDashboard /> : <Login />}
          />
        </Routes>
      </Container>

      <PolicyChatWidget policyText="" />

      <Box
        component="footer"
        sx={{
          py: { xs: 2, sm: 3 },
          mt: "auto",
          backgroundColor: "background.paper",
          textAlign: "center",
          px: 2,
        }}
      >
        <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: "0.75rem", sm: "0.875rem" } }}>
          PolicySight — Your Policy, Decoded. Your Claim, Defended.
        </Typography>
      </Box>
    </>
  );
};

export default App;