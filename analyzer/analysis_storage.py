import sqlalchemy as sa
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import chromadb
from chromadb.config import Settings

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

class AnalysisStorage:
    def __init__(self, storage_path: str = "./analysis_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Initialize SQLite database
        self.db_path = self.storage_path / "analysis.db"
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Initialize vector embeddings
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.vector_dim = 384  # Dimension of the embedding model
        
        # Initialize Chroma for vector storage
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.storage_path / "chroma_db"),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="analysis_embeddings",
            metadata={"description": "Code analysis results embeddings"}
        )
    
    def store_analysis(self, 
                      codebase_path: str,
                      analysis_type: str,
                      results: Dict[str, Any],
                      summary: str = "") -> int:
        """Store analysis results in database and vector store"""
        
        # Calculate metrics for trending
        metrics = self._calculate_metrics(results)
        
        # Create database record
        analysis_record = AnalysisResult(
            codebase_path=codebase_path,
            analysis_type=analysis_type,
            summary=summary or self._generate_summary(results),
            full_results=results,
            metrics=metrics,
            issue_count=metrics.get('total_issues', 0),
            quality_score=metrics.get('quality_score', 0),
            complexity_score=metrics.get('complexity_score', 0)
        )
        
        self.session.add(analysis_record)
        self.session.commit()
        
        # Generate and store vector embedding
        embedding_text = self._prepare_embedding_text(results, summary)
        embedding = self.embedding_model.encode(embedding_text).tolist()
        
        # Store in Chroma
        self.collection.add(
            documents=[embedding_text],
            metadatas=[{
                "record_id": analysis_record.id,
                "codebase_path": codebase_path,
                "analysis_type": analysis_type,
                "timestamp": analysis_record.timestamp.isoformat()
            }],
            ids=[str(analysis_record.id)]
        )
        
        return analysis_record.id
    
    def search_similar_analyses(self, 
                              query: str, 
                              codebase_filter: str = None,
                              n_results: int = 5) -> List[Dict[str, Any]]:
        """Semantic search through past analyses"""
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Search in Chroma
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={"codebase_path": codebase_filter} if codebase_filter else None
        )
        
        # Get full records from SQLite
        similar_analyses = []
        for i, record_id in enumerate(results['ids'][0]):
            record = self.session.query(AnalysisResult).filter(
                AnalysisResult.id == int(record_id)
            ).first()
            
            if record:
                similar_analyses.append({
                    'record': record,
                    'similarity_score': results['distances'][0][i] if results['distances'] else 0
                })
        
        return similar_analyses
    
    def get_analysis_trends(self, 
                          codebase_path: str, 
                          days_back: int = 30) -> Dict[str, Any]:
        """Get trends for a codebase over time"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
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
        """Calculate quality metrics from analysis results"""
        metrics = {}
        
        # Issue count
        static_issues = len(results.get('static_analysis', {}).get('sonarqube', {}).get('issues', []))
        semgrep_issues = len(results.get('static_analysis', {}).get('semgrep', {}).get('results', []))
        metrics['total_issues'] = static_issues + semgrep_issues
        
        # Quality score (0-100, higher is better)
        base_score = 100
        penalty = min(metrics['total_issues'] * 2, 50)  # Max 50 point penalty for issues
        metrics['quality_score'] = max(base_score - penalty, 0)
        
        # Complexity score
        call_complexity = len(results.get('dynamic_analysis', {}).get('call_graph', {}).get('most_complex', []))
        file_complexity = len(results.get('static_analysis', {}).get('custom_analysis', {}).get('large_files', []))
        metrics['complexity_score'] = call_complexity + file_complexity
        
        return metrics
    
    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """Generate summary text for embedding"""
        static = results.get('static_analysis', {})
        dynamic = results.get('dynamic_analysis', {})
        
        summary_parts = [
            f"Issues found: {len(static.get('sonarqube', {}).get('issues', []))}",
            f"Code quality: {static.get('summary', {}).get('quality_metrics', {})}",
            f"Dynamic analysis: {dynamic.get('execution_summary', 'No data')}",
        ]
        
        return ". ".join(summary_parts)
    
    def _prepare_embedding_text(self, results: Dict[str, Any], summary: str) -> str:
        """Prepare text for vector embedding"""
        embedding_parts = [summary]
        
        # Add key findings from analysis
        if 'llm_analysis' in results:
            embedding_parts.append(results['llm_analysis'][:500])  # Limit length
        
        # Add issue descriptions
        issues = results.get('static_analysis', {}).get('sonarqube', {}).get('issues', [])
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