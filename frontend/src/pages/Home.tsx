import React from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Typography,
  Paper,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  Chip,
} from "@mui/material";
import DescriptionIcon from "@mui/icons-material/Description";
import GavelIcon from "@mui/icons-material/Gavel";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import ShieldIcon from "@mui/icons-material/Shield";

const modules = [
  {
    title: "Policy Decoder",
    icon: <DescriptionIcon sx={{ fontSize: 48 }} />,
    description:
      "Upload your SLIP document and get a plain-English breakdown of your coverage limits, deductibles, and hidden gaps.",
    path: "/decoder",
    color: "primary.main",
    chip: "Free",
  },
  {
    title: "Claims Advocate",
    icon: <GavelIcon sx={{ fontSize: 48 }} />,
    description:
      "Upload accident photos and get a professional-grade valuation. Compare your policy limits against the carrier's offer.",
    path: "/claims",
    color: "secondary.main",
    chip: "$99/claim",
  },
  {
    title: "Rate Trajectory",
    icon: <TrendingUpIcon sx={{ fontSize: 48 }} />,
    description:
      "See what your premium will be next year. Compare against market averages and get a 'Stay' or 'Switch' recommendation.",
    path: "/trajectory",
    color: "warning.main",
    chip: "$29/month",
  },
  {
    title: "Lapse Bridge",
    icon: <ShieldIcon sx={{ fontSize: 48 }} />,
    description:
      "Never let your coverage lapse. We monitor your renewal window and automatically bridge the gap if needed.",
    path: "/lapse",
    color: "error.main",
    chip: "Free",
  },
];

const Home: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Box>
      {/* Hero Section */}
      <Box sx={{ textAlign: "center", mb: { xs: 4, sm: 6 }, mt: 2 }}>
        <Typography variant="h3" gutterBottom fontWeight={700} sx={{ fontSize: { xs: "1.6rem", sm: "2.2rem", md: "3rem" } }}>
          Your Policy, Decoded.
          <br />
          Your Claim, Defended.
        </Typography>
        <Typography
          variant="h6"
          color="text.secondary"
          sx={{ maxWidth: 600, mx: "auto", mb: 3, px: { xs: 1, sm: 0 }, fontSize: { xs: "0.9rem", sm: "1.1rem" } }}
        >
          The first neutral, third-party tool that connects your Policy, Premium,
          and Claim into one intelligent dashboard.
        </Typography>
        <Box sx={{ display: "flex", gap: 2, justifyContent: "center", flexDirection: { xs: "column", sm: "row" }, alignItems: "center", px: { xs: 2, sm: 0 } }}>
          <Button
            variant="contained"
            size="large"
            fullWidth={false}
            onClick={() => navigate("/decoder")}
            sx={{ width: { xs: "100%", sm: "auto" } }}
          >
            Decode Your Policy
          </Button>
          <Button
            variant="outlined"
            size="large"
            fullWidth={false}
            onClick={() => navigate("/claims")}
            sx={{ width: { xs: "100%", sm: "auto" } }}
          >
            Analyze a Claim
          </Button>
        </Box>
      </Box>

      {/* Module Cards */}
      <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
        Core Modules
      </Typography>
      <Grid container spacing={3}>
        {modules.map((mod) => (
          <Grid item xs={12} sm={6} key={mod.title}>
            <Card
              onClick={() => navigate(mod.path)}
              sx={{
                height: "100%",
                display: "flex",
                flexDirection: "column",
                cursor: "pointer",
                transition: "transform 0.2s, box-shadow 0.2s",
                "&:hover": {
                  transform: "translateY(-4px)",
                  boxShadow: 4,
                },
              }}
            >
              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ color: mod.color, mb: 2 }}>{mod.icon}</Box>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                  <Typography variant="h5" component="div">
                    {mod.title}
                  </Typography>
                  <Chip label={mod.chip} size="small" color={mod.chip === "Free" ? "success" : "default"} />
                </Box>
                <Typography variant="body1" color="text.secondary">
                  {mod.description}
                </Typography>
              </CardContent>
              <CardActions>
                <Button size="small" onClick={(e) => { e.stopPropagation(); navigate(mod.path); }}>
                  Get Started
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Stats Section */}
      <Paper sx={{ mt: { xs: 4, sm: 6 }, p: { xs: 2, sm: 4 }, textAlign: "center" }}>
        <Typography variant="h5" gutterBottom sx={{ fontSize: { xs: "1.1rem", sm: "1.5rem" } }}>
          Why PolicySight?
        </Typography>
        <Grid container spacing={{ xs: 2, sm: 3 }} sx={{ mt: 1 }}>
          <Grid item xs={12} sm={4}>
            <Typography variant="h4" color="primary.main" fontWeight={700} sx={{ fontSize: { xs: "1.5rem", sm: "2.125rem" } }}>
              70%
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: "0.8rem", sm: "0.875rem" } }}>
              of consumers renew blindly without comparing coverage value
            </Typography>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography variant="h4" color="secondary.main" fontWeight={700} sx={{ fontSize: { xs: "1.5rem", sm: "2.125rem" } }}>
              $1,500+
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: "0.8rem", sm: "0.875rem" } }}>
              average legal fee saved by using AI claims advocacy
            </Typography>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography variant="h4" color="warning.main" fontWeight={700} sx={{ fontSize: { xs: "1.5rem", sm: "2.125rem" } }}>
              0%
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: "0.8rem", sm: "0.875rem" } }}>
              coverage gaps with our automated Lapse Bridge
            </Typography>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default Home;