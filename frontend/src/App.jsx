import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useEffect } from "react";

import AuthPage from "./pages/AuthPage";
import SearchPage from "./pages/SearchPage";
import SubmitPage from "./pages/SubmitPage"; 
import Tickets from "./pages/Tickets";
import Runbooks from "./pages/Runbooks";
import LogsPage from "./pages/LogsPage";
import ProtectedLayout from "./components/ProtectedLayout";

// Check if logged in using the same key auth uses
function isLoggedIn() {
  return !!localStorage.getItem("ams_user");
}

// Protected route: only for logged-in users
function ProtectedRoute({ children }) {
  return isLoggedIn() ? children : <Navigate to="/" replace />;
}

// Public route: redirect logged-in users away from login/register
function PublicRoute({ children }) {
  return isLoggedIn() ? <Navigate to="/search" replace /> : children;
}

export default function App() {

  return (
    <BrowserRouter>
      <Routes>
        {/* Public route: login/register */}
        <Route
          path="/"
          element={
            <PublicRoute>
              <AuthPage />
            </PublicRoute>
          }
        />

        {/* Protected routes wrapped with Sidebar layout */}
        <Route
          path="/search"
          element={
            <ProtectedRoute>
              <ProtectedLayout>
                <SearchPage />
              </ProtectedLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/submit"  // <--- added SubmitPage route
          element={
            <ProtectedRoute>
              <ProtectedLayout>
                <SubmitPage />
              </ProtectedLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/tickets"
          element={
            <ProtectedRoute>
              <ProtectedLayout>
                <Tickets />
              </ProtectedLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/runbooks"
          element={
            <ProtectedRoute>
              <ProtectedLayout>
                <Runbooks />
              </ProtectedLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/logs"
          element={
            <ProtectedRoute>
              <ProtectedLayout>
                <LogsPage />
              </ProtectedLayout>
            </ProtectedRoute>
          }
        />


        {/* Fallback: redirect any unknown route to login */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}