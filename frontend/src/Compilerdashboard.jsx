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
} from "recharts";
import {
  Play,
  FileCode,
  Layers,
  ListTree,
  Loader2,
  Search,
  Sparkles,
  Copy,
  Check,
  Hash,
  Activity,
  Code2,
  Terminal,
} from "lucide-react";

const SAMPLES = {
  "Array Sum": `int compute_sum(int* arr, int length) {
    int total = 0;
    for (int i = 0; i < length; ++i) {
        total += arr[i];
    }
    return total;
}`,
  "Matrix Multiplication": `void matrix_multiply(int A[4][4], int B[4][4], int C[4][4]) {
    for (int row = 0; row < 4; ++row) {
        for (int col = 0; col < 4; ++col) {
            int dot_product = 0;
            for (int k = 0; k < 4; ++k) {
                dot_product += A[row][k] * B[k][col];
            }
            C[row][col] = dot_product;
        }
    }
}`,
  "Scoped Symbol Table": `int global_seed = 42;

struct Node {
    int value;
    Node* next;
};

Node* create_node(int value) {
    Node* new_node = (Node*)malloc(sizeof(Node));
    new_node->value = value + global_seed;
    new_node->next = NULL;
    return new_node;
}`,
};

const MOCK_WORKLOAD = {
  identifier_stream: ["compute_sum", "arr", "length", "total", "i", "i", "length", "i", "total", "arr", "i", "total"],
  interned_identifiers: { compute_sum: 0, arr: 1, length: 2, total: 3, i: 4 },
  symbols: [
    { name: "compute_sum", scope_id: 0, scope_depth: 0, location: { line: 1, column: 5 }, data_type: "int", role: "DECLARATION", intern_id: 0 },
    { name: "arr", scope_id: 0, scope_depth: 0, location: { line: 1, column: 21 }, data_type: "int*", role: "DECLARATION", intern_id: 1 },
    { name: "length", scope_id: 0, scope_depth: 0, location: { line: 1, column: 30 }, data_type: "int", role: "DECLARATION", intern_id: 2 },
    { name: "total", scope_id: 1, scope_depth: 1, location: { line: 2, column: 9 }, data_type: "int", role: "DECLARATION", intern_id: 3 },
    { name: "i", scope_id: 1, scope_depth: 1, location: { line: 3, column: 14 }, data_type: "int", role: "DECLARATION", intern_id: 4 },
    { name: "i", scope_id: 1, scope_depth: 1, location: { line: 3, column: 21 }, data_type: null, role: "REFERENCE", intern_id: 4 },
    { name: "length", scope_id: 1, scope_depth: 1, location: { line: 3, column: 25 }, data_type: null, role: "REFERENCE", intern_id: 2 },
    { name: "i", scope_id: 1, scope_depth: 1, location: { line: 3, column: 35 }, data_type: null, role: "REFERENCE", intern_id: 4 },
    { name: "total", scope_id: 2, scope_depth: 2, location: { line: 4, column: 9 }, data_type: null, role: "REFERENCE", intern_id: 3 },
    { name: "arr", scope_id: 2, scope_depth: 2, location: { line: 4, column: 18 }, data_type: null, role: "REFERENCE", intern_id: 1 },
    { name: "i", scope_id: 2, scope_depth: 2, location: { line: 4, column: 22 }, data_type: null, role: "REFERENCE", intern_id: 4 },
    { name: "total", scope_id: 1, scope_depth: 1, location: { line: 6, column: 12 }, data_type: null, role: "REFERENCE", intern_id: 3 },
  ],
  scopes: {
    0: { scope_id: 0, parent_id: null, depth: 0, scope_type: "GLOBAL", symbol_names: ["compute_sum", "arr", "length"], child_scope_ids: [1] },
    1: { scope_id: 1, parent_id: 0, depth: 1, scope_type: "FUNCTION", symbol_names: ["total", "i"], child_scope_ids: [2] },
    2: { scope_id: 2, parent_id: 1, depth: 2, scope_type: "BLOCK", symbol_names: [], child_scope_ids: [] },
  },
  workload_metrics: {
    total_identifiers: 12,
    unique_identifiers: 5,
    average_identifier_length: 4.42,
    min_identifier_length: 1,
    max_identifier_length: 11,
    identifier_frequency: { compute_sum: 1, arr: 2, length: 2, total: 3, i: 4 },
    repetition_ratio: 0.583,
    uniqueness_ratio: 0.417,
    scope_count: 3,
    max_scope_depth: 2,
    identifiers_per_scope: { 0: 3, 1: 6, 2: 3 },
  },
  source_code: SAMPLES["Array Sum"],
};

