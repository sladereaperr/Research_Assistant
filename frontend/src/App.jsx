import React, { useEffect, useRef, useState } from "react";
import {
  Play,
  Loader2,
  FileText,
  AlertCircle,
  CheckCircle,
  Brain,
  Sparkles,
  Zap,
  TrendingUp,
  MessageSquare,
  ExternalLink,
  Target,
  FlaskConical,
  Database,
  Compass,
  Lightbulb,
  Beaker,
  Workflow,
  Cog,
} from "lucide-react";

// --- Utility to pick agent appearance ---
const getAgentInfo = (message) => {
  const msg = typeof message === "string" ? message : JSON.stringify(message);
  if (msg.includes("Domain Scout"))
    return { icon: Compass, accent: "from-blue-500 to-indigo-500" };
  if (msg.includes("Question Generator"))
    return { icon: Lightbulb, accent: "from-yellow-400 to-amber-500" };
  if (msg.includes("Data Alchemist"))
    return { icon: FlaskConical, accent: "from-emerald-400 to-emerald-600" };
  if (msg.includes("Experiment Designer"))
    return { icon: Beaker, accent: "from-cyan-400 to-cyan-600" };
  if (msg.includes("Critic"))
    return { icon: Target, accent: "from-amber-400 to-amber-600" };
  if (msg.includes("Orchestrator"))
    return { icon: Workflow, accent: "from-purple-400 to-purple-600" };
  if (msg.includes("System"))
    return { icon: Cog, accent: "from-slate-400 to-slate-600" };
  if (msg.includes("Error") || msg.includes("❌"))
    return { icon: AlertCircle, accent: "from-red-500 to-rose-600" };
  if (msg.includes("Complete") || msg.includes("✅"))
    return { icon: CheckCircle, accent: "from-green-400 to-emerald-600" };
  return { icon: MessageSquare, accent: "from-indigo-400 to-indigo-600" };
};

const agentNetwork = [
  { name: "Domain Scout", icon: Compass, desc: "Discovers emerging domains" },
  {
    name: "Question Generator",
    icon: Lightbulb,
    desc: "Formulates research questions",
  },
  {
    name: "Data Alchemist",
    icon: FlaskConical,
    desc: "Collects & processes data",
  },
  { name: "Experiment Designer", icon: Beaker, desc: "Designs experiments" },
  { name: "Critic", icon: Target, desc: "Evaluates & iterates" },
  { name: "Orchestrator", icon: Workflow, desc: "Coordinates agents" },
];

