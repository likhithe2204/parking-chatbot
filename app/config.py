from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "data" / "static"
CHROMA_DIR = ROOT / "chroma_db"
COLLECTION_NAME = "parking_static"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50
ADMIN_DB_PATH = ROOT / "data" / "admin.db"
RESERVATIONS_FILE = ROOT / "data" / "confirmed_reservations.txt"