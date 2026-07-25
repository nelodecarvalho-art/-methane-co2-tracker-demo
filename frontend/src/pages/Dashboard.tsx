import { useCallback, useEffect, useState } from "react";
import { AlertsList } from "../components/AlertsList";
import { ComplianceReportPanel } from "../components/ComplianceReportPanel";
import { ReadingsChart } from "../components/ReadingsChart";
import { AlertOut, ApiError, ReadingOut, fetchAlerts, fetchReadings } from "../services/api";

interface DashboardProps {
  token: string;
  onSignOut: () => void;
}

export function Dashboard({ token, onSignOut }: DashboardProps) {
  const [readings, setReadings] = useState<ReadingOut[]>([]);
  const [alerts, setAlerts] = useState<AlertOut[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [readingsPage, alertsPage] = await Promise.all([
        fetchReadings(token, { limit: "200" }),
        fetchAlerts(token, { limit: "50" }),
      ]);
      setReadings(readingsPage.items);
      setAlerts(alertsPage.items);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        onSignOut(); // token expirado/inválido — volta pro login
      } else {
        setError("Falha ao carregar dados da API. Verifique se o backend está no ar.");
      }
    } finally {
      setLoading(false);
    }
  }, [token, onSignOut]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="dashboard">
      <header className="dashboard__header">
        <h1>Methane &amp; CO2 Tracker</h1>
        <div className="dashboard__actions">
          <button onClick={() => void load()} disabled={loading}>
            {loading ? "Atualizando..." : "Atualizar"}
          </button>
          <button onClick={onSignOut} className="dashboard__signout">
            Sair
          </button>
        </div>
      </header>

      {error && <p className="error-banner">{error}</p>}

      <section>
        <h2>Leituras recentes</h2>
        <ReadingsChart readings={readings} />
      </section>

      <section>
        <h2>Eventos de alerta</h2>
        <AlertsList alerts={alerts} />
      </section>

      <section>
        <h2>Relatório de compliance ANP/EPA</h2>
        <ComplianceReportPanel token={token} onAuthError={onSignOut} />
      </section>
    </div>
  );
}
