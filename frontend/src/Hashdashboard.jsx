import { useState, useMemo } from "react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
} from "recharts";
import {
  Download,
  Zap,
  GitBranch,
  Gauge,
  Trophy,
  Activity,
  Database,
  Copy,
  Check,
  TrendingDown,
  Layers,
  Sparkles,
  ShieldCheck,
} from "lucide-react";

const MOCK_REPORT = {
  per_function: [
    { name: "DJB2", bucket_count: 67, items_inserted: 50, insert_time_sec: 0.000412, lookup_time_sec: 0.000891, lookups_performed: 120, collisions: 9, max_chain_length: 3, non_empty_buckets: 41, load_factor: 0.746, estimated_memory_bytes: 8432, bucket_distribution: [1,0,2,1,0,0,1,3,0,1,0,0,2,1,1,0,0,1,0,2,1,0,1,0,0,1,1,0,2,0,1,0,1,1,0,0,1,2,0,1,0,1,0,0,1,1,0,2,0,1,1,0,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1] },
    { name: "FNV-1a", bucket_count: 67, items_inserted: 50, insert_time_sec: 0.000398, lookup_time_sec: 0.000743, lookups_performed: 120, collisions: 5, max_chain_length: 2, non_empty_buckets: 45, load_factor: 0.746, estimated_memory_bytes: 8432, bucket_distribution: [1,1,0,1,0,1,1,0,1,0,1,1,0,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1] },
    { name: "SDBM", bucket_count: 67, items_inserted: 50, insert_time_sec: 0.000405, lookup_time_sec: 0.000812, lookups_performed: 120, collisions: 7, max_chain_length: 3, non_empty_buckets: 43, load_factor: 0.746, estimated_memory_bytes: 8432, bucket_distribution: [0,1,1,2,0,1,0,1,1,0,3,0,1,0,1,1,0,1,0,1,1,0,0,1,1,0,1,1,0,1,0,1,1,0,1,0,0,1,1,0,2,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1] },
    { name: "Jenkins (one-at-a-time)", bucket_count: 67, items_inserted: 50, insert_time_sec: 0.000487, lookup_time_sec: 0.000759, lookups_performed: 120, collisions: 6, max_chain_length: 2, non_empty_buckets: 44, load_factor: 0.746, estimated_memory_bytes: 8432, bucket_distribution: [1,0,1,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,0,1,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1] },
    { name: "CRC32", bucket_count: 67, items_inserted: 50, insert_time_sec: 0.000521, lookup_time_sec: 0.000698, lookups_performed: 120, collisions: 4, max_chain_length: 2, non_empty_buckets: 46, load_factor: 0.746, estimated_memory_bytes: 8432, bucket_distribution: [1,1,0,1,1,0,1,1,0,1,1,0,1,1,0,1,0,1,1,0,1,1,0,1,1,0,1,1,0,1,0,1,1,0,1,1,0,1,1,0,1,0,1,1,0,1,1,0,1,1,0,1,0,1,1,0,1,1,0,1,1,0,1,1,0,1,1] },
  ],
  recommended_function: "CRC32",
  recommendation_reason:
    "CRC32 was determined to be optimal for this AST workload. It exhibited the lowest collision frequency (4) and an ideal maximum chain length of 2 across 67 buckets, providing maximum throughput for nested identifier lookups.",
  workload_summary: {
    total_identifiers: 120,
    unique_identifiers: 50,
    average_identifier_length: 6.4,
    uniqueness_ratio: 0.417,
    repetition_ratio: 0.583,
    scope_count: 4,
  },
};

const FN_COLORS = {
  DJB2: "#38BDF8",
  "FNV-1a": "#C084FC",
  SDBM: "#FBBF24",
  "Jenkins (one-at-a-time)": "#34D399",
  CRC32: "#10B981",
};

function fmtSec(v) {
  return `${(v * 1000).toFixed(3)} ms`;
}
function fmtBytes(v) {
  return `${(v / 1024).toFixed(1)} KB`;
}
function fmtPct(v) {
  return `${(v * 100).toFixed(1)}%`;
}

