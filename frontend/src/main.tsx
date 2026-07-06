import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { ThemeProvider, createTheme, CssBaseline } from "@mui/material";
import { ClerkProvider } from "@clerk/clerk-react";
import App from "./App";

const clerkPubKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || "";

const theme = createTheme({
  palette: {
    primary: {
      main: "#1a237e", // Deep navy blue
    },
    secondary: {
      main: "#00897b", // Teal
    },
    background: {
      default: "#f5f5f5",
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h3: {
      fontWeight: 700,
      fontSize: "2rem",
      "@media (min-width:600px)": { fontSize: "2.5rem" },
      "@media (min-width:900px)": { fontSize: "3rem" },
    },
    h4: {
      fontWeight: 600,
      fontSize: "1.5rem",
      "@media (min-width:600px)": { fontSize: "1.75rem" },
      "@media (min-width:900px)": { fontSize: "2.125rem" },
    },
    h5: {
      fontWeight: 600,
    },
  },
  components: {
    MuiContainer: {
      styleOverrides: {
        root: {
          paddingLeft: 16,
          paddingRight: 16,
          "@media (min-width:600px)": { paddingLeft: 24, paddingRight: 24 },
        },
      },
    },
  },
});

/**
 * ClerkProvider wraps the app when VITE_CLERK_PUBLISHABLE_KEY is set.
 * In development (no key), the app falls back to local JWT auth.
 */
const Root: React.FC = () => {
  const content = (
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <App />
      </ThemeProvider>
    </BrowserRouter>
  );

  if (clerkPubKey) {
    return (
      <ClerkProvider publishableKey={clerkPubKey} appearance={{
        variables: { colorPrimary: "#1a237e" },
      }}>
        {content}
      </ClerkProvider>
    );
  }

  return content;
};

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);
