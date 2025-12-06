"""
Build Complete RAG Pipeline (Simple version without emojis for Windows)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings, validate_settings
from src.processing.pdf_processor import process_all_documents, PDFProcessor
from src.processing.chunker import DocumentChunker, chunk_documents
from src.processing.embedder import Embedder, embed_all_chunks_from_json
from src.rag.vector_store import create_vector_store_from_embeddings
from src.rag.retriever import Retriever
import json


def main():
    print("=" * 80)
    print("FORMULA STUDENT RAG PIPELINE BUILDER")
    print("=" * 80)

    # Validate settings
    print("\n[1/5] Validating Configuration...")
    errors = validate_settings()
    if errors:
        print("\n[ERROR] Configuration errors found:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("[OK] Configuration valid")

    # Step 1: Process PDFs
    print("\n" + "=" * 80)
    print("[2/5] Processing PDF Documents")
    print("=" * 80)

    processed_dir = settings.base_dir / "data" / "processed"
    handbook_chunks_path = processed_dir / "fsa_handbook_chunks.json"
    rules_chunks_path = processed_dir / "fs_rules_chunks.json"

    if handbook_chunks_path.exists() and rules_chunks_path.exists():
        print("[OK] Chunks already exist. Skipping PDF processing.")
    else:
        print("Processing PDFs...")
        handbook_doc, rules_doc = process_all_documents(
            settings.fsa_handbook_full_path,
            settings.fs_rules_full_path
        )

        print("Creating semantic chunks...")
        handbook_chunks, rules_chunks = chunk_documents(
            handbook_doc,
            rules_doc,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )

        processed_dir.mkdir(parents=True, exist_ok=True)

        with open(handbook_chunks_path, 'w', encoding='utf-8') as f:
            json.dump([{
                "chunk_id": c.chunk_id,
                "text": c.text,
                "metadata": c.metadata,
                "char_count": c.char_count,
                "word_count": c.word_count
            } for c in handbook_chunks], f, indent=2, ensure_ascii=False)

        with open(rules_chunks_path, 'w', encoding='utf-8') as f:
            json.dump([{
                "chunk_id": c.chunk_id,
                "text": c.text,
                "metadata": c.metadata,
                "char_count": c.char_count,
                "word_count": c.word_count
            } for c in rules_chunks], f, indent=2, ensure_ascii=False)

        print(f"[OK] Saved chunks to {processed_dir}")

    # Step 2: Generate Embeddings
    print("\n" + "=" * 80)
    print("[3/5] Generating Embeddings")
    print("=" * 80)

    embeddings_dir = settings.base_dir / "data" / "embeddings"
    handbook_embeddings_path = embeddings_dir / "fsa_handbook_embeddings.json"
    rules_embeddings_path = embeddings_dir / "fs_rules_embeddings.json"

    if handbook_embeddings_path.exists() and rules_embeddings_path.exists():
        print("[OK] Embeddings already exist. Skipping.")
    else:
        print("Generating embeddings (this may take a few minutes)...\n")

        print("Embedding FSA Handbook...")
        embed_all_chunks_from_json(
            handbook_chunks_path,
            handbook_embeddings_path,
            show_progress=True
        )

        print("\nEmbedding FS Rules...")
        embed_all_chunks_from_json(
            rules_chunks_path,
            rules_embeddings_path,
            show_progress=True
        )

        print(f"\n[OK] Saved embeddings to {embeddings_dir}")

    # Step 3: Create Vector Store
    print("\n" + "=" * 80)
    print("[4/5] Building Vector Store")
    print("=" * 80)

    print("Creating hybrid vector store...")
    vector_store = create_vector_store_from_embeddings(
        embeddings_paths=[handbook_embeddings_path, rules_embeddings_path],
        use_hybrid=True
    )

    stats = vector_store.get_statistics()
    print(f"\n[OK] Vector store created:")
    print(f"  - Total chunks: {stats['total_chunks']}")
    print(f"  - Dimension: {stats['dimension']}")
    print(f"  - Document types: {stats['document_types']}")

    # Step 4: Test Retrieval
    print("\n" + "=" * 80)
    print("[5/5] Testing Retrieval")
    print("=" * 80)

    retriever = Retriever(vector_store=vector_store)

    test_queries = [
        "How many fire extinguishers are required?",
        "What is the skidpad scoring formula?",
        "Acceleration event rules",
    ]

    print("\nTesting retrieval with sample queries...\n")

    for query in test_queries:
        print(f"\nQuery: \"{query}\"")
        print("-" * 60)

        result = retriever.retrieve_with_priority_boost(query, top_k=3)
        print(f"Retrieved {result.total_found} chunks")

        for i, chunk in enumerate(result.chunks[:2], 1):
            doc_type = chunk.metadata.get('document_type', 'Unknown')
            pages = chunk.metadata.get('page_range', 'Unknown')
            print(f"  {i}. [{doc_type}] Pages {pages} (Score: {chunk.score:.3f})")
            print(f"     {chunk.text[:100]}...")

    # Final Summary
    print("\n" + "=" * 80)
    print("RAG PIPELINE BUILD COMPLETE!")
    print("=" * 80)

    print("\n[OK] Summary:")
    print(f"  - PDFs processed: 2")
    print(f"  - Total chunks: {stats['total_chunks']}")
    print(f"  - Vector store ready: Yes")
    print(f"  - Retriever tested: Yes")

    print("\n[NEXT STEPS]")
    print("  1. Run: python main.py")
    print("  2. Start asking questions!")

    print("\n[OK] RAG pipeline is ready to use!")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    exit(main())
