#!/usr/bin/env python3
"""
Document verification module for markdown to PDF converter.
Provides functionality to track document state and avoid unnecessary file recreation.
"""

import sqlite3
import hashlib
from pathlib import Path
from typing import Dict, Optional


class DocumentStateManager:
    """Manages document state using SQLite database to avoid unnecessary file recreation."""
    
    def __init__(self, db_path: str = "state/document_state.db"):
        """Initialize the document state manager.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
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
            Dictionary containing markdown_hash, pdf_hash, style_profile, and updated_at, or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT markdown_hash, pdf_hash, style_profile, updated_at 
                    FROM document_state 
                    WHERE filename = ?
                """, (filename,))
                result = cursor.fetchone()
                
                if result:
                    return {
                        'markdown_hash': result[0],
                        'pdf_hash': result[1],
                        'style_profile': result[2],
                        'updated_at': result[3]
                    }
                return None
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to get document state: {e}")
    
    def save_document_state(self, filename: str, markdown_hash: str, pdf_hash: Optional[str] = None, style_profile: str = 'a4-print') -> None:
        """Save document state to database.
        
        Args:
            filename: Name of the document file
            markdown_hash: SHA-256 hash of the markdown file
            pdf_hash: SHA-256 hash of the PDF file (optional)
            style_profile: Style profile used for generation (default: 'a4-print')
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO document_state 
                    (filename, markdown_hash, pdf_hash, style_profile, updated_at) 
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (filename, markdown_hash, pdf_hash, style_profile))
                conn.commit()
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to save document state: {e}")
    
    def needs_regeneration(self, filename: str, current_markdown_hash: str, pdf_path: Path, current_style_profile: str = 'a4-print') -> bool:
        """Check if PDF needs regeneration based on hash comparison, file existence, and style profile.
        
        Args:
            filename: Name of the document file
            current_markdown_hash: Current SHA-256 hash of the markdown file
            pdf_path: Path to the expected PDF file
            current_style_profile: Current style profile being used
            
        Returns:
            True if PDF needs regeneration, False otherwise
        """
        state = self.get_document_state(filename)
        
        if not state:
            # No record exists, needs generation
            return True
        
        if state['markdown_hash'] != current_markdown_hash:
            # Markdown has changed, needs regeneration
            return True
        
        # Check for style profile mismatch - only regenerate if profiles differ
        stored_profile = state.get('style_profile')
        if stored_profile != current_style_profile:
            # Style profile mismatch detected, needs regeneration
            return True
        
        if not state['pdf_hash']:
            # No PDF hash recorded, needs generation
            return True
        
        # Check if PDF file actually exists
        if not pdf_path.exists():
            # PDF file is missing, needs generation
            return True
        
        # Verify that the existing PDF matches the stored hash
        try:
            current_pdf_hash = calculate_file_hash(pdf_path)
            if current_pdf_hash != state['pdf_hash']:
                # PDF file exists but hash doesn't match, needs regeneration
                return True
        except RuntimeError:
            # Failed to calculate hash of existing PDF, needs regeneration
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
                    SELECT filename, markdown_hash, pdf_hash, style_profile, created_at, updated_at
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
                        'created_at': row[4],
                        'updated_at': row[5]
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
        """Clear all documents from the database.
        
        Returns:
            Number of documents removed
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM document_state")
                count = cursor.fetchone()[0]
                cursor.execute("DELETE FROM document_state")
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
