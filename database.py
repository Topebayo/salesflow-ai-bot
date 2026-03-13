"""
=============================================================================
DATABASE MODULE - PERSISTENT CONVERSATION STORAGE
=============================================================================
Handles all database operations using SQLite for persistent storage.
Stores conversation history and contact/lead information.

Tables:
  - conversations: Stores every message (user + AI) with timestamps
  - contacts: Tracks unique leads with first_seen, last_seen, message_count

Note: SQLite is perfect for development and small-to-medium scale.
      For high-traffic production, swap to PostgreSQL or Redis.
=============================================================================
"""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Database file lives next to the other project files
DB_PATH = Path(__file__).parent / "salesflow.db"


class Database:
    """
    Persistent storage for conversations and contact tracking.
    Uses SQLite — no external services required.
    """

    def __init__(self, db_path: str = None):
        """
        Initialize the database and create tables if they don't exist.

        Args:
            db_path: Optional custom path for the database file.
                     Defaults to salesflow.db in the project root.
        """
        self.db_path = db_path or str(DB_PATH)
        self._init_db()
        logger.info(f"💾 Database initialized at: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with optimized settings."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent read performance
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        """Create database tables and indexes if they don't exist."""
        with self._get_connection() as conn:
            # Conversations table — stores every message
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'model')),
                    content TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Contacts table — tracks unique leads/customers
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    phone_number TEXT PRIMARY KEY,
                    name TEXT,
                    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0
                )
            """)

            # Index for fast conversation lookups by phone number
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_phone
                ON conversations(phone_number)
            """)

            # Index for timestamp-based queries (analytics)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_timestamp
                ON conversations(timestamp)
            """)

            conn.commit()
            logger.info("✅ Database tables verified/created successfully")

    # =========================================================================
    # CONVERSATION OPERATIONS
    # =========================================================================

    def save_message(self, phone_number: str, role: str, content: str):
        """
        Save a single message to the database.

        Args:
            phone_number: The user's WhatsApp phone number
            role: 'user' for customer messages, 'model' for AI responses
            content: The message text content
        """
        with self._get_connection() as conn:
            # Save the message
            conn.execute(
                "INSERT INTO conversations (phone_number, role, content) VALUES (?, ?, ?)",
                (phone_number, role, content)
            )

            # Update or create contact record
            conn.execute("""
                INSERT INTO contacts (phone_number, message_count, last_seen)
                VALUES (?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(phone_number) DO UPDATE SET
                    message_count = message_count + 1,
                    last_seen = CURRENT_TIMESTAMP
            """, (phone_number,))

            conn.commit()

    def get_conversation_history(self, phone_number: str, limit: int = 50) -> list:
        """
        Retrieve conversation history for a specific user.
        Returns messages in the format expected by Gemini's start_chat(history=...).

        Args:
            phone_number: The user's WhatsApp phone number
            limit: Maximum number of messages to retrieve (most recent)

        Returns:
            List of dicts with 'role' and 'parts' keys, compatible with Gemini API
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                """SELECT role, content FROM conversations
                   WHERE phone_number = ?
                   ORDER BY timestamp ASC
                   LIMIT ?""",
                (phone_number, limit)
            )
            history = [
                {"role": row[0], "parts": [row[1]]}
                for row in cursor.fetchall()
            ]
            return history

    def has_conversation(self, phone_number: str) -> bool:
        """
        Check if a conversation exists for a phone number.

        Args:
            phone_number: The user's WhatsApp phone number

        Returns:
            True if conversation history exists
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM conversations WHERE phone_number = ?",
                (phone_number,)
            )
            return cursor.fetchone()[0] > 0

    def clear_conversation(self, phone_number: str) -> bool:
        """
        Clear all conversation history for a specific user.

        Args:
            phone_number: The user's WhatsApp phone number

        Returns:
            True if a conversation was cleared, False if none existed
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM conversations WHERE phone_number = ?",
                (phone_number,)
            )
            conn.commit()
            cleared = cursor.rowcount > 0
            if cleared:
                logger.info(f"🗑️ Conversation cleared for: {phone_number}")
            return cleared

    def get_conversation_count(self) -> int:
        """
        Get the total number of unique conversations (distinct phone numbers).

        Returns:
            Number of unique conversations in the database
        """
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT COUNT(DISTINCT phone_number) FROM conversations"
            )
            return cursor.fetchone()[0]

    # =========================================================================
    # CONTACT / LEAD OPERATIONS
    # =========================================================================

    def get_all_contacts(self) -> list:
        """
        Retrieve all contacts/leads, ordered by most recently active.

        Returns:
            List of contact dicts with phone_number, name, first_seen,
            last_seen, and message_count
        """
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM contacts ORDER BY last_seen DESC"
            )
            return [dict(row) for row in cursor.fetchall()]

    def update_contact_name(self, phone_number: str, name: str):
        """
        Update a contact's name (e.g., from WhatsApp profile data).

        Args:
            phone_number: The contact's phone number
            name: The contact's display name
        """
        with self._get_connection() as conn:
            conn.execute(
                """UPDATE contacts SET name = ?
                   WHERE phone_number = ? AND (name IS NULL OR name = '')""",
                (name, phone_number)
            )
            conn.commit()

    # =========================================================================
    # ANALYTICS / STATS
    # =========================================================================

    def get_stats(self) -> dict:
        """
        Get comprehensive database statistics for analytics.

        Returns:
            Dict with total_contacts, total_messages, messages_today,
            conversations_today, and top_contacts
        """
        with self._get_connection() as conn:
            total_contacts = conn.execute(
                "SELECT COUNT(*) FROM contacts"
            ).fetchone()[0]

            total_messages = conn.execute(
                "SELECT COUNT(*) FROM conversations"
            ).fetchone()[0]

            messages_today = conn.execute(
                "SELECT COUNT(*) FROM conversations WHERE DATE(timestamp) = DATE('now')"
            ).fetchone()[0]

            conversations_today = conn.execute(
                """SELECT COUNT(DISTINCT phone_number) FROM conversations
                   WHERE DATE(timestamp) = DATE('now')"""
            ).fetchone()[0]

            # Top 5 most active contacts
            conn.row_factory = sqlite3.Row
            top_contacts = conn.execute(
                """SELECT phone_number, name, message_count, last_seen
                   FROM contacts ORDER BY message_count DESC LIMIT 5"""
            ).fetchall()

            return {
                "total_contacts": total_contacts,
                "total_messages": total_messages,
                "messages_today": messages_today,
                "conversations_today": conversations_today,
                "top_contacts": [dict(c) for c in top_contacts]
            }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================
# Create a single database instance to be imported by other modules.

db = Database()
