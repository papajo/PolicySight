import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "https://policysight-backend.fly.dev/api",
});

/**
 * Request interceptor for auth token.
 * When Clerk is configured, the frontend exchanges Clerk's JWT for a
 * PolicySight access token via /api/auth/clerk-session and stores it
 * in localStorage. This interceptor attaches that token to every request.
 *
 * If you need to use Clerk's raw token directly (e.g., for Clerk-hosted
 * endpoints), you can import @clerk/clerk-react's useAuth() in components
 * and pass the token explicitly via headers.
 */
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("auth_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * Response interceptor for error handling.
 * On 401, clear the local token so the app redirects to login.
 */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("user_email");
      localStorage.removeItem("user_id");
      // Optionally redirect to login
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
