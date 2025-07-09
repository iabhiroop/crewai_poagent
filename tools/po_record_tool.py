from crewai.tools import BaseTool
from typing import Dict, Any, List
import json
import os
from datetime import datetime, timedelta
import random
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from bson import ObjectId

# Global database configuration
MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "poagent_db"
COLLECTION_NAME = "PO_records"

class PORecordTool(BaseTool):
    name: str = "PO Record Management System"
    description: str = (
        "Comprehensive PO processing system that records orders in MongoDB database and manages production queue. "
        "This tool saves extracted purchase order data to MongoDB (localhost:27017 -> poagent_db -> PO_records collection). "
        "Each extracted order becomes a separate document in the collection.\n\n"
        
        "SUPPORTED ACTIONS:\n"
        "1. 'record_extracted_orders' - Save multiple orders from extraction results\n"
        
        "USAGE EXAMPLES:\n"
        "Action: record_extracted_orders\n"
        "Parameters: extracted_data (dict/json string containing extraction results)\n\n"
        
        "EXPECTED INPUT FORMAT for extracted_data:\n"
        "{\n"
        "  'extraction_status': '',\n"
        "  'documents_processed': ,\n"
        "  'extraction_timestamp': ,\n"
        "  'extracted_orders': [\n"
        "    {\n"
        "      'order_id': ,\n"
        "      'source_file': ,\n"
        "      'customer_details': {\n"
        "        'company_name': ,\n"
        "        'contact_person': ,\n"
        "        'email': ,\n"
        "        'phone': ,\n"
        "        'billing_address': ,\n"
        "        'shipping_address': \n"
        "      },\n"
        "      'order_items': [\n"
        "        {\n"
        "          'item_code': '',\n"
        "          'description': '',\n"
        "          'quantity': ,\n"
        "          'unit_price': ,\n"
        "          'total_price': ,\n"
        "          'specifications': '',\n"
        "          'delivery_date': '\n"
        "        }\n"
        "      ],\n"
        "      'order_totals': {\n"
        "        'subtotal': ,\n"
        "        'tax_amount': ,\n"
        "        'shipping_cost': ,\n"
        "        'total_amount': ,\n"
        "        'currency': ''\n"
        "      },\n"
        "      'delivery_requirements': {\n"
        "        'delivery_date': '',\n"
        "        'shipping_method': '',\n"
        "        'special_instructions': ''\n"
        "      },\n"
        "      'payment_terms': {\n"
        "        'terms': '',\n"
        "        'due_date': ''\n"
        "      }\n"
        "    }\n"
        "  ],\n"
        "  'validation_summary': {\n"
        "    'total_orders_extracted':,\n"
        "    'high_confidence_extractions': ,\n"
        "    'medium_confidence_extractions': ,\n"
        "    'low_confidence_extractions': ,\n"
        "    'ready_for_production_queue': \n"
        "  }\n"
        "}\n\n"
    )

    def __init__(self):
        super().__init__()

    def _get_mongodb_connection(self):
        """Establish connection to MongoDB"""
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            # Test connection
            client.admin.command('ismaster')
            return client
        except ConnectionFailure as e:
            raise Exception(f"Failed to connect to MongoDB: {str(e)}")
    
    def _prepare_order_document(self, order_data: Dict[str, Any], extraction_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare order data for MongoDB insertion"""
        document = {
            "_id": order_data.get("order_id", str(ObjectId())),
            "order_id": order_data.get("order_id"),
            "source_file": order_data.get("source_file"),
            "extraction_confidence": order_data.get("extraction_confidence"),
            "customer_details": order_data.get("customer_details", {}),
            "order_items": order_data.get("order_items", []),
            "order_totals": order_data.get("order_totals", {}),
            "delivery_requirements": order_data.get("delivery_requirements", {}),
            "payment_terms": order_data.get("payment_terms", {}),
            "status": "pending",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Add extraction metadata if provided
        if extraction_metadata:
            document["extraction_metadata"] = {
                "extraction_timestamp": extraction_metadata.get("extraction_timestamp"),
                "documents_processed": extraction_metadata.get("documents_processed"),
                "extraction_status": extraction_metadata.get("extraction_status")
            }
        
        return document
    
    def _save_orders_to_mongodb(self, orders: List[Dict[str, Any]], extraction_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Save multiple orders to MongoDB"""
        client = None
        try:
            client = self._get_mongodb_connection()
            db = client[DATABASE_NAME]
            collection = db[COLLECTION_NAME]
            
            saved_orders = []
            errors = []
            
            for order in orders:
                try:
                    document = self._prepare_order_document(order, extraction_metadata)
                    
                    # Use upsert to handle duplicate order IDs
                    result = collection.replace_one(
                        {"_id": document["_id"]}, 
                        document, 
                        upsert=True
                    )
                    
                    saved_orders.append({
                        "order_id": document["order_id"],
                        "action": "inserted" if result.upserted_id else "updated",
                        "document_id": str(document["_id"])
                    })
                    
                except Exception as e:
                    errors.append({
                        "order_id": order.get("order_id", "Unknown"),
                        "error": str(e)
                    })
            return {
                "status": "success" if not errors else "partial_success",
                "saved_orders": saved_orders,
                "total_saved": len(saved_orders),
                "errors": errors,
                "database": DATABASE_NAME,
                "collection": COLLECTION_NAME
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to save orders to MongoDB: {str(e)}",
                "saved_orders": [],
                "total_saved": 0,
                "errors": []
            }
        finally:
            if client:
                client.close()
    
    def _run(self, action: str, extracted_data: 'str | dict' = None, **kwargs) -> str:
        """
        Execute the PO record management action.
        The action to perform is specified by the `action` parameter, and additional required data is 
        provided via keyword arguments.
        Parameters:
            action (str): The action to perform. Supported actions are:
                - "record_extracted_orders": Record multiple extracted orders.
            extracted_data (str or dict): The extracted data containing orders and metadata.

            **kwargs:
                
        """
        try:
            if action == "record_extracted_orders":
                if extracted_data is None:
                    extracted_data = kwargs.get("extracted_data")
                if not extracted_data:
                    return json.dumps({
                        "status": "error",
                        "message": "extracted_data parameter is required for record_extracted_orders action"
                    })
                
                # Parse extracted_data if it's a string
                if isinstance(extracted_data, str):
                    try:
                        extracted_data = json.loads(extracted_data)
                    except json.JSONDecodeError:
                        return json.dumps({
                            "status": "error",
                            "message": "Invalid JSON format in extracted_data"
                        })
                
                extracted_orders = extracted_data.get("extracted_orders", [])
                if not extracted_orders:
                    return json.dumps({
                        "status": "error",
                        "message": "No extracted_orders found in the data"
                    })
                
                # Extract metadata for context
                extraction_metadata = {
                    "extraction_timestamp": extracted_data.get("extraction_timestamp"),
                    "documents_processed": extracted_data.get("documents_processed"),
                    "extraction_status": extracted_data.get("extraction_status"),
                    "validation_summary": extracted_data.get("validation_summary")
                }
                
                result = self._save_orders_to_mongodb(extracted_orders, extraction_metadata)
                return json.dumps(result, indent=2)
            
            elif action == "record_single_po":
                po_data = kwargs.get("po_data")
                if not po_data:
                    return json.dumps({
                        "status": "error",
                        "message": "po_data parameter is required for record_single_po action"
                    })
                
                # Parse po_data if it's a string
                if isinstance(po_data, str):
                    try:
                        po_data = json.loads(po_data)
                    except json.JSONDecodeError:
                        return json.dumps({
                            "status": "error",
                            "message": "Invalid JSON format in po_data"
                        })
                
                result = self._save_orders_to_mongodb([po_data])
                return json.dumps(result, indent=2)
            
            elif action == "get_order_status":
                order_id = kwargs.get("order_id")
                if not order_id:
                    return json.dumps({
                        "status": "error",
                        "message": "order_id parameter is required for get_order_status action"
                    })
                client = None
                try:
                    client = self._get_mongodb_connection()
                    db = client[DATABASE_NAME]
                    collection = db[COLLECTION_NAME]
                    
                    order = collection.find_one({"order_id": order_id})
                    if order:
                        # Convert ObjectId to string for JSON serialization
                        order["_id"] = str(order["_id"])
                        return json.dumps({
                            "status": "success",
                            "order": order
                        }, default=str, indent=2)
                    else:
                        return json.dumps({
                            "status": "not_found",
                            "message": f"Order {order_id} not found in database"
                        })
                finally:
                    if client:
                        client.close()
            
            else:
                return json.dumps({
                    "status": "error",
                    "message": f"Unknown action: {action}. Supported actions: record_extracted_orders, record_single_po, get_order_status"
                })
                
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Unexpected error: {str(e)}"
            })

    
