import { useState } from "react";
import { LoginForm } from "./components/LoginForm";
import { Dashboard } from "./pages/Dashboard";

const STORAGE_KEY = "mct_access_token";

function App() {
  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem(STORAGE_KEY),
  );

  function handleLogin(newToken: string) {
    localStorage.setItem(STORAGE_KEY, newToken);
    setToken(newToken);
  }

  function handleSignOut() {
    localStorage.removeItem(STORAGE_KEY);
    setToken(null);
  }

  if (!token) {
    return <LoginForm onSubmit={handleLogin} />;
  }

  return <Dashboard token={token} onSignOut={handleSignOut} />;
}

export default App;
