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

    # Profiling Tool Configuration
    # Scalene Configuration Options
    # Scalene is a high-performance CPU, GPU, and memory profiler for Python
    SCALENE_ENABLED = os.getenv("SCALENE_ENABLED", "true").lower() == "true"
    SCALENE_TIMEOUT = int(os.getenv("SCALENE_TIMEOUT", "180"))  # Timeout in seconds for Scalene profiling
    SCALENE_CPU_ONLY = os.getenv("SCALENE_CPU_ONLY", "false").lower() == "true"  # Run CPU-only profiling (disables memory/GPU profiling)
    SCALENE_MEMORY_DEPTH = int(os.getenv("SCALENE_MEMORY_DEPTH", "10"))  # Memory profiling depth (stack frames to analyze)
    SCALENE_GPU_ENABLED = os.getenv("SCALENE_GPU_ENABLED", "true").lower() == "true"  # Enable GPU profiling (requires CUDA)

    # VizTracer Configuration Options
    # VizTracer is a low-overhead function-level tracer and profiler for Python
    VIZTRACER_ENABLED = os.getenv("VIZTRACER_ENABLED", "true").lower() == "true"
    VIZTRACER_TIMEOUT = int(os.getenv("VIZTRACER_TIMEOUT", "120"))  # Timeout in seconds for VizTracer tracing
    VIZTRACER_LOG_ARGS = os.getenv("VIZTRACER_LOG_ARGS", "true").lower() == "true"  # Log function arguments
    VIZTRACER_LOG_RETVAL = os.getenv("VIZTRACER_LOG_RETVAL", "true").lower() == "true"  # Log function return values
    VIZTRACER_MAX_DEPTH = int(os.getenv("VIZTRACER_MAX_DEPTH", "20"))  # Maximum call stack depth to trace
    VIZTRACER_PERF_MODE = os.getenv("VIZTRACER_PERF_MODE", "false").lower() == "true"  # Enable performance optimization mode (reduces overhead)

settings = Settings()