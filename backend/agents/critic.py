from ..utils.async_utils import maybe_await
from typing import Dict, Any, List
from ..utils.llm import llm_client
from ..utils.memory import memory_manager

class CriticAgent:
    def __init__(self):
        self.name = "Critic"
    
    async def critique_research(self, state: Any) -> Dict[str, Any]:
        """Critically evaluate the research"""
        experiment_results = state.experiment_results
        
        state.add_message(f"🎯 {self.name}: Initiating critical analysis...")
        
        # Critique methodology
        methodology_critique = await self._critique_methodology(state)
        
        # Critique results
        results_critique = await self._critique_results(state)
        
        # Critique limitations
        limitations = await self._identify_limitations(state)
        
        # Overall assessment
        overall_score = await self._overall_assessment(
            methodology_critique,
            results_critique,
            experiment_results
        )
        
        state.add_message(f"📋 {self.name}: Analysis complete. Overall quality score: {overall_score:.2f}/10")
        
        # Determine if iteration is needed
        should_iterate = self._should_iterate(overall_score, state)
        
        if should_iterate and state.iteration_count < state.max_iterations:
            state.add_message(f"🔄 {self.name}: Recommending iteration to address identified issues")
            state.should_iterate = True
        else:
            state.add_message(f"✅ {self.name}: Research meets quality threshold or max iterations reached")
            state.should_iterate = False
        
        critique = {
            "methodology": methodology_critique,
            "results": results_critique,
            "limitations": limitations,
            "overall_score": overall_score,
            "should_iterate": should_iterate,
            "recommendations": self._generate_recommendations(methodology_critique, results_critique)
        }
        
        state.critiques.append(critique)
        state.confidence_scores['critique'] = overall_score * 10
        
        # Add to memory
        memory_manager.add_memory(
            f"Critique iteration {state.iteration_count + 1}: Score {overall_score}/10",
            {"type": "critique", "agent": self.name}
        )
        
        return critique
    

    async def _critique_methodology(self, state: Any) -> Dict[str, Any]:
        """Critique the experimental methodology (robust to LLM returning list)"""
        design = state.experiment_design

        state.add_message(f"🔍 {self.name}: Evaluating methodology...")

        prompt = f"""Critically evaluate this experimental methodology:

Hypothesis: {state.hypothesis}
Methodology: {design}

Identify:
1. Strengths (2-3 points)
2. Weaknesses (2-3 points)
3. Potential biases
4. Missing controls

Return ONLY JSON:
{{
  "strengths": ["strength1", "strength2"],
  "weaknesses": ["weakness1", "weakness2"],
  "biases": ["bias1", "bias2"],
  "missing_controls": ["control1", "control2"],
  "methodology_score": 0-10
}}"""

        raw = await maybe_await(llm_client.generate_json(prompt, temperature=0.6))

        # Defensive normalization: if LLM returned a list, take the first element if it's a dict
        critique = {}
        if isinstance(raw, list):
            if len(raw) == 0:
                critique = {}
            else:
                first = raw[0]
                if isinstance(first, dict):
                    critique = first
                else:
                    # if it's a list of strings etc., wrap sensibly
                    critique = {"strengths": first if isinstance(first, list) else [str(first)]}
        elif isinstance(raw, dict):
            critique = raw
        else:
            critique = {}

        # fallback defaults
        critique.setdefault("strengths", ["Clear hypothesis formulation", "Appropriate statistical test selected"])
        critique.setdefault("weaknesses", ["Limited sample size", "Potential confounding variables not addressed"])
        critique.setdefault("biases", ["Selection bias in data collection"])
        critique.setdefault("missing_controls", ["Need for randomization", "Lack of blinding"])
        # ensure a numeric methodology_score
        try:
            ms = float(critique.get("methodology_score", 6.5))
            critique["methodology_score"] = max(0.0, min(10.0, ms))
        except Exception:
            critique["methodology_score"] = 6.5

        return critique


    async def _critique_results(self, state: Any) -> Dict[str, Any]:
        """Critique the results (robust to LLM returning list)"""
        results = state.experiment_results

        state.add_message(f"📊 {self.name}: Analyzing statistical validity...")

        stats = results.get('statistical_results', {}) if isinstance(results, dict) else {}
        p_value = stats.get('p_value', 1.0)
        effect_size = stats.get('effect_size', 0.0)

        prompt = f"""Critically evaluate these results:

P-value: {p_value}
Effect Size: {effect_size}
Interpretation: {results.get('interpretation', 'None') if isinstance(results, dict) else 'None'}

Assess:
1. Statistical significance
2. Practical significance
3. Potential issues
4. Alternative explanations

Return ONLY JSON:
{{
  "statistical_validity": "assessment",
  "practical_significance": "assessment",
  "issues": ["issue1", "issue2"],
  "alternative_explanations": ["explanation1", "explanation2"],
  "results_score": 0-10
}}"""

        raw = await maybe_await(llm_client.generate_json(prompt, temperature=0.6))

        # Normalize like above
        critique = {}
        if isinstance(raw, list):
            first = raw[0] if raw else {}
            critique = first if isinstance(first, dict) else {}
        elif isinstance(raw, dict):
            critique = raw
        else:
            critique = {}

        # sensible defaults if LLM failed or structure unexpected
        if "statistical_validity" not in critique:
            critique["statistical_validity"] = "Marginally significant" if p_value < 0.10 else "Not significant"
        if "practical_significance" not in critique:
            critique["practical_significance"] = "Moderate effect size" if abs(effect_size) > 0.3 else "Small effect"
        critique.setdefault("issues", ["Limited statistical power", "Potential Type II error"])
        critique.setdefault("alternative_explanations", ["Random variation", "Unmeasured confounders"])
        try:
            rs = float(critique.get("results_score", 7.0 if p_value < 0.05 else 5.0))
            critique["results_score"] = max(0.0, min(10.0, rs))
        except Exception:
            critique["results_score"] = 7.0 if p_value < 0.05 else 5.0

        return critique

    
    async def _identify_limitations(self, state: Any) -> List[str]:
        """Identify research limitations"""
        state.add_message(f"⚠️ {self.name}: Documenting limitations...")
        
        limitations = [
            "Limited sample size may affect generalizability",
            "Synthetic data components reduce real-world applicability",
            "Cross-sectional design limits causal inference",
            "Potential unmeasured confounding variables",
            "Limited external validity due to data sources"
        ]
        
        # Add specific limitations based on results
        if state.experiment_results:
            stats = state.experiment_results.get('statistical_results', {})
            if stats.get('p_value', 1.0) > 0.05:
                limitations.append("Results do not reach conventional statistical significance")
            if abs(stats.get('effect_size', 0.0)) < 0.3:
                limitations.append("Small effect size limits practical implications")
        
        return limitations[:5]
    
    async def _overall_assessment(
        self,
        methodology_critique: Dict[str, Any] | list,
        results_critique: Dict[str, Any] | list,
        experiment_results: Dict[str, Any]
    ) -> float:
        """Calculate overall quality score (handles list or dict critiques)"""
        # normalize inputs if LLM returned lists unexpectedly
        if isinstance(methodology_critique, list):
            methodology_critique = methodology_critique[0] if methodology_critique else {}
        if isinstance(results_critique, list):
            results_critique = results_critique[0] if results_critique else {}

        method_score = float(methodology_critique.get('methodology_score', 6.0))
        results_score = float(results_critique.get('results_score', 6.0))

        # Adjust based on confidence
        confidence = experiment_results.get('confidence', 0.5) if isinstance(experiment_results, dict) else 0.5
        confidence_bonus = confidence * 2  # Up to 2 points for high confidence

        overall = (method_score + results_score) / 2 + confidence_bonus
        overall = min(10.0, max(0.0, overall))

        return round(overall, 1)

    
    def _should_iterate(self, overall_score: float, state: Any) -> bool:
        """Determine if iteration is needed"""
        # Never iterate if we've reached max iterations
        if state.iteration_count >= state.max_iterations:
            return False
        
        # Don't iterate if we've already done at least one iteration and score is decent
        if state.iteration_count >= 1 and overall_score >= 6.5:
            return False
        
        # Iterate if score is below threshold (only on first iteration)
        if state.iteration_count == 0 and overall_score < 6.0:
            return True
        
        # Don't iterate if score is good enough
        if overall_score >= 7.0:
            return False
        
        # Check if p-value is too high (only iterate once for this)
        if state.iteration_count == 0 and state.experiment_results:
            stats = state.experiment_results.get('statistical_results', {})
            if stats.get('p_value', 0.0) > 0.10:  # More lenient threshold
                return True
        
        return False
    
    def _generate_recommendations(
        self,
        methodology_critique: Dict[str, Any],
        results_critique: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for improvement"""
        recommendations = []
        
        # Based on methodology weaknesses
        weaknesses = methodology_critique.get('weaknesses', [])
        for weakness in weaknesses[:2]:
            recommendations.append(f"Address {weakness} in next iteration")
        
        # Based on results issues
        issues = results_critique.get('issues', [])
        for issue in issues[:2]:
            recommendations.append(f"Mitigate {issue} with additional analysis")
        
        # General recommendations
        recommendations.extend([
            "Increase sample size for more robust results",
            "Consider alternative statistical approaches",
            "Validate findings with independent dataset"
        ])
        
        return recommendations[:5]

# Global agent instance
critic = CriticAgent()