"""
Build Complete RAG Pipeline

This script:
1. Processes PDFs → chunks
2. Generates embeddings
3. Creates vector store
4. Tests retrieval

Run this after setting up your .env file with GEMINI_API_KEY.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings, validate_settings, print_settings_summary
from src.processing.pdf_processor import process_all_documents, PDFProcessor
from src.processing.chunker import DocumentChunker, chunk_documents
from src.processing.embedder import Embedder, embed_all_chunks_from_json
from src.rag.vector_store import create_vector_store_from_embeddings
from src.rag.retriever import Retriever
import json


def main():
    """Main RAG build function"""

    print("=" * 80)
    print(" FORMULA STUDENT RAG PIPELINE BUILDER")
    print("=" * 80)

    # Validate settings
    print("\n📋 Validating Configuration...")
    print_settings_summary()

    errors = validate_settings()
    if errors:
        print("\n❌ Configuration errors found. Please fix and retry.")
        return 1

    # Step 1: Process PDFs
    print("\n" + "=" * 80)
    print("STEP 1: Processing PDF Documents")
    print("=" * 80)

    processed_dir = settings.base_dir / "data" / "processed"

    handbook_chunks_path = processed_dir / "fsa_handbook_chunks.json"
    rules_chunks_path = processed_dir / "fs_rules_chunks.json"

    if handbook_chunks_path.exists() and rules_chunks_path.exists():
        print("✓ Chunks already exist. Skipping PDF processing.")
        print(f"  - {handbook_chunks_path}")
        print(f"  - {rules_chunks_path}")
        print("\nDelete these files if you want to reprocess PDFs.")
    else:
        print("Processing PDFs...")
        handbook_doc, rules_doc = process_all_documents(
            settings.fsa_handbook_full_path,
            settings.fs_rules_full_path
        )

        # Print stats
        processor = PDFProcessor()
        handbook_stats = processor.get_document_statistics(handbook_doc)
        rules_stats = processor.get_document_statistics(rules_doc)

        print(f"\n  FSA Handbook: {handbook_stats['total_pages']} pages, {handbook_stats['total_words']:,} words")
        print(f"  FS Rules: {rules_stats['total_pages']} pages, {rules_stats['total_words']:,} words")

        # Chunk documents
        print("\nCreating semantic chunks...")
        handbook_chunks, rules_chunks = chunk_documents(
            handbook_doc,
            rules_doc,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )

        # Save chunks
        processed_dir.mkdir(parents=True, exist_ok=True)

        with open(handbook_chunks_path, 'w', encoding='utf-8') as f:
            json.dump([
                {
                    "chunk_id": c.chunk_id,
                    "text": c.text,
                    "metadata": c.metadata,
                    "char_count": c.char_count,
                    "word_count": c.word_count
                }
                for c in handbook_chunks
            ], f, indent=2, ensure_ascii=False)

        with open(rules_chunks_path, 'w', encoding='utf-8') as f:
            json.dump([
                {
                    "chunk_id": c.chunk_id,
                    "text": c.text,
                    "metadata": c.metadata,
                    "char_count": c.char_count,
                    "word_count": c.word_count
                }
                for c in rules_chunks
            ], f, indent=2, ensure_ascii=False)

        print(f"\n✓ Saved chunks to {processed_dir}")

    # Step 2: Generate Embeddings
    print("\n" + "=" * 80)
    print("STEP 2: Generating Embeddings")
    print("=" * 80)

    embeddings_dir = settings.base_dir / "data" / "embeddings"
    handbook_embeddings_path = embeddings_dir / "fsa_handbook_embeddings.json"
    rules_embeddings_path = embeddings_dir / "fs_rules_embeddings.json"

    if handbook_embeddings_path.exists() and rules_embeddings_path.exists():
        print("✓ Embeddings already exist. Skipping embedding generation.")
        print(f"  - {handbook_embeddings_path}")
        print(f"  - {rules_embeddings_path}")
        print("\nDelete these files if you want to regenerate embeddings.")
    else:
        if not settings.gemini_api_key:
            print("❌ GEMINI_API_KEY not set. Cannot generate embeddings.")
            print("   Please set it in your .env file.")
            return 1

        print("Generating embeddings (this may take a few minutes)...\n")

        # Embed FSA Handbook
        print("Embedding FSA Handbook...")
        embed_all_chunks_from_json(
            handbook_chunks_path,
            handbook_embeddings_path,
            show_progress=True
        )

        # Embed FS Rules
        print("\nEmbedding FS Rules...")
        embed_all_chunks_from_json(
            rules_chunks_path,
            rules_embeddings_path,
            show_progress=True
        )

        print(f"\n✓ Saved embeddings to {embeddings_dir}")

    # Step 3: Create Vector Store
    print("\n" + "=" * 80)
    print("STEP 3: Building Vector Store")
    print("=" * 80)

    print("Creating hybrid vector store...")
    vector_store = create_vector_store_from_embeddings(
        embeddings_paths=[handbook_embeddings_path, rules_embeddings_path],
        use_hybrid=True
    )

    stats = vector_store.get_statistics()
    print(f"\n✓ Vector store created:")
    print(f"  - Total chunks: {stats['total_chunks']}")
    print(f"  - Dimension: {stats['dimension']}")
    print(f"  - Document types: {stats['document_types']}")

    # Step 4: Create Retriever and Test
    print("\n" + "=" * 80)
    print("STEP 4: Testing Retrieval")
    print("=" * 80)

    retriever = Retriever(vector_store=vector_store)

    # Test queries
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

        print(f"Retrieved {result.total_found} chunks using {result.retrieval_method}")

        for i, chunk in enumerate(result.chunks[:3], 1):
            doc_type = chunk.metadata.get('document_type', 'Unknown')
            pages = chunk.metadata.get('page_range', 'Unknown')
            print(f"\n  {i}. [{doc_type}] Pages {pages} (Score: {chunk.score:.3f})")
            print(f"     Preview: {chunk.text[:150]}...")

    # Step 5: Save Vector Store (Optional)
    print("\n" + "=" * 80)
    print("STEP 5: Saving Vector Store (Optional)")
    print("=" * 80)

    vector_store_path = settings.base_dir / "data" / "vector_store"

    save_choice = input("\nWould you like to save the vector store to disk? (y/n): ").lower()

    if save_choice == 'y':
        vector_store.save(vector_store_path)
        print(f"\n✓ Vector store saved to {vector_store_path}")
        print("   You can load it later with: VectorStore.load(path)")
    else:
        print("\n  Skipped saving vector store.")

    # Final Summary
    print("\n" + "=" * 80)
    print(" RAG PIPELINE BUILD COMPLETE!")
    print("=" * 80)

    print("\n📊 Final Summary:")
    print(f"  ✓ PDFs processed: 2")
    print(f"  ✓ Total chunks: {stats['total_chunks']}")
    print(f"  ✓ Embeddings generated: {stats['total_chunks']}")
    print(f"  ✓ Vector store ready: Yes")
    print(f"  ✓ Retriever tested: Yes")

    print("\n🎯 Next Steps:")
    print("  1. Test retrieval with your own queries")
    print("  2. Build the reasoning agents (router + gemini 3.0)")
    print("  3. Create the FastAPI backend")
    print("  4. Build the chat interface")

    print("\n✅ RAG pipeline is ready to use!")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    exit(main())
