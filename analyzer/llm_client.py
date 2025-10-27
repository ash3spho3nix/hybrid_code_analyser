import requests
import json
from typing import Dict, Any, List
from config.settings import settings

class LLMClient:
    def __init__(self, backend: str = "ollama"):
        self.backend = backend
        self.base_url = settings.OLLAMA_BASE_URL if backend == "ollama" else settings.VLLM_BASE_URL
        self.model = settings.MODEL_NAME
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate response from LLM"""
        if self.backend == "ollama":
            return self._call_ollama(prompt, max_tokens)
        else:
            return self._call_vllm(prompt, max_tokens)
    
    def _call_ollama(self, prompt: str, max_tokens: int) -> str:
        """Call Ollama API"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.1
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120
            )
            return response.json().get("response", "Error: No response")
        except Exception as e:
            return f"Error calling Ollama: {str(e)}"
    
    def _call_vllm(self, prompt: str, max_tokens: int) -> str:
        """Call vLLM API (OpenAI compatible)"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": 0.1
        }
        
        try:
            endpoint = "/v1/completions" if "v1" in self.base_url else "/completions"
            response = requests.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                timeout=120
            )
            return response.json()["choices"][0]["text"]
        except Exception as e:
            return f"Error calling vLLM: {str(e)}"
    
    def compare_codebases(self, analysis_a: Dict, analysis_b: Dict, question: str) -> str:
        """Compare two codebase analyses"""
        prompt = f"""
        CODEBASE COMPARISON ANALYSIS
        
        CODEBASE A ANALYSIS:
        {json.dumps(analysis_a, indent=2)}
        
        CODEBASE B ANALYSIS:  
        {json.dumps(analysis_b, indent=2)}
        
        USER QUESTION: {question}
        
        Provide a detailed comparison focusing on:
        1. Architectural differences and compatibility
        2. Code quality metrics comparison
        3. Potential integration challenges
        4. Recommendations for merging or integration
        
        Answer:
        """
        return self.generate(prompt)
    
    def analyze_single(self, analysis_results: Dict, question: str) -> str:
        """Analyze single codebase"""
        prompt = f"""
        CODE ANALYSIS REPORT
        
        ANALYSIS RESULTS:
        {json.dumps(analysis_results, indent=2)}
        
        USER QUESTION: {question}
        
        Provide comprehensive analysis focusing on:
        1. Critical issues and their root causes
        2. Code quality assessment
        3. Security vulnerabilities
        4. Performance implications
        5. Recommended fixes
        
        Answer:
        """
        return self.generate(prompt)