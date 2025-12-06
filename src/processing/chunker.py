"""
Document Chunking Module

Smart chunking strategy for Formula Student documents.
Uses larger chunks to leverage Gemini 3.0's excellent context handling.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re
from .pdf_processor import PDFDocument, PDFPage


@dataclass
class Chunk:
    """Represents a text chunk with metadata"""
    chunk_id: str
    text: str
    metadata: Dict
    char_count: int
    word_count: int


class DocumentChunker:
    """Chunks documents intelligently based on semantic boundaries"""

    def __init__(
        self,
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100
    ):
        """
        Initialize chunker.

        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks in characters
            min_chunk_size: Minimum chunk size to avoid tiny chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

        # Patterns for identifying section boundaries
        self.section_patterns = [
            r'^([DATB])\s*(\d+(?:\.\d+)*)',  # Rule IDs: D 4.3.3, AT 8.2.1
            r'^\d+\.\d+\s+[A-Z]',  # Numbered sections: 4.3 SCORING
            r'^[A-Z][A-Z\s]{5,}$',  # ALL CAPS headings
        ]

    def is_section_boundary(self, line: str) -> bool:
        """
        Check if a line is a section boundary.

        Args:
            line: Text line to check

        Returns:
            True if line is a section boundary
        """
        line = line.strip()
        for pattern in self.section_patterns:
            if re.match(pattern, line):
                return True
        return False

    def split_into_semantic_chunks(self, text: str, metadata: Dict) -> List[Chunk]:
        """
        Split text into chunks at semantic boundaries.

        Args:
            text: Text to chunk
            metadata: Metadata to attach to chunks

        Returns:
            List of Chunk objects
        """
        chunks = []
        lines = text.split('\n')

        current_chunk_lines = []
        current_char_count = 0
        chunk_counter = 0

        for i, line in enumerate(lines):
            line_length = len(line) + 1  # +1 for newline

            # Check if adding this line would exceed chunk size
            if current_char_count + line_length > self.chunk_size and current_chunk_lines:
                # Check if next line is a section boundary
                is_boundary = self.is_section_boundary(line)

                if is_boundary or current_char_count >= self.chunk_size:
                    # Create chunk from accumulated lines
                    chunk_text = '\n'.join(current_chunk_lines)

                    if len(chunk_text) >= self.min_chunk_size:
                        chunks.append(self._create_chunk(
                            chunk_text,
                            chunk_counter,
                            metadata
                        ))
                        chunk_counter += 1

                    # Start new chunk with overlap
                    overlap_lines = self._get_overlap_lines(
                        current_chunk_lines,
                        self.chunk_overlap
                    )
                    current_chunk_lines = overlap_lines
                    current_char_count = sum(len(l) + 1 for l in overlap_lines)

            current_chunk_lines.append(line)
            current_char_count += line_length

        # Add final chunk
        if current_chunk_lines:
            chunk_text = '\n'.join(current_chunk_lines)
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append(self._create_chunk(
                    chunk_text,
                    chunk_counter,
                    metadata
                ))

        return chunks

    def _get_overlap_lines(self, lines: List[str], target_overlap: int) -> List[str]:
        """
        Get the last N lines that fit within target overlap size.

        Args:
            lines: List of lines
            target_overlap: Target overlap size in characters

        Returns:
            List of overlap lines
        """
        overlap_lines = []
        overlap_size = 0

        for line in reversed(lines):
            line_size = len(line) + 1
            if overlap_size + line_size > target_overlap:
                break
            overlap_lines.insert(0, line)
            overlap_size += line_size

        return overlap_lines

    def _create_chunk(self, text: str, chunk_num: int, base_metadata: Dict) -> Chunk:
        """
        Create a Chunk object with metadata.

        Args:
            text: Chunk text
            chunk_num: Chunk number
            base_metadata: Base metadata to extend

        Returns:
            Chunk object
        """
        # Extract rule IDs from chunk
        rule_pattern = re.compile(r'([DATB])\s*(\d+(?:\.\d+)*)')
        rule_ids = list(set(rule_pattern.findall(text)))

        metadata = {
            **base_metadata,
            "chunk_number": chunk_num,
            "rule_ids": rule_ids,
        }

        chunk_id = f"{base_metadata.get('document_type', 'unknown')}_{chunk_num}"

        return Chunk(
            chunk_id=chunk_id,
            text=text.strip(),
            metadata=metadata,
            char_count=len(text),
            word_count=len(text.split())
        )

    def chunk_document(self, document: PDFDocument) -> List[Chunk]:
        """
        Chunk an entire PDF document.

        Args:
            document: PDFDocument to chunk

        Returns:
            List of Chunk objects
        """
        all_chunks = []

        # Process pages in groups for better context preservation
        page_group_size = 5  # Process 5 pages at a time
        total_pages = len(document.pages)

        for start_idx in range(0, total_pages, page_group_size):
            end_idx = min(start_idx + page_group_size, total_pages)
            page_group = document.pages[start_idx:end_idx]

            # Combine page group into single text
            combined_text = '\n\n'.join([
                f"--- Page {page.page_number} ---\n{page.text}"
                for page in page_group
            ])

            # Metadata for this group
            metadata = {
                "document_type": document.document_type,
                "filename": document.filename,
                "page_range": (page_group[0].page_number, page_group[-1].page_number),
                "source": document.document_type,
            }

            # Chunk the combined text
            chunks = self.split_into_semantic_chunks(combined_text, metadata)
            all_chunks.extend(chunks)

        print(f"Created {len(all_chunks)} chunks from {document.filename}")
        return all_chunks

    def get_chunk_statistics(self, chunks: List[Chunk]) -> Dict:
        """
        Get statistics about chunks.

        Args:
            chunks: List of Chunk objects

        Returns:
            Dictionary with statistics
        """
        if not chunks:
            return {}

        char_counts = [chunk.char_count for chunk in chunks]
        word_counts = [chunk.word_count for chunk in chunks]

        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(char_counts) // len(char_counts),
            "min_chunk_size": min(char_counts),
            "max_chunk_size": max(char_counts),
            "avg_word_count": sum(word_counts) // len(word_counts),
            "total_characters": sum(char_counts),
            "total_words": sum(word_counts),
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def chunk_documents(
    handbook_doc: PDFDocument,
    rules_doc: PDFDocument,
    chunk_size: int = 2000,
    chunk_overlap: int = 200
) -> Tuple[List[Chunk], List[Chunk]]:
    """
    Chunk both FSA Handbook and FS Rules documents.

    Args:
        handbook_doc: FSA Handbook PDFDocument
        rules_doc: FS Rules PDFDocument
        chunk_size: Target chunk size
        chunk_overlap: Chunk overlap size

    Returns:
        Tuple of (handbook_chunks, rules_chunks)
    """
    from typing import Tuple

    chunker = DocumentChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    print("\nChunking FSA Handbook...")
    handbook_chunks = chunker.chunk_document(handbook_doc)
    stats = chunker.get_chunk_statistics(handbook_chunks)
    print(f"[OK] FSA Handbook: {stats['total_chunks']} chunks, avg size: {stats['avg_chunk_size']} chars")

    print("\nChunking FS Rules...")
    rules_chunks = chunker.chunk_document(rules_doc)
    stats = chunker.get_chunk_statistics(rules_chunks)
    print(f"[OK] FS Rules: {stats['total_chunks']} chunks, avg size: {stats['avg_chunk_size']} chars")

    return handbook_chunks, rules_chunks
