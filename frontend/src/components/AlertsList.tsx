import { AlertOut } from "../services/api";

interface AlertsListProps {
  alerts: AlertOut[];
}

export function AlertsList({ alerts }: AlertsListProps) {
  if (alerts.length === 0) {
    return <p className="empty-state">Nenhum alerta no período selecionado.</p>;
  }

  return (
    <table className="alerts-table">
      <thead>
        <tr>
          <th>Sensor</th>
          <th>Gás</th>
          <th>Início</th>
          <th>Status</th>
          <th>Máx. (ppm)</th>
          <th>Notificado</th>
        </tr>
      </thead>
      <tbody>
        {alerts.map((alert) => (
          <tr key={alert.id} className={`alerts-table__row--${alert.status}`}>
            <td>{alert.sensor_id}</td>
            <td>{alert.gas_type}</td>
            <td>{new Date(alert.started_at).toLocaleString()}</td>
            <td>{alert.status}</td>
            <td>{alert.max_ppm}</td>
            <td>{alert.notified_at ? "sim" : "não"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
