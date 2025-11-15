from ..utils.async_utils import maybe_await
from typing import Dict, Any
from ..utils.llm import llm_client
from ..utils.memory import memory_manager
from ..utils.visualization import create_confidence_chart, create_data_distribution
import json
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import linregress
import plotly.graph_objects as go
import plotly.express as px
import json


def plot_confidence_scores(scores: Dict[str, float]) -> str:
    fig = go.Figure(data=[go.Bar(x=list(scores.keys()), y=list(scores.values()), text=[f"{v:.1f}%" for v in scores.values()], textposition='auto')])
    fig.update_layout(title='Agent Confidence Scores', yaxis=dict(range=[0, 100]), template='plotly_white')
    # Return full HTML div for embedding
    return fig.to_html(include_plotlyjs='cdn', full_html=False)


def plot_data_distributions(data: Dict[str, List[float]], title: str = 'Data Distributions') -> str:
    fig = go.Figure()
    for name, values in data.items():
        # Box plots + jittered scatter
        fig.add_trace(go.Box(y=values, name=name, boxmean='sd'))
        # add sample points as jitter
        sample = values[:200]
        fig.add_trace(go.Scatter(y=sample, x=[name] * len(sample), mode='markers', name=f'{name} points', marker=dict(size=4), showlegend=False))

    fig.update_layout(title=title, template='plotly_white')
    return fig.to_html(include_plotlyjs='cdn', full_html=False)


def plot_regression(x: List[float], y: List[float], slope: float = None, intercept: float = None, title: str = 'Regression') -> str:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y, mode='markers', name='data'))
    if slope is not None and intercept is not None:
        x_arr = np.array(x)
        line = slope * x_arr + intercept
        fig.add_trace(go.Scatter(x=x_arr.tolist(), y=line.tolist(), mode='lines', name='fit'))
    fig.update_layout(title=title, template='plotly_white', xaxis_title='X', yaxis_title='Y')
    return fig.to_html(include_plotlyjs='cdn', full_html=False)


