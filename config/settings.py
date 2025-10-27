import os

class Settings:
    # LLM Configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000")
    MODEL_NAME = os.getenv("MODEL_NAME", "codellama:34b")
    
    # Analysis Configuration
    MAX_CONTEXT_LENGTH = 16000
    ANALYSIS_TIMEOUT = 300
    
    # Tool Paths
    SEMGREP_PATH = os.getenv("SEMGREP_PATH", "semgrep")
    SONAR_SCANNER_PATH = os.getenv("SONAR_SCANNER_PATH", "sonar-scanner")

settings = Settings()