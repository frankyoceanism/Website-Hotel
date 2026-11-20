import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { api } from "../api.js";
import Auth from "../components/authentification/auth.jsx";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const [authOpen, setAuthOpen] = useState(false);
  const [afterLogin, setAfterLogin] = useState(null); // tujuan setelah login berhasil

  const navigate = useNavigate();

  // Cek sesi login sekali saat website pertama dibuka
  useEffect(() => {
    let batal = false;

    api
      .me()
      .then((res) => {
        if (!batal) setUser(res.loggedIn ? res.user : null);
      })
      .catch(() => {
        if (!batal) setUser(null);
      })
      .finally(() => {
        if (!batal) setLoading(false);
      });

    return () => {
      batal = true;
    };
  }, []);

  // Buka dialog login. redirectTo = halaman tujuan setelah login (opsional)
  const openAuth = useCallback((redirectTo = null) => {
    setAfterLogin(redirectTo);
    setAuthOpen(true);
  }, []);

  const closeAuth = useCallback(() => setAuthOpen(false), []);

  const handleLoginSuccess = (loggedUser) => {
    setUser(loggedUser);

    if (loggedUser.role === "admin") {
      navigate("/admin");
    } else if (afterLogin) {
      navigate(afterLogin);
    }
  };

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      setUser(null);
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, openAuth, logout }}>
      {children}

      <Auth open={authOpen} onClose={closeAuth} onSuccess={handleLoginSuccess} />
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error();
  return ctx;
}