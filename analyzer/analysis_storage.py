"""
Main AnalysisStorage module that combines all functionality from helper modules.
This file maintains the original interface while splitting implementation across smaller files.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
import logging
import os
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from analyzer.analysis_storage_models import AnalysisResult, ExecutionLog, Base
from analyzer.analysis_storage_base import AnalysisStorageBase
from analyzer.analysis_storage_vector import AnalysisStorageVector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisStorage(AnalysisStorageBase, AnalysisStorageVector):
    """
    Main AnalysisStorage class that combines all functionality.
    This class inherits from all helper classes to maintain the original interface.
    """
    def __init__(self, storage_path: str = "./analysis_data"):
        # Initialize the base class
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Initialize SQLite database
        self.db_path = self.storage_path / "analysis.db"
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        
        # Check if database exists and perform migration if needed
        if self.db_path.exists():
            self._migrate_database_schema()
        
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Initialize vector embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.vector_dim = 384  # Dimension of the embedding model
        
        # Initialize FAISS for vector storage
        self.faiss_index_path = self.storage_path / "faiss_index.bin"
        self.faiss_metadata_path = self.storage_path / "faiss_metadata.json"
        self.faiss_index = None
        self.faiss_id_to_record_id = {}  # Map FAISS IDs to SQLite record IDs
        self.record_id_to_faiss_id = {}  # Map SQLite record IDs to FAISS IDs
        
        # Load or create FAISS index
        self._initialize_faiss_index()
        
        # Load metadata and consistency check
        self._load_metadata_and_validate()
       
    def store_analysis(
                      self, 
                      codebase_path: str,
                      analysis_type: str,
                      results: Dict[str, Any],
                      summary: str = "") -> int:
        """Store analysis results in database and vector store"""
         
        # Calculate metrics for trending
        metrics = self._calculate_metrics(results)
         
        # Extract execution failure information
        execution_failures = results.get("execution_failures", [])
        failure_count = results.get("failure_count", 0)
         
        # Extract completeness metrics
        coverage_percentage = 0.0
        files_discovered = 0
        files_analyzed = 0
        files_skipped = 0
        completeness_context = ""
         
        # Get completeness metrics based on analysis type
        if analysis_type == "static":
            coverage_percentage = results.get("summary", {}).get("coverage_percentage", 0.0)
            files_discovered = results.get("custom_analysis", {}).get("files_discovered", 0)
            files_analyzed = results.get("custom_analysis", {}).get("files_analyzed", 0)
            files_skipped = results.get("custom_analysis", {}).get("files_skipped", 0)
            completeness_context = results.get("analysis_completeness", {}).get("completeness_context", "")
        elif analysis_type == "dynamic":
            coverage_percentage = results.get("method_coverage_percentage", 0.0)
            files_discovered = results.get("execution_coverage", {}).get("scripts_discovered", 0)
            files_analyzed = results.get("execution_coverage", {}).get("scripts_analyzed", 0)
            files_skipped = results.get("execution_coverage", {}).get("scripts_skipped", 0)
            completeness_context = results.get("analysis_completeness", {}).get("completeness_context", "")
        else:  # comparison or other types
            coverage_percentage = results.get("analysis_completeness", {}).get("coverage_metrics", {}).get("overall_coverage", 0.0)
            completeness_context = results.get("analysis_completeness", {}).get("coverage_metrics", {}).get("completeness_context", "")
         
        # Determine analysis status based on failures and coverage
        analysis_status = "complete"
        if failure_count > 0:
            # Check if any failures are actual errors (not analysis findings)
            actual_errors = [f for f in execution_failures if not f.get("is_analysis_finding", True)]
            if actual_errors:
                analysis_status = "partial" if len(actual_errors) < failure_count else "failed"
            else:
                analysis_status = "partial"  # Only analysis findings, still partial
        elif coverage_percentage < 100:
            analysis_status = "partial"  # Complete execution but incomplete coverage
         
        # Extract profiling data for new columns
        scalene_data = results.get('scalene_profiling', {})
        viztracer_data = results.get('viztracer_tracing', {})
         
        # Extract profiling timestamps
        scalene_timestamp = scalene_data.get('timestamp')
        viztracer_timestamp = viztracer_data.get('timestamp')
         
        # Convert string timestamps to datetime objects if needed
        if isinstance(scalene_timestamp, str):
            scalene_timestamp = datetime.fromisoformat(scalene_timestamp)
        if isinstance(viztracer_timestamp, str):
            viztracer_timestamp = datetime.fromisoformat(viztracer_timestamp)
         
        # Create database record
        analysis_record = AnalysisResult(
            codebase_path=codebase_path,
            analysis_type=analysis_type,
            summary=summary or self._generate_summary(results),
            full_results=results,
            metrics=metrics,
            issue_count=metrics.get('total_issues', 0),
            quality_score=metrics.get('quality_score', 0),
            complexity_score=metrics.get('complexity_score', 0),
            failure_count=failure_count,
            execution_failures=execution_failures,
            analysis_status=analysis_status,
            coverage_percentage=coverage_percentage,
            completeness_context=completeness_context,
            files_discovered=files_discovered,
            files_analyzed=files_analyzed,
            files_skipped=files_skipped,
             
            # Scalene profiling data
            scalene_cpu_data=scalene_data.get('cpu_data'),
            scalene_memory_data=scalene_data.get('memory_data'),
            scalene_gpu_data=scalene_data.get('gpu_data'),
            scalene_ai_suggestions=scalene_data.get('ai_suggestions'),
            scalene_timestamp=scalene_timestamp,
            has_scalene_data=1 if scalene_data else 0,
            scalene_coverage=scalene_data.get('coverage', 0.0),
            peak_memory_usage=scalene_data.get('peak_usage', 0.0),
            cpu_hotspot_count=scalene_data.get('hot_spot_count', 0),
            scalene_execution_time=scalene_data.get('execution_time', 0.0),
            average_cpu_usage=scalene_data.get('average_cpu_usage', 0.0),
            average_memory_usage=scalene_data.get('average_memory_usage', 0.0),
            gpu_utilization=scalene_data.get('gpu_utilization', 0.0),
             
            # VizTracer profiling data
            viztracer_call_data=viztracer_data.get('call_data'),
            viztracer_exception_data=viztracer_data.get('exception_data'),
            viztracer_flow_data=viztracer_data.get('flow_data'),
            viztracer_timestamp=viztracer_timestamp,
            has_viztracer_data=1 if viztracer_data else 0,
            viztracer_coverage=viztracer_data.get('coverage', 0.0),
            function_call_count=viztracer_data.get('call_count', 0),
            exception_count=viztracer_data.get('exception_count', 0),
            viztracer_execution_time=viztracer_data.get('execution_time', 0.0)
        )
        
        self.session.add(analysis_record)
        self.session.commit()
         
        # Generate and store vector embedding
        embedding_text = self._prepare_embedding_text(results, summary)
        embedding = self.embedding_model.encode(embedding_text)
         
        # Store in FAISS
        self._add_vector_to_faiss(analysis_record.id, embedding, {
            "codebase_path": codebase_path,
            "analysis_type": analysis_type,
            "timestamp": analysis_record.timestamp.isoformat(),
            "analysis_status": analysis_status,
            "failure_count": failure_count
        })
         
        return analysis_record.id
       
    def store_execution_logs(self, analysis_id: int, execution_failures: List[Dict[str, Any]]):
        """Store execution logs for an analysis in the execution_logs table"""
        for failure in execution_failures:
            execution_log = ExecutionLog(
                analysis_id=analysis_id,
                log_level=failure.get('severity', 'ERROR'),
                message=failure.get('message', ''),
                context=failure.get('context', ''),
                raw_error=failure.get('raw_error', ''),
                traceback=failure.get('traceback', ''),
                execution_details={
                    'failure_type': failure.get('failure_type', 'UNKNOWN_ERROR'),
                    'is_analysis_finding': failure.get('is_analysis_finding', False),
                    'timestamp': failure.get('timestamp', datetime.utcnow().isoformat()),
                    'execution_log': failure.get('execution_log', '')
                }
            )
            self.session.add(execution_log)
         
        self.session.commit()
        logger.info(f"Stored {len(execution_failures)} execution logs for analysis {analysis_id}")
       
    def get_execution_logs(self, analysis_id: int) -> List[Dict[str, Any]]:
        """Retrieve execution logs for a specific analysis"""
        logs = self.session.query(ExecutionLog).filter(
            ExecutionLog.analysis_id == analysis_id
        ).order_by(ExecutionLog.timestamp).all()
         
        return [{
            'id': log.id,
            'timestamp': log.timestamp.isoformat(),
            'log_level': log.log_level,
            'message': log.message,
            'context': log.context,
            'raw_error': log.raw_error,
            'traceback': log.traceback,
            'execution_details': log.execution_details
        } for log in logs]
       
    def get_error_analysis(self, codebase_path: str = None, days_back: int = 30) -> Dict[str, Any]:
        """Get error analysis and trends across analyses"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
         
        query = self.session.query(ExecutionLog).filter(
            ExecutionLog.timestamp >= cutoff_date
        )
         
        if codebase_path:
            # Join with AnalysisResult to filter by codebase
            query = query.join(AnalysisResult).filter(
                AnalysisResult.codebase_path == codebase_path
            )
         
        logs = query.order_by(ExecutionLog.timestamp).all()
         
        error_analysis = {
            'total_logs': len(logs),
            'by_severity': {
                'INFO': 0,
                'WARNING': 0,
                'ERROR': 0,
                'CRITICAL': 0
            },
            'by_type': {},
            'timeline': [],
            'recent_errors': []
        }
         
        for log in logs:
            # Count by severity
            severity = log.log_level
            if severity in error_analysis['by_severity']:
                error_analysis['by_severity'][severity] += 1
             
            # Count by failure type
            failure_type = log.execution_details.get('failure_type', 'UNKNOWN')
            error_analysis['by_type'][failure_type] = error_analysis['by_type'].get(failure_type, 0) + 1
             
            # Add to timeline
            error_analysis['timeline'].append({
                'timestamp': log.timestamp.isoformat(),
                'severity': severity,
                'failure_type': failure_type
            })
             
            # Add recent errors (limit to 10)
            if severity in ['ERROR', 'CRITICAL'] and len(error_analysis['recent_errors']) < 10:
                error_analysis['recent_errors'].append({
                    'timestamp': log.timestamp.isoformat(),
                    'severity': severity,
                    'message': log.message,
                    'context': log.context,
                    'failure_type': failure_type,
                    'raw_error': log.raw_error[:200] + '...' if len(log.raw_error) > 200 else log.raw_error
                })
         
        return error_analysis
       
    def get_raw_errors(self, analysis_id: int) -> List[Dict[str, Any]]:
        """Get raw error data for debugging purposes"""
        logs = self.session.query(ExecutionLog).filter(
            ExecutionLog.analysis_id == analysis_id,
            ExecutionLog.log_level.in_(['ERROR', 'CRITICAL'])
        ).order_by(ExecutionLog.timestamp).all()
         
        return [{
            'id': log.id,
            'timestamp': log.timestamp.isoformat(),
            'severity': log.log_level,
            'failure_type': log.execution_details.get('failure_type', 'UNKNOWN'),
            'message': log.message,
            'context': log.context,
            'raw_error': log.raw_error,
            'traceback': log.traceback,
            'execution_log': log.execution_details.get('execution_log', ''),
            'is_analysis_finding': log.execution_details.get('is_analysis_finding', False)
        } for log in logs]
       
    def delete_analysis(self, record_id: int) -> bool:
        """Delete analysis record and its associated vector"""
        # First remove from FAISS if it exists
        if record_id in self.record_id_to_faiss_id:
            faiss_id = self.record_id_to_faiss_id[record_id]
             
            # Remove from FAISS index
            if self.faiss_index:
                faiss_id_array = np.array([faiss_id], dtype=np.int64)
                self.faiss_index.remove_ids(faiss_id_array)
             
            # Clean up metadata
            del self.faiss_id_to_record_id[faiss_id]
            del self.record_id_to_faiss_id[record_id]
             
            self._save_faiss_index()
            logger.info(f"Removed vector for record {record_id} with FAISS ID {faiss_id}")
         
        # Delete from SQLite
        record = self.session.query(AnalysisResult).filter(AnalysisResult.id == record_id).first()
        if record:
            self.session.delete(record)
            self.session.commit()
            return True
         
        return False
       
    def get_vector_metadata(self, record_id: int) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific vector"""
        if record_id not in self.record_id_to_faiss_id:
            return None
         
        faiss_id = self.record_id_to_faiss_id[record_id]
         
        # Get the record from SQLite
        record = self.session.query(AnalysisResult).filter(AnalysisResult.id == record_id).first()
         
        if record:
            return {
                'faiss_id': faiss_id,
                'record_id': record_id,
                'codebase_path': record.codebase_path,
                'analysis_type': record.analysis_type,
                'timestamp': record.timestamp.isoformat(),
                'vector_dimension': self.vector_dim
            }
         
        return None
       
    def get_analysis_trends(self, 
                           codebase_path: str, 
                           days_back: int = 30) -> Dict[str, Any]:
        """Get trends for a codebase over time"""
        # Calculate cutoff datenow, fixing utcnow usage
        cutoff_date = datetime.now() - timedelta(days=days_back)
         
        records = self.session.query(AnalysisResult).filter(
            AnalysisResult.codebase_path == codebase_path,
            AnalysisResult.timestamp >= cutoff_date
        ).order_by(AnalysisResult.timestamp).all()
         
        trends = {
            'timestamps': [r.timestamp.isoformat() for r in records],
            'issue_counts': [r.issue_count for r in records],
            'quality_scores': [r.quality_score for r in records],
            'complexity_scores': [r.complexity_score for r in records],
            'summary_stats': {
                'total_analyses': len(records),
                'avg_issues': np.mean([r.issue_count for r in records]) if records else 0,
                'quality_trend': self._calculate_trend([r.quality_score for r in records]),
                'complexity_trend': self._calculate_trend([r.complexity_score for r in records])
            }
        }
         
        return trends
       
    def get_comparison_history(self, codebase_a: str, codebase_b: str) -> List[Dict[str, Any]]:
        """Get history of comparisons between two codebases"""
         
        records = self.session.query(AnalysisResult).filter(
            AnalysisResult.analysis_type == 'comparison',
            AnalysisResult.codebase_path.in_([codebase_a, codebase_b])
        ).order_by(AnalysisResult.timestamp.desc()).limit(10).all()
         
        return [
            {
                'id': r.id,
                'timestamp': r.timestamp.isoformat(),
                'summary': r.summary,
                'metrics': r.metrics
            }
            for r in records
        ]
       
    def export_analysis(self, record_id: int, export_path: str) -> bool:
        """Export analysis to JSON file"""
        record = self.session.query(AnalysisResult).filter(
            AnalysisResult.id == record_id
        ).first()
         
        if not record:
            return False
         
        export_data = {
            'metadata': {
                'id': record.id,
                'codebase_path': record.codebase_path,
                'analysis_type': record.analysis_type,
                'timestamp': record.timestamp.isoformat()
            },
            'summary': record.summary,
            'metrics': record.metrics,
            'full_results': record.full_results
        }
         
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)
         
        return True
       
    def _calculate_metrics(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Calculate quality metrics from analysis results including completeness"""
        metrics = {}
         
        # Issue count (excluding analysis findings)
        semgrep_issues = len(results.get('static_analysis', {}).get('semgrep', {}).get('results', []))
        actual_failures = len([f for f in results.get('execution_failures', []) if not f.get('is_analysis_finding', True)])
        metrics['total_issues'] = semgrep_issues + actual_failures
         
        # Quality score (0-100, higher is better)
        base_score = 100
        penalty = min(metrics['total_issues'] * 2, 50)  # Max 50 point penalty for issues
         
        # Adjust for analysis completeness
        completeness_penalty = 0
        coverage_percentage = 0.0
         
        # Get coverage percentage based on analysis type
        if 'static_analysis' in results:
            coverage_percentage = results.get('static_analysis', {}).get('summary', {}).get('coverage_percentage', 0.0)
        elif 'method_coverage_percentage' in results:
            coverage_percentage = results.get('method_coverage_percentage', 0.0)
        else:
            coverage_percentage = results.get('analysis_completeness', {}).get('coverage_metrics', {}).get('overall_coverage', 0.0)
         
        # Coverage-based penalty
        if coverage_percentage < 50:
            completeness_penalty = 30  # Significant penalty for low coverage
        elif coverage_percentage < 80:
            completeness_penalty = 15  # Moderate penalty for medium coverage
        elif coverage_percentage < 100:
            completeness_penalty = 5   # Small penalty for high but incomplete coverage
         
        metrics['quality_score'] = max(base_score - penalty - completeness_penalty, 0)
         
        # Complexity score
        call_complexity = len(results.get('dynamic_analysis', {}).get('call_graph', {}).get('most_complex', []))
        file_complexity = len(results.get('static_analysis', {}).get('custom_analysis', {}).get('large_files', []))
        metrics['complexity_score'] = call_complexity + file_complexity
         
        # Add failure metrics
        metrics['failure_count'] = results.get('failure_count', 0)
        metrics['analysis_findings'] = len([f for f in results.get('execution_failures', []) if f.get('is_analysis_finding', False)])
         
        # Add coverage metrics
        metrics['coverage_percentage'] = coverage_percentage
        metrics['completeness_score'] = coverage_percentage  # 0-100 scale
         
        # Add Scalene metrics
        if 'scalene_profiling' in results:
            scalene = results['scalene_profiling']
            metrics['cpu_hotspots'] = scalene.get('hot_spot_count', 0)
            metrics['peak_memory_mb'] = scalene.get('peak_usage', 0)
            metrics['memory_allocations'] = scalene.get('allocation_count', 0)
            metrics['cpu_coverage'] = scalene.get('coverage', 0.0)
            metrics['average_cpu_usage'] = scalene.get('average_cpu_usage', 0.0)
            metrics['average_memory_usage'] = scalene.get('average_memory_usage', 0.0)
            metrics['gpu_utilization'] = scalene.get('gpu_utilization', 0.0)
            metrics['scalene_execution_time'] = scalene.get('execution_time', 0.0)
             
            # Adjust quality score based on profiling results
            # Penalize for high memory usage or many hotspots
            memory_penalty = min(scalene.get('peak_usage', 0) / 100, 10)  # Max 10 point penalty
            hotspot_penalty = min(scalene.get('hot_spot_count', 0) / 5, 10)  # Max 10 point penalty
            metrics['quality_score'] = max(metrics['quality_score'] - memory_penalty - hotspot_penalty, 0)
         
        # Add VizTracer metrics
        if 'viztracer_tracing' in results:
            viztracer = results['viztracer_tracing']
            metrics['function_calls'] = viztracer.get('call_count', 0)
            metrics['exceptions_traced'] = viztracer.get('exception_count', 0)
            metrics['execution_flow_complexity'] = len(viztracer.get('execution_flow', []))
            metrics['trace_coverage'] = viztracer.get('coverage', 0.0)
            metrics['viztracer_execution_time'] = viztracer.get('execution_time', 0.0)
             
            # Adjust quality score based on tracing results
            # Penalize for many exceptions or complex execution flow
            exception_penalty = min(viztracer.get('exception_count', 0) / 2, 10)  # Max 10 point penalty
            complexity_penalty = min(len(viztracer.get('execution_flow', [])) / 100, 5)  # Max 5 point penalty
            metrics['quality_score'] = max(metrics['quality_score'] - exception_penalty - complexity_penalty, 0)
         
        return metrics
       
    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """Generate summary text for embedding with completeness metrics"""
        static = results.get('static_analysis', {})
        dynamic = results.get('dynamic_analysis', {})
         
        summary_parts = [
            f"Issues found: {len(static.get('semgrep', {}).get('results', []))}",
            f"Code quality: {static.get('summary', {}).get('quality_metrics', {})}",
            f"Dynamic analysis: {dynamic.get('execution_summary', 'No data')}",
        ]
         
        # Add coverage and completeness information
        coverage_percentage = 0.0
        if 'static_analysis' in results:
            coverage_percentage = results.get('static_analysis', {}).get('summary', {}).get('coverage_percentage', 0.0)
        elif 'method_coverage_percentage' in results:
            coverage_percentage = results.get('method_coverage_percentage', 0.0)
        else:
            coverage_percentage = results.get('analysis_completeness', {}).get('coverage_metrics', {}).get('overall_coverage', 0.0)
         
        summary_parts.append(f"Analysis coverage: {coverage_percentage:.1f}%")
         
        # Add failure information if present
        if results.get('execution_failures'):
            failure_count = len(results['execution_failures'])
            analysis_findings = len([f for f in results['execution_failures'] if f.get('is_analysis_finding', False)])
            actual_errors = failure_count - analysis_findings
             
            summary_parts.append(f"Analysis completeness: {results.get('analysis_completeness', {}).get('status', 'unknown')}")
            summary_parts.append(f"Execution failures: {failure_count} total ({analysis_findings} findings, {actual_errors} errors)")
             
            # Add completeness context if available
            completeness_context = ""
            if 'analysis_completeness' in results and 'coverage_metrics' in results['analysis_completeness']:
                completeness_context = results['analysis_completeness']['coverage_metrics'].get('completeness_context', "")
            elif 'completeness_context' in results:
                completeness_context = results['completeness_context']
             
            if completeness_context:
                summary_parts.append(f"Completeness context: {completeness_context}")
         
        # Add Scalene summary
        if 'scalene_profiling' in results:
            scalene = results['scalene_profiling']
            summary_parts.append(f"Scalene: {scalene.get('hot_spot_count', 0)} CPU hotspots, {scalene.get('peak_usage', 0):.1f}MB peak memory, {scalene.get('coverage', 0.0):.2f}% CPU coverage")
            summary_parts.append(f"Scalene execution: {scalene.get('execution_time', 0.0):.2f}s, {scalene.get('average_cpu_usage', 0.0):.1f}% CPU, {scalene.get('average_memory_usage', 0.0):.1f}MB avg memory")
            if scalene.get('gpu_utilization', 0.0) > 0:
                summary_parts.append(f"GPU utilization: {scalene.get('gpu_utilization', 0.0):.1f}%")
         
        # Add VizTracer summary
        if 'viztracer_tracing' in results:
            viztracer = results['viztracer_tracing']
            summary_parts.append(f"VizTracer: {viztracer.get('call_count', 0)} function calls, {viztracer.get('exception_count', 0)} exceptions traced, {viztracer.get('coverage', 0.0):.2f}% trace coverage")
            summary_parts.append(f"VizTracer execution: {viztracer.get('execution_time', 0.0):.2f}s, {len(viztracer.get('execution_flow', []))} execution flow points")
         
        return ". ".join(summary_parts)
       
    def _prepare_embedding_text(self, results: Dict[str, Any], summary: str) -> str:
        """Prepare text for vector embedding"""
        embedding_parts = [summary]
         
        # Add key findings from analysis
        if 'llm_analysis' in results:
            embedding_parts.append(results['llm_analysis'][:500])  # Limit length
         
        # Add issue descriptions
        issues = results.get('static_analysis', {}).get('semgrep', {}).get('results', [])
        for issue in issues[:5]:  # Top 5 issues
            embedding_parts.append(issue.get('message', ''))
         
        return ". ".join(embedding_parts)
       
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend from time series data"""
        if len(values) < 2:
            return "stable"
         
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
         
        avg_first = np.mean(first_half)
        avg_second = np.mean(second_half)
         
        if avg_second > avg_first * 1.1:
            return "improving"
        elif avg_second < avg_first * 0.9:
            return "worsening"
        else:
            return "stable"