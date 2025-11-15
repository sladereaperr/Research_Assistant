from ..utils.async_utils import maybe_await
from typing import Dict, Any, List
from ..utils.llm import llm_client
from ..tools.search import search_tool
from ..tools.scraper import scraper_tool
from ..tools.data_processor import data_processor
from ..utils.memory import memory_manager
import random

class DataAlchemistAgent:
    def __init__(self):
        self.name = "Data Alchemist"
    
    async def collect_data(self, state: Any) -> Dict[str, Any]:
        """Collect and process data for the research question"""
        question = state.selected_question or {}
        domain = state.selected_domain or {}
        
        if not question:
            state.add_message(f"⚠️ {self.name}: No question selected, using fallback...")
            question = {"question": "How can emerging technologies be applied to solve current limitations?", "rationale": "General research question"}
        
        state.add_message(f"🧪 {self.name}: Initiating data collection protocol...")
        
        # Identify data sources
        prompt = f"""Given this research question, identify 3-5 diverse data sources that could provide relevant information.

Question: {question.get('question', 'Unknown')}
Domain: {domain.get('domain', 'Unknown')}

Consider:
- Academic papers (ArXiv, journals)
- Public datasets
- GitHub repositories
- Technical blogs
- Research reports

Return ONLY JSON:
{{
  "data_sources": [
    {{
      "type": "arxiv|github|dataset|web",
      "search_query": "specific search terms",
      "expected_data": "what data we expect to find"
    }}
  ]
}}"""
        
        sources_data = await maybe_await(llm_client.generate_json(prompt))
        data_sources = sources_data.get('data_sources', [])
        
        if not data_sources:
            data_sources = self._get_fallback_sources(question)
        
        state.add_message(f"📍 {self.name}: Identified {len(data_sources)} data sources")
        
        # Collect data from each source
        collected_data = {}
        
        for i, source in enumerate(data_sources[:3], 1):
            state.add_message(f"📥 {self.name}: Collecting data from source {i}/{min(3, len(data_sources))}...")
            
            if source.get('type') == 'arxiv':
                papers = await maybe_await(search_tool.search_arxiv(source.get('search_query', ''), max_results=3))

                collected_data[f'arxiv_source_{i}'] = papers
            else:
                search_results = await maybe_await(search_tool.search_emerging_domains(source.get('search_query', '')))

                
                # inside DataAlchemistAgent.collect_data
                scraped_content = []
                for result in search_results[:2]:
                    url = result.get('url', '')
                    if not url:
                        continue
                    content = await scraper_tool.scrape_url(url)

                    # Defensive: handle None or unexpected return types
                    if not isinstance(content, dict):
                        state.add_message(f"⚠️ {self.name}: Scraper returned unexpected result for {url}, skipping.")
                        continue

                    # Now check success flag safely
                    if content.get('success'):
                        scraped_content.append(content)
                    else:
                        # Log error info if available
                        err = content.get('error') or content.get('status') or 'unknown error'
                        state.add_message(f"⚠️ {self.name}: Failed to scrape {url}: {err}")

                
                collected_data[f'web_source_{i}'] = scraped_content
        
        state.add_message(f"🔬 {self.name}: Processing and cleaning collected data...")
        
        # Process and extract structured data
        processed_data = await self._process_collected_data(collected_data)
        
        # Generate synthetic data if needed (for demonstration)
        if not processed_data or len(processed_data.get('numeric_data', {}).keys()) < 2:
            state.add_message(f"🎲 {self.name}: Generating synthetic data for analysis...")
            processed_data = self._generate_synthetic_data(question)
        
        # Clean the data
        cleaned_data = data_processor.clean_data(processed_data.get('numeric_data', {}))
        
        state.add_message(f"✅ {self.name}: Data collection complete. {len(cleaned_data)} datasets ready.")
        
        # Add to memory
        memory_manager.add_memory(
            f"Collected data from {len(data_sources)} sources for question: {question.get('question', 'Unknown')}",
            {"type": "data_collection", "agent": self.name}
        )
        
        confidence = 0.75 if cleaned_data else 0.50
        
        state.data_sources = data_sources
        state.collected_data = {
            'raw': collected_data,
            'processed': processed_data,
            'cleaned': cleaned_data
        }
        state.confidence_scores['data_collection'] = confidence * 100
        
        return {
            "data_sources": data_sources,
            "collected_data": collected_data,
            "cleaned_data": cleaned_data,
            "confidence": confidence
        }
    
    async def _process_collected_data(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process collected data to extract structured information"""
        processed = {
            "text_data": [],
            "numeric_data": {},
            "metadata": {}
        }
        
        for source_key, source_data in collected_data.items():
            if isinstance(source_data, list):
                for item in source_data:
                    if isinstance(item, dict):
                        # Extract text
                        if 'content' in item:
                            processed['text_data'].append(item['content'][:1000])
                        elif 'summary' in item:
                            processed['text_data'].append(item['summary'])
                        
                        # Extract numeric data if present
                        if 'content' in item:
                            extracted = await maybe_await(scraper_tool.extract_data_from_text(item['content']))

                            if extracted.get('numbers'):
                                processed['numeric_data'][f'{source_key}_numbers'] = extracted['numbers'][:50]
        
        return processed
    
    def _generate_synthetic_data(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Generate synthetic data for demonstration"""
        # Generate 2-3 datasets with different distributions
        data = {
            "numeric_data": {
                "baseline_metrics": list(np.random.normal(100, 15, 50)),
                "experimental_metrics": list(np.random.normal(110, 18, 50)),
                "control_group": list(np.random.normal(95, 12, 50)),
            },
            "text_data": [
                f"Synthetic data generated for research question analysis",
                f"This data simulates real-world measurements related to {question.get('question', 'the research question')}"
            ],
            "metadata": {
                "synthetic": True,
                "reason": "Insufficient real data collected",
                "distribution": "normal"
            }
        }
        
        return data
    
    def _get_fallback_sources(self, question: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback data sources"""
        return [
            {
                "type": "arxiv",
                "search_query": question.get('question', '')[:100],
                "expected_data": "Academic papers and research findings"
            },
            {
                "type": "web",
                "search_query": f"{question.get('question', '')} research data",
                "expected_data": "Research reports and datasets"
            },
            {
                "type": "github",
                "search_query": f"{question.get('question', '')} implementation",
                "expected_data": "Code repositories and documentation"
            }
        ]

# Import numpy for synthetic data
import numpy as np

# Global agent instance
data_alchemist = DataAlchemistAgent()