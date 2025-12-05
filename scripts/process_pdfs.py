"""
Script to process PDF documents and create chunks.

This script:
1. Loads the FSA Handbook and FS Rules PDFs
2. Extracts text from all pages
3. Creates semantic chunks
4. Saves chunks to JSON files
5. Prints statistics
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from src.processing.pdf_processor import process_all_documents, PDFProcessor
from src.processing.chunker import DocumentChunker, chunk_documents
import json


def main():
    """Main processing function"""

    print("=" * 70)
    print("Formula Student PDF Processing Pipeline")
    print("=" * 70)

    # Check if PDFs exist
    if not settings.fsa_handbook_full_path.exists():
        print(f"❌ FSA Handbook not found at: {settings.fsa_handbook_full_path}")
        return

    if not settings.fs_rules_full_path.exists():
        print(f"❌ FS Rules not found at: {settings.fs_rules_full_path}")
        return

    print(f"\n✓ Found FSA Handbook: {settings.fsa_handbook_full_path.name}")
    print(f"✓ Found FS Rules: {settings.fs_rules_full_path.name}")

    # Process PDFs
    print("\n" + "=" * 70)
    print("Step 1: Extracting Text from PDFs")
    print("=" * 70)

    handbook_doc, rules_doc = process_all_documents(
        settings.fsa_handbook_full_path,
        settings.fs_rules_full_path
    )

    # Print document statistics
    processor = PDFProcessor()

    print("\n📊 FSA Handbook Statistics:")
    handbook_stats = processor.get_document_statistics(handbook_doc)
    for key, value in handbook_stats.items():
        if key != "rule_ids_sample":
            print(f"  - {key}: {value}")

    print("\n📊 FS Rules Statistics:")
    rules_stats = processor.get_document_statistics(rules_doc)
    for key, value in rules_stats.items():
        if key != "rule_ids_sample":
            print(f"  - {key}: {value}")

    # Chunk documents
    print("\n" + "=" * 70)
    print("Step 2: Creating Semantic Chunks")
    print("=" * 70)

    handbook_chunks, rules_chunks = chunk_documents(
        handbook_doc,
        rules_doc,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap
    )

    # Save chunks to JSON
    print("\n" + "=" * 70)
    print("Step 3: Saving Chunks to JSON")
    print("=" * 70)

    output_dir = settings.base_dir / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save FSA Handbook chunks
    handbook_output = output_dir / "fsa_handbook_chunks.json"
    handbook_data = [
        {
            "chunk_id": chunk.chunk_id,
            "text": chunk.text,
            "metadata": chunk.metadata,
            "char_count": chunk.char_count,
            "word_count": chunk.word_count
        }
        for chunk in handbook_chunks
    ]

    with open(handbook_output, 'w', encoding='utf-8') as f:
        json.dump(handbook_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved FSA Handbook chunks to: {handbook_output}")

    # Save FS Rules chunks
    rules_output = output_dir / "fs_rules_chunks.json"
    rules_data = [
        {
            "chunk_id": chunk.chunk_id,
            "text": chunk.text,
            "metadata": chunk.metadata,
            "char_count": chunk.char_count,
            "word_count": chunk.word_count
        }
        for chunk in rules_chunks
    ]

    with open(rules_output, 'w', encoding='utf-8') as f:
        json.dump(rules_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved FS Rules chunks to: {rules_output}")

    # Final statistics
    print("\n" + "=" * 70)
    print("Processing Complete!")
    print("=" * 70)

    chunker = DocumentChunker()
    handbook_chunk_stats = chunker.get_chunk_statistics(handbook_chunks)
    rules_chunk_stats = chunker.get_chunk_statistics(rules_chunks)

    print("\n📊 Final Statistics:")
    print(f"\nFSA Handbook:")
    print(f"  - Total chunks: {handbook_chunk_stats['total_chunks']}")
    print(f"  - Avg chunk size: {handbook_chunk_stats['avg_chunk_size']} chars")
    print(f"  - Total words: {handbook_chunk_stats['total_words']:,}")

    print(f"\nFS Rules:")
    print(f"  - Total chunks: {rules_chunk_stats['total_chunks']}")
    print(f"  - Avg chunk size: {rules_chunk_stats['avg_chunk_size']} chars")
    print(f"  - Total words: {rules_chunk_stats['total_words']:,}")

    print(f"\nTotal chunks: {handbook_chunk_stats['total_chunks'] + rules_chunk_stats['total_chunks']}")

    print("\n✅ All documents processed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
