from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class ResearchState:
    """State for the research workflow"""
    # Domain discovery
    discovered_domains: List[Dict[str, Any]] = field(default_factory=list)
    selected_domain: Optional[Dict[str, Any]] = None
    
    # Question generation
    research_questions: List[Dict[str, Any]] = field(default_factory=list)
    selected_question: Optional[Dict[str, Any]] = None
    
    # Data collection
    data_sources: List[Dict[str, Any]] = field(default_factory=list)
    collected_data: Dict[str, Any] = field(default_factory=dict)
    
    # Experiment
    hypothesis: Optional[str] = None
    experiment_design: Optional[Dict[str, Any]] = None
    experiment_results: Optional[Dict[str, Any]] = None
    
    # Critique and iteration
    critiques: List[Dict[str, Any]] = field(default_factory=list)
    iteration_count: int = 0
    max_iterations: int = 2  # Reduced from 5 to 2 for faster completion
    
    # Final output
    research_paper: Optional[str] = None
    visualizations: Dict[str, str] = field(default_factory=dict)
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    
    # Agent communications
    messages: List[str] = field(default_factory=list)
    agent_outputs: Dict[str, Any] = field(default_factory=dict)
    
    # Control flow
    should_iterate: bool = True
    is_complete: bool = False
    
    def add_message(self, message: str):
        """Add a message to the state"""
        self.messages.append(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary"""
        return {
            "discovered_domains": self.discovered_domains,
            "selected_domain": self.selected_domain,
            "research_questions": self.research_questions,
            "selected_question": self.selected_question,
            "data_sources": self.data_sources,
            "hypothesis": self.hypothesis,
            "iteration_count": self.iteration_count,
            "confidence_scores": self.confidence_scores,
            "is_complete": self.is_complete,
        }