import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ReadingOut } from "../services/api";

interface ChartRow {
  time: string;
  CH4?: number;
  CH4Anomaly?: boolean;
  CO2?: number;
  CO2Anomaly?: boolean;
}

function pivotByTime(readings: ReadingOut[]): ChartRow[] {
  const byTime = new Map<string, ChartRow>();
  const sorted = [...readings].sort((a, b) => a.time.localeCompare(b.time));

  for (const reading of sorted) {
    const row = byTime.get(reading.time) ?? { time: reading.time };
    if (reading.gas_type === "CH4") {
      row.CH4 = reading.concentration_ppm;
      row.CH4Anomaly = reading.is_anomaly;
    } else if (reading.gas_type === "CO2") {
      row.CO2 = reading.concentration_ppm;
      row.CO2Anomaly = reading.is_anomaly;
    }
    byTime.set(reading.time, row);
  }

  return Array.from(byTime.values());
}

const ANOMALY_COLOR = "#a61e1e";

interface AnomalyDotProps {
  cx?: number;
  cy?: number;
  payload?: ChartRow;
}

// Marca com um ponto vermelho só as leituras que o Isolation Forest
// (backend/app/anomaly/detector.py) sinalizou; as demais ficam sem marcador,
// mantendo a linha limpa.
function anomalyDot(anomalyKey: "CH4Anomaly" | "CO2Anomaly") {
  return ({ cx, cy, payload }: AnomalyDotProps) => {
    if (!payload?.[anomalyKey] || cx === undefined || cy === undefined) {
      return <circle cx={cx ?? 0} cy={cy ?? 0} r={0} />;
    }
    return <circle cx={cx} cy={cy} r={5} fill={ANOMALY_COLOR} stroke="#fff" strokeWidth={1} />;
  };
}

interface ReadingsChartProps {
  readings: ReadingOut[];
}

export function ReadingsChart({ readings }: ReadingsChartProps) {
  if (readings.length === 0) {
    return <p className="empty-state">Sem leituras no período selecionado.</p>;
  }

  const data = pivotByTime(readings);
  const hasAnomalies = data.some((row) => row.CH4Anomaly || row.CO2Anomaly);

  return (
    <>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="time"
            tickFormatter={(value: string) => new Date(value).toLocaleTimeString()}
          />
          <YAxis label={{ value: "ppm", angle: -90, position: "insideLeft" }} />
          <Tooltip labelFormatter={(value) => new Date(value as string).toLocaleString()} />
          <Legend />
          <Line type="monotone" dataKey="CH4" stroke="#2f9e44" dot={anomalyDot("CH4Anomaly")} connectNulls />
          <Line type="monotone" dataKey="CO2" stroke="#e8590c" dot={anomalyDot("CO2Anomaly")} connectNulls />
        </LineChart>
      </ResponsiveContainer>
      {hasAnomalies && (
        <p className="chart-legend-note">
          <span className="chart-legend-note__dot" /> leitura marcada como anomalia pelo detector
        </p>
      )}
    </>
  );
}
