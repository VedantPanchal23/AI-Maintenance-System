"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { equipmentAPI, sensorAPI, predictionAPI } from "@/lib/api";
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
} from "@heroicons/react/24/outline";

export default function EquipmentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [equipment, setEquipment] = useState(null);
  const [sensorData, setSensorData] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [predicting, setPredicting] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [eqRes, sensorRes, predRes] = await Promise.all([
          equipmentAPI.get(params.id),
          sensorAPI.query(params.id, { limit: 100 }),
          predictionAPI.history(params.id, { limit: 20 }),
        ]);
        setEquipment(eqRes.data);
        setSensorData(sensorRes.data.items || sensorRes.data || []);
        setPredictions(predRes.data.items || predRes.data || []);
      } catch (err) {
        console.error("Failed to load equipment:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [params.id]);

  const handlePredict = async () => {
    setPredicting(true);
    try {
      // Get latest sensor reading for this equipment
      let sensorPayload = {};
      try {
        const { data: latest } = await sensorAPI.latest(params.id);
        sensorPayload = {
          air_temperature: latest.air_temperature || 300,
          process_temperature: latest.process_temperature || 310,
          rotational_speed: latest.rotational_speed || 1500,
          torque: latest.torque || 40,
          tool_wear: latest.tool_wear || 100,
          vibration: latest.vibration || 5.0,
        };
      } catch {
        // Use defaults if no sensor data available
        sensorPayload = {
          air_temperature: 300,
          process_temperature: 310,
          rotational_speed: 1500,
          torque: 40,
          tool_wear: 100,
          vibration: 5.0,
        };
      }
      const { data } = await predictionAPI.predict(params.id, sensorPayload);
      setPredictions((prev) => [data, ...prev]);
    } catch (err) {
      console.error("Prediction failed:", err);
    } finally {
      setPredicting(false);
    }
  };

  if (loading) return <PageSpinner />;
  if (!equipment) {
    return (
      <div className="card text-center py-12">
        <p className="text-slate-500">Equipment not found</p>
      </div>
    );
  }

  const latestPred = predictions[0];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.back()}
          className="p-2 rounded-lg hover:bg-slate-100"
        >
          <ArrowLeftIcon className="h-5 w-5 text-slate-500" />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-slate-900">
            {equipment.name}
          </h1>
          <p className="text-sm text-slate-500">
            {equipment.equipment_type?.replace(/_/g, " ")} •{" "}
            {equipment.location || "—"}
          </p>
        </div>
        <StatusBadge status={equipment.status || "operational"} />
        <button
          onClick={handlePredict}
          disabled={predicting}
          className="btn-primary"
        >
          {predicting ? "Analyzing..." : "Run Prediction"}
        </button>
      </div>

      {/* Overview cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Equipment Info */}
        <div className="card">
          <h3 className="text-sm font-semibold text-slate-900 mb-3">
            Equipment Details
          </h3>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate-500">Type</dt>
              <dd className="font-medium capitalize">
                {equipment.equipment_type?.replace(/_/g, " ")}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Model</dt>
              <dd className="font-medium">{equipment.model || "—"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Serial</dt>
              <dd className="font-medium">{equipment.serial_number || "—"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Installed</dt>
              <dd className="font-medium">
                {formatDate(equipment.installation_date)}
              </dd>
            </div>
          </dl>
        </div>

        {/* Risk Gauge */}
        <div className="card flex flex-col items-center justify-center">
          <h3 className="text-sm font-semibold text-slate-900 mb-3">
            Current Risk Level
          </h3>
          {latestPred ? (
            <>
              <div className="relative">
                <RiskGauge
                  value={(latestPred.failure_probability || 0) * 100}
                  size={140}
                  label="Failure Risk"
                />
              </div>
              <div className="mt-3 space-y-1 text-center">
                <RiskBadge
                  level={latestPred.risk_level}
                  probability={latestPred.failure_probability}
                />
                <p className="text-xs text-slate-500">
                  Type: {latestPred.failure_type?.replace(/_/g, " ") || "—"}
                </p>
              </div>
            </>
          ) : (
            <p className="text-sm text-slate-400">No prediction data</p>
          )}
        </div>

        {/* Latest Sensor Reading */}
        <div className="card">
          <h3 className="text-sm font-semibold text-slate-900 mb-3">
            Latest Sensor Data
          </h3>
          {sensorData.length > 0 ? (
            <dl className="space-y-2 text-sm">
              {[
                ["Air Temp", "air_temperature", "K"],
                ["Process Temp", "process_temperature", "K"],
                ["RPM", "rotational_speed", "rpm"],
                ["Torque", "torque", "Nm"],
                ["Tool Wear", "tool_wear", "min"],
                ["Vibration", "vibration", "mm/s"],
              ].map(([label, key, unit]) => (
                <div key={key} className="flex justify-between">
                  <dt className="text-slate-500">{label}</dt>
                  <dd className="font-medium">
                    {sensorData[sensorData.length - 1]?.[key] !== undefined
                      ? `${Number(sensorData[sensorData.length - 1][key]).toFixed(1)} ${unit}`
                      : "—"}
                  </dd>
                </div>
              ))}
            </dl>
          ) : (
            <p className="text-sm text-slate-400">No sensor data</p>
          )}
        </div>
      </div>

      {/* Sensor Charts */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <BoltIcon className="h-5 w-5 text-cyan-500" />
          <h2 className="text-sm font-semibold text-slate-900">
            Sensor History
          </h2>
        </div>
        <SensorChart
          data={sensorData}
          sensors={[
            "air_temperature",
            "process_temperature",
            "rotational_speed",
            "torque",
          ]}
          height={320}
        />
      </div>

      {/* Prediction History */}
      <div className="card">
        <h2 className="text-sm font-semibold text-slate-900 mb-4">
          Prediction History
        </h2>
        {predictions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-2 text-slate-500 font-medium">
                    Time
                  </th>
                  <th className="text-left py-2 text-slate-500 font-medium">
                    Risk
                  </th>
                  <th className="text-left py-2 text-slate-500 font-medium">
                    Probability
                  </th>
                  <th className="text-left py-2 text-slate-500 font-medium">
                    Failure Type
                  </th>
                  <th className="text-left py-2 text-slate-500 font-medium">
                    Confidence
                  </th>
                </tr>
              </thead>
              <tbody>
                {predictions.map((pred, idx) => (
                  <tr
                    key={idx}
                    className="border-b border-slate-100 hover:bg-slate-50"
                  >
                    <td className="py-2">{formatDate(pred.created_at)}</td>
                    <td className="py-2">
                      <RiskBadge level={pred.risk_level} />
                    </td>
                    <td className="py-2">
                      {((pred.failure_probability || 0) * 100).toFixed(1)}%
                    </td>
                    <td className="py-2 capitalize">
                      {pred.failure_type?.replace(/_/g, " ") || "—"}
                    </td>
                    <td className="py-2">
                      {((pred.confidence || 0) * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-slate-400 text-center py-6">
            No predictions yet. Click &quot;Run Prediction&quot; above.
          </p>
        )}
      </div>
    </div>
  );
}
