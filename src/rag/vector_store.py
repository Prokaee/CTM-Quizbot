"""
Vector Store Module

In-memory vector store using FAISS for fast similarity search.
Can be extended to use Vertex AI Vector Search for production.
"""

import faiss
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import pickle

from src.processing.embedder import EmbeddedChunk


@dataclass
class SearchResult:
    """Result from vector search"""
    chunk_id: str
    text: str
    metadata: Dict
    score: float
    rank: int


class VectorStore:
    """In-memory vector store using FAISS"""

    def __init__(self, dimension: int = 768):
        """
        Initialize vector store.

        Args:
            dimension: Embedding dimension (default 768 for text-embedding-004)
        """
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product (for cosine similarity)
        self.chunks: List[EmbeddedChunk] = []
        self.chunk_map: Dict[str, EmbeddedChunk] = {}

    def add_chunks(self, embedded_chunks: List[EmbeddedChunk]) -> None:
        """
        Add embedded chunks to the vector store.

        Args:
            embedded_chunks: List of embedded chunks to add
        """
        if not embedded_chunks:
            return

        # Normalize embeddings for cosine similarity
        embeddings_matrix = np.array([
            self._normalize_vector(chunk.embedding)
            for chunk in embedded_chunks
        ]).astype('float32')

        # Add to FAISS index
        self.index.add(embeddings_matrix)

        # Store chunks
        self.chunks.extend(embedded_chunks)

        # Update chunk map
        for chunk in embedded_chunks:
            self.chunk_map[chunk.chunk_id] = chunk

        print(f"[OK] Added {len(embedded_chunks)} chunks to vector store")
        print(f"  Total chunks in store: {len(self.chunks)}")

    def _normalize_vector(self, vector: List[float]) -> np.ndarray:
        """
        Normalize vector for cosine similarity.

        Args:
            vector: Input vector

        Returns:
            Normalized numpy array
        """
        vec_np = np.array(vector, dtype='float32')
        norm = np.linalg.norm(vec_np)
        if norm == 0:
            return vec_np
        return vec_np / norm

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        Search for similar chunks.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filter (e.g., {"document_type": "FSA_Handbook"})

        Returns:
            List of SearchResult objects
        """
        if len(self.chunks) == 0:
            return []

        # Normalize query
        query_normalized = self._normalize_vector(query_embedding).reshape(1, -1)

        # Search in FAISS
        scores, indices = self.index.search(query_normalized, min(top_k * 2, len(self.chunks)))

        # Convert to SearchResult
        results = []
        for rank, (idx, score) in enumerate(zip(indices[0], scores[0])):
            if idx == -1:  # FAISS returns -1 for empty results
                continue

            chunk = self.chunks[idx]

            # Apply metadata filter if provided
            if filter_metadata:
                if not self._matches_filter(chunk.metadata, filter_metadata):
                    continue

            results.append(SearchResult(
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                metadata=chunk.metadata,
                score=float(score),
                rank=rank + 1
            ))

            if len(results) >= top_k:
                break

        return results

    def _matches_filter(self, metadata: Dict, filter_dict: Dict) -> bool:
        """
        Check if metadata matches filter.

        Args:
            metadata: Chunk metadata
            filter_dict: Filter dictionary

        Returns:
            True if matches
        """
        for key, value in filter_dict.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True

    def get_chunk_by_id(self, chunk_id: str) -> Optional[EmbeddedChunk]:
        """
        Get chunk by ID.

        Args:
            chunk_id: Chunk identifier

        Returns:
            EmbeddedChunk or None
        """
        return self.chunk_map.get(chunk_id)

    def get_statistics(self) -> Dict:
        """
        Get vector store statistics.

        Returns:
            Dictionary with statistics
        """
        doc_types = {}
        for chunk in self.chunks:
            doc_type = chunk.metadata.get('document_type', 'unknown')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

        return {
            "total_chunks": len(self.chunks),
            "dimension": self.dimension,
            "document_types": doc_types,
            "index_size": self.index.ntotal
        }

    def save(self, save_path: Path) -> None:
        """
        Save vector store to disk.

        Args:
            save_path: Directory to save store
        """
        save_path.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        index_path = save_path / "faiss.index"
        faiss.write_index(self.index, str(index_path))

        # Save chunks
        chunks_path = save_path / "chunks.pkl"
        with open(chunks_path, 'wb') as f:
            pickle.dump(self.chunks, f)

        print(f"[OK] Saved vector store to {save_path}")

    @classmethod
    def load(cls, load_path: Path) -> 'VectorStore':
        """
        Load vector store from disk.

        Args:
            load_path: Directory to load from

        Returns:
            VectorStore instance
        """
        # Load FAISS index
        index_path = load_path / "faiss.index"
        index = faiss.read_index(str(index_path))

        # Load chunks
        chunks_path = load_path / "chunks.pkl"
        with open(chunks_path, 'rb') as f:
            chunks = pickle.load(f)

        # Create store
        dimension = index.d
        store = cls(dimension=dimension)
        store.index = index
        store.chunks = chunks

        # Rebuild chunk map
        store.chunk_map = {chunk.chunk_id: chunk for chunk in chunks}

        print(f"[OK] Loaded vector store from {load_path}")
        print(f"  Total chunks: {len(chunks)}")

        return store


# ============================================================================
# HYBRID VECTOR STORE (Semantic + Keyword)
# ============================================================================

class HybridVectorStore(VectorStore):
    """
    Vector store with hybrid search (semantic + keyword matching).
    """

    def __init__(self, dimension: int = 768):
        super().__init__(dimension)
        self.keyword_index: Dict[str, List[str]] = {}  # keyword -> [chunk_ids]

    def add_chunks(self, embedded_chunks: List[EmbeddedChunk]) -> None:
        """Add chunks and build keyword index"""
        super().add_chunks(embedded_chunks)

        # Build keyword index for rule IDs
        for chunk in embedded_chunks:
            # Extract rule IDs from metadata
            rule_ids = chunk.metadata.get('rule_ids', [])
            for rule_id in rule_ids:
                # Normalize rule ID (e.g., "D 4.3.3" or tuple format)
                if isinstance(rule_id, tuple):
                    rule_str = f"{rule_id[0]} {'.'.join(str(x) for x in rule_id[1:] if x)}"
                else:
                    rule_str = str(rule_id)

                if rule_str not in self.keyword_index:
                    self.keyword_index[rule_str] = []

                self.keyword_index[rule_str].append(chunk.chunk_id)

    def search_hybrid(
        self,
        query_embedding: List[float],
        query_text: str,
        top_k: int = 5,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3
    ) -> List[SearchResult]:
        """
        Hybrid search combining semantic and keyword matching.

        Args:
            query_embedding: Query embedding
            query_text: Query text (for keyword extraction)
            top_k: Number of results
            semantic_weight: Weight for semantic search (0-1)
            keyword_weight: Weight for keyword search (0-1)

        Returns:
            List of SearchResult objects
        """
        # Semantic search
        semantic_results = self.search(query_embedding, top_k=top_k * 2)

        # Keyword search (look for rule IDs in query)
        import re
        rule_pattern = re.compile(r'([DATB])\s*(\d+(?:\.\d+)*)')
        rule_matches = rule_pattern.findall(query_text)

        keyword_chunk_ids = set()
        for match in rule_matches:
            rule_id = f"{match[0]} {match[1]}"
            chunk_ids = self.keyword_index.get(rule_id, [])
            keyword_chunk_ids.update(chunk_ids)

        # Combine results
        combined_scores: Dict[str, float] = {}

        # Add semantic scores
        for result in semantic_results:
            combined_scores[result.chunk_id] = semantic_weight * result.score

        # Boost keyword matches
        for chunk_id in keyword_chunk_ids:
            if chunk_id in combined_scores:
                combined_scores[chunk_id] += keyword_weight
            else:
                combined_scores[chunk_id] = keyword_weight

        # Sort by combined score
        sorted_chunks = sorted(
            combined_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]

        # Create results
        results = []
        for rank, (chunk_id, score) in enumerate(sorted_chunks):
            chunk = self.chunk_map[chunk_id]
            results.append(SearchResult(
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                metadata=chunk.metadata,
                score=score,
                rank=rank + 1
            ))

        return results


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_vector_store_from_embeddings(
    embeddings_paths: List[Path],
    use_hybrid: bool = True
) -> VectorStore:
    """
    Create vector store from embedding files.

    Args:
        embeddings_paths: List of paths to embedding JSON files
        use_hybrid: Whether to use hybrid search

    Returns:
        VectorStore instance
    """
    from src.processing.embedder import Embedder

    embedder = Embedder()

    # Determine dimension
    dimension = embedder.get_embedding_dimension()

    # Create store
    if use_hybrid:
        store = HybridVectorStore(dimension=dimension)
    else:
        store = VectorStore(dimension=dimension)

    # Load and add all embeddings
    for path in embeddings_paths:
        if path.exists():
            embedded_chunks = embedder.load_embeddings(path)
            store.add_chunks(embedded_chunks)
        else:
            print(f"[WARN]  Embeddings not found: {path}")

    return store
