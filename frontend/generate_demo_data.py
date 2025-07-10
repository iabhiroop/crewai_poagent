"""
Demo data generator for the AI Purchase Order System Frontend
Run this script to generate sample data for testing the dashboard
"""

import json
import sqlite3
import os
from datetime import datetime, timedelta
import random

def create_sample_inventory():
    """Create sample inventory data in SQLite"""
    print("Creating sample inventory data...")
    
    # Create data directory in parent folder if it doesn't exist
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(parent_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    db_path = os.path.join(data_dir, "inventory.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table
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
    
    # Clear existing data
    cursor.execute("DELETE FROM inventory")
    
    # Sample data
    sample_data = [
        ("Office Paper A4", 75, 15.99, "Office Supplies", "Paper Corp", "orders@papercorp.com", 50),
        ("Printer Ink Cartridges", 25, 45.50, "Office Supplies", "Paper Corp", "orders@papercorp.com", 15),
        ("Computer Monitors", 11, 299.99, "Electronics", "Tech Hardware", "test.mail.iitm.indusai@gmail.com", 10),
        ("Desk Chairs", 8, 150.00, "Furniture", "Office Furniture Co", "orders@officefurniture.com", 5),
        ("USB Cables", 8, 12.99, "Electronics", "Tech Hardware", "test.mail.iitm.indusai@gmail.com", 20),
        ("Notebooks", 45, 5.99, "Office Supplies", "Paper Corp", "orders@papercorp.com", 30),
        ("Pens (Box of 12)", 20, 8.50, "Office Supplies", "Paper Corp", "orders@papercorp.com", 15),
        ("Laptops", 13, 899.99, "Electronics", "Tech Hardware", "test.mail.iitm.indusai@gmail.com", 10),
        ("Coffee Pods", 150, 25.99, "Pantry", "Coffee Co", "supplies@coffeeco.com", 25),
        ("Cleaning Supplies", 20, 35.00, "Maintenance", "Cleaning Services", "orders@cleaningco.com", 15),
        ("Wireless Mice", 15, 29.99, "Electronics", "Tech Hardware", "test.mail.iitm.indusai@gmail.com", 12),
        ("Keyboards", 6, 79.99, "Electronics", "Tech Hardware", "test.mail.iitm.indusai@gmail.com", 10),
        ("Staplers", 25, 18.50, "Office Supplies", "Paper Corp", "orders@papercorp.com", 8),
        ("Paper Clips", 100, 3.99, "Office Supplies", "Paper Corp", "orders@papercorp.com", 50),
        ("Desk Lamps", 12, 45.00, "Furniture", "Office Furniture Co", "orders@officefurniture.com", 8),
        ("Whiteboards", 8, 125.00, "Office Supplies", "Paper Corp", "orders@papercorp.com", 5),
        ("File Cabinets", 5, 299.99, "Furniture", "Office Furniture Co", "orders@officefurniture.com", 3),
        ("Printer Paper", 80, 12.99, "Office Supplies", "Paper Corp", "orders@papercorp.com", 40),
        ("Ethernet Cables", 15, 15.99, "Electronics", "Tech Hardware", "test.mail.iitm.indusai@gmail.com", 25),
        ("Conference Tables", 4, 599.99, "Furniture", "Office Furniture Co", "orders@officefurniture.com", 2)
    ]
    
    cursor.executemany('''
        INSERT INTO inventory (item_name, quantity, unit_price, category, supplier, supplier_email, min_threshold)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', sample_data)
    
    conn.commit()
    conn.close()
    print(f"✅ Created {len(sample_data)} inventory items")

def create_sample_purchase_queue():
    """Create sample purchase queue data"""
    print("Creating sample purchase queue...")
    
    # Create data directory in parent folder if it doesn't exist
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(parent_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    queue_data = {
        "pending_requests": [
            {
                "request_id": "PQ_20250710_143022",
                "timestamp": "2025-07-10T14:30:22",
                "status": "pending",
                "validation_data": {
                    "budget_status": "approved",
                    "total_cost": 2850.50,
                    "supplier_count": 2,
                    "priority_items": 3,
                    "estimated_delivery": "2025-07-20",
                    "approval_code": "APV-2025-001"
                },
                "created_by": "purchase_validation_agent"
            },
            {
                "request_id": "PQ_20250710_151245",
                "timestamp": "2025-07-10T15:12:45",
                "status": "pending",
                "validation_data": {
                    "budget_status": "approved",
                    "total_cost": 1250.00,
                    "supplier_count": 1,
                    "priority_items": 1,
                    "estimated_delivery": "2025-07-18",
                    "approval_code": "APV-2025-002"
                },
                "created_by": "purchase_validation_agent"
            }
        ],
        "completed_requests": [
            {
                "request_id": "PQ_20250709_093015",
                "timestamp": "2025-07-09T09:30:15",
                "status": "completed",
                "completed_at": "2025-07-10T10:15:30",
                "validation_data": {
                    "budget_status": "approved",
                    "total_cost": 1875.25,
                    "supplier_count": 1,
                    "priority_items": 2,
                    "po_number": "PO-2025-001"
                },
                "created_by": "purchase_validation_agent",
                "processed_by": "purchase_order_agent"
            }
        ],
        "metadata": {
            "created_at": "2025-07-10T08:00:00",
            "last_updated": "2025-07-10T15:12:45"
        }
    }
    
    queue_file_path = os.path.join(data_dir, "purchase_queue.json")
    with open(queue_file_path, "w") as f:
        json.dump(queue_data, f, indent=2)
    
    print(f"✅ Created purchase queue with {len(queue_data['pending_requests'])} pending and {len(queue_data['completed_requests'])} completed requests")

def create_sample_mongo_data():
    """Create sample MongoDB data (if MongoDB is available)"""
    try:
        from pymongo import MongoClient
        
        print("Creating sample MongoDB data...")
        
        client = MongoClient("mongodb://localhost:27017")
        db = client["poagent_db"]
        collection = db["PO_records"]
        
        # Clear existing data
        collection.delete_many({})
        
        sample_orders = [
            {
                "order_id": "PO-2025-001",
                "source_file": "/attachments/PO-2025-001.pdf",
                "extraction_confidence": 0.95,
                "customer_details": {
                    "company_name": "ABC Manufacturing Ltd",
                    "contact_person": "John Smith",
                    "email": "john.smith@abcmanuf.com",
                    "phone": "+1-555-0123",
                    "billing_address": "123 Business St, City, State 12345",
                    "shipping_address": "456 Factory Rd, City, State 12345"
                },
                "order_items": [
                    {
                        "item_code": "PART-001",
                        "description": "Steel Widget Type A",
                        "quantity": 500,
                        "unit_price": 25.50,
                        "total_price": 12750.00,
                        "specifications": "Grade A steel, 10cm x 5cm",
                        "delivery_date": "2025-07-25"
                    },
                    {
                        "item_code": "PART-002", 
                        "description": "Aluminum Connector",
                        "quantity": 200,
                        "unit_price": 15.75,
                        "total_price": 3150.00,
                        "specifications": "6061-T6 aluminum",
                        "delivery_date": "2025-07-25"
                    }
                ],
                "order_totals": {
                    "subtotal": 15900.00,
                    "tax_amount": 1590.00,
                    "shipping_cost": 200.00,
                    "total_amount": 17690.00,
                    "currency": "USD"
                },
                "delivery_requirements": {
                    "delivery_date": "2025-07-25",
                    "shipping_method": "Standard Ground",
                    "special_instructions": "Deliver to loading dock"
                },
                "payment_terms": {
                    "terms": "Net 30",
                    "due_date": "2025-08-24"
                },
                "recorded_at": "2025-07-10T14:30:00"
            },
            {
                "order_id": "PO-2025-002",
                "source_file": "/attachments/PO-2025-002.pdf",
                "extraction_confidence": 0.88,
                "customer_details": {
                    "company_name": "XYZ Corp",
                    "contact_person": "Sarah Johnson",
                    "email": "sarah.j@xyzcorp.com",
                    "phone": "+1-555-0456",
                    "billing_address": "789 Corporate Blvd, City, State 67890",
                    "shipping_address": "789 Corporate Blvd, City, State 67890"
                },
                "order_items": [
                    {
                        "item_code": "ELEC-101",
                        "description": "Circuit Board Assembly",
                        "quantity": 100,
                        "unit_price": 85.00,
                        "total_price": 8500.00,
                        "specifications": "PCB with standard components",
                        "delivery_date": "2025-07-30"
                    }
                ],
                "order_totals": {
                    "subtotal": 8500.00,
                    "tax_amount": 850.00,
                    "shipping_cost": 150.00,
                    "total_amount": 9500.00,
                    "currency": "USD"
                },
                "delivery_requirements": {
                    "delivery_date": "2025-07-30",
                    "shipping_method": "Express",
                    "special_instructions": "Handle with care - fragile electronics"
                },
                "payment_terms": {
                    "terms": "Net 15",
                    "due_date": "2025-08-14"
                },
                "recorded_at": "2025-07-10T16:45:00"
            }
        ]
        
        collection.insert_many(sample_orders)
        client.close()
        
        print(f"✅ Created {len(sample_orders)} supplier orders in MongoDB")
        
    except Exception as e:
        print(f"⚠️ Could not create MongoDB data: {e}")
        print("Make sure MongoDB is running on localhost:27017")

def main():
    """Generate all sample data"""
    print("🚀 Generating demo data for AI Purchase Order System...")
    print("=" * 60)
    
    # Create sample data
    create_sample_inventory()
    create_sample_purchase_queue()
    create_sample_mongo_data()
    
    print("=" * 60)
    print("✅ Demo data generation complete!")
    print("\nGenerated files:")
    print("📄 ../data/inventory.db - SQLite database with inventory data")
    print("📄 ../data/purchase_queue.json - Purchase queue with pending/completed requests")
    print("🗄️ MongoDB: poagent_db.PO_records - Supplier order records")
    print("\nYou can now run the frontend dashboard:")
    print("👉 streamlit run app.py")

if __name__ == "__main__":
    main()
