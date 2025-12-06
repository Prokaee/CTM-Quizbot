"""
Retrieval Module

Orchestrates document retrieval using vector search and optional reranking.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass

from src.processing.embedder import Embedder
from .vector_store import VectorStore, HybridVectorStore, SearchResult
from config.settings import settings


@dataclass
class RetrievalResult:
    """Result from retrieval pipeline"""
    chunks: List[SearchResult]
    query: str
    query_embedding: List[float]
    retrieval_method: str
    total_found: int


class Retriever:
    """Main retrieval orchestrator"""

    def __init__(
        self,
        vector_store: VectorStore,
        embedder: Optional[Embedder] = None,
        top_k: int = None
    ):
        """
        Initialize retriever.

        Args:
            vector_store: Vector store instance
            embedder: Embedder instance (creates new if None)
            top_k: Number of results to retrieve (from settings if None)
        """
        self.vector_store = vector_store
        self.embedder = embedder or Embedder()
        self.top_k = top_k or settings.top_k_retrieval

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_document_type: Optional[str] = None,
        use_hybrid: bool = True
    ) -> RetrievalResult:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: Query text
            top_k: Number of results (uses instance default if None)
            filter_document_type: Filter by document type ("FSA_Handbook" or "FS_Rules")
            use_hybrid: Use hybrid search if available

        Returns:
            RetrievalResult object
        """
        top_k = top_k or self.top_k

        # Generate query embedding
        query_embedding = self.embedder.embed_query(query)

        # Perform search
        if use_hybrid and isinstance(self.vector_store, HybridVectorStore):
            # Hybrid search
            results = self.vector_store.search_hybrid(
                query_embedding=query_embedding,
                query_text=query,
                top_k=top_k
            )
            method = "hybrid"
        else:
            # Pure semantic search
            filter_metadata = (
                {"document_type": filter_document_type}
                if filter_document_type
                else None
            )

            results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                filter_metadata=filter_metadata
            )
            method = "semantic"

        return RetrievalResult(
            chunks=results,
            query=query,
            query_embedding=query_embedding,
            retrieval_method=method,
            total_found=len(results)
        )

    def retrieve_with_priority_boost(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> RetrievalResult:
        """
        Retrieve with FSA Handbook priority boost.

        According to project rules: FSA Handbook > FS Rules
        This method boosts FSA Handbook chunks in the ranking.

        Args:
            query: Query text
            top_k: Number of results

        Returns:
            RetrievalResult with boosted FSA chunks
        """
        top_k = top_k or self.top_k

        # Get more results than needed
        initial_result = self.retrieve(
            query=query,
            top_k=top_k * 2,
            use_hybrid=True
        )

        # Apply priority boost
        boosted_results = []
        for result in initial_result.chunks:
            doc_type = result.metadata.get('document_type', '')

            # Boost FSA Handbook scores by 1.5x
            if doc_type == 'FSA_Handbook':
                result.score = result.score * 1.5

            boosted_results.append(result)

        # Re-sort by boosted scores
        boosted_results.sort(key=lambda x: x.score, reverse=True)

        # Take top_k
        final_results = boosted_results[:top_k]

        # Reassign ranks
        for rank, result in enumerate(final_results, 1):
            result.rank = rank

        return RetrievalResult(
            chunks=final_results,
            query=query,
            query_embedding=initial_result.query_embedding,
            retrieval_method="hybrid_with_fsa_boost",
            total_found=len(final_results)
        )

    def retrieve_by_rule_id(self, rule_id: str) -> List[SearchResult]:
        """
        Retrieve chunks that reference a specific rule ID.

        Args:
            rule_id: Rule ID (e.g., "D 4.3.3")

        Returns:
            List of matching chunks
        """
        # Use rule ID as query
        query = f"Rule {rule_id}"

        result = self.retrieve(
            query=query,
            top_k=10,  # Get more results for rule lookups
            use_hybrid=True  # Hybrid will catch exact rule ID matches
        )

        # Filter to only chunks that actually contain the rule ID
        filtered = []
        for chunk in result.chunks:
            rule_ids = chunk.metadata.get('rule_ids', [])

            # Check if rule_id matches any stored rule IDs
            for stored_rule in rule_ids:
                if isinstance(stored_rule, tuple):
                    stored_str = f"{stored_rule[0]} {'.'.join(str(x) for x in stored_rule[1:] if x)}"
                else:
                    stored_str = str(stored_rule)

                if rule_id.replace(' ', '') in stored_str.replace(' ', ''):
                    filtered.append(chunk)
                    break

        return filtered

    def format_context_for_llm(self, retrieval_result: RetrievalResult) -> str:
        """
        Format retrieved chunks as context for LLM.

        Args:
            retrieval_result: Retrieval result

        Returns:
            Formatted context string
        """
        if not retrieval_result.chunks:
            return "No relevant context found."

        context_parts = ["**Retrieved Rule Sections:**\n"]

        for result in retrieval_result.chunks:
            doc_type = result.metadata.get('document_type', 'Unknown')
            page_range = result.metadata.get('page_range', 'Unknown')

            context_parts.append(f"\n--- {doc_type} (Pages {page_range}) [Relevance: {result.score:.3f}] ---")
            context_parts.append(result.text)
            context_parts.append("")

        return "\n".join(context_parts)

    def get_statistics(self) -> Dict:
        """
        Get retriever statistics.

        Returns:
            Statistics dictionary
        """
        vector_stats = self.vector_store.get_statistics()

        return {
            "vector_store": vector_stats,
            "top_k_default": self.top_k,
            "embedding_model": self.embedder.model_name,
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_retriever_from_config() -> Retriever:
    """
    Create retriever from configuration.

    Returns:
        Configured Retriever instance
    """
    from pathlib import Path
    from .vector_store import create_vector_store_from_embeddings

    # Get embedding paths
    embeddings_dir = settings.base_dir / "data" / "embeddings"
    embedding_paths = [
        embeddings_dir / "fsa_handbook_embeddings.json",
        embeddings_dir / "fs_rules_embeddings.json"
    ]

    # Create vector store
    print("Creating vector store from embeddings...")
    vector_store = create_vector_store_from_embeddings(
        embeddings_paths=embedding_paths,
        use_hybrid=True
    )

    # Create retriever
    retriever = Retriever(
        vector_store=vector_store,
        top_k=settings.top_k_retrieval
    )

    print("\n[OK] Retriever ready!")
    stats = retriever.get_statistics()
    print(f"  Total chunks indexed: {stats['vector_store']['total_chunks']}")
    print(f"  Default top-k: {stats['top_k_default']}")

    return retriever
