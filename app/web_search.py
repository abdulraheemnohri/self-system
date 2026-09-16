"""
Web Search Skill for Complete Self System

Provides advanced web search capabilities with result processing and summarization
"""

import json
import requests
from typing import Dict, Any, List, Optional
from .llm import simple_llm_reply


class WebSearchSkill:
    """Skill for performing web searches and processing results"""
    
    def __init__(self):
        self.name = "web_search"
        self.description = "Advanced web search with result processing and summarization"
        self.version = "1.0.0"
    
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Perform a web search and return results"""
        try:
            # Use a search API or scrape results
            url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num={limit}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            for g in soup.find_all('div', class_='g'):
                link = g.find('a')
                if link and 'href' in link.attrs:
                    url = link['href']
                    if url.startswith('/url?q='):
                        url = url[7:].split('&')[0]
                    title_el = g.find('h3')
                    title = title_el.get_text() if title_el else "No title"
                    snippet_el = g.find('div', {'data-sncf': True})
                    snippet = snippet_el.get_text() if snippet_el else ""
                    results.append({
                        'title': title,
                        'url': url,
                        'snippet': snippet
                    })
                if len(results) >= limit:
                    break
            
            return results
        except ImportError:
            return []
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def summarize_results(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Summarize search results using LLM"""
        if not results:
            return "No results to summarize"
        
        prompt = f"Summarize the following search results for query: '{query}'\n\n"
        for i, result in enumerate(results[:5], 1):
            prompt += f"{i}. {result.get('title', 'No title')}\n   URL: {result.get('url', '')}\n   Snippet: {result.get('snippet', '')[:200]}\n\n"
        
        prompt += "Provide a concise summary of the most relevant information."
        
        messages = [
            {'role': 'system', 'content': 'You are a helpful research assistant.'},
            {'role': 'user', 'content': prompt}
        ]
        
        return simple_llm_reply(messages, max_tokens=2000, temperature=0.3)
    
    def extract_key_information(self, query: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract key information from search results"""
        if not results:
            return {'query': query, 'results': []}
        
        prompt = f"Extract key facts, dates, names, and important information from these search results for query: '{query}'\n\n"
        for i, result in enumerate(results[:5], 1):
            prompt += f"{i}. {result.get('title', 'No title')}\n   Snippet: {result.get('snippet', '')[:300]}\n\n"
        
        prompt += "Return the extracted information as a JSON object with keys: facts, dates, names, sources."
        
        messages = [
            {'role': 'system', 'content': 'You are a data extraction assistant. Return only valid JSON.'},
            {'role': 'user', 'content': prompt}
        ]
        
        response = simple_llm_reply(messages, max_tokens=2000, temperature=0.2)
        
        try:
            return json.loads(response)
        except:
            return {'query': query, 'raw_response': response}
    
    def compare_sources(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Compare information from different sources"""
        if len(results) < 2:
            return "Need at least 2 results to compare"
        
        prompt = f"Compare the information from different sources for query: '{query}'\n\n"
        for i, result in enumerate(results[:5], 1):
            prompt += f"Source {i}: {result.get('title', 'No title')}\n"
            prompt += f"URL: {result.get('url', '')}\n"
            prompt += f"Content: {result.get('snippet', '')[:400]}\n\n"
        
        prompt += "Identify agreements, disagreements, and gaps in the information. Highlight the most reliable sources."
        
        messages = [
            {'role': 'system', 'content': 'You are a fact-checking assistant.'},
            {'role': 'user', 'content': prompt}
        ]
        
        return simple_llm_reply(messages, max_tokens=2000, temperature=0.3)
    
    def execute(self, action: str, **kwargs) -> Any:
        """Execute a skill action"""
        if action == 'search':
            return self.search(kwargs.get('query'), kwargs.get('limit', 5))
        elif action == 'summarize':
            return self.summarize_results(kwargs.get('query'), kwargs.get('results', []))
        elif action == 'extract':
            return self.extract_key_information(kwargs.get('query'), kwargs.get('results', []))
        elif action == 'compare':
            return self.compare_sources(kwargs.get('query'), kwargs.get('results', []))
        else:
            raise ValueError(f"Unknown action: {action}")


skill = WebSearchSkill()


def get_skill_info() -> Dict[str, Any]:
    return {
        'name': skill.name,
        'version': skill.version,
        'description': skill.description,
        'actions': ['search', 'summarize', 'extract', 'compare'],
        'capabilities': {
            'search': {
                'description': 'Perform web search',
                'parameters': {'query': 'string', 'limit': 'integer'}
            },
            'summarize': {
                'description': 'Summarize search results',
                'parameters': {'query': 'string', 'results': 'list'}
            },
            'extract': {
                'description': 'Extract key information from results',
                'parameters': {'query': 'string', 'results': 'list'}
            },
            'compare': {
                'description': 'Compare information from different sources',
                'parameters': {'query': 'string', 'results': 'list'}
            }
        }
    }
