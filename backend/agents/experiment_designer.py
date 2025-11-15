from ..utils.async_utils import maybe_await

from typing import Dict, Any, List
from ..utils.llm import llm_client
from ..tools.data_processor import data_processor
from ..utils.memory import memory_manager
import numpy as np
from scipy.stats import linregress


class ExperimentDesignerAgent:
    def __init__(self):
        self.name = "Experiment Designer"

    async def design_experiment(self, state: Any) -> Dict[str, Any]:
        """Design and execute experiments (keeps original LLM hypothesis step)."""
        question = getattr(state, "selected_question", {}) or {}
        data = getattr(state, "collected_data", {}).get("cleaned", {}) or {}

        state.add_message(f"🔬 {self.name}: Analyzing data structure and formulating hypothesis...")

        # Formulate hypothesis (existing behavior)
        prompt = f"""Based on this research question and available data, formulate a testable hypothesis.

Question: {question.get('question', 'Unknown')}
Available Data: {list(data.keys())}

Return ONLY JSON:
{{
  "hypothesis": "clear, testable hypothesis statement",
  "null_hypothesis": "corresponding null hypothesis",
  "test_type": "t-test|correlation|regression|anova",
  "expected_outcome": "what we expect to find",
  "significance_level": 0.05
}}"""

        hypothesis_data = await maybe_await(llm_client.generate_json(prompt))


        if not hypothesis_data or not isinstance(hypothesis_data, dict) or "hypothesis" not in hypothesis_data:
            hypothesis_data = self._get_fallback_hypothesis(question)

        state.add_message(f"💭 {self.name}: Hypothesis: {hypothesis_data.get('hypothesis', 'Unknown')}")

        # Design experiment metadata (existing behavior)
        state.add_message(f"⚗️ {self.name}: Designing experimental protocol...")

        experiment_design = {
            "hypothesis": hypothesis_data,
            "methodology": self._design_methodology(hypothesis_data, data),
            "variables": self._identify_variables(data),
        }

        state.add_message(f"🧮 {self.name}: Executing statistical analysis...")

        # --- NEW: advanced analysis (replaces older _execute_experiment behavior) ---
        results = await self._run_advanced_analysis(data)

        state.add_message(f"📊 {self.name}: Analysis complete. Interpreting results...")

        # Interpret results using existing _interpret_results (keeps LLM-based interpretation)
        interpretation = await self._interpret_results(results.get("statistical_results", {}), hypothesis_data)

        # calculate confidence (reuse your function but feed merged view)
        confidence = self._calculate_confidence(results.get("statistical_results", {}))

        state.add_message(f"✨ {self.name}: Experiment complete (confidence: {confidence:.2%})")

        # Add to memory (keeps your memory usage) — accept memory_manager API as synchronous
        try:
            mem_text = f"Experiment: {hypothesis_data.get('hypothesis', 'Unknown')} - p-value: {results.get('statistical_results', {}).get('p_value', 'N/A')}"
            memory_manager.add_memory(mem_text, {"type": "experiment", "agent": self.name})
        except Exception:
            # don't crash agent if memory subsystem fails
            state.add_message(f"⚠️ {self.name}: Failed to persist experiment to memory (non-fatal).")

        # Populate state in the same structure your code expects
        state.hypothesis = hypothesis_data.get("hypothesis")
        state.experiment_design = experiment_design
        state.experiment_results = {
            "statistical_results": results.get("statistical_results", {}),
            "interpretation": interpretation,
            "confidence": confidence,
            "detailed": results.get("detailed", {}),
        }
        # keep old convention: percentage in confidence_scores
        state.confidence_scores = getattr(state, "confidence_scores", {})
        state.confidence_scores["experiment"] = confidence * 100

        return {
            "hypothesis": hypothesis_data,
            "design": experiment_design,
            "results": results.get("statistical_results", {}),
            "interpretation": interpretation,
            "confidence": confidence,
        }

    async def _run_advanced_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        The improved `design_and_run` logic adapted for the agent.
        Returns dict with 'statistical_results', 'detailed', 'interpretation'.
        """
        results: Dict[str, Any] = {}

        # Find numeric lists (heuristic: a list with at least 2 numeric entries and finite values)
        numeric_keys: List[str] = []
        for k, v in data.items():
            if isinstance(v, list) and len(v) >= 2:
                sample = v[:min(5, len(v))]
                if all(isinstance(x, (int, float, np.number)) and np.isfinite(float(x)) for x in sample):
                    numeric_keys.append(k)

        # Descriptive stats
        detailed: Dict[str, Any] = {}
        try:
            descriptive = {k: data_processor.compute_statistics(data[k]) for k in numeric_keys}
            detailed["descriptive"] = descriptive
        except Exception as e:
            detailed["descriptive"] = {"error": str(e)}

        # t-test (first two numeric series)
        if len(numeric_keys) >= 2:
            try:
                g1 = [float(x) for x in data[numeric_keys[0]][:200] if np.isfinite(float(x))]
                g2 = [float(x) for x in data[numeric_keys[1]][:200] if np.isfinite(float(x))]
                ttest = data_processor.perform_ttest(g1, g2)
                # ensure keys exist and normalized
                if not isinstance(ttest, dict):
                    ttest = {"p_value": ttest} if isinstance(ttest, (int, float)) else {"error": "unexpected t-test result"}
                detailed["t_test"] = ttest
                detailed["group1_stats"] = data_processor.compute_statistics(g1)
                detailed["group2_stats"] = data_processor.compute_statistics(g2)
            except Exception as e:
                detailed["t_test"] = {"error": str(e)}

        # Linear regression (first vs second)
        if len(numeric_keys) >= 2:
            try:
                x = np.array([float(v) for v in data[numeric_keys[0]][:500] if np.isfinite(float(v))])
                y = np.array([float(v) for v in data[numeric_keys[1]][:500] if np.isfinite(float(v))])
                L = min(len(x), len(y))
                if L >= 2:
                    x = x[:L]
                    y = y[:L]
                    slope, intercept, r_value, p_value, std_err = linregress(x, y)
                    lr = {
                        "slope": float(slope),
                        "intercept": float(intercept),
                        "r_squared": float(r_value ** 2),
                        "p_value": float(p_value),
                        "std_err": float(std_err),
                    }
                    detailed["linear_regression"] = lr
                else:
                    detailed["linear_regression"] = {"error": "not enough paired samples for regression"}
            except Exception as e:
                detailed["linear_regression"] = {"error": str(e)}

        # Correlations (use data_processor.correlation_analysis)
        if len(numeric_keys) >= 2:
            try:
                corr_input = {k: [float(v) for v in data[k][:500] if np.isfinite(float(v))] for k in numeric_keys}
                corr_res = data_processor.correlation_analysis(corr_input)
                detailed["correlations"] = corr_res
            except Exception as e:
                detailed["correlations"] = {"error": str(e)}

        results["detailed"] = detailed

        # Compose 'statistical_results' top-level summary to match your system expectations
        # Prefer explicit None checks (0 should be honored)
        stat_p_value = None
        stat_effect_size = None
        stat_significant = False

        # prefer t-test p-value if available and valid
        t_test = detailed.get("t_test")
        if isinstance(t_test, dict) and "p_value" in t_test and t_test.get("p_value") is not None:
            try:
                stat_p_value = float(t_test.get("p_value"))
            except Exception:
                stat_p_value = None

            # effect size if present
            if "effect_size" in t_test and t_test.get("effect_size") is not None:
                try:
                    stat_effect_size = float(t_test.get("effect_size"))
                except Exception:
                    stat_effect_size = None

            stat_significant = bool(t_test.get("significant", False))

        # fallback to linear regression p-value if t-test absent
        if stat_p_value is None:
            lr = detailed.get("linear_regression", {})
            if isinstance(lr, dict) and lr.get("p_value") is not None:
                try:
                    stat_p_value = float(lr.get("p_value"))
                except Exception:
                    stat_p_value = None
            if stat_effect_size is None and isinstance(lr, dict) and lr.get("r_squared") is not None:
                try:
                    stat_effect_size = float(lr.get("r_squared"))
                except Exception:
                    stat_effect_size = None
            if stat_p_value is not None:
                stat_significant = stat_p_value < 0.05

        # final safe defaults
        if stat_p_value is None:
            stat_p_value = 1.0
        if stat_effect_size is None:
            stat_effect_size = 0.0

        results["statistical_results"] = {
            "p_value": float(stat_p_value),
            "effect_size": float(stat_effect_size),
            "significant": bool(stat_significant),
        }

        # Programmatic summary (keeps your _summarize_results idea)
        results["interpretation"] = self._summarize_results(detailed)

        return results

    async def _interpret_results(self, results: Dict[str, Any], hypothesis: Dict[str, Any]) -> str:
        """
        Keep your LLM-based interpretation function but accept new results shape.
        `results` is expected to be a dict representing statistical_results summary.
        """
        # results here will be the 'statistical_results' summary dict.
        p_value = float(results.get("p_value", 1.0))
        effect_size = float(results.get("effect_size", 0.0))
        significant = bool(results.get("significant", False))

        prompt = f"""Interpret these experimental results in the context of the hypothesis.

