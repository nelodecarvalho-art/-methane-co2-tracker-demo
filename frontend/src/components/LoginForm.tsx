import { FormEvent, useState } from "react";
import { API_BASE_URL, ApiError, demoLogin, login } from "../services/api";

interface LoginFormProps {
  onSubmit: (token: string) => void;
}

// Só true no build da demo pública (VITE_DEMO_MODE=true), nunca numa
// instalação real de cliente — ver frontend/.env.example. Não expõe mais
// credencial nenhuma aqui: o botão "Entrar como Visitante" chama
// /auth/demo-login no backend, que emite o token sem senha nenhuma
// trafegando (e sem existir se DEMO_ACCOUNT_EMAIL não estiver configurado
// no backend).
const DEMO_MODE = import.meta.env.VITE_DEMO_MODE === "true";

export function LoginForm({ onSubmit }: LoginFormProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await login(email.trim(), password);
      onSubmit(result.access_token);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError("E-mail ou senha inválidos.");
      } else {
        setError("Falha ao conectar à API. Verifique se o backend está no ar.");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleDemoLogin() {
    setLoading(true);
    setError(null);
    try {
      const result = await demoLogin();
      onSubmit(result.access_token);
    } catch {
      setError("Não foi possível entrar como visitante agora.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="login-form" onSubmit={handleSubmit}>
      <h1>Methane &amp; CO2 Tracker</h1>
      <p>Entre com seu e-mail e senha para acessar o dashboard.</p>
      {DEMO_MODE && (
        <p className="login-form__demo-hint">Esta é uma demonstração pública com dados fictícios.</p>
      )}
      <input
        type="email"
        placeholder="E-mail"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        autoFocus
        required
      />
      <input
        type="password"
        placeholder="Senha"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      <button type="submit" disabled={loading}>
        {loading ? "Entrando..." : "Entrar"}
      </button>
      {DEMO_MODE && (
        <button type="button" onClick={handleDemoLogin} disabled={loading} className="login-form__demo-button">
          Entrar como Visitante
        </button>
      )}
      {error && <p className="error-banner">{error}</p>}
      <p className="login-form__hint">API: {API_BASE_URL}</p>
    </form>
  );
}
