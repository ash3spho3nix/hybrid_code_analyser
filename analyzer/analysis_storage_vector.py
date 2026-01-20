from typing import Dict, Any, List, Optional
import numpy as np
import faiss
import json
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisStorageVector:
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.faiss_index_path = self.storage_path / "faiss_index.bin"
        self.faiss_metadata_path = self.storage_path / "faiss_metadata.json"
        self.faiss_index = None
        self.faiss_id_to_record_id = {}  # Map FAISS IDs to SQLite record IDs
        self.record_id_to_faiss_id = {}  # Map SQLite record IDs to FAISS IDs
        self.vector_dim = 384  # Dimension of the embedding model
        
        # Initialize FAISS index
        self._initialize_faiss_index()
        self._load_metadata_and_validate()
       
    def _initialize_faiss_index(self):
        """Initialize FAISS index - create new or load existing"""
        if self.faiss_index_path.exists():
            try:
                self._load_faiss_index()
                logger.info("Loaded existing FAISS index")
            except Exception as e:
                logger.warning(f"Failed to load FAISS index: {e}. Creating new index.")
                self._create_new_faiss_index()
        else:
            self._create_new_faiss_index()
       
    def _create_new_faiss_index(self):
        """Create a new FAISS index"""
        # Use IndexFlatL2 for exact search (L2 distance)
        self.faiss_index = faiss.IndexFlatL2(self.vector_dim)
        logger.info("Created new FAISS index")
       
    def _load_faiss_index(self):
        """Load FAISS index from disk"""
        self.faiss_index = faiss.read_index(str(self.faiss_index_path))
        logger.info(f"Loaded FAISS index with {self.faiss_index.ntotal} vectors")
       
    def _save_faiss_index(self):
        """Save FAISS index to disk"""
        try:
            faiss.write_index(self.faiss_index, str(self.faiss_index_path))
            self._save_metadata()
            logger.info(f"Saved FAISS index with {self.faiss_index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")
            raise
       
    def _load_metadata_and_validate(self):
        """Load metadata and validate consistency with SQLite"""
        if self.faiss_metadata_path.exists():
            try:
                with open(self.faiss_metadata_path, 'r') as f:
                    metadata = json.load(f)
                    self.faiss_id_to_record_id = metadata.get('faiss_id_to_record_id', {})
                    self.record_id_to_faiss_id = metadata.get('record_id_to_faiss_id', {})
                 
                # Validate consistency
                self._validate_consistency()
                logger.info(f"Loaded metadata for {len(self.faiss_id_to_record_id)} vectors")
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}. Starting with empty metadata.")
                self.faiss_id_to_record_id = {}
                self.record_id_to_faiss_id = {}
        else:
            self.faiss_id_to_record_id = {}
            self.record_id_to_faiss_id = {}
       
    def _save_metadata(self):
        """Save metadata to disk"""
        metadata = {
            'faiss_id_to_record_id': self.faiss_id_to_record_id,
            'record_id_to_faiss_id': self.record_id_to_faiss_id,
            'last_updated': datetime.utcnow().isoformat(),
            'vector_count': self.faiss_index.ntotal if self.faiss_index else 0
        }
         
        with open(self.faiss_metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
       
    def _validate_consistency(self):
        """Validate consistency between FAISS index and SQLite database"""
        if not self.faiss_index or not self.faiss_id_to_record_id:
            return
         
        # Check if FAISS index size matches metadata
        if self.faiss_index.ntotal != len(self.faiss_id_to_record_id):
            logger.warning(f"FAISS index size mismatch: index has {self.faiss_index.ntotal} vectors, metadata has {len(self.faiss_id_to_record_id)} entries")
             
        # Check if all record IDs in metadata exist in SQLite
        missing_records = []
        for record_id in self.faiss_id_to_record_id.values():
            # This would need a session to check, so we'll skip this validation
            # in the vector-only class and handle it in the main class
            pass
         
        if missing_records:
            logger.warning(f"Found {len(missing_records)} orphaned vectors for missing SQLite records")
            # Clean up orphaned vectors
            self._cleanup_orphaned_vectors(missing_records)
       
    def _cleanup_orphaned_vectors(self, record_ids: List[int]):
        """Remove vectors for records that no longer exist in SQLite"""
        if not self.faiss_index:
            return
         
        # Find FAISS IDs for orphaned records
        faiss_ids_to_remove = []
        for record_id in record_ids:
            if record_id in self.record_id_to_faiss_id:
                faiss_id = self.record_id_to_faiss_id[record_id]
                faiss_ids_to_remove.append(faiss_id)
                 
                # Clean up metadata
                del self.faiss_id_to_record_id[faiss_id]
                del self.record_id_to_faiss_id[record_id]
         
        if faiss_ids_to_remove:
            # Convert to numpy array for FAISS
            faiss_id_array = np.array(faiss_ids_to_remove, dtype=np.int64)
            self.faiss_index.remove_ids(faiss_id_array)
            logger.info(f"Removed {len(faiss_ids_to_remove)} orphaned vectors")
            self._save_faiss_index()
       
    def _add_vector_to_faiss(self, record_id: int, embedding: np.ndarray, metadata: Dict[str, Any]):
        """Add a vector to FAISS index with proper ID mapping"""
        if not self.faiss_index:
            self._create_new_faiss_index()
         
        # Convert embedding to float32 array (required by FAISS)
        embedding_array = embedding.astype(np.float32).reshape(1, -1)
         
        # Add to FAISS index - FAISS will assign its own internal ID
        self.faiss_index.add(embedding_array)
         
        # The FAISS ID is the position in the index (0-based)
        # Since we just added one vector, the new ID is ntotal - 1
        faiss_id = self.faiss_index.ntotal - 1
         
        # Update ID mappings
        self.faiss_id_to_record_id[faiss_id] = record_id
        self.record_id_to_faiss_id[record_id] = faiss_id
         
        # Save index and metadata
        self._save_faiss_index()
         
        logger.info(f"Added vector for record {record_id} with FAISS ID {faiss_id}")
       
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the FAISS index"""
        if not self.faiss_index:
            return {'vector_count': 0, 'is_trained': False}
         
        return {
            'vector_count': self.faiss_index.ntotal,
            'is_trained': self.faiss_index.is_trained,
            'dimension': self.faiss_index.d,
            'metadata_count': len(self.faiss_id_to_record_id)
        }
       
    def search_similar_analyses(self, 
                               query: str, 
                               codebase_filter: str = None,
                               n_results: int = 5) -> List[Dict[str, Any]]:
        """Semantic search through past analyses using FAISS"""
        
        if not self.faiss_index or self.faiss_index.ntotal == 0:
            logger.warning("FAISS index is empty, no results to return")
            return []
         
        # Generate query embedding
        from sentence_transformers import SentenceTransformer
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        query_embedding = embedding_model.encode(query).astype(np.float32)
         
        # Search in FAISS
        distances, faiss_ids = self.faiss_index.search(query_embedding.reshape(1, -1), n_results)
         
        # Get full records from SQLite with optional filtering
        similar_analyses = []
        for i, faiss_id in enumerate(faiss_ids[0]):
            if faiss_id == -1:  # No more results
                continue
                 
            # Look up the record ID using our mapping
            record_id = self.faiss_id_to_record_id.get(faiss_id)
            if not record_id:
                logger.warning(f"FAISS ID {faiss_id} not found in metadata")
                continue
             
            # Note: This method would need a session to get the actual record
            # For now, we'll return just the metadata we have
            similar_analyses.append({
                'faiss_id': faiss_id,
                'record_id': record_id,
                'similarity_score': 1.0 / (1.0 + distances[0][i])  # Convert distance to similarity
            })
         
        return similar_analyses