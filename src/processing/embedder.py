"""
Embedding Generation Module

Generates embeddings for text chunks using Google's text-embedding-004 model.
"""

import google.generativeai as genai
from typing import List, Dict, Optional
import numpy as np
from dataclasses import dataclass
import json
from pathlib import Path
from tqdm import tqdm

from config.settings import settings
from .chunker import Chunk


@dataclass
class EmbeddedChunk:
    """Chunk with its embedding vector"""
    chunk_id: str
    text: str
    embedding: List[float]
    metadata: Dict
    embedding_model: str


class Embedder:
    """Generates embeddings for text chunks"""

    def __init__(self, model_name: str = None):
        """
        Initialize embedder.

        Args:
            model_name: Embedding model to use (default from settings)
        """
        self.model_name = model_name or settings.embedding_model

        # Initialize Gemini API if not already done
        if settings.gemini_api_key:
            try:
                genai.configure(api_key=settings.gemini_api_key)
            except:
                pass  # Already configured

    def embed_text(self, text: str, task_type: str = "retrieval_document") -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            task_type: Task type for embedding
                - "retrieval_document": For documents to be retrieved
                - "retrieval_query": For search queries

        Returns:
            Embedding vector as list of floats
        """
        result = genai.embed_content(
            model=f"models/{self.model_name}",
            content=text,
            task_type=task_type
        )

        return result['embedding']

    def embed_texts(
        self,
        texts: List[str],
        task_type: str = "retrieval_document",
        show_progress: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            task_type: Task type for embeddings
            show_progress: Whether to show progress bar

        Returns:
            List of embedding vectors
        """
        embeddings = []

        iterator = tqdm(texts, desc="Generating embeddings") if show_progress else texts

        for text in iterator:
            embedding = self.embed_text(text, task_type=task_type)
            embeddings.append(embedding)

        return embeddings

    def embed_chunks(
        self,
        chunks: List[Chunk],
        show_progress: bool = True
    ) -> List[EmbeddedChunk]:
        """
        Generate embeddings for chunks.

        Args:
            chunks: List of Chunk objects
            show_progress: Whether to show progress bar

        Returns:
            List of EmbeddedChunk objects
        """
        embedded_chunks = []

        iterator = tqdm(chunks, desc="Embedding chunks") if show_progress else chunks

        for chunk in iterator:
            embedding = self.embed_text(chunk.text, task_type="retrieval_document")

            embedded_chunk = EmbeddedChunk(
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                embedding=embedding,
                metadata=chunk.metadata,
                embedding_model=self.model_name
            )

            embedded_chunks.append(embedded_chunk)

        return embedded_chunks

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.

        Args:
            query: Query text

        Returns:
            Embedding vector
        """
        return self.embed_text(query, task_type="retrieval_query")

    def save_embeddings(
        self,
        embedded_chunks: List[EmbeddedChunk],
        output_path: Path
    ) -> None:
        """
        Save embeddings to file.

        Args:
            embedded_chunks: List of embedded chunks
            output_path: Path to save embeddings
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = [
            {
                "chunk_id": ec.chunk_id,
                "text": ec.text,
                "embedding": ec.embedding,
                "metadata": ec.metadata,
                "embedding_model": ec.embedding_model
            }
            for ec in embedded_chunks
        ]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"[OK] Saved {len(embedded_chunks)} embeddings to {output_path}")

    def load_embeddings(self, input_path: Path) -> List[EmbeddedChunk]:
        """
        Load embeddings from file.

        Args:
            input_path: Path to embeddings file

        Returns:
            List of EmbeddedChunk objects
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        embedded_chunks = [
            EmbeddedChunk(
                chunk_id=item["chunk_id"],
                text=item["text"],
                embedding=item["embedding"],
                metadata=item["metadata"],
                embedding_model=item["embedding_model"]
            )
            for item in data
        ]

        print(f"[OK] Loaded {len(embedded_chunks)} embeddings from {input_path}")

        return embedded_chunks

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings from this model.

        Returns:
            Embedding dimension (typically 768 for text-embedding-004)
        """
        # Generate a test embedding to get dimension
        test_embedding = self.embed_text("test")
        return len(test_embedding)


# ============================================================================
# SIMILARITY FUNCTIONS
# ============================================================================

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score (0 to 1)
    """
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)

    dot_product = np.dot(vec1_np, vec2_np)
    norm1 = np.linalg.norm(vec1_np)
    norm2 = np.linalg.norm(vec2_np)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot_product / (norm1 * norm2))


def find_most_similar(
    query_embedding: List[float],
    chunk_embeddings: List[EmbeddedChunk],
    top_k: int = 5
) -> List[tuple[EmbeddedChunk, float]]:
    """
    Find most similar chunks to a query.

    Args:
        query_embedding: Query embedding vector
        chunk_embeddings: List of embedded chunks
        top_k: Number of top results to return

    Returns:
        List of (chunk, similarity_score) tuples, sorted by similarity
    """
    similarities = []

    for chunk in chunk_embeddings:
        similarity = cosine_similarity(query_embedding, chunk.embedding)
        similarities.append((chunk, similarity))

    # Sort by similarity (descending)
    similarities.sort(key=lambda x: x[1], reverse=True)

    return similarities[:top_k]


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def embed_all_chunks_from_json(
    chunks_json_path: Path,
    output_path: Path,
    show_progress: bool = True
) -> List[EmbeddedChunk]:
    """
    Load chunks from JSON and generate embeddings.

    Args:
        chunks_json_path: Path to chunks JSON file
        output_path: Path to save embeddings
        show_progress: Show progress bar

    Returns:
        List of embedded chunks
    """
    # Load chunks from JSON
    with open(chunks_json_path, 'r', encoding='utf-8') as f:
        chunks_data = json.load(f)

    # Convert to Chunk objects
    from .chunker import Chunk
    chunks = [
        Chunk(
            chunk_id=item["chunk_id"],
            text=item["text"],
            metadata=item["metadata"],
            char_count=item["char_count"],
            word_count=item["word_count"]
        )
        for item in chunks_data
    ]

    print(f"Loaded {len(chunks)} chunks from {chunks_json_path}")

    # Generate embeddings
    embedder = Embedder()
    embedded_chunks = embedder.embed_chunks(chunks, show_progress=show_progress)

    # Save embeddings
    embedder.save_embeddings(embedded_chunks, output_path)

    return embedded_chunks


def create_embeddings_for_all_documents():
    """
    Create embeddings for all processed documents.
    """
    data_dir = settings.base_dir / "data"
    processed_dir = data_dir / "processed"
    embeddings_dir = data_dir / "embeddings"

    # Embed FSA Handbook
    handbook_chunks = processed_dir / "fsa_handbook_chunks.json"
    handbook_embeddings = embeddings_dir / "fsa_handbook_embeddings.json"

    if handbook_chunks.exists():
        print("\n" + "=" * 70)
        print("Embedding FSA Handbook")
        print("=" * 70)
        embed_all_chunks_from_json(handbook_chunks, handbook_embeddings)
    else:
        print(f"[WARN]  FSA Handbook chunks not found at {handbook_chunks}")

    # Embed FS Rules
    rules_chunks = processed_dir / "fs_rules_chunks.json"
    rules_embeddings = embeddings_dir / "fs_rules_embeddings.json"

    if rules_chunks.exists():
        print("\n" + "=" * 70)
        print("Embedding FS Rules")
        print("=" * 70)
        embed_all_chunks_from_json(rules_chunks, rules_embeddings)
    else:
        print(f"[WARN]  FS Rules chunks not found at {rules_chunks}")

    print("\n[OK] All embeddings generated successfully!")
