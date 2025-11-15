import React, { useState } from "react";
import {
  Play,
  Loader2,
  FileText,
  AlertCircle,
  CheckCircle,
  Brain,
  Database,
  FlaskConical,
  Target,
  MessageSquare,
} from "lucide-react";

export default function App() {
  const [isRunning, setIsRunning] = useState(false);
  const [messages, setMessages] = useState([]);
  const [result, setResult] = useState(null);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);

  const startResearch = async () => {
    setIsRunning(true);
    setMessages([]);
    setResult(null);
    setProgress(0);
    setError(null);

    try {
      const response = await fetch("/api/research/start", {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Failed to start research");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Normalize newlines and split into SSE-style messages
        const parts = buffer.split(/\r?\n/);
        buffer = parts.pop() || "";

        for (const rawLine of parts) {
          const line = rawLine.trim();
          if (!line) continue;

          // SSE lines usually start with "data: "
          if (line.startsWith("data:")) {
            let jsonText = line.slice(5).trim();
            // Some servers use multiple data: lines or send `data: [json]\n\n`
            try {
              const data = JSON.parse(jsonText);

              if (data.type === "message") {
                // Ensure content is string (defensive)
                const content =
                  typeof data.content === "string"
                    ? data.content
                    : JSON.stringify(data.content);
                setMessages((prev) => [...prev, content]);
              } else if (data.type === "progress") {
                setProgress(
                  typeof data.value === "number" ? data.value : (prev) => prev
                );
              } else if (data.type === "complete") {
                setResult(data.result || null);
                setIsRunning(false);
              } else if (data.type === "error") {
                setError(data.message || "Unknown error from stream");
                setIsRunning(false);
              }
            } catch (e) {
              // not JSON — just push raw text so user can debug
              setMessages((prev) => [...prev, line]);
              console.warn("Could not parse SSE JSON:", jsonText, e);
            }
          } else {
            // Non data: line — push for debugging/visibility
            setMessages((prev) => [...prev, line]);
          }
        }
      }

      // Attempt to decode any leftover buffer
      if (buffer.trim()) {
        try {
          const maybe = buffer.trim();
          if (maybe.startsWith("data:")) {
            const jsonText = maybe.slice(5).trim();
            const data = JSON.parse(jsonText);
            if (data.type === "complete") setResult(data.result || null);
            if (data.type === "progress") setProgress(data.value || 0);
          } else {
            setMessages((prev) => [...prev, buffer.trim()]);
          }
        } catch {
          setMessages((prev) => [...prev, buffer.trim()]);
        }
      }
    } catch (err) {
      console.error("Error:", err);
      setError(err.message || "Unknown error");
      setMessages((prev) => [...prev, `❌ Error: ${err.message || err}`]);
      setIsRunning(false);
    }
  };

  const getAgentIcon = (message) => {
    const msg = typeof message === "string" ? message : JSON.stringify(message);
    if (msg.includes("Domain Scout")) return "🔍";
    if (msg.includes("Question Generator")) return "💡";
    if (msg.includes("Data Alchemist")) return "🧪";
    if (msg.includes("Experiment Designer")) return "🔬";
    if (msg.includes("Critic")) return "🎯";
    if (msg.includes("Orchestrator")) return "🎭";
    if (msg.includes("System")) return "⚙️";
    return "📝";
  };

  const getMessageColor = (message) => {
    const msg = typeof message === "string" ? message : JSON.stringify(message);
    if (msg.includes("Error") || msg.includes("❌"))
      return "border-l-red-500 bg-red-500/10";
    if (msg.includes("Complete") || msg.includes("✅"))
      return "border-l-green-500 bg-green-500/10";
    if (msg.includes("Critic")) return "border-l-yellow-500 bg-yellow-500/10";
    return "border-l-purple-500 bg-white/5";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4 sm:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8 sm:mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Brain className="text-purple-400" size={48} />
            <h1 className="text-3xl sm:text-5xl font-bold text-white">
              Autonomous AI Research Assistant
            </h1>
          </div>
          <p className="text-lg sm:text-xl text-purple-200">
            Multi-Agent System for Emerging Scientific Domain Discovery
          </p>
          <div className="mt-4 flex items-center justify-center gap-2 text-sm text-purple-300">
            <CheckCircle size={16} />
            <span>
              6 Specialized Agents • Zero Human Intervention • Full Autonomy
            </span>
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-500/20 border border-red-500 rounded-xl p-4 text-red-200">
            <div className="flex items-center gap-2">
              <AlertCircle size={20} />
              <span className="font-semibold">Error:</span>
            </div>
            <p className="mt-2">{error}</p>
          </div>
        )}

        {/* Control Panel */}
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 sm:p-8 mb-8 border border-white/20 shadow-2xl">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mb-6">
            <div className="text-center sm:text-left">
              <h2 className="text-2xl font-bold text-white mb-2">
                Research Control
              </h2>
              <p className="text-purple-200">
                Click to start autonomous research process
              </p>
            </div>
            <button
              onClick={startResearch}
              disabled={isRunning}
              className={`flex items-center gap-2 px-8 py-4 rounded-xl font-semibold text-lg transition-all transform hover:scale-105 ${
                isRunning
                  ? "bg-gray-600 cursor-not-allowed"
                  : "bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 shadow-lg hover:shadow-xl"
              } text-white w-full sm:w-auto justify-center`}
            >
              {isRunning ? (
                <>
                  <Loader2 className="animate-spin" size={24} />
                  Running...
                </>
              ) : (
                <>
                  <Play size={24} />
                  Start Research
                </>
              )}
            </button>
          </div>

          {/* Progress Bar */}
          {isRunning && (
            <div className="mb-4">
              <div className="flex justify-between text-sm text-purple-200 mb-2">
                <span>Research Progress</span>
                <span>{progress}%</span>
              </div>
              <div className="w-full bg-white/20 rounded-full h-3 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-purple-500 via-pink-500 to-purple-500 h-3 rounded-full transition-all duration-500 animate-pulse"
                  style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
                />
              </div>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8">
          {/* Messages Panel */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 shadow-2xl">
            <div className="flex items-center gap-2 mb-4">
              <MessageSquare className="text-purple-400" size={24} />
              <h3 className="text-xl font-bold text-white">Agent Activity</h3>
              {isRunning && (
                <div className="ml-auto">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  </div>
                </div>
              )}
            </div>
            <div className="space-y-2 max-h-96 overflow-y-auto scrollbar-thin scrollbar-thumb-purple-500 scrollbar-track-white/10">
              {messages.length === 0 ? (
                <div className="text-center py-12">
                  <Brain
                    className="mx-auto mb-4 text-purple-400/50"
                    size={48}
                  />
                  <p className="text-purple-200">
                    Waiting to start research...
                  </p>
                  <p className="text-purple-300 text-sm mt-2">
                    Click "Start Research" to begin autonomous analysis
                  </p>
                </div>
              ) : (
                messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`rounded-lg p-3 text-sm text-purple-100 border-l-4 ${getMessageColor(
                      msg
                    )} transition-all duration-300 hover:bg-white/10`}
                  >
                    <span className="mr-2">{getAgentIcon(msg)}</span>
                    <span className="whitespace-pre-wrap break-words">
                      {msg}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Results Panel */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 shadow-2xl">
            <div className="flex items-center gap-2 mb-4">
              <FileText className="text-purple-400" size={24} />
              <h3 className="text-xl font-bold text-white">Research Output</h3>
            </div>
            {!result ? (
              <div className="text-center py-12">
                <FileText
                  className="mx-auto mb-4 text-purple-400/50"
                  size={48}
                />
                <p className="text-purple-200">Results will appear here...</p>
                <p className="text-purple-300 text-sm mt-2">
                  The system will generate a complete research paper
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                  <h4 className="font-semibold text-white mb-2 flex items-center gap-2">
                    <Target size={16} className="text-purple-400" />
                    Domain
                  </h4>
                  <p className="text-purple-200">{result.domain || "—"}</p>
                </div>
                <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                  <h4 className="font-semibold text-white mb-2 flex items-center gap-2">
                    <FlaskConical size={16} className="text-purple-400" />
                    Research Question
                  </h4>
                  <p className="text-purple-200">{result.question || "—"}</p>
                </div>
                <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                  <h4 className="font-semibold text-white mb-2 flex items-center gap-2">
                    <Database size={16} className="text-purple-400" />
                    Confidence Score
                  </h4>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-white/20 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full transition-all duration-1000"
                        style={{
                          width: `${Math.max(
                            0,
                            Math.min(100, result.confidence || 0)
                          )}%`,
                        }}
                      />
                    </div>
                    <span className="text-white font-semibold">
                      {(typeof result.confidence === "number"
                        ? result.confidence
                        : 0
                      ).toFixed(1)}
                      %
                    </span>
                  </div>
                  <div className="mt-2 text-sm text-purple-300">
                    {result.confidence >= 80 && "🌟 High confidence"}
                    {result.confidence >= 60 &&
                      result.confidence < 80 &&
                      "✓ Moderate confidence"}
                    {result.confidence < 60 &&
                      "⚠ Low confidence - needs more iteration"}
                  </div>
                </div>

                {result.paperUrl ? (
                  <a
                    href={result.paperUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold py-3 px-4 rounded-lg text-center transition-all transform hover:scale-105 shadow-lg hover:shadow-xl"
                  >
                    📄 View Full Research Paper
                  </a>
                ) : (
                  <div className="text-center text-sm text-purple-300">
                    No paper URL available
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Agent Architecture Info */}
        <div className="mt-8 bg-white/10 backdrop-blur-lg rounded-2xl p-6 border border-white/20 shadow-2xl">
          <h3 className="text-xl font-bold text-white mb-4 text-center">
            Active Agent Network
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {[
              {
                name: "Domain Scout",
                icon: "🔍",
                desc: "Discovers emerging domains",
              },
              {
                name: "Question Generator",
                icon: "💡",
                desc: "Formulates research questions",
              },
              {
                name: "Data Alchemist",
                icon: "🧪",
                desc: "Collects & processes data",
              },
              {
                name: "Experiment Designer",
                icon: "🔬",
                desc: "Designs experiments",
              },
              { name: "Critic", icon: "🎯", desc: "Evaluates & iterates" },
              { name: "Orchestrator", icon: "🎭", desc: "Coordinates agents" },
            ].map((agent, idx) => (
              <div
                key={idx}
                className="bg-white/5 rounded-lg p-3 text-center border border-white/10 hover:bg-white/10 transition-all transform hover:scale-105"
                title={agent.desc}
              >
                <div
                  className={`w-3 h-3 rounded-full mx-auto mb-2 transition-all ${
                    isRunning
                      ? "bg-green-500 animate-pulse shadow-lg shadow-green-500/50"
                      : "bg-gray-500"
                  }`}
                />
                <div className="text-2xl mb-1">{agent.icon}</div>
                <p className="text-xs text-purple-200 font-medium">
                  {agent.name}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-purple-300 text-sm">
          <p>
            Powered by Google Gemini • LangGraph • Multi-Agent Orchestration
          </p>
          <p className="mt-2">
            🚀 Fully Autonomous • 🔄 Self-Iterating • 🧠 Zero Human Intervention
          </p>
        </div>
      </div>
    </div>
  );
}
