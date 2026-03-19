"use client";

import React, { useEffect, useState } from "react";
import { mlAdminAPI } from "@/lib/api";
import { useAuthStore } from "@/lib/store";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
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
  emerald: { bg: "bg-emerald-50 text-emerald-600", icon: "text-emerald-600" },
  blue:    { bg: "bg-blue-50 text-blue-600",    icon: "text-blue-600" },
  amber:   { bg: "bg-amber-50 text-amber-600",   icon: "text-amber-600" },
  violet:  { bg: "bg-violet-50 text-violet-600",  icon: "text-violet-600" },
};

export default function MLAdminPage() {
  const user = useAuthStore((s) => s.user);
  const [activeModel, setActiveModel] = useState(null);
  const [models, setModels] = useState([]);
  const [training, setTraining] = useState({});
  const [results, setResults] = useState({});
  const [backtestResults, setBacktestResults] = useState({});
  const [loading, setLoading] = useState(true);
  const [trainingAll, setTrainingAll] = useState(false);
  const [accessError, setAccessError] = useState(false);

  const refreshActiveModel = () => {
    mlAdminAPI.activeModel().then(({ data }) => setActiveModel(data)).catch(() => {});
    mlAdminAPI.listModels().then(({ data }) => setModels(data)).catch(() => {});
  };

  useEffect(() => {
    Promise.all([
      mlAdminAPI.activeModel().then(({ data }) => setActiveModel(data)),
      mlAdminAPI.listModels().then(({ data }) => setModels(data)),
    ])
      .catch((err) => {
        if (err.response?.status === 403) setAccessError(true);
      })
      .finally(() => setLoading(false));
  }, []);

  const fiData = Object.entries(activeModel?.feature_importance || {})
    .map(([name, value]) => ({
      name: name.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" "),
      importance: value * 100,
    }))
    .sort((a, b) => b.importance - a.importance)
    .slice(0, 5); // top 5

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

  const handleBacktest = async (modelId) => {
    setBacktestResults((p) => ({ ...p, [modelId]: { loading: true } }));
    try {
      const { data } = await mlAdminAPI.backtest(modelId);
      setBacktestResults((p) => ({ ...p, [modelId]: { loading: false, data } }));
    } catch (err) {
      setBacktestResults((p) => ({
        ...p,
        [modelId]: { loading: false, error: err.response?.data?.detail || "Backtest failed" },
      }));
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

  if (accessError || !user || !["admin", "engineer"].includes(user.role)) {
    return (
      <div className="flex flex-col items-center justify-center py-24 space-y-4">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-100">
          <ShieldExclamationIcon className="h-8 w-8 text-slate-400" />
        </div>
        <h2 className="text-lg font-semibold text-slate-700">Access Restricted</h2>
        <p className="text-sm text-slate-400 max-w-sm text-center leading-relaxed">
          ML model management requires engineer or administrator privileges. Contact your
          organization admin to request access.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 py-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">ML Operations</h1>
          <p className="text-slate-500 dark:text-slate-400 mt-1">
            Train, orchestrate, and deploy machine learning models
          </p>
        </div>
        <button onClick={handleTrainAll} disabled={isAnyTraining} className="btn-primary shrink-0 relative overflow-hidden group">
          <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
          <SparklesIcon className="h-4 w-4 relative z-10" />
          <span className="relative z-10">{trainingAll ? "Training All…" : "Train All Models"}</span>
        </button>
      </div>

      {/* Active model info & Feature Importance */}
      {activeModel && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          <div className="card !bg-brand-50/50 dark:!bg-brand-900/10 !border-brand-200/60 dark:!border-brand-500/20 shadow-brand-500/5">
            <h3 className="text-xs font-bold text-brand-900 dark:text-brand-100 uppercase tracking-widest mb-4">Current Active Model</h3>
            <div className="flex items-start gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-100 dark:bg-brand-500/20 shadow-inner">
                <CheckCircleIcon className="h-7 w-7 text-brand-600 dark:text-brand-400" />
              </div>
              <div className="space-y-1">
                <p className="text-lg font-bold text-slate-900 dark:text-white">
                  {activeModel.algorithm.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
                </p>
                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-500 dark:text-slate-400 font-medium">
                  <span>v{activeModel.version}</span>
                  <span className="w-1 h-1 rounded-full bg-slate-300 dark:bg-slate-600" />
                  <span>F1: {((activeModel.metrics?.f1 || 0) * 100).toFixed(1)}%</span>
                  <span className="w-1 h-1 rounded-full bg-slate-300 dark:bg-slate-600" />
                  <span>AUC: {((activeModel.metrics?.auc_roc || 0) * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-brand-200/50 dark:border-brand-500/20">
               <p className="text-xs text-slate-400 dark:text-slate-500 truncate bg-slate-100 dark:bg-surface-800 px-3 py-1.5 rounded-lg border border-slate-200/60 dark:border-surface-700/50 inline-flex font-mono">
                 {activeModel.model_path.split("/").pop().split("\\").pop()}
               </p>
            </div>
          </div>

          {fiData.length > 0 && (
            <div className="card h-full">
              <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-widest mb-4">Driving Factors (Feature Importance)</h3>
              <div className="h-28 w-full -ml-4">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={fiData} layout="vertical" margin={{ top: 0, right: 20, left: 40, bottom: 0 }}>
                    <XAxis type="number" hide />
                    <YAxis 
                      dataKey="name" 
                      type="category" 
                      axisLine={false} 
                      tickLine={false} 
                      tick={{ fill: "#64748b", fontSize: 11, fontWeight: 500 }}
                      width={100}
                    />
                    <Tooltip 
                      cursor={{ fill: "rgba(255,255,255,0.05)" }}
                      contentStyle={{ borderRadius: "12px", border: "none", backgroundColor: "#0f172a", color: "#fff", padding: "8px 12px", fontSize: "12px", boxShadow: "0 10px 25px -5px rgba(0,0,0,0.5)" }}
                      formatter={(val) => [`${val.toFixed(1)}%`, "Influence"]}
                    />
                    <Bar dataKey="importance" radius={[0, 4, 4, 0]} barSize={8}>
                      {fiData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill="url(#colorFi)" />
                      ))}
                    </Bar>
                    <defs>
                      <linearGradient id="colorFi" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.8} />
                        <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0.9} />
                      </linearGradient>
                    </defs>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
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
      {/* Historical Models Table */}
      {models.length > 0 && (
        <div className="card mt-2">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-4 uppercase tracking-widest">Historical Models & Replay Backtesting</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700/50">
                  <th className="pb-3 px-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">Model Name</th>
                  <th className="pb-3 px-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">Algorithm</th>
                  <th className="pb-3 px-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">F1 Score</th>
                  <th className="pb-3 px-2 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/50">
                {models.map((model) => (
                  <React.Fragment key={model.id || model.version}>
                    <tr className="hover:bg-slate-50 dark:hover:bg-surface-800/30 transition-colors">
                      <td className="py-3 px-2 text-sm font-medium text-slate-900 dark:text-white flex items-center gap-2">
                        {model.is_active && <span className="flex h-2 w-2 rounded-full bg-emerald-500"></span>}
                        {model.name || `${model.algorithm}_v${model.version}`}
                      </td>
                      <td className="py-3 px-2 text-sm text-slate-500 dark:text-slate-400 capitalize">{model.algorithm.replace("_", " ")}</td>
                      <td className="py-3 px-2 text-sm text-slate-500 dark:text-slate-400">{model.f1_score ? (model.f1_score * 100).toFixed(1) + "%" : "N/A"}</td>
                      <td className="py-3 px-2 text-right">
                        {model.id && (
                          <button 
                            onClick={() => handleBacktest(model.id)}
                            disabled={backtestResults[model.id]?.loading}
                            className="text-xs font-semibold text-brand-600 dark:text-brand-400 hover:text-brand-700 dark:hover:text-brand-300 bg-brand-50 dark:bg-brand-500/10 hover:bg-brand-100 dark:hover:bg-brand-500/20 px-3 py-1.5 rounded-md transition-colors disabled:opacity-50"
                          >
                            {backtestResults[model.id]?.loading ? "Running..." : "Run Replay Backtest"}
                          </button>
                        )}
                      </td>
                    </tr>
                    {backtestResults[model.id]?.data && (
                      <tr className="bg-slate-50/50 dark:bg-surface-800/20 border-b border-slate-100 dark:border-slate-800/50">
                        <td colSpan={4} className="py-4 px-4">
                          <div className="flex flex-col gap-2">
                            <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
                              <CheckCircleIcon className="h-4 w-4" />
                              Backtest Complete - {backtestResults[model.id].data.samples_tested.toLocaleString()} samples evaluated
                            </span>
                            <div className="grid grid-cols-4 gap-4 mt-2">
                              <div>
                                <span className="text-2xs text-slate-500 uppercase tracking-wider">Simulated F1</span>
                                <p className="text-sm font-bold text-slate-800 dark:text-slate-200">{(backtestResults[model.id].data.metrics.f1 * 100).toFixed(1)}%</p>
                              </div>
                              <div>
                                <span className="text-2xs text-slate-500 uppercase tracking-wider">Simulated Accuracy</span>
                                <p className="text-sm font-bold text-slate-800 dark:text-slate-200">{(backtestResults[model.id].data.metrics.accuracy * 100).toFixed(1)}%</p>
                              </div>
                              <div>
                                <span className="text-2xs text-slate-500 uppercase tracking-wider">True Positives</span>
                                <p className="text-sm font-bold text-slate-800 dark:text-slate-200">{backtestResults[model.id].data.metrics.true_positives}</p>
                              </div>
                              <div>
                                <span className="text-2xs text-slate-500 uppercase tracking-wider">False Negatives</span>
                                <p className="text-sm font-bold text-red-500">{backtestResults[model.id].data.metrics.false_negatives}</p>
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                    {backtestResults[model.id]?.error && (
                      <tr className="bg-red-50/50 dark:bg-red-500/5">
                        <td colSpan={4} className="py-3 px-4 text-xs text-red-600 dark:text-red-400 font-medium flex items-center gap-2">
                          <XCircleIcon className="h-4 w-4" />
                          {backtestResults[model.id].error}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
