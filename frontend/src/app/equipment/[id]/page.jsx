"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { equipmentAPI, sensorAPI, predictionAPI, createSensorWebSocket } from "@/lib/api";
import SensorChart from "@/components/SensorChart";
import RiskGauge from "@/components/RiskGauge";
import { StatusBadge, RiskBadge } from "@/components/StatusBadge";
import { PageSpinner } from "@/components/Loading";
import { formatDate } from "@/lib/utils";
import {
  ArrowLeftIcon,
  BoltIcon,
  CpuChipIcon,
  ExclamationTriangleIcon,
  SignalIcon,
  ClockIcon,
} from "@heroicons/react/24/outline";

export default function EquipmentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [equipment, setEquipment] = useState(null);
  const [sensorData, setSensorData] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [predicting, setPredicting] = useState(false);
  const [predictError, setPredictError] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const eqRes = await equipmentAPI.get(params.id);
        setEquipment(eqRes.data);
        const [sensorRes, predRes] = await Promise.allSettled([
          sensorAPI.query(params.id, { limit: 100 }),
          predictionAPI.history(params.id, { limit: 20 }),
        ]);
        if (sensorRes.status === "fulfilled") {
          const sd = sensorRes.value.data;
          setSensorData(sd.items || sd || []);
        }
        if (predRes.status === "fulfilled") {
          const pd = predRes.value.data;
          setPredictions(pd.items || pd || []);
        }
      } catch (err) {
        setError(err.message || "Failed to load equipment details");
      } finally {
        setLoading(false);
      }
    }
    load();

    // Listen for real-time sensor readings and automatic ML predictions
    const ws = createSensorWebSocket((msg) => {
      if (msg?.type === "prediction" && msg.equipment_id === params.id) {
        setPredictions((prev) => {
          // Prevent duplicates by checking timestamp
          if (prev.length > 0 && prev[0].timestamp === msg.timestamp) return prev;
          return [msg, ...prev].slice(0, 20);
        });
      } else if (msg?.type === "sensor_reading" && msg.data?.equipment_id === params.id) {
        setSensorData((prev) => [...prev, msg.data].slice(-100));
      }
    });

    return () => {
      ws.close();
    };
  }, [params.id]);

  const handlePredict = async () => {
    setPredicting(true);
    try {
      let sensorPayload = {};
      try {
        const { data: latest } = await sensorAPI.latest(params.id);
        sensorPayload = {
          air_temperature: latest.air_temperature ?? 300,
          process_temperature: latest.process_temperature ?? 310,
          rotational_speed: latest.rotational_speed ?? 1500,
          torque: latest.torque ?? 40,
          tool_wear: latest.tool_wear ?? 100,
          vibration: latest.vibration ?? 5.0,
        };
      } catch {
        sensorPayload = {
          air_temperature: 300, process_temperature: 310,
          rotational_speed: 1500, torque: 40, tool_wear: 100, vibration: 5.0,
        };
      }
      const { data } = await predictionAPI.predict(params.id, sensorPayload);
      setPredictions((prev) => [data, ...prev]);
    } catch (err) {
      setPredictError(err.message || "Prediction failed");
    } finally {
      setPredicting(false);
    }
  };

  if (loading) return <PageSpinner />;
  if (error) {
    return (
      <div className="card empty-state py-16">
        <ExclamationTriangleIcon className="h-10 w-10 text-red-300 mx-auto mb-3" />
        <p className="font-medium text-slate-500">{error}</p>
        <button onClick={() => router.back()} className="btn-secondary mt-4 text-sm">Go Back</button>
      </div>
    );
  }
  if (!equipment) {
    return (
      <div className="card empty-state py-16">
        <CpuChipIcon className="h-10 w-10 text-slate-300 mx-auto mb-3" />
        <p className="font-medium text-slate-500">Equipment not found</p>
      </div>
    );
  }

  const latestPred = predictions[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-4">
        <button
          onClick={() => router.back()}
          className="self-start p-2 rounded-xl hover:bg-slate-100 transition-colors"
        >
          <ArrowLeftIcon className="h-5 w-5 text-slate-400" />
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="page-title truncate">{equipment.name}</h1>
            <StatusBadge status={equipment.status || "operational"} />
          </div>
          <p className="page-subtitle">
            {equipment.equipment_type?.replace(/_/g, " ")} •{" "}
            {equipment.location || "No location set"}
          </p>
        </div>
        <button
          onClick={() => { setPredictError(null); handlePredict(); }}
          disabled={predicting}
          className="btn-primary shrink-0"
        >
          <BoltIcon className="h-4 w-4" />
          {predicting ? "Analyzing..." : "Run Prediction"}
        </button>
      </div>

      {predictError && (
        <div className="rounded-lg bg-red-50 border border-red-100 px-4 py-3 text-sm text-red-600">
          {predictError}
        </div>
      )}

      {/* Overview cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Equipment Info */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <CpuChipIcon className="h-4 w-4 text-brand-500" />
            <h3 className="section-title">Equipment Details</h3>
          </div>
          <dl className="space-y-3 text-sm">
            {[
              ["Type", equipment.equipment_type?.replace(/_/g, " ")],
              ["Model", equipment.model_number],
              ["Serial", equipment.serial_number],
              ["Installed", formatDate(equipment.installation_date)],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between items-center">
                <dt className="text-slate-400">{label}</dt>
                <dd className="font-medium text-slate-700 capitalize">{value || "—"}</dd>
              </div>
            ))}
          </dl>
        </div>

        {/* Risk Gauge */}
        <div className="card flex flex-col items-center justify-center">
          <h3 className="section-title mb-4">Current Risk Level</h3>
          {latestPred ? (
            <>
              <RiskGauge
                value={(latestPred.failure_probability || 0) * 100}
                size={140}
                label="Failure Risk"
              />
              <div className="mt-4 space-y-1.5 text-center">
                <RiskBadge
                  level={latestPred.risk_level}
                  probability={latestPred.failure_probability}
                />
                <p className="text-2xs text-slate-400">
                  Type: {latestPred.failure_type?.replace(/_/g, " ") || "—"}
                </p>
              </div>
            </>
          ) : (
            <div className="empty-state py-6">
              <p className="text-sm text-slate-400">No prediction data</p>
            </div>
          )}
        </div>

        {/* Latest Sensor Reading */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <SignalIcon className="h-4 w-4 text-cyan-500" />
            <h3 className="section-title">Latest Sensor Data</h3>
          </div>
          {sensorData.length > 0 ? (
            <dl className="space-y-3 text-sm">
              {[
                ["Air Temp", "air_temperature", "K"],
                ["Process Temp", "process_temperature", "K"],
                ["RPM", "rotational_speed", "rpm"],
                ["Torque", "torque", "Nm"],
                ["Tool Wear", "tool_wear", "min"],
                ["Vibration", "vibration", "mm/s"],
              ].map(([label, key, unit]) => (
                <div key={key} className="flex justify-between items-center">
                  <dt className="text-slate-400">{label}</dt>
                  <dd className="font-medium text-slate-700 tabular-nums">
                    {sensorData[sensorData.length - 1]?.[key] !== undefined
                      ? `${Number(sensorData[sensorData.length - 1][key]).toFixed(1)} ${unit}`
                      : "—"}
                  </dd>
                </div>
              ))}
            </dl>
          ) : (
            <div className="empty-state py-6">
              <p className="text-sm text-slate-400">No sensor data</p>
            </div>
          )}
        </div>
      </div>

      {/* Sensor Charts */}
      <div className="card">
        <div className="flex items-center gap-2.5 mb-4">
          <BoltIcon className="h-5 w-5 text-cyan-500" />
          <h2 className="section-title">Sensor History</h2>
        </div>
        <SensorChart
          data={sensorData}
          sensors={["air_temperature", "process_temperature", "rotational_speed", "torque"]}
          height={320}
        />
      </div>

      {/* Prediction History */}
      <div className="card">
        <div className="flex items-center gap-2.5 mb-4">
          <ClockIcon className="h-5 w-5 text-violet-500" />
          <h2 className="section-title">Prediction History</h2>
        </div>
        {predictions.length > 0 ? (
          <div className="overflow-x-auto -mx-5">
            <table className="w-full text-sm min-w-[640px]">
              <thead>
                <tr>
                  <th className="table-header pl-5">Time</th>
                  <th className="table-header">Risk</th>
                  <th className="table-header">Probability</th>
                  <th className="table-header">Failure Type</th>
                  <th className="table-header pr-5">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {predictions.map((pred, idx) => (
                  <tr key={pred.id || idx} className="table-row">
                    <td className="table-cell pl-5 text-slate-500">{formatDate(pred.timestamp)}</td>
                    <td className="table-cell"><RiskBadge level={pred.risk_level} /></td>
                    <td className="table-cell font-medium tabular-nums">
                      {((pred.failure_probability || 0) * 100).toFixed(1)}%
                    </td>
                    <td className="table-cell capitalize text-slate-600">
                      {pred.failure_type?.replace(/_/g, " ") || "—"}
                    </td>
                    <td className="table-cell pr-5 font-medium tabular-nums">
                      {((pred.confidence || 0) * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state py-8">
            <p className="text-sm text-slate-400">No predictions yet. Click &quot;Run Prediction&quot; above.</p>
          </div>
        )}
      </div>
    </div>
  );
}
