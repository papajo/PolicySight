import React from "react";
import ClerkLogin from "./ClerkLogin";
import LocalLogin from "./LocalLogin";

const clerkKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY || "";

/**
 * Routes to the correct login page based on Clerk configuration.
 * - If VITE_CLERK_PUBLISHABLE_KEY is set → renders ClerkLogin (inside ClerkProvider)
 * - Otherwise → renders LocalLogin (local JWT)
 *
 * IMPORTANT: ClerkLogin uses useAuth() which requires ClerkProvider.
 * Since ClerkProvider wraps the entire app in main.tsx when the key is set,
 * ClerkLogin is always inside the provider.
 */
const LoginRouter: React.FC = () => {
  if (clerkKey) {
    return <ClerkLogin />;
  }
  return <LocalLogin />;
};

export default LoginRouter;
