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
  Menu,
  MenuItem,
  useMediaQuery,
  useTheme,
  Divider,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import MoreVertIcon from "@mui/icons-material/MoreVert";
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

/* ── All nav items ── */
const ALL_NAV = [
  { label: "Home", path: "/", icon: <HomeIcon fontSize="small" /> },
  { label: "Decoder", path: "/decoder", icon: <PolicyIcon fontSize="small" /> },
  { label: "Claims", path: "/claims", icon: <GavelOutlinedIcon fontSize="small" /> },
  { label: "Forecast", path: "/trajectory", icon: <TrendingUpIcon fontSize="small" /> },
  { label: "Lapse Bridge", path: "/lapse", icon: <ShieldIcon fontSize="small" /> },
  { label: "Timeline", path: "/timeline", icon: <TimelineIcon fontSize="small" /> },
  { label: "Scenarios", path: "/scenario", icon: <ScienceIcon fontSize="small" /> },
  { label: "Claim Intake", path: "/intake", icon: <InputIcon fontSize="small" /> },
  { label: "Decisions", path: "/decision", icon: <BalanceIcon fontSize="small" /> },
  { label: "Audit", path: "/audit", icon: <AssessmentIcon fontSize="small" /> },
  { label: "Edge Cases", path: "/edge-cases", icon: <BugReportIcon fontSize="small" /> },
  { label: "Cost Estimator", path: "/cost-estimator", icon: <AttachMoneyIcon fontSize="small" /> },
  { label: "State Rules", path: "/states", icon: <MapIcon fontSize="small" /> },
  { label: "Feedback", path: "/feedback", icon: <FeedbackIcon fontSize="small" /> },
  { label: "Compare", path: "/compare", icon: <CompareIcon fontSize="small" /> },
  { label: "Copilot", path: "/copilot", icon: <SmartToyIcon fontSize="small" /> },
];

/* ── Always visible in the top bar ── */
const PRIMARY_NAV = ALL_NAV.filter((i) =>
  ["/", "/decoder", "/claims", "/trajectory", "/copilot"].includes(i.path)
);
/* ── Everything else goes in the "More" menu ── */
const MORE_NAV = ALL_NAV.filter((i) =>
  !["/", "/decoder", "/claims", "/trajectory", "/copilot"].includes(i.path)
);

