#!/usr/bin/env python3
"""
Document verification module for markdown to PDF converter.
Provides functionality to track document state and avoid unnecessary file recreation.

MIT License - Copyright (c) 2025 Markdown to PDF Converter
"""

import sqlite3
import hashlib
from pathlib import Path
from typing import Dict, Optional


class DocumentStateManager:
    """Manages document state using SQLite database to avoid unnecessary file recreation."""
    
    def __init__(self, db_path: str):
        """Initialize the document state manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the SQLite database and create the document_state table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS document_state (
                        filename TEXT PRIMARY KEY,
                        markdown_hash TEXT NOT NULL,
                        pdf_hash TEXT,
                        style_profile TEXT DEFAULT 'a4-print',
                        max_diagram_width TEXT,
                        max_diagram_height TEXT,
                        page_margins TEXT,
                        has_page_numbers INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to initialize database: {e}")
    
    def get_document_state(self, filename: str) -> Optional[Dict[str, str]]:
        """Get document state from database.
        
        Args:
            filename: Name of the document file
            
        Returns:
            Dictionary containing markdown_hash, pdf_hash, style_profile, diagram dimensions, margins, page_numbers, and updated_at, or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT markdown_hash, pdf_hash, style_profile, 
                           max_diagram_width, max_diagram_height, page_margins, 
                           has_page_numbers, updated_at 
                    FROM document_state 
                    WHERE filename = ?
                """, (filename,))
                result = cursor.fetchone()
                
                if result:
                    return {
                        'markdown_hash': result[0],
                        'pdf_hash': result[1],
                        'style_profile': result[2],
                        'max_diagram_width': result[3],
                        'max_diagram_height': result[4],
                        'page_margins': result[5],
                        'has_page_numbers': result[6],
                        'updated_at': result[7]
                    }
                return None
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to get document state: {e}")
    
    def save_document_state(self, filename: str, markdown_hash: str, pdf_hash: Optional[str] = None, 
                           style_profile: str = 'a4-print',
                           max_diagram_width = None, max_diagram_height = None,
                           page_margins: Optional[str] = None,
                           has_page_numbers: bool = True) -> None:
        """Save document state to database.
        
        Args:
            filename: Name of the document file
            markdown_hash: SHA-256 hash of the markdown file
            pdf_hash: SHA-256 hash of the output file (optional)
            style_profile: Style profile used for generation (default: 'a4-print')
            max_diagram_width: Maximum diagram width setting (pixels or percentage)
            max_diagram_height: Maximum diagram height setting (pixels or percentage)
            page_margins: Page margins setting
            has_page_numbers: Whether page numbers are enabled (default: True)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO document_state 
                    (filename, markdown_hash, pdf_hash, style_profile,
                     max_diagram_width, max_diagram_height, page_margins, has_page_numbers, updated_at) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (filename, markdown_hash, pdf_hash, style_profile,
                      str(max_diagram_width) if max_diagram_width is not None else None,
                      str(max_diagram_height) if max_diagram_height is not None else None,
                      page_margins,
                      1 if has_page_numbers else 0))
                conn.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to save document state: {e}")
    
    def needs_regeneration(self, filename: str, current_markdown_hash: str, pdf_path: Path, 
                          current_style_profile: str = 'a4-print',
                          current_max_diagram_width = None, current_max_diagram_height = None,
                          current_page_margins: Optional[str] = None,
                          current_has_page_numbers: bool = True) -> bool:
        """Check if output needs regeneration based on hash comparison, file existence, and configuration.
        
        Args:
            filename: Name of the document file
            current_markdown_hash: Current SHA-256 hash of the markdown file
            pdf_path: Path to the expected output file
            current_style_profile: Current style profile being used
            current_max_diagram_width: Current max diagram width setting
            current_max_diagram_height: Current max diagram height setting
            current_page_margins: Current page margins setting
            current_has_page_numbers: Whether page numbers are currently enabled
            
        Returns:
            True if output needs regeneration, False otherwise
        """
        state = self.get_document_state(filename)
        
        if not state:
            # No record exists, needs generation
            return True
        
        if state['markdown_hash'] != current_markdown_hash:
            # Markdown has changed, needs regeneration
            return True
        
        # Check for style profile mismatch
        stored_profile = state.get('style_profile')
        if stored_profile != current_style_profile:
            # Style profile mismatch detected, needs regeneration
            return True
        
        # Check for diagram width mismatch
        stored_width = state.get('max_diagram_width')
        current_width_str = str(current_max_diagram_width) if current_max_diagram_width is not None else None
        if stored_width != current_width_str:
            # Diagram width setting changed, needs regeneration
            return True
        
        # Check for diagram height mismatch
        stored_height = state.get('max_diagram_height')
        current_height_str = str(current_max_diagram_height) if current_max_diagram_height is not None else None
        if stored_height != current_height_str:
            # Diagram height setting changed, needs regeneration
            return True
        
        # Check for page margins mismatch
        stored_margins = state.get('page_margins')
        if stored_margins != current_page_margins:
            # Page margins setting changed, needs regeneration
            return True
        
        # Check for page numbers setting mismatch
        stored_page_numbers = state.get('has_page_numbers')
        current_page_numbers_int = 1 if current_has_page_numbers else 0
        if stored_page_numbers != current_page_numbers_int:
            # Page numbers setting changed, needs regeneration
            return True
        
        if not state['pdf_hash']:
            # No output hash recorded, needs generation
            return True
        
        # Check if output file actually exists
        if not pdf_path.exists():
            # Output file is missing, needs generation
            return True
        
        # Verify that the existing output matches the stored hash
        try:
            current_pdf_hash = calculate_file_hash(pdf_path)
            if current_pdf_hash != state['pdf_hash']:
                # Output file exists but hash doesn't match, needs regeneration
                return True
        except RuntimeError:
            # Failed to calculate hash of existing output, needs regeneration
            return True
        
        return False
    
    def update_pdf_hash(self, filename: str, pdf_hash: str) -> None:
        """Update only the PDF hash for an existing document.
        
        Args:
            filename: Name of the document file
            pdf_hash: SHA-256 hash of the PDF file
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE document_state 
                    SET pdf_hash = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE filename = ?
                """, (pdf_hash, filename))
                conn.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to update PDF hash: {e}")
    
    def get_all_documents(self) -> list[Dict[str, str]]:
        """Get all document states from database.
        
        Returns:
            List of dictionaries containing document state information
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT filename, markdown_hash, pdf_hash, style_profile, max_diagram_width, 
                           max_diagram_height, page_margins, has_page_numbers, created_at, updated_at
                    FROM document_state
                    ORDER BY updated_at DESC
                """)
                results = cursor.fetchall()
                
                return [
                    {
                        'filename': row[0],
                        'markdown_hash': row[1],
                        'pdf_hash': row[2],
                        'style_profile': row[3],
                        'max_diagram_width': row[4],
                        'max_diagram_height': row[5],
                        'page_margins': row[6],
                        'has_page_numbers': row[7],
                        'created_at': row[8],
                        'updated_at': row[9]
                    }
                    for row in results
                ]
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to get all documents: {e}")
    
    def remove_document(self, filename: str) -> None:
        """Remove a document from the database.
        
        Args:
            filename: Name of the document file to remove
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM document_state WHERE filename = ?", (filename,))
                conn.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to remove document: {e}")
    
    def clear_all_documents(self) -> int:
        """Clear all documents from the database and recreate the table with current schema.
        
        Returns:
            Number of documents removed
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM document_state")
                count = cursor.fetchone()[0]
                cursor.execute("DROP TABLE IF EXISTS document_state")
                cursor.execute("""
                    CREATE TABLE document_state (
                        filename TEXT PRIMARY KEY,
                        markdown_hash TEXT NOT NULL,
                        pdf_hash TEXT,
                        style_profile TEXT DEFAULT 'a4-print',
                        max_diagram_width TEXT,
                        max_diagram_height TEXT,
                        page_margins TEXT,
                        has_page_numbers INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                return count
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to clear all documents: {e}")


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        SHA-256 hash as hexadecimal string
        
    Raises:
        RuntimeError: If file cannot be read or hashing fails
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise RuntimeError(f"Failed to calculate hash for {file_path}: {e}")


def verify_pdf_exists_and_matches(pdf_path: Path, expected_hash: str) -> bool:
    """Verify that a PDF file exists and matches the expected hash.
    
    Args:
        pdf_path: Path to the PDF file
        expected_hash: Expected SHA-256 hash of the PDF file
        
    Returns:
        True if PDF exists and matches hash, False otherwise
    """
    if not pdf_path.exists():
        return False
    
    try:
        actual_hash = calculate_file_hash(pdf_path)
        return actual_hash == expected_hash
    except RuntimeError:
        return False

