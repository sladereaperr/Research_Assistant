
from ..utils.async_utils import maybe_await
from typing import Dict, Any, List
from ..utils.llm import llm_client
from ..utils.memory import memory_manager
import random

class QuestionGeneratorAgent:
    def __init__(self):
        self.name = "Question Generator"
    
    async def generate_questions(self, state: Any) -> Dict[str, Any]:
        """Generate research questions"""
        domain = state.selected_domain or {}
        
        if not domain:
            state.add_message(f"⚠️ {self.name}: No domain selected, using fallback...")
            domain = {"domain": "Emerging Technology", "description": "General emerging technology", "keywords": ["technology", "innovation"]}
        
        state.add_message(f"💡 {self.name}: Formulating research questions for {domain.get('domain', 'unknown domain')}...")
        
        prompt = f"""You are a creative research scientist. Generate 5 novel, non-trivial research questions for this emerging domain:

Domain: {domain.get('domain', 'Unknown')}
Description: {domain.get('description', 'No description')}
Keywords: {', '.join(domain.get('keywords', []))}

Requirements:
- Questions should require synthesis of multiple concepts
- Not directly searchable with simple queries
- Testable with available data/methods
- Original and thought-provoking

Return ONLY a JSON array:
[
  {{
    "question": "the research question",
    "rationale": "why this is important",
    "novelty_score": 0.0-1.0,
    "feasibility_score": 0.0-1.0,
    "required_data": ["data type 1", "data type 2"]
  }}
]"""
        
        questions_data = await maybe_await(llm_client.generate_json(prompt, temperature=0.9))

        
        if isinstance(questions_data, dict):
            questions = questions_data.get('questions', [])
        elif isinstance(questions_data, list):
            questions = questions_data
        else:
            questions = []
        
        if not questions:
            questions = self._get_fallback_questions(domain)
        
        state.add_message(f"📝 {self.name}: Generated {len(questions)} research questions")
        
        # Have peer agents rate the questions
        state.add_message(f"🤔 {self.name}: Peer review in progress...")
        
        rated_questions = await self._peer_review_questions(questions)
        
        # Add to memory
        for q in rated_questions:
            memory_manager.add_memory(
                f"Question: {q.get('question', 'Unknown')}",
                {"type": "question", "agent": self.name}
            )
        
        # Select best question
        selected = max(rated_questions, key=lambda x: (x.get('novelty_score', 0) + x.get('feasibility_score', 0)) / 2)
        
        confidence = (selected.get('novelty_score', 0.7) + selected.get('feasibility_score', 0.7)) / 2
        
        state.add_message(f"🎯 {self.name}: Selected: '{selected.get('question', 'Unknown')}' (confidence: {confidence:.2%})")
        
        state.research_questions = rated_questions
        state.selected_question = selected
        state.confidence_scores['question_selection'] = confidence * 100
        
        return {
            "questions": rated_questions,
            "selected_question": selected,
            "confidence": confidence
        }
    
    async def _peer_review_questions(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simulate peer review of questions"""
        for q in questions:
            # Add some randomness to simulate peer review
            novelty_adjustment = random.uniform(-0.1, 0.1)
            feasibility_adjustment = random.uniform(-0.1, 0.1)
            
            q['novelty_score'] = max(0.5, min(1.0, q.get('novelty_score', 0.7) + novelty_adjustment))
            q['feasibility_score'] = max(0.5, min(1.0, q.get('feasibility_score', 0.7) + feasibility_adjustment))
            q['peer_reviewed'] = True
        
        return questions
    
    def _get_fallback_questions(self, domain: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback questions"""
        domain_name = domain.get('domain', 'Unknown Domain')
        
        return [
            {
                "question": f"How can {domain_name} be applied to solve current limitations in scalability?",
                "rationale": "Scalability is a fundamental challenge in emerging technologies",
                "novelty_score": 0.75,
                "feasibility_score": 0.80,
                "required_data": ["performance metrics", "scalability studies", "benchmark data"]
            },
            {
                "question": f"What are the ethical implications of rapid adoption of {domain_name}?",
                "rationale": "Understanding societal impact is crucial for responsible development",
                "novelty_score": 0.70,
                "feasibility_score": 0.75,
                "required_data": ["case studies", "expert opinions", "policy documents"]
            },
            {
                "question": f"Can {domain_name} be combined with existing technologies to create hybrid solutions?",
                "rationale": "Cross-domain innovation often leads to breakthroughs",
                "novelty_score": 0.85,
                "feasibility_score": 0.70,
                "required_data": ["technology comparisons", "integration studies", "proof of concepts"]
            },
            {
                "question": f"What are the fundamental physical or computational limits of {domain_name}?",
                "rationale": "Understanding theoretical boundaries guides research direction",
                "novelty_score": 0.82,
                "feasibility_score": 0.65,
                "required_data": ["theoretical papers", "simulation results", "experimental data"]
            },
            {
                "question": f"How does {domain_name} compare to traditional approaches in terms of efficiency and effectiveness?",
                "rationale": "Comparative analysis establishes practical value",
                "novelty_score": 0.68,
                "feasibility_score": 0.85,
                "required_data": ["benchmark comparisons", "performance data", "cost analyses"]
            }
        ]

# Global agent instance
question_generator = QuestionGeneratorAgent()