# AI Purchase Order System Frontend Configuration

# Database Settings
SQLITE_DB_PATH = "../data/inventory.db"
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB_NAME = "poagent_db"
MONGO_COLLECTION = "PO_records"
PURCHASE_QUEUE_FILE = "../data/purchase_queue.json"

# UI Settings
PAGE_TITLE = "AI Purchase Order System"
PAGE_ICON = "🤖"
LAYOUT = "wide"

# Chart Colors
CHART_COLORS = {
    "primary": "#1f77b4",
    "success": "#28a745", 
    "warning": "#ffc107",
    "danger": "#dc3545",
    "info": "#17a2b8"
}

# Status Color Mapping
STATUS_COLORS = {
    "Critical": "#ffebee",
    "Low": "#fff3e0", 
    "Medium": "#e8f5e8",
    "Good": "#e3f2fd"
}

# Default Values
DEFAULT_ITEMS_PER_PAGE = 50
DEFAULT_CHART_HEIGHT = 400
REFRESH_INTERVAL = 30  # seconds
