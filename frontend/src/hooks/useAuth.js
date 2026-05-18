import { useState, useEffect } from "react";
import { auth } from "../utils/auth";

export function useAuth() {
  const [user, setUser] = useState(() => auth.getUser());

  // sync on mount + tab changes
  useEffect(() => {
    const syncUser = () => {
      setUser(auth.getUser());
    };

    window.addEventListener("storage", syncUser);
    return () => window.removeEventListener("storage", syncUser);
  }, []);

  function login(email, password) {
    const res = auth.login(email, password);
    const updatedUser = auth.getUser(); // always trust storage
    setUser(updatedUser);
    return res;
  }

  function logout() {
    auth.logout();
    setUser(null);
  }

  return { user, login, logout };
}