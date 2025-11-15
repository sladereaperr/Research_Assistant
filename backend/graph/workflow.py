from ..utils.async_utils import maybe_await
from langgraph.graph import StateGraph, END
from typing import Dict, Any
from .state import ResearchState
from ..agents.domain_scout import domain_scout
from ..agents.question_generator import question_generator
from ..agents.data_alchemist import data_alchemist
from ..agents.experiment_designer import experiment_designer
from ..agents.critic import critic
from ..agents.orchestrator import orchestrator

class ResearchWorkflow:
    def __init__(self):
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the research workflow graph"""
        workflow = StateGraph(ResearchState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize)
        workflow.add_node("discover_domain", self._discover_domain)
        workflow.add_node("generate_questions", self._generate_questions)
        workflow.add_node("collect_data", self._collect_data)
        workflow.add_node("design_experiment", self._design_experiment)
        workflow.add_node("critique", self._critique)
        workflow.add_node("iterate_or_finalize", self._iterate_or_finalize)
        workflow.add_node("generate_paper", self._generate_paper)
        
        # Add edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "discover_domain")
        workflow.add_edge("discover_domain", "generate_questions")
        workflow.add_edge("generate_questions", "collect_data")
        workflow.add_edge("collect_data", "design_experiment")
        workflow.add_edge("design_experiment", "critique")
        workflow.add_edge("critique", "iterate_or_finalize")
        
        # Conditional edge for iteration
        workflow.add_conditional_edges(
            "iterate_or_finalize",
            self._should_continue,
            {
                "iterate": "collect_data",
                "finalize": "generate_paper"
            }
        )
        
        workflow.add_edge("generate_paper", END)
        
        return workflow.compile()
    
    async def _initialize(self, state: ResearchState) -> ResearchState:
        """Initialize the research process"""
        state.add_message("🚀 System: Initializing autonomous research assistant...")
        await orchestrator.coordinate_research(state)
        return state
    
    async def _discover_domain(self, state: ResearchState) -> ResearchState:
        """Discover emerging domain"""
        await domain_scout.discover_domains(state)
        return state
    
    async def _generate_questions(self, state: ResearchState) -> ResearchState:
        """Generate research questions"""
        await question_generator.generate_questions(state)
        return state
    
    async def _collect_data(self, state: ResearchState) -> ResearchState:
        """Collect data"""
        if state.iteration_count > 0:
            state.add_message(f"🔄 System: Iteration {state.iteration_count + 1} - Refining data collection...")
        
        await data_alchemist.collect_data(state)
        return state
    
    async def _design_experiment(self, state: ResearchState) -> ResearchState:
        """Design and execute experiment"""
        await experiment_designer.design_experiment(state)
        return state
    
    async def _critique(self, state: ResearchState) -> ResearchState:
        """Critique the research"""
        critique_result = await critic.critique_research(state)
        state.should_iterate = critique_result.get('should_iterate', False)
        return state
    
    async def _iterate_or_finalize(self, state: ResearchState) -> ResearchState:
        """Decide whether to iterate or finalize"""
        # Increment iteration count at the start of this function
        # This represents the iteration we just completed
        state.iteration_count += 1
        
        if state.should_iterate and state.iteration_count < state.max_iterations:
            state.add_message(f"🔄 System: Completed iteration {state.iteration_count}/{state.max_iterations}. Continuing...")
        else:
            state.add_message(f"✅ System: Research iterations complete (completed {state.iteration_count}/{state.max_iterations}). Generating final paper...")
            state.should_iterate = False  # Ensure we don't continue
        
        return state
    
    async def _generate_paper(self, state: ResearchState) -> ResearchState:
        """Generate final paper"""
        # defensively support orchestrator.generate_final_paper being async OR sync (returning dict)
        res = await maybe_await(orchestrator.generate_final_paper(state))

        # If the orchestrator returned a dict (paper + visualizations), merge into state for downstream use
        if isinstance(res, dict):
            # res might contain keys: 'paper', 'visualizations'
            paper = res.get('paper')
            visualizations = res.get('visualizations')
            if paper:
                state.research_paper = paper
            if visualizations:
                state.visualizations = visualizations
        # otherwise assume the orchestrator updated state in-place

        return state

    
    def _should_continue(self, state: ResearchState) -> str:
        """Determine if we should iterate or finalize"""
        if state.should_iterate and state.iteration_count < state.max_iterations:
            return "iterate"
        return "finalize"
    
    async def run(self, initial_state: ResearchState = None) -> ResearchState:
        """Run the workflow"""
        if initial_state is None:
            initial_state = ResearchState()
        
        final_state = await self.workflow.ainvoke(initial_state)
        return final_state

# Global workflow instance
research_workflow = ResearchWorkflow()