export default function AIResearchAssistant() {
  const [isRunning, setIsRunning] = useState(false);
  const [messages, setMessages] = useState([]);
  const [result, setResult] = useState(null);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [startTime, setStartTime] = useState(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const endRef = useRef(null);

  useEffect(() => {
    if (endRef.current) endRef.current.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    let t;
    if (isRunning && startTime) {
      t = setInterval(
        () => setElapsedTime(Math.floor((Date.now() - startTime) / 1000)),
        1000
      );
    }
    return () => clearInterval(t);
  }, [isRunning, startTime]);

  const formatTime = (s) =>
    `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

  const startResearch = async () => {
    setIsRunning(true);
    setMessages([]);
    setResult(null);
    setProgress(0);
    setError(null);
    setStartTime(Date.now());
    setElapsedTime(0);

    try {
      const res = await fetch("/api/research/start", { method: "POST" });
      if (!res.ok) throw new Error("Failed to start research");

      const reader = res.body.getReader();
      const dec = new TextDecoder();
      let buf = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        const parts = buf.split(/\r?\n/);
        buf = parts.pop() || "";
        for (const p of parts) {
          const line = p.trim();
          if (!line) continue;
          if (line.startsWith("data:")) {
            try {
              const d = JSON.parse(line.slice(5).trim());
              if (d.type === "message") {
                const content =
                  typeof d.content === "string"
                    ? d.content
                    : JSON.stringify(d.content);
                setMessages((m) => [...m, content]);
              } else if (d.type === "progress") {
                setProgress(typeof d.value === "number" ? d.value : progress);
              } else if (d.type === "complete") {
                const completeResult = d.result || null;
                // Ensure paperUrl is set even if sessionId is available
                if (
                  completeResult &&
                  completeResult.sessionId &&
                  !completeResult.paperUrl
                ) {
                  completeResult.paperUrl = `/api/research/paper/${completeResult.sessionId}`;
                }
                setResult(completeResult);
                setIsRunning(false);
              } else if (d.type === "error") {
                setError(d.message || "Unknown error");
                setIsRunning(false);
              }
            } catch (e) {
              setMessages((m) => [...m, line]);
            }
          } else {
            setMessages((m) => [...m, line]);
          }
        }
      }

      if (buf.trim()) setMessages((m) => [...m, buf.trim()]);
    } catch (err) {
      setError(err.message || String(err));
      setMessages((m) => [...m, `❌ Error: ${err.message || err}`]);
      setIsRunning(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-indigo-950 text-slate-100 py-12">
      <div className="max-w-7xl mx-auto px-6">
        {/* Header */}
        <header className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 mb-8">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-gradient-to-br from-indigo-700 to-purple-600 shadow-lg">
              <Brain size={44} className="text-white" />
            </div>
            <div>
              <h1 className="text-3xl sm:text-4xl font-extrabold text-white">
                AI Research Assistant
              </h1>
              <p className="text-sm text-slate-300">
                Autonomous multi-agent research orchestration
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 flex-wrap">
            <span className="px-3 py-1 rounded-full bg-slate-800/50 border border-slate-700 text-sm text-slate-300">
              Agents
            </span>
            <span className="px-3 py-1 rounded-full bg-slate-800/50 border border-slate-700 text-sm text-slate-300">
              Full Autonomy
            </span>
            <button
              onClick={startResearch}
              disabled={isRunning}
              className={`flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all ${
                isRunning
                  ? "bg-slate-700 cursor-not-allowed text-slate-400"
                  : "bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white hover:shadow-lg hover:shadow-indigo-500/50"
              }`}
            >
              {isRunning ? (
                <>
                  <Loader2 className="animate-spin" size={18} /> Running
                </>
              ) : (
                <>
                  <Play size={18} /> Start Research
                </>
              )}
            </button>
          </div>
        </header>

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-500/20 border-2 border-red-500/50 rounded-xl p-4 text-red-100">
            <div className="flex items-center gap-2">
              <AlertCircle size={20} />
              <span className="font-semibold">Error:</span>
              <span>{error}</span>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Activity logs */}
          <div className="lg:col-span-2 bg-slate-900/50 border border-slate-700 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-slate-700 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <MessageSquare size={18} className="text-indigo-300" />
                <h2 className="text-xl font-bold text-white">Activity Logs</h2>
              </div>
              <div className="flex items-center gap-3">
                {isRunning && (
                  <span className="text-emerald-400 text-sm font-semibold">
                    Live
                  </span>
                )}
                <span className="text-sm text-slate-400">
                  {formatTime(elapsedTime)}
                </span>
              </div>
            </div>
            <div className="h-[520px] overflow-y-auto bg-gradient-to-b from-slate-950/40 to-slate-900/40 p-4">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20">
                  <Sparkles size={48} className="text-indigo-500/30 mb-4" />
                  <p className="text-slate-400">
                    No activity yet — click{" "}
                    <span className="font-medium text-white">
                      Start Research
                    </span>
                    .
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {messages.map((m, i) => {
                    const agent = getAgentInfo(m);
                    const Icon = agent.icon;
                    return (
                      <div
                        key={i}
                        className="flex gap-3 items-start rounded-lg p-3 bg-slate-800/30 border border-slate-700 hover:bg-slate-800/50 transition-colors"
                      >
                        <div className="flex-shrink-0">
                          <div
                            className={`p-2 rounded-md bg-gradient-to-br ${agent.accent}`}
                          >
                            <Icon size={18} className="text-white opacity-95" />
                          </div>
                        </div>
                        <div className="flex-1 text-sm whitespace-pre-wrap break-words text-slate-200">
                          {m}
                        </div>
                      </div>
                    );
                  })}
                  <div ref={endRef} />
                </div>
              )}
            </div>
          </div>

          {/* Right: Results */}
          <div className="bg-slate-900/50 border border-slate-700 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-slate-700">
              <div className="flex items-center gap-3 mb-1">
                <FileText size={18} className="text-indigo-300" />
                <h2 className="text-xl font-bold text-white">Results</h2>
              </div>
              <p className="text-sm text-slate-400">Summary & artifacts</p>
            </div>
            <div className="p-4">
              {!result ? (
                <div className="py-12 text-center">
                  <FileText
                    size={56}
                    className="mx-auto text-indigo-600/20 mb-4"
                  />
                  <p className="text-slate-400 mb-2">
                    Results will appear here
                  </p>
                  <p className="text-xs text-slate-500">
                    When research completes, you'll get a paper link and
                    confidence scores.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Target size={16} className="text-indigo-400" />
                        <h4 className="font-semibold text-white">Domain</h4>
                      </div>
                      <span className="text-sm text-slate-300">
                        {result.domain || "—"}
                      </span>
                    </div>
                    <div className="h-px bg-slate-700 my-2" />
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <FlaskConical size={16} className="text-indigo-400" />
                        <h4 className="font-semibold text-white">
                          Research Question
                        </h4>
                      </div>
                      <span className="text-sm text-slate-300 text-right max-w-[60%]">
                        {result.question || "—"}
                      </span>
                    </div>
                    <div className="h-px bg-slate-700 my-2" />
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Database size={16} className="text-indigo-400" />
                        <h4 className="font-semibold text-white">Confidence</h4>
                      </div>
                      <div className="w-24 bg-slate-800 rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-emerald-500 to-green-500 h-2 rounded-full transition-all duration-1000"
                          style={{
                            width: `${Math.max(
                              0,
                              Math.min(100, result.confidence || 0)
                            )}%`,
                          }}
                        />
                      </div>
                    </div>
                    <p className="text-xs text-slate-400 mt-2">
                      {result.confidence >= 80
                        ? "🌟 High confidence"
                        : result.confidence >= 60
                        ? "✓ Moderate confidence"
                        : "⚠ Low confidence"}
                    </p>
                  </div>

                  {result && (result.paperUrl || result.sessionId) && (
                    <div className="mt-4 space-y-2">
                      <a
                        className="block"
                        href={
                          result.paperUrl ||
                          `/api/research/paper/${result.sessionId}`
                        }
                        target="_blank"
                        rel="noreferrer"
                      >
                        <button className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold rounded-lg transition-all hover:shadow-lg hover:shadow-indigo-500/50">
                          <FileText size={18} /> View Generated Paper
                          <ExternalLink size={16} />
                        </button>
                      </a>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Agent network */}
        <div className="mt-8">
          <div className="bg-slate-900/40 border border-slate-700 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-slate-700">
              <div className="flex items-center gap-3 mb-1">
                <Workflow size={18} className="text-indigo-300" />
                <h2 className="text-xl font-bold text-white">Agent Network</h2>
              </div>
              <p className="text-sm text-slate-400">
                Specialized AI agents working in harmony
              </p>
            </div>
            <div className="p-4">
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
                {agentNetwork.map((a, i) => {
                  const Icon = a.icon;
                  return (
                    <div
                      key={i}
                      className="p-3 rounded-xl bg-slate-800/30 border border-slate-700 flex flex-col items-center gap-2 hover:scale-105 hover:bg-slate-800/50 transition-all cursor-pointer"
                    >
                      <div className="p-2 rounded-md bg-gradient-to-br from-indigo-700 to-purple-600 shadow-md">
                        <Icon size={22} className="text-white" />
                      </div>
                      <div className="text-center">
                        <div className="text-sm font-semibold text-white">
                          {a.name}
                        </div>
                        <div className="text-xs text-slate-400">{a.desc}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-8 text-center text-slate-400">
          <div className="inline-flex items-center gap-4 py-3 px-5 rounded-2xl bg-slate-900/30 border border-slate-800">
            <div className="flex items-center gap-2">
              <Zap size={14} /> Fully Autonomous
            </div>
            <div className="h-4 w-px bg-slate-700" />
            <div className="flex items-center gap-2">
              <TrendingUp size={14} /> Self-Iterating
            </div>
            <div className="h-4 w-px bg-slate-700" />
            <div className="flex items-center gap-2">
              <Brain size={14} /> Zero Human Intervention
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