const SCOPE_TAG_COLORS = {
  GLOBAL: "from-blue-500 to-cyan-500 text-cyan-300 border-cyan-500/30",
  FUNCTION: "from-purple-500 to-pink-500 text-purple-300 border-purple-500/30",
  BLOCK: "from-emerald-500 to-teal-500 text-emerald-300 border-emerald-500/30",
};

// ---------------------------------------------------------------------------
// Modern Code Studio Editor with Presets
// ---------------------------------------------------------------------------
function CodeStudio({ code, setCode, onAnalyze, loading }) {
  const [copied, setCopied] = useState(false);
  const lineCount = useMemo(() => (code ? code.split("\n").length : 0), [code]);

  const handleCopy = () => {
    if (!code) return;
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="rounded-3xl bg-[#131627]/90 border border-slate-800/80 shadow-2xl backdrop-blur-xl overflow-hidden mb-8">
      {/* Editor Header */}
      <div className="px-6 py-4 bg-[#181C33]/90 border-b border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-rose-500/80" />
            <span className="w-3 h-3 rounded-full bg-amber-500/80" />
            <span className="w-3 h-3 rounded-full bg-emerald-500/80" />
          </div>
          <div className="h-4 w-px bg-slate-700" />
          <div className="flex items-center gap-2 text-xs font-mono text-slate-300">
            <FileCode size={15} className="text-cyan-400" />
            <span>ast_pipeline_input.cpp</span>
          </div>
        </div>

        {/* Preset Selector Buttons with Distinct Padding */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <span className="text-xs font-mono text-slate-400 mr-1">Presets:</span>
          {Object.keys(SAMPLES).map((key) => (
            <button
              key={key}
              onClick={() => setCode(SAMPLES[key])}
              className="px-3.5 py-1.5 rounded-xl text-xs font-medium bg-[#131627] hover:bg-indigo-950/60 border border-slate-700 text-slate-300 hover:text-white hover:border-indigo-500/50 transition-all duration-200"
            >
              {key}
            </button>
          ))}
          <button
            onClick={handleCopy}
            className="p-2 rounded-xl bg-[#131627] border border-slate-700 text-slate-400 hover:text-white hover:border-slate-500 transition-colors ml-1"
            title="Copy code"
          >
            {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
          </button>
        </div>
      </div>

      {/* Code Textarea with Line Numbers */}
      <div className="flex relative font-mono text-sm leading-6">
        <div className="select-none py-5 px-4 text-right text-slate-600 bg-[#0E101D] border-r border-slate-800/80 w-14">
          {Array.from({ length: Math.max(lineCount, 8) }).map((_, i) => (
            <div key={i}>{i + 1}</div>
          ))}
        </div>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="// Enter C/C++ source code to analyze AST identifiers..."
          rows={9}
          className="w-full p-5 bg-[#0A0C16] text-slate-200 outline-none resize-none placeholder-slate-600 font-mono text-sm"
        />
      </div>

      {/* Editor Action Footer */}
      <div className="px-6 py-4 bg-[#181C33]/90 border-t border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
          <span>{lineCount} Lines</span>
          <span>·</span>
          <span>{code.length} Characters</span>
          <span>·</span>
          <span className="text-cyan-400">Clang Lexer Frontend</span>
        </div>

        <button
          onClick={onAnalyze}
          disabled={loading || !code.trim()}
          className="flex items-center gap-3 px-7 py-3 rounded-xl font-semibold text-sm bg-gradient-to-r from-indigo-600 via-blue-600 to-cyan-500 text-white shadow-xl shadow-indigo-600/30 hover:opacity-95 transition-all hover:scale-[1.02] active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading ? (
            <Loader2 size={17} className="animate-spin text-white" />
          ) : (
            <Play size={17} className="fill-white" />
          )}
          {loading ? "Analyzing Pipeline..." : "Run Pipeline Analysis"}
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Telemetry Stat Cards Grid
// ---------------------------------------------------------------------------
function TelemetryStrip({ metrics }) {
  const cards = [
    { label: "Total Identifiers", value: metrics.total_identifiers, sub: "Token Stream", gradient: "from-blue-500 to-cyan-500" },
    { label: "Unique Interns", value: metrics.unique_identifiers, sub: "Unique AST Tokens", gradient: "from-indigo-500 to-purple-500" },
    { label: "Avg Token Len", value: `${metrics.average_identifier_length.toFixed(1)} ch`, sub: "Entropy Metric", gradient: "from-purple-500 to-pink-500" },
    { label: "Repetition Index", value: `${(metrics.repetition_ratio * 100).toFixed(0)}%`, sub: "Symbol Reuse", gradient: "from-cyan-500 to-emerald-500" },
    { label: "Lexical Scopes", value: metrics.scope_count, sub: "Environments", gradient: "from-emerald-500 to-teal-500" },
    { label: "Max Scope Depth", value: `Depth ${metrics.max_scope_depth}`, sub: "AST Nesting", gradient: "from-amber-500 to-orange-500" },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
      {cards.map((c) => (
        <div
          key={c.label}
          className="p-5 rounded-2xl bg-[#131627]/90 border border-slate-800/80 shadow-lg relative overflow-hidden transition-all hover:-translate-y-1 hover:border-slate-700"
        >
          <div className={`absolute top-0 left-0 right-0 h-1 bg-gradient-to-r ${c.gradient}`} />
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
// Frequency & Scope Load Charts with Area / Glow Aesthetics
// ---------------------------------------------------------------------------
function FrequencyAreaChart({ metrics }) {
  const data = useMemo(
    () =>
      Object.entries(metrics.identifier_frequency)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 8)
        .map(([name, count]) => ({ name, count })),
    [metrics]
  );

  return (
    <div className="p-6 rounded-3xl bg-[#131627]/90 border border-slate-800/80 shadow-xl backdrop-blur-xl">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Hash size={16} />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Identifier Occurrence Distribution</h3>
            <p className="text-xs text-slate-400 font-mono">AST frequency spectrum</p>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="cyanGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#38BDF8" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#38BDF8" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="name" tick={{ fill: "#94A3B8", fontSize: 11, fontFamily: "monospace" }} axisLine={false} tickLine={false} />
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
          />
          <Area type="monotone" dataKey="count" stroke="#38BDF8" strokeWidth={3} fillOpacity={1} fill="url(#cyanGrad)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function ScopeLoadBarChart({ metrics, scopes }) {
  const data = Object.entries(metrics.identifiers_per_scope).map(([scopeId, count]) => {
    const scope = scopes[scopeId];
    return {
      name: `#${scopeId} ${scope ? scope.scope_type : ""}`,
      count,
    };
  });

  return (
    <div className="p-6 rounded-3xl bg-[#131627]/90 border border-slate-800/80 shadow-xl backdrop-blur-xl">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <Activity size={16} />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Workload per Lexical Scope</h3>
            <p className="text-xs text-slate-400 font-mono">Isolated identifier loads</p>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="purpleGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#A855F7" />
              <stop offset="100%" stopColor="#6366F1" />
            </linearGradient>
          </defs>
          <XAxis dataKey="name" tick={{ fill: "#94A3B8", fontSize: 11, fontFamily: "monospace" }} axisLine={false} tickLine={false} />
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
          />
          <Bar dataKey="count" radius={[6, 6, 0, 0]} fill="url(#purpleGrad)" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Interactive Scope Hierarchy
// ---------------------------------------------------------------------------
function ScopeNode({ scope, scopes, depth }) {
  if (!scope) return null;
  const tagStyle = SCOPE_TAG_COLORS[scope.scope_type] || "from-slate-600 to-slate-700 text-slate-300 border-slate-600";

  return (
    <div className="relative">
      <div
        className="flex items-center gap-3 py-3 px-4 my-2 rounded-2xl transition-all duration-200 border border-slate-800/80 bg-[#15192E]/60 hover:bg-[#181D36]"
        style={{ marginLeft: depth * 28 }}
      >
        <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 shadow-md shadow-cyan-400/50" />
        <span className="text-xs font-mono px-2.5 py-1 rounded-lg bg-slate-900 text-slate-300 border border-slate-800">
          Scope #{scope.scope_id}
        </span>
        <span className={`text-xs font-mono font-bold px-2.5 py-0.5 rounded-lg border bg-gradient-to-r ${tagStyle}`}>
          {scope.scope_type}
        </span>
        {scope.symbol_names && scope.symbol_names.length > 0 ? (
          <div className="flex items-center gap-2 flex-wrap ml-auto">
            {scope.symbol_names.map((sym) => (
              <span
                key={sym}
                className="text-xs font-mono px-2.5 py-1 rounded-lg bg-slate-900/90 text-slate-200 border border-slate-700"
              >
                {sym}
              </span>
            ))}
          </div>
        ) : (
          <span className="text-xs text-slate-500 font-mono ml-auto italic">
            No local declarations
          </span>
        )}
      </div>
      {scope.child_scope_ids &&
        scope.child_scope_ids.map((childId) => (
          <ScopeNode key={childId} scope={scopes[childId]} scopes={scopes} depth={depth + 1} />
        ))}
    </div>
  );
}

function ScopeHierarchy({ scopes }) {
  const root = scopes[0];
  return (
    <div className="p-6 rounded-3xl bg-[#131627]/90 border border-slate-800/80 shadow-xl backdrop-blur-xl mb-8">
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <ListTree size={16} />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">AST Lexical Scope Tree</h3>
            <p className="text-xs text-slate-400 font-mono">Nested variable lifetime hierarchy</p>
          </div>
        </div>
      </div>
      <div className="p-3 rounded-2xl bg-[#0C0E1A] border border-slate-800/80">
        {root ? <ScopeNode scope={root} scopes={scopes} depth={0} /> : <div className="p-4 text-xs text-slate-500">No scope data</div>}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Searchable Symbol Table
// ---------------------------------------------------------------------------
function SymbolTable({ symbols }) {
  const [filter, setFilter] = useState("");
  const [roleFilter, setRoleFilter] = useState("ALL");

  const filtered = useMemo(() => {
    return symbols.filter((sym) => {
      const matchSearch =
        sym.name.toLowerCase().includes(filter.toLowerCase()) ||
        (sym.data_type && sym.data_type.toLowerCase().includes(filter.toLowerCase()));
      const matchRole = roleFilter === "ALL" || sym.role === roleFilter;
      return matchSearch && matchRole;
    });
  }, [symbols, filter, roleFilter]);

  return (
    <div className="rounded-3xl bg-[#131627]/90 border border-slate-800/80 shadow-xl backdrop-blur-xl overflow-hidden mb-8">
      <div className="px-6 py-5 bg-[#181C33]/90 border-b border-slate-800 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Layers size={16} />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Extracted Symbol Matrix</h3>
            <p className="text-xs text-slate-400 font-mono">
              {filtered.length} of {symbols.length} identifiers mapped
            </p>
          </div>
        </div>

        {/* Filter Controls with Generous Padding */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="relative">
            <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="Search symbols..."
              className="pl-9 pr-4 py-2 rounded-xl text-xs font-mono bg-[#0E101D] border border-slate-700 text-slate-200 outline-none focus:border-indigo-500 transition-colors w-48"
            />
          </div>

          <div className="flex items-center gap-1.5 p-1 rounded-xl bg-[#0E101D] border border-slate-700">
            {["ALL", "DECLARATION", "REFERENCE"].map((r) => (
              <button
                key={r}
                onClick={() => setRoleFilter(r)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all ${
                  roleFilter === r
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {r}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="overflow-x-auto max-h-96 overflow-y-auto">
        <table className="w-full text-xs font-mono text-left">
          <thead className="sticky top-0 bg-[#101324] border-b border-slate-800 text-slate-400">
            <tr>
              <th className="px-6 py-3.5 uppercase font-semibold">Identifier</th>
              <th className="px-6 py-3.5 uppercase font-semibold">Role</th>
              <th className="px-6 py-3.5 uppercase font-semibold">Type</th>
              <th className="px-6 py-3.5 uppercase font-semibold">Scope</th>
              <th className="px-6 py-3.5 uppercase font-semibold">Source Coordinates</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/40">
            {filtered.map((sym, i) => (
              <tr key={i} className="hover:bg-slate-800/25 transition-colors">
                <td className="px-6 py-3 font-semibold text-white">{sym.name}</td>
                <td className="px-6 py-3">
                  <span
                    className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold border ${
                      sym.role === "DECLARATION"
                        ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"
                        : "bg-slate-800/80 text-slate-300 border-slate-700"
                    }`}
                  >
                    {sym.role}
                  </span>
                </td>
                <td className="px-6 py-3 text-cyan-300 font-semibold">{sym.data_type || "—"}</td>
                <td className="px-6 py-3 text-slate-400">Scope #{sym.scope_id}</td>
                <td className="px-6 py-3 text-indigo-400 font-medium">
                  Line {sym.location.line}, Col {sym.location.column}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Root Compiler Dashboard
// ---------------------------------------------------------------------------
export default function CompilerDashboard({
  workload: workloadProp = null,
  apiUrl = null,
  onAnalyzed = null,
  useMockIfNoApi = true,
}) {
  const [code, setCode] = useState(SAMPLES["Array Sum"]);
  const [workload, setWorkload] = useState(workloadProp || MOCK_WORKLOAD);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAnalyze = async () => {
    if (!code.trim()) return;
    setLoading(true);
    setError(null);
    try {
      if (apiUrl) {
        const res = await fetch(`${apiUrl}/api/analyze`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ source_code: code }),
        });
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body?.detail?.message || `Execution failed (${res.status})`);
        }
        const data = await res.json();
        setWorkload(data.workload);
        if (onAnalyzed) onAnalyzed(data);
      } else if (useMockIfNoApi) {
        await new Promise((r) => setTimeout(r, 600));
        setWorkload(MOCK_WORKLOAD);
        if (onAnalyzed) {
          onAnalyzed({
            workload: MOCK_WORKLOAD,
            hash_analysis: {
              per_function: [
                { name: "DJB2", bucket_count: 67, items_inserted: 50, insert_time_sec: 0.000412, lookup_time_sec: 0.000891, lookups_performed: 120, collisions: 9, max_chain_length: 3, non_empty_buckets: 41, load_factor: 0.746, estimated_memory_bytes: 8432, bucket_distribution: [1,0,2,1,0,0,1,3,0,1,0,0,2,1,1,0,0,1,0,2,1,0,1,0,0,1,1,0,2,0,1,0,1,1,0,0,1,2,0,1,0,1,0,0,1,1,0,2,0,1,1,0,0,1,0,1,0,1,0,0,1,0,1,0,1,0,1] },
                { name: "FNV-1a", bucket_count: 67, items_inserted: 50, insert_time_sec: 0.000398, lookup_time_sec: 0.000743, lookups_performed: 120, collisions: 5, max_chain_length: 2, non_empty_buckets: 45, load_factor: 0.746, estimated_memory_bytes: 8432, bucket_distribution: [1,1,0,1,0,1,1,0,1,0,1,1,0,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1] },
                { name: "SDBM", bucket_count: 67, items_inserted: 50, insert_time_sec: 0.000405, lookup_time_sec: 0.000812, lookups_performed: 120, collisions: 7, max_chain_length: 3, non_empty_buckets: 43, load_factor: 0.746, estimated_memory_bytes: 8432, bucket_distribution: [0,1,1,2,0,1,0,1,1,0,3,0,1,0,1,1,0,1,0,1,1,0,0,1,1,0,1,1,0,1,0,1,1,0,1,0,0,1,1,0,2,0,1,0,1,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,0,1,1,0,1] },
                { name: "Jenkins (one-at-a-time)", bucket_count: 67, items_inserted: 50, insert_time_sec: 0.000487, lookup_time_sec: 0.000759, lookups_performed: 120, collisions: 6, max_chain_length: 2, non_empty_buckets: 44, load_factor: 0.746, estimated_memory_bytes: 8432, bucket_distribution: [1,0,1,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,0,1,1,0,1,1,0,1,0,1,0,1,1,0,1,0,1,1,0,1,1,0,1,0,1,0,1,1,0,1,1,0,1,0,1,1,0,1,0,1] },
                { name: "CRC32", bucket_count: 67, items_inserted: 50, insert_time_sec: 0.000521, lookup_time_sec: 0.000698, lookups_performed: 120, collisions: 4, max_chain_length: 2, non_empty_buckets: 46, load_factor: 0.746, estimated_memory_bytes: 8432, bucket_distribution: [1,1,0,1,1,0,1,1,0,1,1,0,1,1,0,1,0,1,1,0,1,1,0,1,1,0,1,1,0,1,0,1,1,0,1,1,0,1,1,0,1,0,1,1,0,1,1,0,1,1,0,1,0,1,1,0,1,1,0,1,1,0,1,1,0,1,1] },
              ],
              recommended_function: "CRC32",
              recommendation_reason: "CRC32 demonstrated superior entropy distribution with minimum collisions (4) and fast lookup throughput.",
              workload_summary: {
                total_identifiers: 120,
                unique_identifiers: 50,
                average_identifier_length: 6.4,
                uniqueness_ratio: 0.417,
                repetition_ratio: 0.583,
                scope_count: 4,
              },
            },
          });
        }
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
          AST Compiler Analysis Studio
        </h1>
        <p className="text-sm text-slate-400 font-mono mt-1">
          Lexical Token Extractor & Symbol Namespace Decomposition
        </p>
      </div>

      <CodeStudio
        code={code}
        setCode={setCode}
        onAnalyze={handleAnalyze}
        loading={loading}
      />

      {error && (
        <div className="rounded-2xl p-4 mb-6 bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm font-mono flex items-center gap-3">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" />
          {error}
        </div>
      )}

      {workload && (
        <>
          <TelemetryStrip metrics={workload.workload_metrics} />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <FrequencyAreaChart metrics={workload.workload_metrics} />
            <ScopeLoadBarChart metrics={workload.workload_metrics} scopes={workload.scopes} />
          </div>
          <ScopeHierarchy scopes={workload.scopes} />
          <SymbolTable symbols={workload.symbols} />
        </>
      )}
    </div>
  );
}