// ---------------------------------------------------------------------------
// 3D Glass Recommendation Hero Card (Inspired by Image 5 & 2)
// ---------------------------------------------------------------------------
function WinnerHeroCard({ report }) {
  const best = report.per_function.find((f) => f.name === report.recommended_function);

  return (
    <div className="rounded-3xl p-8 mb-8 bg-gradient-to-br from-indigo-950/70 via-[#12162C]/90 to-[#0F1222] border border-indigo-500/40 shadow-2xl relative overflow-hidden backdrop-blur-xl">
      {/* Glow highlight */}
      <div className="absolute top-0 right-0 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 relative z-10">
        <div className="flex items-start gap-5">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-400 to-teal-600 p-[1px] shadow-xl shadow-emerald-500/20 shrink-0">
            <div className="w-full h-full bg-[#0B0D17] rounded-[15px] flex items-center justify-center">
              <Trophy size={32} className="text-emerald-400" />
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-mono font-bold uppercase tracking-widest px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                ★ Optimal Recommendation
              </span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold font-mono text-white tracking-tight">
              {report.recommended_function}
            </h2>
            <p className="text-sm text-slate-300 mt-2 max-w-2xl leading-relaxed">
              {report.recommendation_reason}
            </p>
          </div>
        </div>

        {best && (
          <div className="flex items-center gap-3 flex-wrap bg-[#0E1122]/80 p-3 rounded-2xl border border-slate-800">
            <div className="px-4 py-3 rounded-xl bg-[#14182E] border border-slate-700 text-center">
              <div className="text-xs font-mono text-slate-400">Collisions</div>
              <div className="text-xl font-bold font-mono text-emerald-400">{best.collisions}</div>
            </div>
            <div className="px-4 py-3 rounded-xl bg-[#14182E] border border-slate-700 text-center">
              <div className="text-xs font-mono text-slate-400">Avg Lookup</div>
              <div className="text-xl font-bold font-mono text-cyan-400">{fmtSec(best.lookup_time_sec)}</div>
            </div>
            <div className="px-4 py-3 rounded-xl bg-[#14182E] border border-slate-700 text-center">
              <div className="text-xs font-mono text-slate-400">Load Factor</div>
              <div className="text-xl font-bold font-mono text-purple-400">{best.load_factor.toFixed(2)}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Telemetry Summary Cards
// ---------------------------------------------------------------------------
function TelemetryStrip({ summary }) {
  const cards = [
    { label: "Total Stream", value: summary.total_identifiers, sub: "Scanned Tokens", color: "from-blue-500 to-cyan-500" },
    { label: "Unique Interns", value: summary.unique_identifiers, sub: "Intern Table", color: "from-indigo-500 to-purple-500" },
    { label: "Avg Token Len", value: `${summary.average_identifier_length.toFixed(1)} ch`, sub: "Character Entropy", color: "from-purple-500 to-pink-500" },
    { label: "Repetition Index", value: fmtPct(summary.repetition_ratio), sub: "Lookup Reuse", color: "from-cyan-500 to-emerald-500" },
    { label: "Uniqueness Skew", value: fmtPct(summary.uniqueness_ratio), sub: "Collision Dispersion", color: "from-emerald-500 to-teal-500" },
    { label: "Scope Domains", value: summary.scope_count, sub: "Active Scopes", color: "from-amber-500 to-orange-500" },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
      {cards.map((c) => (
        <div
          key={c.label}
          className="p-5 rounded-2xl bg-[#131627]/90 border border-slate-800/80 shadow-lg relative overflow-hidden transition-all hover:-translate-y-1 hover:border-slate-700"
        >
          <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${c.color}`} />
          <div className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-2">
            {c.label}
          </div>
          <div className="text-2xl font-bold font-mono text-white mb-1">
            {c.value}
          </div>
          <div className="text-[11px] text-slate-500 font-mono">{c.sub}</div>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Candidate Benchmark Matrix Table
// ---------------------------------------------------------------------------
function BenchmarkTable({ report }) {
  const sorted = useMemo(() => {
    return [...report.per_function].sort((a, b) => a.collisions - b.collisions);
  }, [report]);

  return (
    <div className="rounded-3xl bg-[#131627]/90 border border-slate-800/80 shadow-xl backdrop-blur-xl overflow-hidden mb-8">
      <div className="px-6 py-5 bg-[#181C33]/90 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Layers size={16} />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Candidate Algorithm Matrix</h3>
            <p className="text-xs text-slate-400 font-mono">Ranked by lowest collision score</p>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs font-mono">
          <thead className="bg-[#101324] border-b border-slate-800 text-slate-400 uppercase">
            <tr>
              <th className="px-6 py-3.5 text-left font-semibold">Rank / Function</th>
              <th className="px-5 py-3.5 text-right font-semibold">Insert Latency</th>
              <th className="px-5 py-3.5 text-right font-semibold">Lookup Latency</th>
              <th className="px-5 py-3.5 text-right font-semibold">Collisions</th>
              <th className="px-5 py-3.5 text-right font-semibold">Max Chain</th>
              <th className="px-5 py-3.5 text-right font-semibold">Load Factor</th>
              <th className="px-6 py-3.5 text-right font-semibold">Memory</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/40">
            {sorted.map((fn, idx) => {
              const isWinner = fn.name === report.recommended_function;
              return (
                <tr
                  key={fn.name}
                  className={`transition-colors ${
                    isWinner ? "bg-emerald-500/10 hover:bg-emerald-500/15" : "hover:bg-slate-800/25"
                  }`}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-3">
                      <span
                        className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                          idx === 0 ? "bg-amber-500 text-black shadow-md shadow-amber-500/30" : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {idx + 1}
                      </span>
                      <span
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: FN_COLORS[fn.name] || "#38BDF8" }}
                      />
                      <span className="font-semibold text-white text-sm">{fn.name}</span>
                      {isWinner && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-emerald-500 text-black ml-2 shadow-sm">
                          Winner
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-5 py-4 text-right text-slate-300">{fmtSec(fn.insert_time_sec)}</td>
                  <td className="px-5 py-4 text-right text-cyan-400 font-semibold">{fmtSec(fn.lookup_time_sec)}</td>
                  <td className="px-5 py-4 text-right">
                    <span
                      className={`px-2.5 py-1 rounded-lg ${
                        fn.collisions <= 5
                          ? "bg-emerald-950 text-emerald-300 border border-emerald-700"
                          : "text-slate-300"
                      }`}
                    >
                      {fn.collisions}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-right text-slate-300">{fn.max_chain_length}</td>
                  <td className="px-5 py-4 text-right text-slate-300">{fn.load_factor.toFixed(2)}</td>
                  <td className="px-6 py-4 text-right text-slate-400">{fmtBytes(fn.estimated_memory_bytes)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Metric Bar Charts Grid
// ---------------------------------------------------------------------------
function MetricChartCard({ title, icon: Icon, report, dataKey, formatValue, unit, gradientColors }) {
  const data = report.per_function.map((fn) => ({
    name: fn.name.split(" ")[0],
    fullName: fn.name,
    value: fn[dataKey],
  }));

  return (
    <div className="p-6 rounded-3xl bg-[#131627]/90 border border-slate-800/80 shadow-xl backdrop-blur-xl">
      <div className="flex items-center gap-2.5 mb-5">
        <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
          <Icon size={16} />
        </div>
        <h3 className="text-sm font-semibold text-white">{title}</h3>
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <XAxis dataKey="name" tick={{ fill: "#94A3B8", fontSize: 11, fontFamily: "monospace" }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: "#94A3B8", fontSize: 10, fontFamily: "monospace" }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#181C33",
              borderColor: "#334155",
              borderRadius: "12px",
              fontSize: "12px",
              fontFamily: "monospace",
              color: "#FFF",
            }}
            formatter={(value) => [formatValue ? formatValue(value) : value, unit || ""]}
          />
          <Bar dataKey="value" radius={[6, 6, 0, 0]}>
            {data.map((d) => (
              <Cell
                key={d.fullName}
                fill={
                  d.fullName === report.recommended_function
                    ? "#10B981"
                    : FN_COLORS[d.fullName] || "#6366F1"
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Bucket Chain Histogram (Interactive Selector)
// ---------------------------------------------------------------------------
function BucketHistogram({ report }) {
  const [selected, setSelected] = useState(report.per_function[0]?.name || "CRC32");
  const fn = report.per_function.find((f) => f.name === selected) || report.per_function[0];
  const data = fn.bucket_distribution.map((count, idx) => ({ bucket: idx, count }));

  return (
    <div className="p-6 rounded-3xl bg-[#131627]/90 border border-slate-800/80 shadow-xl backdrop-blur-xl mb-8">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Database size={16} />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Bucket Distribution Spectrum</h3>
            <p className="text-xs text-slate-400 font-mono">
              {fn.non_empty_buckets} / {fn.bucket_count} Buckets Occupied · Max Chain: {fn.max_chain_length}
            </p>
          </div>
        </div>

        {/* Function Filter Buttons with Distinct Padding & Spacing */}
        <div className="flex items-center gap-2 flex-wrap">
          {report.per_function.map((f) => (
            <button
              key={f.name}
              onClick={() => setSelected(f.name)}
              className={`px-4 py-2 rounded-xl text-xs font-mono font-medium transition-all border ${
                selected === f.name
                  ? "bg-gradient-to-r from-indigo-600 to-cyan-600 text-white border-cyan-400 shadow-md shadow-cyan-500/20 scale-[1.02]"
                  : "bg-[#0E101D] text-slate-400 border-slate-800 hover:text-slate-200 hover:border-slate-700"
              }`}
            >
              {f.name.split(" ")[0]}
            </button>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={data} margin={{ top: 0, right: 10, left: -20, bottom: 0 }}>
          <XAxis dataKey="bucket" hide />
          <YAxis tick={{ fill: "#94A3B8", fontSize: 10, fontFamily: "monospace" }} axisLine={false} tickLine={false} allowDecimals={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#181C33",
              borderColor: "#334155",
              borderRadius: "12px",
              fontSize: "12px",
              fontFamily: "monospace",
              color: "#FFF",
            }}
            labelFormatter={(v) => `Bucket Index #${v}`}
            formatter={(v) => [`${v} keys`, "Chain Depth"]}
          />
          <Bar dataKey="count" radius={[2, 2, 0, 0]} fill={FN_COLORS[selected] || "#38BDF8"} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Export & Share Suite with Distinct Clean Buttons
// ---------------------------------------------------------------------------
function ExportSuite({ report }) {
  const [copied, setCopied] = useState(false);

  const handleExport = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `hash_benchmarks_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleCopyJSON = () => {
    navigator.clipboard.writeText(JSON.stringify(report, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={handleCopyJSON}
        className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#14182E] border border-slate-700 text-xs font-mono text-slate-300 hover:text-white hover:border-slate-500 transition-colors shadow-sm"
      >
        {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
        {copied ? "Copied JSON" : "Copy Payload"}
      </button>

      <button
        onClick={handleExport}
        className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-500 text-white font-semibold text-xs shadow-lg shadow-indigo-500/25 hover:opacity-95 transition-all hover:scale-105 active:scale-95"
      >
        <Download size={14} />
        Export JSON Report
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Root Hash Dashboard
// ---------------------------------------------------------------------------
export default function HashDashboard({ report = MOCK_REPORT }) {
  const metricCharts = useMemo(
    () => [
      { title: "Insertion Latency", icon: Zap, dataKey: "insert_time_sec", formatValue: fmtSec },
      { title: "Lookup Latency", icon: Zap, dataKey: "lookup_time_sec", formatValue: fmtSec },
      { title: "Collisions Encountered", icon: GitBranch, dataKey: "collisions", formatValue: (v) => v },
      { title: "Effective Load Factor", icon: Gauge, dataKey: "load_factor", formatValue: (v) => v.toFixed(2) },
    ],
    []
  );

  return (
    <div className="w-full">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Hash Benchmark Arena
          </h1>
          <p className="text-sm text-slate-400 font-mono mt-1">
            Real-time latency, collision density, and bucket distribution metrics
          </p>
        </div>
        <ExportSuite report={report} />
      </div>

      <WinnerHeroCard report={report} />
      <TelemetryStrip summary={report.workload_summary} />
      <BenchmarkTable report={report} />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {metricCharts.map((m) => (
          <MetricChartCard key={m.dataKey} report={report} {...m} />
        ))}
      </div>

      <BucketHistogram report={report} />
    </div>
  );
}