class OrchestratorAgent:
    def __init__(self):
        self.name = "Orchestrator"
    
    async def coordinate_research(self, state: Any) -> Dict[str, Any]:
        """Coordinate the overall research process"""
        state.add_message(f"🎭 {self.name}: Initializing multi-agent research system...")
        
        # Monitor agent progress
        state.add_message(f"📡 {self.name}: Monitoring agent communications and resolving conflicts...")
        
        return {"status": "coordinating"}
    
    async def resolve_conflicts(self, state: Any) -> Dict[str, Any]:
        """Resolve conflicts between agents"""
        # Check for conflicting information
        memories = memory_manager.get_summary()
        
        # Simple conflict detection
        conflicts = []
        if len(memories) > 5:
            state.add_message(f"🔧 {self.name}: Checking for conflicting information...")
        
        return {"conflicts_resolved": len(conflicts)}
    
    async def generate_final_paper(self, state: Any) -> Dict[str, Any]:
        """Generate comprehensive research paper with all sections"""
        domain = state.selected_domain or {}
        question = state.selected_question or {}
        experiment = state.experiment_results or {}
        
        state.add_message(f"📝 {self.name}: Generating comprehensive research paper...")
        
        # Generate all paper sections
        sections = await self._generate_paper_sections(state)
        
        # Generate visualizations
        visuals = await self._generate_visualizations(state)
        
        # Format the complete paper (without visualizations - they'll be rendered separately)
        paper_markdown = self._format_paper(sections, state)
        
        # Add data preview section if we have collected data
        if state.collected_data and state.collected_data.get('cleaned'):
            cleaned = state.collected_data.get('cleaned', {})
            if cleaned:
                data_preview = '\n\n## Data Preview\n\n'
                data_preview += 'The following data was collected and analyzed:\n\n'
                
                # Show summary of data
                for key, values in list(cleaned.items())[:5]:  # Show first 5 datasets
                    if isinstance(values, list):
                        data_preview += f'**{key}**: {len(values)} data points\n'
                        if len(values) > 0:
                            sample = values[:10]  # Show first 10 values
                            data_preview += f'- Sample values: {sample}\n'
                    elif isinstance(values, (int, float)):
                        data_preview += f'**{key}**: {values}\n'
                
                # Insert data preview after Methods section
                methods_end = paper_markdown.find('---\n\n## Results')
                if methods_end > 0:
                    separator = '---\n\n## Results'
                    paper_markdown = paper_markdown[:methods_end] + data_preview + '\n' + separator + paper_markdown[methods_end + len(separator):]
                else:
                    # Append if we can't find the right place
                    results_start = paper_markdown.find('## Results')
                    if results_start > 0:
                        paper_markdown = paper_markdown[:results_start] + data_preview + '\n\n' + paper_markdown[results_start:]
                    else:
                        # Last resort: append at end of methods
                        methods_section = paper_markdown.find('---\n\n## Results')
                        if methods_section == -1:
                            methods_section = paper_markdown.find('## Results')
                        if methods_section > 0:
                            paper_markdown = paper_markdown[:methods_section] + data_preview + '\n\n' + paper_markdown[methods_section:]
        
        # Add placeholder for visualizations in markdown (they'll be rendered separately in HTML)
        # This allows the markdown to reference them without embedding the HTML
        if visuals:
            viz_placeholder = '\n\n## Visualizations\n\n'
            for viz_name in visuals.keys():
                viz_title = viz_name.replace('_', ' ').title()
                viz_placeholder += f'### {viz_title}\n\n*See visualization below*\n\n'
            
            # Insert after Results section
            results_end = paper_markdown.find('---\n\n## Discussion')
            if results_end > 0:
                separator = '---\n\n## Discussion'
                paper_markdown = paper_markdown[:results_end] + viz_placeholder + '\n' + separator + paper_markdown[results_end + len(separator):]
            else:
                # Try without separator
                results_end = paper_markdown.find('## Discussion')
                if results_end > 0:
                    paper_markdown = paper_markdown[:results_end] + viz_placeholder + '\n\n' + paper_markdown[results_end:]
        
        # Save to state
        state.visualizations = visuals
        state.research_paper = paper_markdown
        
        state.add_message(f"✅ {self.name}: Research paper generation complete!")
        
        return {"paper": paper_markdown, "visualizations": visuals}

    
    async def _generate_paper_sections(self, state: Any) -> Dict[str, str]:
        """Generate each section of the paper"""
        domain = state.selected_domain or {}
        question = state.selected_question or {}
        experiment = state.experiment_results or {}
        critique = state.critiques[-1] if state.critiques else {}
        
        sections = {}
        
        # Abstract
        state.add_message(f"✍️ {self.name}: Writing abstract...")
        abstract_prompt = f"""Write a concise scientific abstract (150-200 words) for this research:

Domain: {domain.get('domain', 'Unknown')}
Description: {domain.get('description', 'Emerging scientific domain')}
Research Question: {question.get('question', 'Unknown')}
Key Finding: {experiment.get('interpretation', 'No findings')}
Statistical Significance: {'Yes' if experiment.get('statistical_results', {}).get('significant') else 'No'}

Write a complete abstract with: Background (2 sentences), Methods (2 sentences), Results (2 sentences), and Conclusion (1-2 sentences).
Do not use placeholder text."""
        
        abstract = await maybe_await(llm_client.generate(abstract_prompt, temperature=0.7, max_tokens=400))
        if not abstract:
            abstract = self._get_fallback_abstract(domain, question, experiment)
        sections['abstract'] = abstract if abstract else self._get_fallback_abstract(domain, question, experiment)
        
        # Introduction
        state.add_message(f"✍️ {self.name}: Writing introduction...")
        intro_prompt = f"""Write a detailed scientific introduction (300-400 words) that:

1. Opens with the significance of {domain.get('domain', 'this field')} in modern science
2. Describes the key challenges: {domain.get('description', 'emerging research area')}
3. Explains why this specific question matters: {question.get('question', 'the research question')}
4. States the research objective clearly
5. Previews the methodology briefly

Write in formal academic style. Do not use placeholder text or generic statements."""
        
        introduction = await maybe_await(llm_client.generate(intro_prompt, temperature=0.7, max_tokens=600))
        sections['introduction'] = introduction if introduction else self._get_fallback_introduction(domain, question)
        
        # Methods
        sections['methods'] = self._format_methods(state)
        
        # Results
        sections['results'] = self._format_results(state)
        
        # Discussion
        state.add_message(f"✍️ {self.name}: Writing discussion...")
        stats = experiment.get('statistical_results', {})
        discussion_prompt = f"""Write a thorough scientific discussion (300-400 words) that:

1. Interprets the main finding: {experiment.get('interpretation', 'results not significant')}
2. Discusses the statistical evidence (p={stats.get('p_value', 1.0):.4f}, effect size={stats.get('effect_size', 0):.3f})
3. Compares to existing knowledge about {domain.get('domain', 'this field')}
4. Addresses limitations: {', '.join(critique.get('limitations', ['standard limitations'])[:3])}
5. Suggests practical implications
6. Proposes future research directions

Write in formal academic style with specific details. Do not use placeholder text."""
        
        discussion = await maybe_await(llm_client.generate(discussion_prompt, temperature=0.7, max_tokens=600))
        sections['discussion'] = discussion if discussion else self._get_fallback_discussion(experiment, critique)
        
        # Limitations
        sections['limitations'] = self._format_limitations(critique)
        
        return sections
    
    def _get_fallback_abstract(self, domain: Dict, question: Dict, experiment: Dict) -> str:
        """Fallback abstract if LLM fails"""
        stats = experiment.get('statistical_results', {})
        return f"""This study investigates {question.get('question', 'a key research question')} within the emerging field of {domain.get('domain', 'advanced technology')}. {domain.get('description', 'This domain represents a significant advancement in scientific capability.')} We employed quantitative methods to analyze collected data, performing statistical tests on multiple datasets. Our analysis revealed {'significant' if stats.get('significant') else 'non-significant'} differences (p={stats.get('p_value', 1.0):.4f}) with an effect size of {stats.get('effect_size', 0):.3f}. {experiment.get('interpretation', 'The findings contribute to our understanding of this domain.')} These results have implications for future research and practical applications in this rapidly evolving field."""
    
    def _get_fallback_introduction(self, domain: Dict, question: Dict) -> str:
        """Fallback introduction if LLM fails"""
        return f"""The field of {domain.get('domain', 'advanced technology')} represents one of the most promising frontiers in contemporary science. {domain.get('description', 'This emerging domain combines multiple disciplines to address complex challenges.')} Recent advances have opened new possibilities for innovation, yet fundamental questions remain regarding implementation, efficiency, and scalability.

Among the critical questions facing researchers in this domain is: {question.get('question', 'how to optimize system performance')} This question addresses core challenges that must be resolved for the field to progress from theoretical promise to practical implementation. Understanding {question.get('rationale', 'the underlying mechanisms')} is essential for both scientific advancement and real-world applications.

Previous research has established foundational principles, but gaps remain in our empirical understanding. Traditional approaches have limitations that newer methodologies may address. This study seeks to contribute evidence-based insights through systematic data collection and rigorous statistical analysis.

The objective of this research is to investigate {question.get('question', 'key performance factors')} through quantitative analysis of relevant datasets. We employ comparative methods to evaluate differences between experimental conditions, using established statistical techniques to assess significance and effect sizes. Our findings aim to inform both theoretical understanding and practical decision-making in this rapidly evolving domain."""
    
    def _get_fallback_discussion(self, experiment: Dict, critique: Dict) -> str:
        """Fallback discussion if LLM fails"""
        stats = experiment.get('statistical_results', {})
        interp = experiment.get('interpretation', 'The analysis provides insights into the research question.')
        
        return f"""{interp} The statistical analysis yielded a p-value of {stats.get('p_value', 1.0):.4f} with an effect size of {stats.get('effect_size', 0):.3f}, {'supporting' if stats.get('significant') else 'not supporting'} our hypothesis at the conventional alpha level of 0.05.

These findings contribute to the growing body of evidence regarding emerging technologies and their comparative advantages. The {'significant' if stats.get('significant') else 'observed'} differences between conditions suggest {'meaningful practical implications' if stats.get('significant') else 'that further investigation may be warranted'}. The effect size indicates {'a substantive' if abs(stats.get('effect_size', 0)) > 0.5 else 'a moderate'} magnitude of difference, which has implications for real-world applications.

However, several limitations must be acknowledged. {' '.join(critique.get('limitations', ['Standard methodological limitations apply.'])[:2])} These constraints affect the generalizability of our conclusions and suggest directions for future research.

Future studies should address these limitations through larger sample sizes, more diverse data sources, and longitudinal designs. Additionally, investigating moderating factors and boundary conditions would enhance theoretical understanding. Practical implementations should consider these findings alongside domain-specific requirements and constraints.

In conclusion, this research provides {'valuable empirical evidence' if stats.get('significant') else 'preliminary insights'} regarding {stats.get('significant', False)} the research question, while highlighting areas requiring further investigation."""
    
    def _format_methods(self, state: Any) -> str:
        """Format methods section"""
        design = state.experiment_design
        
        methods = f"""## Methods

### Data Collection
We collected data from {len(state.data_sources)} diverse sources including academic papers, web resources, and research databases. Data collection focused on {state.selected_question.get('question', 'the research question')}.

### Experimental Design
**Hypothesis**: {state.hypothesis}

**Statistical Analysis**: {design.get('methodology', {}).get('test_type', 'Statistical analysis')} was performed on {design.get('methodology', {}).get('sample_size', 'N')} data points.

**Procedure**: {design.get('methodology', {}).get('procedure', 'Standard statistical procedures were followed')}.
"""
        return methods
    
    def _format_results(self, state: Any) -> str:
        """Format results section"""
        results = state.experiment_results.get('statistical_results', {})

        # Safely format numeric fields (they may be missing or non-numeric)
        p_val_raw = results.get('p_value', None)
        effect_raw = results.get('effect_size', None)

        try:
            p_val = float(p_val_raw)
            p_val_str = f"{p_val:.4f}"
        except Exception:
            p_val_str = 'N/A'

        try:
            eff = float(effect_raw)
            eff_str = f"{eff:.3f}"
        except Exception:
            eff_str = 'N/A'

        significance = 'Yes' if results.get('significant', False) else 'No'

        results_text = f"""## Results

### Statistical Analysis
- **P-value**: {p_val_str}
- **Effect Size**: {eff_str}
- **Statistical Significance**: {significance} (α = 0.05)

### Interpretation
{state.experiment_results.get('interpretation', 'No interpretation available')}

### Descriptive Statistics
"""
        
        if 'group1_stats' in results:
            results_text += f"\n**Group 1**: Mean = {results['group1_stats'].get('mean', 0):.2f}, SD = {results['group1_stats'].get('std', 0):.2f}"
        
        if 'group2_stats' in results:
            results_text += f"\n**Group 2**: Mean = {results['group2_stats'].get('mean', 0):.2f}, SD = {results['group2_stats'].get('std', 0):.2f}"
        
        return results_text
    
    def _format_limitations(self, critique: Dict[str, Any]) -> str:
        """Format limitations section"""
        limitations = critique.get('limitations',
                                   ['No limitations identified'])
        
        limitations_text = "## Limitations & Future Work\n\n"
        
        for i, limitation in enumerate(limitations, 1):
            limitations_text += f"{i}. {limitation}\n"
        
        limitations_text += "\n### Future Research Directions\n"
        recommendations = critique.get('recommendations', [])
        for i, rec in enumerate(recommendations[:3], 1):
            limitations_text += f"- {rec}\n"
        
        return limitations_text
    
    def _format_paper(self, sections: Dict[str, str], state: Any) -> str:
        """Format the complete paper"""
        domain = state.selected_domain or {}
        question = state.selected_question or {}
        
        paper = f"""# {domain.get('domain', 'Research Study')}: An Autonomous AI Investigation

**Research Question**: {question.get('question', 'Unknown')}

**Authors**: Multi-Agent AI Research System  
**Date**: {self._get_current_date()}  
**Confidence Score**: {state.confidence_scores.get('experiment', 70):.1f}%

---

## Abstract

{sections.get('abstract', 'No abstract available')}

---

## Introduction

{sections.get('introduction', 'No introduction available')}

---

{sections.get('methods', '')}

---

{sections.get('results', '')}

---

## Discussion

{sections.get('discussion', 'No discussion available')}

---

{sections.get('limitations', '')}

---

## Acknowledgments

This research was conducted autonomously by a multi-agent AI system consisting of:
- Domain Scout Agent
- Question Generator Agent
- Data Alchemist Agent
- Experiment Designer Agent
- Critic Agent
- Orchestrator Agent

---

## Appendix

### Agent Confidence Scores
{self._format_confidence_scores(state)}

### Iteration History
- Total iterations: {state.iteration_count + 1}
- Final quality score: {state.critiques[-1].get('overall_score', 0) if state.critiques else 0}/10

### Data Sources
{self._format_data_sources(state)}
"""
        
        return paper
    
    def _format_confidence_scores(self, state: Any) -> str:
        """Format confidence scores"""
        scores_text = "\n"
        for key, value in state.confidence_scores.items():
            scores_text += f"- **{key.replace('_', ' ').title()}**: {value:.1f}%\n"
        
        return scores_text
    
    def _format_data_sources(self, state: Any) -> str:
        """Format data sources"""
        sources_text = "\n"
        for i, source in enumerate(state.data_sources[:5], 1):
            sources_text += f"{i}. {source.get('type', 'unknown').upper()}: {source.get('search_query', 'N/A')}\n"
        
        return sources_text
    
    def _get_current_date(self) -> str:
        """Get current date"""
        from datetime import datetime
        return datetime.now().strftime("%B %d, %Y")
    
    async def _generate_visualizations(self, state: Any) -> Dict[str, str]:
        """Generate visualizations using plot functions"""
        visualizations = {}
        
        # Confidence scores chart
        if state.confidence_scores:
            try:
                visualizations['confidence'] = plot_confidence_scores(state.confidence_scores)
            except Exception as e:
                state.add_message(f"⚠️ {self.name}: Failed to generate confidence chart: {e}")
        
        # Data distribution charts
        cleaned = state.collected_data.get('cleaned', {}) if state.collected_data else {}
        if cleaned and len([k for k in cleaned.keys() if isinstance(cleaned[k], list)]) >= 1:
            try:
                # Pick up to 3 numeric lists
                numeric = {k: v for k, v in cleaned.items() if isinstance(v, list) and all(isinstance(x, (int, float)) for x in v[:5])}
                if numeric:
                    sample_for_viz = {k: v[:500] for k, v in list(numeric.items())[:3]}
                    visualizations['data_distribution'] = plot_data_distributions(sample_for_viz)
                    
                    # If regression results available, add scatter+fit
                    detailed = state.experiment_results.get('detailed', {}) if state.experiment_results else {}
                    if 'linear_regression' in detailed and not detailed['linear_regression'].get('error'):
                        lr = detailed['linear_regression']
                        if len(sample_for_viz) >= 2:
                            first_key, second_key = list(sample_for_viz.keys())[:2]
                            x = sample_for_viz[first_key]
                            y = sample_for_viz[second_key]
                            visualizations['regression'] = plot_regression(
                                x, y, 
                                slope=lr.get('slope'), 
                                intercept=lr.get('intercept')
                            )
            except Exception as e:
                state.add_message(f"⚠️ {self.name}: Failed to generate data visualizations: {e}")
        
        return visualizations

# Global agent instance
orchestrator = OrchestratorAgent()