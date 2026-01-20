import sqlalchemy as sa
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from datetime import datetime, timedelta
import os
import pickle
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class AnalysisResult(Base):
    __tablename__ = 'analysis_results'
     
    id = Column(Integer, primary_key=True)
    codebase_path = Column(String, index=True)
    analysis_type = Column(String)  # 'static', 'dynamic', 'comparison'
    timestamp = Column(DateTime, default=datetime.utcnow)
    summary = Column(Text)
    full_results = Column(JSON)  # Store complete analysis as JSON
    metrics = Column(JSON)  # Key metrics for trending
    embedding = Column(Text)  # Store vector embedding as JSON string
     
    # Quality metrics for trending
    issue_count = Column(Integer)
    quality_score = Column(Float)
    complexity_score = Column(Float)
     
    # Execution failure tracking
    failure_count = Column(Integer, default=0)
    execution_failures = Column(JSON)  # Store execution failures as JSON
    analysis_status = Column(String, default="complete")  # 'complete', 'partial', 'failed'
     
    # Completeness metrics
    coverage_percentage = Column(Float, default=0.0)
    completeness_context = Column(Text)
    files_discovered = Column(Integer, default=0)
    files_analyzed = Column(Integer, default=0)
    files_skipped = Column(Integer, default=0)
     
    # Scalene profiling data
    scalene_cpu_data = Column(JSON)  # Scalene CPU profiling results
    scalene_memory_data = Column(JSON)  # Scalene memory profiling results  
    scalene_gpu_data = Column(JSON)  # Scalene GPU profiling results (if available)
    scalene_ai_suggestions = Column(JSON)  # AI optimization suggestions
     
    # VizTracer profiling data
    viztracer_call_data = Column(JSON)  # VizTracer function call tracing
    viztracer_exception_data = Column(JSON)  # VizTracer exception tracing
    viztracer_flow_data = Column(JSON)  # Execution flow visualization data
     
    # Timestamps for profiling data
    scalene_timestamp = Column(DateTime)  # When Scalene profiling was performed
    viztracer_timestamp = Column(DateTime)  # When VizTracer profiling was performed
     
    # Profiling status flags
    has_scalene_data = Column(Integer, default=0)  # Boolean flag for Scalene data presence
    has_viztracer_data = Column(Integer, default=0)  # Boolean flag for VizTracer data presence
     
    # Profiling coverage metrics
    scalene_coverage = Column(Float, default=0.0)  # Scalene profiling coverage percentage
    viztracer_coverage = Column(Float, default=0.0)  # VizTracer tracing coverage percentage
     
    # Performance metrics from profiling
    peak_memory_usage = Column(Float, default=0.0)  # Peak memory usage in MB
    cpu_hotspot_count = Column(Integer, default=0)  # Number of CPU hotspots detected
    function_call_count = Column(Integer, default=0)  # Total function calls traced
    exception_count = Column(Integer, default=0)  # Total exceptions traced
     
    # Execution time metrics
    scalene_execution_time = Column(Float, default=0.0)  # Scalene profiling execution time
    viztracer_execution_time = Column(Float, default=0.0)  # VizTracer profiling execution time
     
    # Resource utilization metrics
    average_cpu_usage = Column(Float, default=0.0)  # Average CPU usage percentage
    average_memory_usage = Column(Float, default=0.0)  # Average memory usage in MB
    gpu_utilization = Column(Float, default=0.0)  # GPU utilization percentage (if applicable)

class ExecutionLog(Base):
    __tablename__ = 'execution_logs'
     
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, sa.ForeignKey('analysis_results.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    log_level = Column(String)  # 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    message = Column(Text)
    context = Column(Text)
    raw_error = Column(Text)
    traceback = Column(Text)
    execution_details = Column(JSON)  # Additional execution context
     
    # Relationship to analysis result
    analysis = sa.orm.relationship("AnalysisResult", backref=sa.orm.backref("execution_logs", lazy=True))