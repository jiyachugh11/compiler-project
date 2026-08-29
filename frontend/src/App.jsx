import { useState } from "react";
import CompilerDashboard from "./CompilerDashboard";
import HashDashboard from "./HashDashboard";
import {
  Code2,
  Activity,
  Layers,
  Sparkles,
  ArrowRight,
  ShieldAlert,
  Cpu,
} from "lucide-react";

const API_URL = "http://localhost:8000";

export default function App() {
  const [tab, setTab] = useState("compiler"); // "compiler" | "hash"
  const [workload, setWorkload] = useState(null);
  const [hashAnalysis, setHashAnalysis] = useState(null);

  const handleAnalyzed = (data) => {
    setWorkload(data.workload);
    setHashAnalysis(data.hash_analysis);
    setTab("hash");
  };

  return (
    <div
      className="min-h-screen text-slate-100 font-sans selection:bg-indigo-500 selection:text-white"
      style={{
        backgroundColor: "#0B0D17",
        backgroundImage: `
          radial-gradient(circle at 15% 10%, rgba(99, 102, 241, 0.15) 0%, transparent 35%),
          radial-gradient(circle at 85% 15%, rgba(56, 189, 248, 0.12) 0%, transparent 40%),
          radial-gradient(circle at 50% 90%, rgba(168, 85, 247, 0.1) 0%, transparent 50%)
        `,
      }}
    >
      {/* Top Glassmorphic Navigation Bar */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-[#0F1222]/80 border-b border-slate-800/80 px-6 py-4">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          
          {/* Logo & Platform Title */}
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-[1px] shadow-lg shadow-indigo-500/25">
              <div className="w-full h-full bg-[#0B0D17] rounded-[15px] flex items-center justify-center">
                <Cpu className="text-cyan-400" size={20} />
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg text-white tracking-tight">
                  HashSense
                </span>
                <span className="text-[10px] uppercase font-mono font-bold tracking-widest px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Pro Engine
                </span>
              </div>
              <p className="text-xs text-slate-400 font-medium">
                AST Symbol Extraction & Hash Telemetry Suite
              </p>
            </div>
          </div>

          {/* Nav Buttons with Distinct Padding & Spacing */}
          <div className="flex items-center gap-3 p-1.5 rounded-2xl bg-[#14172B] border border-slate-800/90 shadow-inner">
            <button
              onClick={() => setTab("compiler")}
              className={`flex items-center gap-2.5 px-6 py-2.5 rounded-xl text-sm font-semibold transition-all duration-300 ${
                tab === "compiler"
                  ? "bg-gradient-to-r from-indigo-600 to-blue-600 text-white shadow-lg shadow-indigo-500/30 scale-[1.02]"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
              }`}
            >
              <Code2 size={16} />
              Compiler Analysis
            </button>

            <button
              onClick={() => setTab("hash")}
              className={`flex items-center gap-2.5 px-6 py-2.5 rounded-xl text-sm font-semibold transition-all duration-300 relative ${
                tab === "hash"
                  ? "bg-gradient-to-r from-indigo-600 to-cyan-600 text-white shadow-lg shadow-cyan-500/30 scale-[1.02]"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
              }`}
            >
              <Activity size={16} />
              Hash Benchmarks
              {hashAnalysis && (
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping absolute top-2 right-2" />
              )}
            </button>
          </div>

          {/* Status Badge */}
          <div className="hidden lg:flex items-center gap-3 px-4 py-2 rounded-xl bg-[#14172B] border border-slate-800 text-xs font-mono text-slate-300">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
            <span>{hashAnalysis ? "Telemetry Synced" : "Engine Idle"}</span>
          </div>

        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div style={{ display: tab === "compiler" ? "block" : "none" }}>
          <CompilerDashboard
            apiUrl={API_URL}
            workload={workload}
            onAnalyzed={handleAnalyzed}
          />
        </div>

        <div style={{ display: tab === "hash" ? "block" : "none" }}>
          {hashAnalysis ? (
            <HashDashboard report={hashAnalysis} />
          ) : (
            <div className="mt-12 max-w-xl mx-auto rounded-3xl p-10 text-center bg-[#131627]/80 border border-slate-800/80 shadow-2xl backdrop-blur-xl">
              <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mx-auto mb-5 shadow-lg shadow-indigo-500/10">
                <Sparkles size={30} />
              </div>
              <h3 className="text-xl font-bold text-white mb-2">
                Awaiting Compiler Pipeline
              </h3>
              <p className="text-sm text-slate-400 leading-relaxed mb-8">
                Run an AST extraction on the Compiler Analysis tab first to stream
                identifiers and benchmark candidate hash algorithms.
              </p>
              <button
                onClick={() => setTab("compiler")}
                className="inline-flex items-center gap-2.5 px-7 py-3.5 rounded-xl font-semibold text-sm bg-gradient-to-r from-indigo-600 to-cyan-500 text-white shadow-xl shadow-indigo-500/30 hover:opacity-95 transition-all hover:scale-105 active:scale-95"
              >
                Go to Compiler Engine
                <ArrowRight size={17} />
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}