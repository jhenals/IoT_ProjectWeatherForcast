/**
 * Session Handler for localhost:5173
 *
 * Uses an HTTP-only session cookie set by the API (localhost:8000).
 * This avoids sharing tokens via localStorage or URL parameters.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Initialize authentication on page load
 * Call this in your main App.vue or main.js
 */
export async function initializeAuth() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/auth/session-status`, {
      method: "GET",
      credentials: "include",
    });

    if (!res.ok) {
      console.log("❌ No valid session found");
      return false;
    }

    const session = await res.json();
    localStorage.setItem("userSession", JSON.stringify(session));
    localStorage.setItem("sessionSavedAt", new Date().toISOString());

    console.log("✅ Session restored from cookie");
    console.log("User:", session.email, "| Role:", session.role);
    return true;
  } catch (error) {
    console.error("Session check failed:", error);
    return false;
  }
}

/**
 * Get current user session
 */
export function getUserSession() {
  const session = localStorage.getItem("userSession");
  return session ? JSON.parse(session) : null;
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated() {
  const session = getUserSession();
  return !!(session && session.role === "admin");
}

/**
 * Redirect to login if not authenticated
 */
export function requireAuth() {
  if (!isAuthenticated()) {
    console.log("Not authenticated - redirecting to login");
    window.location.href = "http://localhost:5500/web-app/src/login.html";
    return false;
  }
  return true;
}

/**
 * Logout - clear session and redirect to login
 */
export function logout() {
  localStorage.removeItem("userSession");
  localStorage.removeItem("sessionSavedAt");

  fetch(`${API_BASE_URL}/api/auth/session-logout`, {
    method: "POST",
    credentials: "include",
  }).finally(() => {
    console.log("✅ Logged out");
    window.location.href = "http://localhost:5500/web-app/src/login.html";
  });
}
