"use client";

import { useEffect, useState } from "react";
import { mlAdminAPI } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { PageSpinner } from "@/components/Loading";
import {
  BeakerIcon,
  PlayIcon,
  CheckCircleIcon,
  XCircleIcon,
  ShieldExclamationIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";

const ALGORITHMS = [
  {
    key: "random_forest",
    name: "Random Forest",
    desc: "Ensemble of decision trees with bagging",
    device: "CPU",
    color: "emerald",
  },
  {
    key: "xgboost",
    name: "XGBoost",
    desc: "Gradient-boosted trees with regularization",
    device: "CPU",
    color: "blue",
  },
  {
    key: "lightgbm",
    name: "LightGBM",
    desc: "Leaf-wise gradient boosting",
    device: "CPU",
    color: "amber",
  },
  {
    key: "neural_network_deep",
    name: "Deep Neural Network",
    desc: "PyTorch 4-layer DNN (256→128→64→32) with BatchNorm",
    device: "GPU (CUDA)",
    color: "violet",
  },
];

const colorMap = {
  emerald: { bg: "bg-emerald-50", icon: "text-emerald-600" },
  blue:    { bg: "bg-blue-50",    icon: "text-blue-600" },
  amber:   { bg: "bg-amber-50",   icon: "text-amber-600" },
  violet:  { bg: "bg-violet-50",  icon: "text-violet-600" },
};

export default function MLAdminPage() {
  const user = useAuthStore((s) => s.user);
  const [activeModel, setActiveModel] = useState(null);
  const [training, setTraining] = useState({});
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState(true);
  const [trainingAll, setTrainingAll] = useState(false);
  const [accessError, setAccessError] = useState(false);

  const refreshActiveModel = () => {
    mlAdminAPI.activeModel().then(({ data }) => setActiveModel(data)).catch(() => {});
  };

  useEffect(() => {
    mlAdminAPI
      .activeModel()
      .then(({ data }) => setActiveModel(data))
      .catch((err) => {
        if (err.response?.status === 403) setAccessError(true);
      })
      .finally(() => setLoading(false));
  }, []);

  const isAnyTraining = Object.values(training).some(Boolean) || trainingAll;

  const handleTrain = async (algorithm) => {
    if (isAnyTraining) return; // concurrency guard
    setTraining((p) => ({ ...p, [algorithm]: true }));
    setResults((p) => ({ ...p, [algorithm]: null }));
    try {
      const { data } = await mlAdminAPI.train(algorithm);
      setResults((p) => ({ ...p, [algorithm]: data }));
      refreshActiveModel();
    } catch (err) {
      setResults((p) => ({
        ...p,
        [algorithm]: { error: err.response?.data?.detail || "Training failed" },
      }));
    } finally {
      setTraining((p) => ({ ...p, [algorithm]: false }));
    }
  };

  const handleTrainAll = async () => {
    if (isAnyTraining) return; // concurrency guard
    setTrainingAll(true);
    for (const algo of ALGORITHMS) {
      setTraining((p) => ({ ...p, [algo.key]: true }));
      setResults((p) => ({ ...p, [algo.key]: null }));
      try {
        const { data } = await mlAdminAPI.train(algo.key);
        setResults((p) => ({ ...p, [algo.key]: data }));
      } catch (err) {
        setResults((p) => ({
          ...p,
          [algo.key]: { error: err.response?.data?.detail || "Training failed" },
        }));
      } finally {
        setTraining((p) => ({ ...p, [algo.key]: false }));
      }
    }
    refreshActiveModel();
    setTrainingAll(false);
  };

  if (loading) return <PageSpinner />;

  if (accessError || (user && user.role !== "admin")) {
    return (
      <div className="flex flex-col items-center justify-center py-24 space-y-4">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-100">
          <ShieldExclamationIcon className="h-8 w-8 text-slate-400" />
        </div>
        <h2 className="text-lg font-semibold text-slate-700">Access Restricted</h2>
        <p className="text-sm text-slate-400 max-w-sm text-center leading-relaxed">
          ML model management requires administrator privileges. Contact your
          organization admin to request access.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="page-title">ML Models</h1>
          <p className="page-subtitle">
            Train, manage, and deploy machine learning models
          </p>
        </div>
        <button onClick={handleTrainAll} disabled={isAnyTraining} className="btn-primary shrink-0">
          <SparklesIcon className="h-4 w-4" />
          {trainingAll ? "Training All…" : "Train All Models"}
        </button>
      </div>

      {/* Active model info */}
      {activeModel && (
        <div className="card !bg-brand-50 !border-brand-200/60">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-100">
              <CheckCircleIcon className="h-5 w-5 text-brand-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-brand-900">
                Active Model: {activeModel.algorithm}
              </p>
              <p className="text-2xs text-brand-600 font-medium">
                Version: {activeModel.version} · F1:{" "}
                {((activeModel.metrics?.f1 || 0) * 100).toFixed(1)}% · AUC:{" "}
                {((activeModel.metrics?.auc_roc || 0) * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Algorithm cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {ALGORITHMS.map((algo) => {
          const result = results[algo.key];
          const isTraining = training[algo.key];
          const colors = colorMap[algo.color];

          return (
            <div key={algo.key} className="card">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${colors.bg}`}>
                    <BeakerIcon className={`h-5 w-5 ${colors.icon}`} />
                  </div>
                  <div>
                    <h3 className="text-[0.8125rem] font-semibold text-slate-800">
                      {algo.name}
                    </h3>
                    <p className="text-2xs text-slate-400 leading-relaxed">{algo.desc}</p>
                    <p className="text-2xs text-slate-400 mt-0.5">
                      Device: {algo.device}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleTrain(algo.key)}
                  disabled={isAnyTraining}
                  className="btn-ghost text-xs py-1.5 shrink-0"
                >
                  {isTraining ? (
                    <span className="flex items-center gap-1.5">
                      <span className="h-3 w-3 border-2 border-brand-600 border-t-transparent rounded-full animate-spin" />
                      Training...
                    </span>
                  ) : (
                    <>
                      <PlayIcon className="h-3.5 w-3.5" />
                      Train
                    </>
                  )}
                </button>
              </div>

              {result && (
                <div className="mt-4 p-3.5 rounded-xl bg-surface-50 border border-slate-100">
                  {result.error ? (
                    <div className="flex items-center gap-2 text-sm text-red-500 font-medium">
                      <XCircleIcon className="h-4 w-4" />
                      {result.error}
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 text-sm text-emerald-600 font-medium">
                        <CheckCircleIcon className="h-4 w-4" />
                        Training complete!
                      </div>
                      <div className="grid grid-cols-3 gap-2">
                        {[["F1 Score", result.metrics?.f1], ["AUC-ROC", result.metrics?.auc_roc], ["Recall", result.metrics?.recall]].map(([label, val]) => (
                          <div key={label}>
                            <span className="text-2xs text-slate-400">{label}</span>
                            <p className="text-sm font-bold text-slate-700 tabular-nums">
                              {((val || 0) * 100).toFixed(1)}%
                            </p>
                          </div>
                        ))}
                      </div>
                      <p className="text-2xs text-slate-400">
                        Duration: {result.training_duration_seconds}s ·
                        Device: {result.device || "CPU"}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
