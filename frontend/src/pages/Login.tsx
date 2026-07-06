import React from "react";
import LoginRouter from "./LoginRouter";

/**
 * Login page — delegates to either Clerk or local auth based on config.
 * ClerkProvider wraps the app in main.tsx when VITE_CLERK_PUBLISHABLE_KEY is set,
 * so ClerkLogin (which uses useAuth) is always inside the provider.
 */
const Login: React.FC = () => {
  return <LoginRouter />;
};

export default Login;