const App: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem("auth_token"));
  const [userEmail, setUserEmail] = useState<string | null>(localStorage.getItem("user_email"));
  const [mobileOpen, setMobileOpen] = useState(false);
  const [moreAnchor, setMoreAnchor] = useState<null | HTMLElement>(null);

  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    setIsAuthenticated(!!token);
    setUserEmail(localStorage.getItem("user_email"));
  }, [location.pathname]);

  useEffect(() => {
    setMobileOpen(false);
    setMoreAnchor(null);
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

  /* ── Mobile drawer content ── */
  const drawerContent = (
    <Box sx={{ width: drawerWidth }}>
      <Box sx={{ p: 2, display: "flex", alignItems: "center", gap: 1 }}>
        <GavelIcon color="primary" />
        <Typography variant="subtitle1" fontWeight={700} color="primary.main">
          PolicySight
        </Typography>
      </Box>
      <Divider />
      <List dense>
        {ALL_NAV.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              component={Link}
              to={item.path}
              selected={location.pathname === item.path}
              sx={{
                py: 0.8,
                "&.Mui-selected": {
                  backgroundColor: "primary.main",
                  color: "white",
                  "&:hover": { backgroundColor: "primary.dark" },
                  "& .MuiListItemIcon-root": { color: "white" },
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 36 }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} primaryTypographyProps={{ fontSize: "0.85rem" }} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      {isAuthenticated && (
        <>
          <Divider />
          <Box sx={{ p: 2 }}>
            <Chip
              avatar={<Avatar sx={{ width: 24, height: 24, fontSize: "0.75rem" }}>{userEmail?.[0]?.toUpperCase() || "U"}</Avatar>}
              label={userEmail || "User"}
              variant="outlined"
              size="small"
              sx={{ maxWidth: "100%", fontSize: "0.75rem" }}
            />
            <Button fullWidth startIcon={<LogoutIcon />} onClick={handleLogout} sx={{ mt: 1, justifyContent: "flex-start" }} color="error" size="small">
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

      {/* ═══════════════ TOP BAR ═══════════════ */}
      <AppBar position="sticky" elevation={0} sx={{ borderBottom: "1px solid rgba(255,255,255,0.12)" }}>
        <Toolbar sx={{ minHeight: { xs: 44, sm: 48 }, px: { xs: 1, sm: 2 } }}>
          {/* Hamburger — opens full drawer on mobile, "More" menu on desktop */}
          {isAuthenticated && (
            <IconButton
              color="inherit"
              edge="start"
              size="small"
              onClick={(e) => {
                if (isMobile) setMobileOpen(true);
                else setMoreAnchor(e.currentTarget);
              }}
              sx={{ mr: 0.5 }}
            >
              <MenuIcon fontSize="small" />
            </IconButton>
          )}

          {/* Logo */}
          <GavelIcon sx={{ mr: 0.5, fontSize: "1.1rem" }} />
          <Typography
            variant="subtitle1"
            component={Link}
            to="/"
            noWrap
            sx={{
              textDecoration: "none",
              color: "inherit",
              fontWeight: 700,
              letterSpacing: 0.5,
              fontSize: { xs: "0.85rem", sm: "0.95rem" },
              mr: 1.5,
            }}
          >
            PolicySight
          </Typography>

          {/* Primary nav buttons — desktop only */}
          {isAuthenticated && !isMobile && (
            <Box sx={{ display: "flex", gap: 0, flexGrow: 1 }}>
              {PRIMARY_NAV.map((item) => {
                const active = location.pathname === item.path;
                return (
                  <Button
                    key={item.path}
                    color="inherit"
                    component={Link}
                    to={item.path}
                    size="small"
                    sx={{
                      fontSize: "0.75rem",
                      minWidth: "auto",
                      px: 1.2,
                      textTransform: "none",
                      fontWeight: active ? 600 : 400,
                      borderRadius: 0,
                      borderBottom: active ? "2px solid #fff" : "2px solid transparent",
                      opacity: active ? 1 : 0.85,
                      "&:hover": { opacity: 1, borderBottom: "2px solid rgba(255,255,255,0.5)" },
                    }}
                  >
                    {item.label}
                  </Button>
                );
              })}
              {/* More button */}
              <Button
                color="inherit"
                size="small"
                startIcon={<MoreVertIcon sx={{ fontSize: "0.9rem" }} />}
                onClick={(e) => setMoreAnchor(e.currentTarget)}
                sx={{
                  fontSize: "0.75rem",
                  minWidth: "auto",
                  px: 1.2,
                  textTransform: "none",
                  borderRadius: 0,
                  opacity: 0.85,
                  "&:hover": { opacity: 1 },
                }}
              >
                More
              </Button>
            </Box>
          )}

          {/* Spacer for mobile */}
          {(isMobile || !isAuthenticated) && <Box sx={{ flexGrow: 1 }} />}

          {/* Right side — user + logout */}
          {isAuthenticated ? (
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
              {!isMobile && (
                <Chip
                  avatar={<Avatar sx={{ width: 22, height: 22, fontSize: "0.7rem" }}>{userEmail?.[0]?.toUpperCase() || "U"}</Avatar>}
                  label={userEmail || "User"}
                  variant="outlined"
                  size="small"
                  sx={{ color: "white", borderColor: "rgba(255,255,255,0.3)", fontSize: "0.7rem", height: 26 }}
                />
              )}
              <IconButton color="inherit" onClick={handleLogout} size="small">
                <LogoutIcon fontSize="small" />
              </IconButton>
            </Box>
          ) : (
            <Button color="inherit" component={Link} to="/login" size="small" sx={{ fontSize: "0.8rem" }}>
              Login
            </Button>
          )}
        </Toolbar>
      </AppBar>

      {/* ═══════════════ "MORE" DROPDOWN (desktop) ═══════════════ */}
      <Menu
        anchorEl={moreAnchor}
        open={Boolean(moreAnchor)}
        onClose={() => setMoreAnchor(null)}
        PaperProps={{
          sx: { mt: 1, maxHeight: 400, width: 220 },
        }}
        transformOrigin={{ horizontal: "left", vertical: "top" }}
        anchorOrigin={{ horizontal: "left", vertical: "bottom" }}
      >
        {MORE_NAV.map((item) => (
          <MenuItem
            key={item.path}
            component={Link}
            to={item.path}
            selected={location.pathname === item.path}
            onClick={() => setMoreAnchor(null)}
            dense
            sx={{ py: 0.6, fontSize: "0.82rem" }}
          >
            <ListItemIcon sx={{ minWidth: 32 }}>{item.icon}</ListItemIcon>
            {item.label}
          </MenuItem>
        ))}
      </Menu>

      {/* ═══════════════ MOBILE DRAWER ═══════════════ */}
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
