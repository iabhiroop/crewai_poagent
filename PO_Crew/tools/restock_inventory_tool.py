import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Type
from pydantic import BaseModel
from crewai.tools import BaseTool
import sqlite3

class RestockAnalysisInput(BaseModel):
    analysis_type: str  # 'restock_needed', 'inventory_status'
    category: Optional[str] = ""
    urgency_level: Optional[str] = "all"  # 'critical', 'medium', 'low', 'all'

class RestockInventoryTool(BaseTool):
    name: str = "RestockInventoryTool"
    description: str = (
        "Inventory management tool that analyzes current stock levels and identifies items needing restocking. "
        "Analysis types: 'restock_needed' (items below threshold), 'inventory_status' (complete overview)"
    )
    args_schema: Type[BaseModel] = RestockAnalysisInput
    db_path: str = ""

    def __init__(self, **kwargs):
        # Get the project root directory (where the main script runs)
        project_root = os.getcwd()
        db_path = os.path.join(project_root, "data", "inventory.db")
        
        # Set the db_path field before calling super().__init__()
        super().__init__(db_path=db_path, **kwargs)
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._initialize_database()

    def _initialize_database(self):
        """Initialize the inventory database with sample data including supplier emails."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create inventory table with supplier_email column
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT UNIQUE NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    category TEXT NOT NULL,
                    supplier TEXT NOT NULL,
                    supplier_email TEXT NOT NULL,
                    min_threshold INTEGER DEFAULT 10,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute("SELECT COUNT(*) FROM inventory")
            if cursor.fetchone()[0] == 0:
                sample_data = [
                    ("Office Paper A4", 57, 15.99, "Office Supplies", "Paper Corp", "orders@papercorp.com", 50),
                    ("Printer Ink Cartridges", 26, 45.50, "Office Supplies", "Paper Corp", "orders@papercorp.com", 10),  # Below threshold
                    ("Computer Monitors", 10, 299.99, "Electronics", "Tech Hardware", "test.mail.iitm.indusai@gmail.com", 50), 
                    ("Desk Chairs", 80, 150.00, "Furniture", "Tech Hardware", "test.mail.iitm.indusai@gmail.com", 5),  # Critical - out of stock
                    ("USB Cables", 12, 12.99, "Electronics", "Tech Hardware", "test.mail.iitm.indusai@gmail.com", 20),  
                    ("Notebooks", 10, 5.99, "Office Supplies", "Paper Corp", "orders@papercorp.com", 30),  # Above threshold
                    ("Pens (Box of 12)", 3, 8.50, "Office Supplies", "Paper Corp", "orders@papercorp.com", 15),
                    ("Laptops", 10, 899.99, "Electronics", "Tech Hardware", "test.mail.iitm.indusai@gmail.com", 3),  # Below threshold
                    ("Coffee Pods", 150, 25.99, "Pantry", "Coffee Co", "sales@coffeeco.com", 25),  # Above threshold
                    ("Cleaning Supplies", 20, 35.00, "Maintenance", "Coffee Co", "sales@coffeeco.com", 10)  
                ]
                cursor.executemany('''
                    INSERT INTO inventory (item_name, quantity, unit_price, category, supplier, supplier_email, min_threshold)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', sample_data)
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Database initialization error: {str(e)}")

    def _get_restock_needed_items(self, cursor, urgency_level: str = "all", category_filter: str = "") -> Dict[str, Any]:
        """Get items that need restocking based on urgency level."""
        base_query = """
            SELECT item_name, quantity, min_threshold, category, supplier, supplier_email, unit_price
            FROM inventory
            WHERE quantity <= min_threshold
        """
        
        conditions = []
        params = []
        
        if category_filter:
            conditions.append("category LIKE ?")
            params.append(f"%{category_filter}%")
        
        if urgency_level != "all":
            if urgency_level == "critical":
                conditions.append("quantity <= 0")
            elif urgency_level == "high":
                conditions.append("quantity > 0 AND quantity <= min_threshold * 0.5")
            elif urgency_level == "medium":
                conditions.append("quantity > min_threshold * 0.5 AND quantity <= min_threshold")
        
        if conditions:
            query = base_query + " AND " + " AND ".join(conditions) + " ORDER BY quantity ASC"
        else:
            query = base_query + " ORDER BY quantity ASC"
        
        cursor.execute(query, params)
        items = cursor.fetchall()
        
        restock_items = []
        for item in items:
            priority = "Critical" if item[1] <= 0 else "High" if item[1] <= item[2] * 0.5 else "Medium"
            restock_items.append({
                "item_name": item[0],
                "current_stock": item[1],
                "min_threshold": item[2],
                "category": item[3],
                "supplier": item[4],
                "supplier_email": item[5],
                "unit_price": item[6],
                "priority": priority,
                "suggested_order_qty": max(item[2] * 1, 10)            })
        
        return {
            "urgency_level": urgency_level,
            "category_filter": category_filter or "All Categories",
            "items_needing_restock": restock_items,
            "total_items": len(restock_items)
        }

    def _run(self, analysis_type: str, category: str = "", urgency_level: str = "all") -> str:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if analysis_type == "restock_needed":
                result = self._get_restock_needed_items(cursor, urgency_level, category)
                return json.dumps(result, indent=2)
            
            elif analysis_type == "inventory_status":
                # Get comprehensive inventory overview
                cursor.execute("SELECT COUNT(*) as total_items FROM inventory")
                total_items = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) as low_stock FROM inventory WHERE quantity <= min_threshold")
                low_stock_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) as critical FROM inventory WHERE quantity <= 0")
                critical_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT SUM(quantity * unit_price) as total_value FROM inventory")
                total_value = cursor.fetchone()[0] or 0
                
                # Get category breakdown
                cursor.execute("""
                    SELECT category, COUNT(*) as item_count, 
                           SUM(CASE WHEN quantity <= min_threshold THEN 1 ELSE 0 END) as low_stock_count
                    FROM inventory 
                    GROUP BY category
                """)
                category_breakdown = cursor.fetchall()
                
                result = {
                    "inventory_overview": {
                        "total_items": total_items,
                        "low_stock_items": low_stock_count,
                        "critical_items": critical_count,
                        "total_inventory_value": round(total_value, 2),
                        "health_score": round((1 - low_stock_count / max(total_items, 1)) * 100, 1)
                    },
                    "category_breakdown": [
                        {
                            "category": cat[0],
                            "total_items": cat[1],
                            "low_stock_items": cat[2],
                            "stock_health": round((1 - cat[2] / max(cat[1], 1)) * 100, 1)
                        }
                        for cat in category_breakdown
                    ]
                }
                return json.dumps(result, indent=2)
            
            else:
                return json.dumps({
                    "error": f"Invalid analysis type: {analysis_type}",
                    "available_types": ["restock_needed", "inventory_status"]
                }, indent=2)
                
        except Exception as e:
            return json.dumps({"error": f"An unexpected error occurred: {str(e)}"}, indent=2)
        finally:
            if conn:
                conn.close()

if __name__ == "__main__":
    test = 1
    if test:
        # For testing, use direct path
        project_root = os.getcwd()
        db_path = os.path.join(project_root, "data", "inventory.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inventory")
        conn.commit()
        conn.close()
    
    tool = RestockInventoryTool()
    print("=== Restock Inventory Tool Test (Simplified) ===")
    print("\n1. Items needing restock:")
    print(tool._run("restock_needed", urgency_level="all"))
    # print("\n2. Inventory status:")
    # print(tool._run("inventory_status"))
