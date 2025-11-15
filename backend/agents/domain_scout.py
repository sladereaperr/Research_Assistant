
from ..utils.async_utils import maybe_await
from typing import Dict, Any, List
from ..utils.llm import llm_client
from ..tools.search import search_tool
from ..utils.memory import memory_manager
import random
import datetime

class DomainScoutAgent:
    def __init__(self):
        self.name = "Domain Scout"
        self.confidence_threshold = 0.6
    
    async def discover_domains(self, state: Any) -> Dict[str, Any]:
        """Discover emerging scientific domains"""
        state.add_message(f"🔍 {self.name}: Initiating scan for emerging scientific domains post-2024...")
        
        # More diverse and specific search queries with randomization
        current_year = datetime.datetime.now().year
        base_queries = [
            f"breakthrough scientific discovery {current_year}",
            f"emerging AI research {current_year}",
            f"quantum computing advances {current_year}",
            f"biotech innovations {current_year}",
            f"climate tech breakthroughs {current_year}",
            f"new technology {current_year}",
            f"cutting edge research {current_year}",
            f"revolutionary science {current_year}",
            f"next generation technology {current_year}",
            f"innovative research {current_year}"
        ]
        
        # Randomize to get different results each time
        search_queries = random.sample(base_queries, min(6, len(base_queries)))
        
        all_results = []
        
        for query in search_queries:
            try:
                state.add_message(f"🔎 {self.name}: Searching for '{query}'...")
                results = await search_tool.search_emerging_domains(query)
                if results:
                    all_results.extend(results)
                    state.add_message(f"   Found {len(results)} results")
                
                # Also search ArXiv directly
                try:
                    arxiv_results = await search_tool.search_arxiv(query, max_results=5)
                    if arxiv_results:
                        all_results.extend(arxiv_results)
                        state.add_message(f"   Found {len(arxiv_results)} ArXiv papers")
                except Exception as e:
                    state.add_message(f"   ⚠️ ArXiv search failed: {str(e)[:50]}")
            except Exception as e:
                state.add_message(f"   ⚠️ Search failed for '{query}': {str(e)[:50]}")
                continue
        
        # Remove duplicates more aggressively
        seen_titles = set()
        unique_results = []
        for result in all_results:
            title = result.get('title', '').lower().strip()
            if title and title not in seen_titles and len(title) > 10:
                seen_titles.add(title)
                unique_results.append(result)
        
        all_results = unique_results
        state.add_message(f"📊 {self.name}: Found {len(all_results)} unique potential sources. Analyzing...")
        
        # Only use LLM if we have actual search results
        if len(all_results) < 3:
            state.add_message(f"⚠️ {self.name}: Insufficient search results ({len(all_results)}). Trying alternative search...")
            # Try a more general search as fallback
            try:
                general_results = await search_tool.search_arxiv("recent research 2024", max_results=10)
                if general_results:
                    all_results.extend(general_results)
                    state.add_message(f"   Added {len(general_results)} general results")
            except:
                pass
        
        if len(all_results) == 0:
            state.add_message(f"❌ {self.name}: No search results found. Using fallback domains...")
            domains = self._get_fallback_domains()
        else:
            # Use LLM to identify emerging domains from real search results
            formatted_results = self._format_results(all_results[:40])  # Use more results
            
            prompt = f"""You are analyzing REAL search results from scientific sources. Extract 5-7 emerging scientific domains that are mentioned in these results.

CRITICAL REQUIREMENTS:
1. Extract domain names DIRECTLY from the search results below
2. Do NOT use generic domains like "AI" or "Machine Learning" - be specific
3. Do NOT use placeholder or example domains
4. Each domain must be mentioned in the actual search results
5. Focus on domains from 2024-2025 that are novel or emerging

Search Results:
{formatted_results}

Return ONLY a JSON array (no markdown, no explanation):
[
  {{
    "domain": "exact domain name from search results",
    "description": "description based on what the search results say",
    "novelty_score": 0.7-0.95,
    "keywords": ["specific", "keywords", "from", "results"],
    "potential_impact": "impact based on search results"
  }}
]

IMPORTANT: If you cannot find 5 distinct domains in the search results, return fewer domains. Do NOT make up domains."""
            
            # Try LLM extraction with retry
            domains = []
            for attempt in range(2):  # Try twice
                try:
                    domains_data = await maybe_await(llm_client.generate_json(prompt, temperature=0.9))
                    
                    if isinstance(domains_data, dict):
                        domains = domains_data.get('domains', [])
                    elif isinstance(domains_data, list):
                        domains = domains_data
                    
                    # Validate domains - be less strict
                    valid_domains = []
                    for domain in domains:
                        if isinstance(domain, dict):
                            domain_name = domain.get('domain', '').strip()
                            # Accept if it has a domain name and it's not a generic fallback
                            if domain_name and len(domain_name) > 5:
                                # Check if it's NOT one of our fallback domains
                                fallback_names = ["Quantum-Enhanced Machine Learning", "Synthetic Biology for Carbon Capture", 
                                                 "Neuromorphic Computing Hardware", "AI-Driven Drug Repurposing", "Molecular Data Storage"]
                                if domain_name not in fallback_names:
                                    # Ensure it has required fields
                                    if not domain.get('description'):
                                        domain['description'] = f"Emerging domain: {domain_name}"
                                    if not domain.get('novelty_score'):
                                        domain['novelty_score'] = 0.8
                                    valid_domains.append(domain)
                    
                    if len(valid_domains) > 0:
                        break  # Success!
                    else:
                        state.add_message(f"   Attempt {attempt + 1}: LLM returned invalid domains, retrying...")
                except Exception as e:
                    state.add_message(f"   Attempt {attempt + 1}: LLM call failed: {str(e)[:50]}")
                    if attempt == 1:
                        break
            
            # Only use fallback if we completely failed
            if len(valid_domains) == 0:
                state.add_message(f"❌ {self.name}: Could not extract valid domains from search results. Using fallback...")
                # Instead of using fallback, try to extract domains directly from search result titles
                extracted_domains = self._extract_domains_from_results(all_results)
                if len(extracted_domains) > 0:
                    domains = extracted_domains
                    state.add_message(f"✅ {self.name}: Extracted {len(domains)} domains directly from search results!")
                else:
                    domains = self._get_fallback_domains()
            else:
                domains = valid_domains
                state.add_message(f"✅ {self.name}: Successfully extracted {len(domains)} domains from search results!")
        
        state.add_message(f"✨ {self.name}: Identified {len(domains)} emerging domains!")
        
        # Add to memory
        for domain in domains:
            memory_manager.add_memory(
                f"Domain: {domain.get('domain', 'Unknown')} - {domain.get('description', '')}",
                {"type": "domain", "agent": self.name}
            )
        
        # Select the most promising domain
        def _combined_score(d):
            novelty = float(d.get('novelty_score', 0.0))
            feasibility = float(d.get('feasibility_score', d.get('feasibility', 0.0) or 0.0))
            # weights: novelty more important than feasibility
            return 0.7 * novelty + 0.3 * feasibility

        selected_domain = max(domains, key=_combined_score)
        confidence = _combined_score(selected_domain)

        
        state.add_message(f"🎯 {self.name}: Selected domain: {selected_domain.get('domain', 'Unknown')} (confidence: {confidence:.2%})")
        
        state.discovered_domains = domains
        state.selected_domain = selected_domain
        state.confidence_scores['domain_selection'] = confidence * 100
        
        # Log selected domain for debugging
        state.add_message(f"📋 {self.name}: Selected domain details: {selected_domain.get('domain', 'Unknown')}")
        
        return {
            "domains": domains,
            "selected_domain": selected_domain,
            "confidence": confidence
        }
    
    def _format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results for LLM"""
        formatted = []
        for i, result in enumerate(results[:40], 1):  # Show more results
            title = result.get('title', 'No title')
            snippet = result.get('snippet', result.get('summary', result.get('content', 'No description')))
            # Clean up the snippet
            if snippet:
                snippet = snippet[:300].replace('\n', ' ').strip()
            formatted.append(f"{i}. {title}\n   {snippet}")
        return "\n\n".join(formatted)
    
    def _extract_domains_from_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract domain names directly from search result titles as last resort"""
        domains = []
        seen = set()
        
        for result in results[:20]:
            title = result.get('title', '')
            if not title or len(title) < 10:
                continue
            
            # Try to extract domain-like phrases from titles
            # Remove common prefixes
            title_clean = title
            for prefix in ['ArXiv:', 'GitHub:', 'Patent:', 'X/Twitter:', 'Research:', 'Study:', 'Paper:']:
                if title_clean.startswith(prefix):
                    title_clean = title_clean[len(prefix):].strip()
            
            # Skip if too generic
            generic_terms = ['research', 'study', 'paper', 'article', 'review', 'analysis']
            if any(term in title_clean.lower() for term in generic_terms) and len(title_clean.split()) < 4:
                continue
            
            # Use title as domain name if it's unique and substantial
            domain_name = title_clean[:80]  # Limit length
            if domain_name.lower() not in seen and len(domain_name.split()) >= 3:
                seen.add(domain_name.lower())
                snippet = result.get('snippet', result.get('summary', ''))[:200]
                domains.append({
                    "domain": domain_name,
                    "description": snippet if snippet else f"Research domain: {domain_name}",
                    "novelty_score": 0.75,
                    "keywords": domain_name.split()[:5],
                    "potential_impact": "Emerging research area"
                })
                
                if len(domains) >= 5:
                    break
        
        return domains
    
    def _get_fallback_domains(self) -> List[Dict[str, Any]]:
        """Fallback domains if search fails"""
        return [
            {
                "domain": "Quantum-Enhanced Machine Learning",
                "description": "Integration of quantum computing principles with deep learning architectures for exponential speedup",
                "novelty_score": 0.85,
                "keywords": ["quantum", "ML", "hybrid algorithms"],
                "potential_impact": "Revolutionary computational efficiency in AI training"
            },
            {
                "domain": "Synthetic Biology for Carbon Capture",
                "description": "Engineered organisms designed to sequester atmospheric CO2 at industrial scale",
                "novelty_score": 0.82,
                "keywords": ["synthetic biology", "climate", "bioengineering"],
                "potential_impact": "Scalable solution for climate change mitigation"
            },
            {
                "domain": "Neuromorphic Computing Hardware",
                "description": "Brain-inspired chip architectures that mimic neural structures for energy-efficient AI",
                "novelty_score": 0.88,
                "keywords": ["neuromorphic", "hardware", "spiking networks"],
                "potential_impact": "1000x more efficient AI inference"
            },
            {
                "domain": "AI-Driven Drug Repurposing",
                "description": "Using large language models to discover new applications for existing pharmaceuticals",
                "novelty_score": 0.79,
                "keywords": ["AI", "drug discovery", "repurposing"],
                "potential_impact": "Faster and cheaper treatment development"
            },
            {
                "domain": "Molecular Data Storage",
                "description": "Encoding digital information in synthetic DNA for ultra-dense, long-term storage",
                "novelty_score": 0.91,
                "keywords": ["DNA storage", "molecular computing", "data preservation"],
                "potential_impact": "Exabyte-scale storage in microscopic volumes"
            }
        ]

# Global agent instance
domain_scout = DomainScoutAgent()