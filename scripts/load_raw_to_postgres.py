"""
Load Raw Telegram Messages from JSON to PostgreSQL
===================================================
Reads JSON files from data/raw/telegram_messages/YYYY-MM-DD/ and loads them
into PostgreSQL raw.telegram_messages table.

Usage:
    python scripts/load_raw_to_postgres.py --date 2026-01-18
"""

import argparse
import json
import logging
import os
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Dict, Any
import psycopg2
from psycopg2.extras import execute_values

load_dotenv()
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection settings
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": int(os.getenv("POSTGRES_PORT")),
    "database": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD")
}


def create_raw_schema_and_table(conn):
    """Create the raw schema and telegram_messages table if they don't exist."""
    logger.info("Creating raw schema and table...")
    
    cur = conn.cursor()
    
    # Create raw schema
    cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    
    # Drop table if exists (for clean reload during development)
    cur.execute("DROP TABLE IF EXISTS raw.telegram_messages;")
    
    # Create table with all fields from scraped JSON
    cur.execute("""
        CREATE TABLE raw.telegram_messages (
            message_id BIGINT,
            channel_name TEXT,
            channel_title TEXT,
            message_date TIMESTAMP WITH TIME ZONE,
            message_text TEXT,
            has_media BOOLEAN,
            image_path TEXT,
            views INTEGER,
            forwards INTEGER,
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    logger.info("✅ Schema and table created successfully")
    cur.close()


def read_json_files(data_path: str, date_str: str) -> List[Dict[str, Any]]:
    """Read all JSON files from the specified date partition."""
    partition_dir = os.path.join(data_path, "raw", "telegram_messages", date_str)
    
    if not os.path.exists(partition_dir):
        raise FileNotFoundError(f"Directory not found: {partition_dir}")
    
    all_messages = []
    json_files = [f for f in os.listdir(partition_dir) if f.endswith('.json') and f != '_manifest.json']
    
    logger.info(f"Found {len(json_files)} JSON files in {partition_dir}")
    
    for filename in json_files:
        filepath = os.path.join(partition_dir, filename)
        logger.info(f"Reading {filename}...")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            messages = json.load(f)
            all_messages.extend(messages)
            logger.info(f"  Loaded {len(messages)} messages from {filename}")
    
    return all_messages


def load_messages_to_postgres(conn, messages: List[Dict[str, Any]]):
    """Bulk insert messages into PostgreSQL."""
    logger.info(f"Loading {len(messages)} messages into PostgreSQL...")
    
    cur = conn.cursor()
    
    # Prepare data tuples
    data = [
        (
            msg.get('message_id'),
            msg.get('channel_name'),
            msg.get('channel_title'),
            msg.get('message_date'),
            msg.get('message_text'),
            msg.get('has_media'),
            msg.get('image_path'),
            msg.get('views'),
            msg.get('forwards')
        )
        for msg in messages
    ]
    
    # Bulk insert using execute_values (much faster than individual inserts)
    execute_values(
        cur,
        """
        INSERT INTO raw.telegram_messages 
        (message_id, channel_name, channel_title, message_date, message_text, 
         has_media, image_path, views, forwards)
        VALUES %s
        """,
        data,
        page_size=1000
    )
    
    conn.commit()
    logger.info(f"✅ Successfully loaded {len(messages)} messages")
    cur.close()


def verify_load(conn):
    """Verify data was loaded correctly."""
    cur = conn.cursor()
    
    # Count total records
    cur.execute("SELECT COUNT(*) FROM raw.telegram_messages;")
    total_count = cur.fetchone()[0]
    logger.info(f"Total records in raw.telegram_messages: {total_count}")
    
    # Count by channel
    cur.execute("""
        SELECT channel_name, COUNT(*) as message_count
        FROM raw.telegram_messages
        GROUP BY channel_name
        ORDER BY message_count DESC;
    """)
    
    logger.info("Messages per channel:")
    for row in cur.fetchall():
        logger.info(f"  {row[0]}: {row[1]} messages")
    
    cur.close()


def main():
    parser = argparse.ArgumentParser(
        description="Load raw Telegram messages from JSON to PostgreSQL"
    )
    parser.add_argument(
        "--date",
        type=str,
        default="2026-01-18",
        help="Date partition to load (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--path",
        type=str,
        default="data",
        help="Base data directory"
    )
    args = parser.parse_args()
    
    try:
        # Connect to PostgreSQL
        logger.info("Connecting to PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info("✅ Connected to PostgreSQL")
        
        # Create schema and table
        create_raw_schema_and_table(conn)
        
        # Read JSON files
        messages = read_json_files(args.path, args.date)
        
        if not messages:
            logger.warning("No messages found to load")
            return
        
        # Load to PostgreSQL
        load_messages_to_postgres(conn, messages)
        
        # Verify
        verify_load(conn)
        
        conn.close()
        logger.info("✅ Process completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
