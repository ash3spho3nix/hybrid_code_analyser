import requests
import json
from typing import Dict, Any, List
from config.settings import settings

class LLMClient:
    def __init__(self, backend: str = "ollama"):
        self.backend = backend
        self.base_url = self._get_base_url(backend)
        self.model = self._get_model_name(backend)
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate response from LLM"""
        if self.backend == "ollama":
            return self._call_ollama(prompt, max_tokens)
        elif self.backend == "lmstudio":
            return self._call_lmstudio(prompt, max_tokens)
        elif self.backend == "vllm":
            return self._call_vllm(prompt, max_tokens)
            
    def _get_base_url(self, backend: str) -> str:
        if backend == "ollama":
            return settings.OLLAMA_BASE_URL
        elif backend == "lmstudio":
            return settings.LMSTUDIO_BASE_URL
        elif backend == "vllm":
            return settings.VLLM_BASE_URL

    def _get_model_name(self, backend: str) -> str:
        if backend == "lmstudio":
            return settings.LMSTUDIO_MODEL_NAME
        elif backend == "vllm":
            return settings.VLLM_MODEL_NAME
        # Default for ollama
        return settings.MODEL_NAME
    
    def _call_lmstudio(self, prompt: str, max_tokens: int) -> str:
        """Call LM Studio API"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "max_tokens": max_tokens,
            "temperature": 0.1
        }
        
        try:
            # LM Studio typically uses an OpenAI-compatible API endpoint
            # The base_url for LM Studio should be configured to point to its API server
            # e.g., http://localhost:1234
            response = requests.post(
                f"{self.base_url}/completions", # Assuming /v1/completions or /completions
                json=payload,
                timeout=120
            )
            response.raise_for_status() # Raise an exception for HTTP errors
            return response.json()["choices"][0]["text"]
        except requests.exceptions.RequestException as e:
            return f"Error calling LM Studio API: {str(e)}"
        except KeyError:
            return "Error: Unexpected response format from LM Studio API"
        except Exception as e:
            return f"An unexpected error occurred with LM Studio: {str(e)}"

    def _call_ollama(self, prompt: str, max_tokens: int) -> str:
        """Call Ollama API"""
        payload: Dict[str, Any] = {
            "model": self.model, # Ollama uses the model name directly
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
        except requests.exceptions.RequestException as e:
            return f"Error calling Ollama API: {str(e)}"
        except KeyError:
            return "Error: Unexpected response format from Ollama API"
        except Exception as e:
            return f"An unexpected error occurred with Ollama: {str(e)}"
    
    def _call_vllm(self, prompt: str, max_tokens: int) -> str:
        """Call vLLM API (OpenAI compatible)"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": 0.1
        }
        
        try:
            endpoint = "/v1/completions" # vLLM typically uses /v1/completions
            response = requests.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                timeout=120 # Increased timeout for potentially longer vLLM responses
            )
            return response.json()["choices"][0]["text"].strip()
        except requests.exceptions.RequestException as e:
            return f"Error calling vLLM API: {str(e)}"
        except KeyError:
            return "Error: Unexpected response format from vLLM API"
        except Exception as e:
            return f"An unexpected error occurred with vLLM: {str(e)}"
    
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