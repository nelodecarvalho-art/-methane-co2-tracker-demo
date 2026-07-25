import { FormEvent, useState } from "react";
import { ApiError, fetchComplianceReportPdf } from "../services/api";

interface ComplianceReportPanelProps {
  token: string;
  onAuthError: () => void;
}

function isoWithTime(date: string, endOfDay: boolean): string {
  return `${date}T${endOfDay ? "23:59:59" : "00:00:00"}Z`;
}

function defaultDate(daysAgo: number): string {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - daysAgo);
  return d.toISOString().slice(0, 10);
}

export function ComplianceReportPanel({ token, onAuthError }: ComplianceReportPanelProps) {
  const [start, setStart] = useState(() => defaultDate(30));
  const [end, setEnd] = useState(() => defaultDate(0));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const blob = await fetchComplianceReportPdf(token, {
        start: isoWithTime(start, false),
        end: isoWithTime(end, true),
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `relatorio-compliance-${start}-a-${end}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        setError("Período inválido: a data final deve ser posterior à inicial.");
      } else if (err instanceof ApiError && err.status === 401) {
        onAuthError(); // token expirado/inválido — volta pro login
      } else {
        setError("Falha ao gerar o relatório. Verifique se o backend está no ar.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="compliance-report" onSubmit={handleSubmit}>
      <div className="compliance-report__fields">
        <label>
          De
          <input
            type="date"
            value={start}
            max={end}
            onChange={(e) => setStart(e.target.value)}
            required
          />
        </label>
        <label>
          Até
          <input
            type="date"
            value={end}
            min={start}
            onChange={(e) => setEnd(e.target.value)}
            required
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "Gerando..." : "Gerar relatório PDF"}
        </button>
      </div>
      {error && <p className="error-banner">{error}</p>}
      <p className="login-form__hint">
        Artefato de apoio ao processo de compliance ANP/EPA do operador — não é uma
        submissão regulatória pronta.
      </p>
    </form>
  );
}
