"use client";

import { useEffect, useState } from "react";
import { mlAdminAPI } from "@/lib/api";
import { PageSpinner } from "@/components/Loading";
import {
  BeakerIcon,
  PlayIcon,
  CheckCircleIcon,
  XCircleIcon,
} from "@heroicons/react/24/outline";

const ALGORITHMS = [
  {
    key: "random_forest",
    name: "Random Forest",
    desc: "Ensemble of decision trees with bagging",
    device: "CPU",
  },
  {
    key: "xgboost",
    name: "XGBoost",
    desc: "Gradient-boosted trees with regularization",
    device: "CPU",
  },
  {
    key: "lightgbm",
    name: "LightGBM",
    desc: "Leaf-wise gradient boosting",
    device: "CPU",
  },
  {
    key: "neural_network_deep",
    name: "Deep Neural Network",
    desc: "PyTorch 4-layer DNN (256→128→64→32) with BatchNorm",
    device: "GPU (CUDA)",
  },
];

export default function MLAdminPage() {
  const [activeModel, setActiveModel] = useState(null);
  const [training, setTraining] = useState({});
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState(true);
  const [trainingAll, setTrainingAll] = useState(false);

  const refreshActiveModel = () => {
    mlAdminAPI.activeModel().then(({ data }) => setActiveModel(data)).catch(() => {});
  };

  useEffect(() => {
    mlAdminAPI
      .activeModel()
      .then(({ data }) => setActiveModel(data))
      .catch(() => {})
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

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">ML Models</h1>
          <p className="text-sm text-slate-500 mt-1">
            Train, manage, and deploy machine learning models
          </p>
        </div>
        <button onClick={handleTrainAll} disabled={isAnyTraining} className="btn-primary">
          <PlayIcon className="h-4 w-4" />
          {trainingAll ? "Training All…" : "Train All Models"}
        </button>
      </div>

      {/* Active model info */}
      {activeModel && (
        <div className="card bg-blue-50 border-blue-200">
          <div className="flex items-center gap-3">
            <CheckCircleIcon className="h-6 w-6 text-blue-600" />
            <div>
              <p className="text-sm font-semibold text-blue-900">
                Active Model: {activeModel.algorithm}
              </p>
              <p className="text-xs text-blue-600">
                Version: {activeModel.version} | F1:{" "}
                {((activeModel.metrics?.f1 || 0) * 100).toFixed(1)}% | AUC:{" "}
                {((activeModel.metrics?.auc_roc || 0) * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Algorithm cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {ALGORITHMS.map((algo) => {
          const result = results[algo.key];
          const isTraining = training[algo.key];

          return (
            <div key={algo.key} className="card">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-50">
                    <BeakerIcon className="h-5 w-5 text-purple-600" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900">
                      {algo.name}
                    </h3>
                    <p className="text-xs text-slate-500">{algo.desc}</p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Device: {algo.device}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleTrain(algo.key)}
                  disabled={isAnyTraining}
                  className="btn-secondary text-xs py-1.5"
                >
                  {isTraining ? (
                    <span className="flex items-center gap-1">
                      <span className="h-3 w-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
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

              {/* Result */}
              {result && (
                <div className="mt-4 p-3 rounded-lg bg-slate-50 border border-slate-200">
                  {result.error ? (
                    <div className="flex items-center gap-2 text-sm text-red-600">
                      <XCircleIcon className="h-4 w-4" />
                      {result.error}
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm text-green-700">
                        <CheckCircleIcon className="h-4 w-4" />
                        Training complete!
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div>
                          <span className="text-slate-500">F1 Score</span>
                          <p className="font-semibold">
                            {((result.metrics?.f1 || 0) * 100).toFixed(1)}%
                          </p>
                        </div>
                        <div>
                          <span className="text-slate-500">AUC-ROC</span>
                          <p className="font-semibold">
                            {((result.metrics?.auc_roc || 0) * 100).toFixed(1)}%
                          </p>
                        </div>
                        <div>
                          <span className="text-slate-500">Recall</span>
                          <p className="font-semibold">
                            {((result.metrics?.recall || 0) * 100).toFixed(1)}%
                          </p>
                        </div>
                      </div>
                      <p className="text-xs text-slate-500">
                        Duration: {result.training_duration_seconds}s |
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
