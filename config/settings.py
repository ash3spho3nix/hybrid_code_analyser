import os

class Settings:
    # LLM Configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LMSTUDIO_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234")
    VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000")
    MODEL_NAME = os.getenv("MODEL_NAME", "codellama:34b")
    LMSTUDIO_MODEL_NAME = os.getenv("LMSTUDIO_MODEL_NAME", "qwen2.5-coder-3b-instruct@q8_0")
    
    # Analysis Configuration
    MAX_CONTEXT_LENGTH = 16000
    ANALYSIS_TIMEOUT = 300
    
    # Tool Paths
    SEMGREP_PATH = os.getenv("SEMGREP_PATH", "semgrep")

settings = Settings()