Hypothesis: {hypothesis.get('hypothesis', 'Unknown')}
P-value: {p_value}
Effect Size: {effect_size}
Significant: {significant}

Provide a clear, scientific interpretation (2-3 sentences)."""

        interpretation = await maybe_await(llm_client.generate(prompt, temperature=0.7))


        if not interpretation:
            if significant:
                interpretation = (
                    f"The results show statistical significance (p={p_value:.4f}), suggesting support for the hypothesis. "
                    f"The effect size of {effect_size:.3f} indicates a meaningful practical impact."
                )
            else:
                interpretation = (
                    f"The results do not show statistical significance (p={p_value:.4f}). "
                    "The hypothesis cannot be supported with the current data and methodology."
                )

        return interpretation

    def _design_methodology(self, hypothesis: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        test_type = hypothesis.get("test_type", "t-test")
        sample_size = 0
        try:
            sample_size = sum(len(v) for v in data.values() if isinstance(v, list))
        except Exception:
            sample_size = 0

        return {
            "test_type": test_type,
            "sample_size": sample_size,
            "controls": "Standard statistical controls applied",
            "procedure": f"Perform {test_type} analysis on available datasets",
        }

    def _identify_variables(self, data: Dict[str, Any]) -> Dict[str, Any]:
        keys = list(data.keys())
        independent = keys[:2] if len(keys) >= 2 else keys[:]
        dependent = keys[2:] if len(keys) > 2 else []
        return {"independent": independent, "dependent": dependent}

    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Keep your confidence logic; results here is the 'statistical_results' dict."""
        p_value = float(results.get("p_value", 1.0))
        effect_size = abs(float(results.get("effect_size", 0.0)))

        if p_value < 0.01 and effect_size > 0.5:
            return 0.90
        elif p_value < 0.05 and effect_size > 0.3:
            return 0.75
        elif p_value < 0.10:
            return 0.60
        else:
            return 0.45

    def _summarize_results(self, detailed_results: Dict[str, Any]) -> str:
        """Adapted summarize that reads the 'detailed' dict."""
        parts: List[str] = []
        tt = detailed_results.get("t_test")
        if isinstance(tt, dict):
            if "error" in tt:
                parts.append("T-test could not be completed.")
            else:
                p_val = tt.get("p_value")
                eff = tt.get("effect_size")
                sig = tt.get("significant", False)
                try:
                    parts.append(
                        f"T-test p={float(p_val):.4f}, effect size={float(eff):.3f} ({'significant' if sig else 'not significant'})"
                    )
                except Exception:
                    parts.append("T-test result available (could not format numeric values).")

        lr = detailed_results.get("linear_regression")
        if isinstance(lr, dict):
            if "error" in lr:
                parts.append("Regression failed to fit.")
            else:
                try:
                    parts.append(f"Linear regression R^2={float(lr.get('r_squared', 0.0)):.3f}, p={float(lr.get('p_value', 1.0)):.4g}")
                except Exception:
                    parts.append("Linear regression result available (could not format).")

        corr = detailed_results.get("correlations")
        if isinstance(corr, dict):
            strong = corr.get("strong_correlations") or []
            if isinstance(strong, (list, tuple)) and len(strong) > 0:
                parts.append(f"Found strong correlations: {len(strong)} pairs")

        return " ".join(parts) if parts else "No statistical analysis performed."

    def _get_fallback_hypothesis(self, question: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "hypothesis": f"There is a significant relationship between the variables relevant to: {question.get('question', 'the research question')}",
            "null_hypothesis": "There is no significant relationship between the variables",
            "test_type": "t-test",
            "expected_outcome": "Statistical significance at p < 0.05",
            "significance_level": 0.05,
        }


# create a global instance (keeps same API as before)
experiment_designer = ExperimentDesignerAgent()
