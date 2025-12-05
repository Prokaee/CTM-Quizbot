"""
PDF Processing Module

Extracts text and metadata from Formula Student PDF documents.
"""

import PyPDF2
import pdfplumber
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import re


@dataclass
class PDFPage:
    """Represents a single page from a PDF"""
    page_number: int
    text: str
    metadata: Dict


@dataclass
class PDFDocument:
    """Represents a processed PDF document"""
    filename: str
    total_pages: int
    pages: List[PDFPage]
    metadata: Dict
    document_type: str  # "FSA_Handbook" or "FS_Rules"


class PDFProcessor:
    """Processes Formula Student PDF documents"""

    def __init__(self):
        self.rule_pattern = re.compile(r'([DATB])\s*(\d+)\.(\d+)(?:\.(\d+))?')  # Matches D 4.3.3, AT 8.2.1, etc.

    def extract_text_pypdf2(self, pdf_path: Path) -> List[PDFPage]:
        """
        Extract text using PyPDF2 (fallback method).

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of PDFPage objects
        """
        pages = []

        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)

            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text = page.extract_text()

                pages.append(PDFPage(
                    page_number=page_num + 1,
                    text=text,
                    metadata={}
                ))

        return pages

    def extract_text_pdfplumber(self, pdf_path: Path) -> List[PDFPage]:
        """
        Extract text using pdfplumber (better layout preservation).

        Args:
            pdf_path: Path to PDF file

        Returns:
            List of PDFPage objects
        """
        pages = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()

                # Extract tables if present
                tables = page.extract_tables()

                pages.append(PDFPage(
                    page_number=page_num + 1,
                    text=text if text else "",
                    metadata={"tables": tables} if tables else {}
                ))

        return pages

    def process_document(self, pdf_path: Path, use_pdfplumber: bool = True) -> PDFDocument:
        """
        Process a PDF document and extract all content.

        Args:
            pdf_path: Path to PDF file
            use_pdfplumber: Whether to use pdfplumber (True) or PyPDF2 (False)

        Returns:
            PDFDocument object
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Choose extraction method
        if use_pdfplumber:
            try:
                pages = self.extract_text_pdfplumber(pdf_path)
            except Exception as e:
                print(f"pdfplumber failed, falling back to PyPDF2: {e}")
                pages = self.extract_text_pypdf2(pdf_path)
        else:
            pages = self.extract_text_pypdf2(pdf_path)

        # Determine document type from filename
        filename = pdf_path.name
        if "FSA" in filename or "Handbook" in filename:
            doc_type = "FSA_Handbook"
        elif "FS-Rules" in filename or "Rules" in filename:
            doc_type = "FS_Rules"
        else:
            doc_type = "Unknown"

        return PDFDocument(
            filename=filename,
            total_pages=len(pages),
            pages=pages,
            metadata={"path": str(pdf_path)},
            document_type=doc_type
        )

    def extract_rule_ids(self, text: str) -> List[str]:
        """
        Extract rule IDs from text (e.g., D 4.3.3, AT 8.2.1).

        Args:
            text: Text to search for rule IDs

        Returns:
            List of rule IDs found
        """
        matches = self.rule_pattern.findall(text)
        rule_ids = []

        for match in matches:
            prefix = match[0]
            if len(match) == 4 and match[3]:
                # Three-level rule (e.g., D 4.3.3)
                rule_id = f"{prefix} {match[1]}.{match[2]}.{match[3]}"
            else:
                # Two-level rule (e.g., D 4.3)
                rule_id = f"{prefix} {match[1]}.{match[2]}"

            rule_ids.append(rule_id)

        return list(set(rule_ids))  # Remove duplicates

    def find_section_boundaries(self, pages: List[PDFPage]) -> Dict[str, Tuple[int, int]]:
        """
        Find major section boundaries in the document.

        Args:
            pages: List of PDFPage objects

        Returns:
            Dict mapping section names to (start_page, end_page)
        """
        sections = {}
        current_section = None

        # Common section patterns in FS documents
        section_patterns = [
            r'^([A-Z][A-Z\s]+)$',  # ALL CAPS headings
            r'^(\d+\.?\s+[A-Z][A-Za-z\s]+)',  # Numbered sections
        ]

        for page in pages:
            lines = page.text.split('\n')
            for line in lines[:10]:  # Check first 10 lines of each page
                line = line.strip()
                for pattern in section_patterns:
                    if re.match(pattern, line):
                        if current_section and current_section not in sections:
                            sections[current_section] = (page.page_number, page.page_number)
                        current_section = line
                        break

        return sections

    def get_document_statistics(self, document: PDFDocument) -> Dict:
        """
        Get statistics about the document.

        Args:
            document: PDFDocument object

        Returns:
            Dictionary with statistics
        """
        total_chars = sum(len(page.text) for page in document.pages)
        total_words = sum(len(page.text.split()) for page in document.pages)

        all_rule_ids = []
        for page in document.pages:
            all_rule_ids.extend(self.extract_rule_ids(page.text))

        return {
            "filename": document.filename,
            "document_type": document.document_type,
            "total_pages": document.total_pages,
            "total_characters": total_chars,
            "total_words": total_words,
            "avg_chars_per_page": total_chars // document.total_pages if document.total_pages > 0 else 0,
            "unique_rule_ids": len(set(all_rule_ids)),
            "rule_ids_sample": list(set(all_rule_ids))[:10]
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def process_fsa_handbook(handbook_path: Path) -> PDFDocument:
    """
    Process the FSA Competition Handbook.

    Args:
        handbook_path: Path to FSA Handbook PDF

    Returns:
        Processed PDFDocument
    """
    processor = PDFProcessor()
    return processor.process_document(handbook_path)


def process_fs_rules(rules_path: Path) -> PDFDocument:
    """
    Process the FS Rules document.

    Args:
        rules_path: Path to FS Rules PDF

    Returns:
        Processed PDFDocument
    """
    processor = PDFProcessor()
    return processor.process_document(rules_path)


def process_all_documents(handbook_path: Path, rules_path: Path) -> Tuple[PDFDocument, PDFDocument]:
    """
    Process both FSA Handbook and FS Rules.

    Args:
        handbook_path: Path to FSA Handbook PDF
        rules_path: Path to FS Rules PDF

    Returns:
        Tuple of (handbook_doc, rules_doc)
    """
    processor = PDFProcessor()

    print("Processing FSA Handbook...")
    handbook = processor.process_document(handbook_path)
    print(f"✓ Processed {handbook.total_pages} pages from FSA Handbook")

    print("Processing FS Rules...")
    rules = processor.process_document(rules_path)
    print(f"✓ Processed {rules.total_pages} pages from FS Rules")

    return handbook, rules
