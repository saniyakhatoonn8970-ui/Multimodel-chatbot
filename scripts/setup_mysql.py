import sys
import os
from sqlalchemy import create_engine, text

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings


def setup_mysql():
    """
    Connects to MySQL server root instance and creates the `mindbridge` database.
    """
    db_url = settings.DATABASE_URL
    if not db_url.startswith("mysql"):
        print("DATABASE_URL is not configured for MySQL. Skipping.")
        return

    # Strip database name from URL to connect to the server instance
    # Format: mysql+pymysql://user:password@host:port/dbname
    base_url = db_url.rsplit("/", 1)[0]
    db_name = db_url.rsplit("/", 1)[1].split("?")[0]

    print(f"Connecting to MySQL server at: {base_url.split('@')[-1] if '@' in base_url else base_url}...")
    try:
        engine = create_engine(base_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"))
            conn.commit()
        print(f"[SUCCESS] Database '{db_name}' is ready on MySQL server.")
    except Exception as e:
        print(f"[ERROR] Could not connect to MySQL server: {e}")
        print("\nPossible solutions:")
        print("1. If MySQL is not running, start it via Windows Services ('services.msc' -> Start 'MySQL80')")
        print("2. Ensure username and password in .env are correct.")
        print("3. Alternatively, leave ALLOW_SQLITE_DEV_FALLBACK=true to use the local SQLite database.")


if __name__ == "__main__":
    setup_mysql()
