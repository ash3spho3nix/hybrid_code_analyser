graph TD
    A[Main Entry Point] --> B[MultiCodebaseAnalyzer]
    B --> C[StaticAnalyzer]
    B --> D[DynamicAnalyzer]
    B --> E[LLMClient]
    C --> F[SemgrepWrapper]
    C --> G[FileDiscoveryService]
    D --> H[Scalene Profiling]
    D --> I[VizTracer Tracing]
    D --> J[Runtime Trace Execution]
    D --> K[Memory Profiling]
    B --> L[AnalysisStorage]
    L --> M[SQLite Database]
    L --> N[FAISS Vector Index]

## Project Tree Structure

```
.
├── main.py
├── project_comparison_analysis.py
├── analyzer/
│   ├── analysis_storage_base.py
│   ├── analysis_storage_models.py
│   ├── analysis_storage_vector.py
│   ├── analysis_storage.py
│   ├── discovery_artifact.py
│   ├── dynamic_analyzer_base.py
│   ├── dynamic_analyzer_execution.py
│   ├── dynamic_analyzer_fixed.py
│   ├── dynamic_analyzer_helpers.py
│   ├── dynamic_analyzer_profiling.py
│   ├── dynamic_analyzer_safe.py
│   ├── dynamic_analyzer.py
│   ├── file_discovery.py
│   ├── file_type_filter.py
│   ├── ignore_rules.py
│   ├── improvement_suggester.py
│   ├── llm_client.py
│   ├── multi_codebase.py
│   ├── path_validator.py
│   └── static_analyzer.py
├── config/
│   ├── ignore_rules_config.py
│   └── settings.py
└── tools/
    └── semgrep_wrapper.py
```
