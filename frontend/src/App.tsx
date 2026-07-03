import React from "react";
import { Routes, Route, Link } from "react-router-dom";
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Button,
  CssBaseline,
} from "@mui/material";
import GavelIcon from "@mui/icons-material/Gavel";
import PolicyDecoder from "./pages/PolicyDecoder";
import ClaimsAdvocate from "./pages/ClaimsAdvocate";
import Trajectory from "./pages/Trajectory";

const App: React.FC = () => {
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
              flexGrow: 1,
              textDecoration: "none",
              color: "inherit",
              fontWeight: 700,
              letterSpacing: 1,
            }}
          >
            PolicySight
          </Typography>
          <Button color="inherit" component={Link} to="/">
            Decoder
          </Button>
          <Button color="inherit" component={Link} to="/claims">
            Claims
          </Button>
          <Button color="inherit" component={Link} to="/trajectory">
            Forecast
          </Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Routes>
          <Route path="/" element={<PolicyDecoder />} />
          <Route path="/claims" element={<ClaimsAdvocate />} />
          <Route path="/trajectory" element={<Trajectory />} />
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