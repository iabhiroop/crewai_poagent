import streamlit as st
import sys
import os
import json
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
import subprocess
import time
import logging
import io
from contextlib import redirect_stdout, redirect_stderr

# Add the parent directory to the path to import our crew modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

try:
    from crewai_poagent.crew import BuyerCrew, SupplierCrew
    from crewai_poagent.tools.purchase_queue_tool import PurchaseQueueTool
    from crewai_poagent.tools.restock_inventory_tool import RestockInventoryTool
except ImportError as e:
    st.error(f"Error importing modules: {e}")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="AI Purchase Order System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .status-running {
        color: #28a745;
    }
    .status-pending {
        color: #ffc107;
    }
    .status-error {
        color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

def load_inventory_data():
    """Load inventory data from SQLite database"""
    try:
        # Use parent directory's data folder
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        db_path = os.path.join(data_dir, "inventory.db")
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("""
            SELECT item_name, quantity, unit_price, category, supplier, 
                   supplier_email, min_threshold,
                   CASE 
                       WHEN quantity <= 0 THEN 'Critical'
                       WHEN quantity <= min_threshold * 0.5 THEN 'Low'
                       WHEN quantity <= min_threshold THEN 'Medium'
                       ELSE 'Good'
                   END as status
            FROM inventory
        """, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error loading inventory data: {e}")
        return pd.DataFrame()

def load_purchase_queue():
    """Load purchase queue data"""
    try:
        # Use parent directory's data folder
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        queue_file_path = os.path.join(data_dir, "purchase_queue.json")
        
        # Temporarily change the queue file path for the tool
        queue_tool = PurchaseQueueTool()
        queue_tool.queue_file = queue_file_path
        queue_data = queue_tool._load_queue()
        return queue_data
    except Exception as e:
        st.error(f"Error loading purchase queue: {e}")
        return {"pending_requests": [], "completed_requests": []}

def load_supplier_orders():
    """Load supplier orders from MongoDB"""
    try:
        client = MongoClient("mongodb://localhost:27017")
        db = client["poagent_db"]
        collection = db["PO_records"]
        orders = list(collection.find({}, {"_id": 0}))
        client.close()
        return orders
    except Exception as e:
        st.warning(f"Could not connect to MongoDB: {e}")
        return []

def setup_logging():
    """Setup logging configuration"""
    # Create logs directory if it doesn't exist
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(parent_dir, "data", "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure logging
    log_file = os.path.join(logs_dir, f"agent_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    
    # Setup file handler
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.INFO)
    
    # Setup console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Setup logger
    logger = logging.getLogger('agent_logger')
    logger.setLevel(logging.INFO)
    logger.handlers.clear()  # Clear existing handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger, log_file

class LogCapture:
    """Capture stdout and stderr for logging"""
    def __init__(self, logger):
        self.logger = logger
        self.stdout_capture = io.StringIO()
        self.stderr_capture = io.StringIO()
        
    def __enter__(self):
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        sys.stdout = self.stdout_capture
        sys.stderr = self.stderr_capture
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        
        # Log captured output
        stdout_content = self.stdout_capture.getvalue()
        stderr_content = self.stderr_capture.getvalue()
        
        if stdout_content:
            self.logger.info(f"STDOUT: {stdout_content}")
        if stderr_content:
            self.logger.error(f"STDERR: {stderr_content}")
        
        return False

def save_agent_logs(log_content, agent_type):
    """Save agent logs to file"""
    try:
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(parent_dir, "data", "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(logs_dir, f"{agent_type}_logs_{timestamp}.txt")
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"=== {agent_type.upper()} CREW LOGS ===\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            f.write(log_content)
        
        return log_file
    except Exception as e:
        st.error(f"Error saving logs: {e}")
        return None

def load_recent_logs(agent_type, limit=5):
    """Load recent log files for an agent type"""
    try:
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(parent_dir, "data", "logs")
        
        if not os.path.exists(logs_dir):
            return []
        
        # Find log files for this agent type
        log_files = []
        for file in os.listdir(logs_dir):
            if file.startswith(f"{agent_type}_logs_") and file.endswith(".txt"):
                file_path = os.path.join(logs_dir, file)
                file_time = os.path.getmtime(file_path)
                log_files.append((file_path, file_time, file))
        
        # Sort by modification time (newest first)
        log_files.sort(key=lambda x: x[1], reverse=True)
        
        return log_files[:limit]
    except Exception as e:
        st.error(f"Error loading logs: {e}")
        return []

def main():
    st.markdown('<h1 class="main-header">🤖 AI Purchase Order System Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["📊 Dashboard", "📦 Inventory Management", "🔄 Purchase Queue", "🏭 Supplier Orders", "⚙️ System Control"]
    )
    
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "📦 Inventory Management":
        show_inventory_management()
    elif page == "🔄 Purchase Queue":
        show_purchase_queue()
    elif page == "🏭 Supplier Orders":
        show_supplier_orders()
    elif page == "⚙️ System Control":
        show_system_control()

def show_dashboard():
    st.header("System Overview")
    
    # Load data
    inventory_df = load_inventory_data()
    queue_data = load_purchase_queue()
    supplier_orders = load_supplier_orders()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_items = len(inventory_df)
        st.metric("Total Inventory Items", total_items)
    
    with col2:
        if not inventory_df.empty:
            low_stock = len(inventory_df[inventory_df['status'].isin(['Critical', 'Low'])])
        else:
            low_stock = 0
        st.metric("Low Stock Items", low_stock, delta=f"-{low_stock}" if low_stock > 0 else "0")
    
    with col3:
        pending_orders = len(queue_data.get("pending_requests", []))
        st.metric("Pending Purchase Orders", pending_orders)
    
    with col4:
        supplier_order_count = len(supplier_orders)
        st.metric("Supplier Orders Received", supplier_order_count)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Inventory Status Distribution")
        if not inventory_df.empty:
            status_counts = inventory_df['status'].value_counts()
            fig = px.pie(values=status_counts.values, names=status_counts.index, 
                        title="Inventory Status Breakdown")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No inventory data available")
    
    with col2:
        st.subheader("Inventory Value by Category")
        if not inventory_df.empty:
            inventory_df['total_value'] = inventory_df['quantity'] * inventory_df['unit_price']
            category_value = inventory_df.groupby('category')['total_value'].sum().reset_index()
            fig = px.bar(category_value, x='category', y='total_value', 
                        title="Total Inventory Value by Category")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No inventory data available")

def show_inventory_management():
    st.header("📦 Inventory Management")
    
    # Load inventory data
    inventory_df = load_inventory_data()
    
    if inventory_df.empty:
        st.warning("No inventory data found. The system may need to be initialized.")
        if st.button("Initialize Sample Inventory"):
            try:
                # Initialize the inventory tool to create sample data
                restock_tool = RestockInventoryTool()
                st.success("Sample inventory data created!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error initializing inventory: {e}")
        return
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        category_filter = st.selectbox("Filter by Category", ["All"] + inventory_df['category'].unique().tolist())
    with col2:
        status_filter = st.selectbox("Filter by Status", ["All", "Critical", "Low", "Medium", "Good"])
    
    # Apply filters
    filtered_df = inventory_df.copy()
    if category_filter != "All":
        filtered_df = filtered_df[filtered_df['category'] == category_filter]
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    
    # Display inventory table
    st.subheader("Current Inventory")
    
    # Color code the status
    def color_status(val):
        if val == 'Critical':
            return 'background-color: #ffebee'
        elif val == 'Low':
            return 'background-color: #fff3e0'
        elif val == 'Medium':
            return 'background-color: #e8f5e8'
        else:
            return 'background-color: #e3f2fd'
    
    styled_df = filtered_df.style.applymap(color_status, subset=['status'])
    st.dataframe(styled_df, use_container_width=True)
    
    # Restock recommendations
    st.subheader("Restock Recommendations")
    restock_needed = filtered_df[filtered_df['status'].isin(['Critical', 'Low', 'Medium'])]
    
    if not restock_needed.empty:
        st.warning(f"Found {len(restock_needed)} items that need restocking!")
        
        # Group by supplier
        supplier_groups = restock_needed.groupby('supplier')
        for supplier, items in supplier_groups:
            with st.expander(f"📧 {supplier} ({len(items)} items)"):
                st.write(f"**Contact:** {items.iloc[0]['supplier_email']}")
                st.dataframe(items[['item_name', 'quantity', 'min_threshold', 'unit_price', 'status']])
                
                total_cost = (items['min_threshold'] * items['unit_price']).sum()
                st.write(f"**Estimated Restock Cost:** ${total_cost:,.2f}")
    else:
        st.success("All items are well-stocked!")

def show_purchase_queue():
    st.header("🔄 Purchase Queue Management")
    
    queue_data = load_purchase_queue()
    
    # Queue statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        pending_count = len(queue_data.get("pending_requests", []))
        st.metric("Pending Requests", pending_count)
    
    with col2:
        completed_count = len(queue_data.get("completed_requests", []))
        st.metric("Completed Requests", completed_count)
    
    with col3:
        total_count = pending_count + completed_count
        st.metric("Total Requests", total_count)
    
    # Pending requests
    st.subheader("Pending Purchase Requests")
    pending_requests = queue_data.get("pending_requests", [])
    
    if pending_requests:
        for i, request in enumerate(pending_requests):
            with st.expander(f"Request {request.get('request_id', f'#{i+1}')} - {request.get('timestamp', 'Unknown time')}"):
                validation_data = request.get("validation_data", {})
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Request Details:**")
                    st.json(validation_data)
                
                with col2:
                    st.write("**Actions:**")
                    if st.button(f"Mark as Completed", key=f"complete_{i}"):
                        try:
                            # Use parent directory's data folder
                            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
                            queue_file_path = os.path.join(data_dir, "purchase_queue.json")
                            
                            queue_tool = PurchaseQueueTool()
                            queue_tool.queue_file = queue_file_path
                            result = queue_tool._mark_completed(request.get('request_id'))
                            st.success(result)
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
    else:
        st.info("No pending purchase requests in queue.")
    
    # Completed requests
    if st.checkbox("Show Completed Requests"):
        st.subheader("Completed Purchase Requests")
        completed_requests = queue_data.get("completed_requests", [])
        
        if completed_requests:
            for request in completed_requests[-5:]:  # Show last 5
                with st.expander(f"✅ {request.get('request_id', 'Unknown')} - Completed"):
                    st.json(request.get("validation_data", {}))
        else:
            st.info("No completed requests yet.")

def show_supplier_orders():
    st.header("🏭 Supplier Orders")
    
    supplier_orders = load_supplier_orders()
    
    if not supplier_orders:
        st.info("No supplier orders found. Make sure MongoDB is running and orders have been processed.")
        return
    
    st.subheader(f"Total Orders Received: {len(supplier_orders)}")
    
    # Display orders
    for i, order in enumerate(supplier_orders):
        with st.expander(f"Order {i+1}: {order.get('customer_details', {}).get('company_name', 'Unknown Company')}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Customer Details:**")
                customer = order.get('customer_details', {})
                st.write(f"Company: {customer.get('company_name', 'N/A')}")
                st.write(f"Contact: {customer.get('contact_person', 'N/A')}")
                st.write(f"Email: {customer.get('email', 'N/A')}")
                st.write(f"Phone: {customer.get('phone', 'N/A')}")
            
            with col2:
                st.write("**Order Summary:**")
                totals = order.get('order_totals', {})
                st.write(f"Total Amount: ${totals.get('total_amount', 0):,.2f}")
                st.write(f"Currency: {totals.get('currency', 'USD')}")
                st.write(f"Items Count: {len(order.get('order_items', []))}")
            
            # Order items
            st.write("**Order Items:**")
            items = order.get('order_items', [])
            if items:
                items_df = pd.DataFrame(items)
                st.dataframe(items_df, use_container_width=True)

def show_system_control():
    st.header("⚙️ System Control")
    
    st.subheader("Run AI Agents")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 🛒 Buyer Crew")
        st.write("Handles inventory monitoring, purchase validation, and PO generation")
        
        if st.button("🚀 Run Buyer Crew", type="primary"):
            with st.spinner("Running Buyer Crew..."):
                try:
                    # Initialize session state for logs if not exists
                    if 'buyer_logs' not in st.session_state:
                        st.session_state.buyer_logs = ""
                    
                    # Clear previous logs
                    st.session_state.buyer_logs = "🚀 Starting Buyer Crew...\n"
                    
                    # Setup logging
                    logger, log_file_path = setup_logging()
                    logger.info("Starting Buyer Crew execution")
                    
                    # This would run the buyer crew
                    inputs = {
                        'procurement_request': 'Analyze inventory levels and validate purchase requirements',
                        'current_date': datetime.now().strftime('%Y-%m-%d'),
                        'current_year': str(datetime.now().year)
                    }
                    
                    st.session_state.buyer_logs += f"📝 Inputs prepared: {inputs}\n"
                    st.session_state.buyer_logs += "⚙️ Initializing crew agents...\n"
                    logger.info(f"Inputs prepared: {inputs}")
                    
                    # Capture stdout/stderr and run the crew
                    with LogCapture(logger) as capture:
                        result = BuyerCrew().crew().kickoff(inputs=inputs)
                    
                    st.session_state.buyer_logs += "✅ Buyer crew completed successfully!\n"
                    st.session_state.buyer_logs += f"📊 Results: {str(result)[:200]}...\n"
                    
                    logger.info("Buyer crew completed successfully")
                    logger.info(f"Results: {str(result)}")
                    
                    # Save logs to file
                    log_file = save_agent_logs(st.session_state.buyer_logs, "buyer")
                    if log_file:
                        st.session_state.buyer_logs += f"💾 Logs saved to: {log_file}\n"
                    
                    st.success("Buyer crew completed successfully!")
                    st.write("**Results:**")
                    st.text(str(result))
                    
                    if log_file:
                        st.info(f"📄 Logs saved to: {os.path.basename(log_file)}")
                    
                except Exception as e:
                    if 'buyer_logs' not in st.session_state:
                        st.session_state.buyer_logs = ""
                    error_msg = f"❌ Error: {str(e)}\n"
                    st.session_state.buyer_logs += error_msg
                    
                    # Log the error
                    if 'logger' in locals():
                        logger.error(f"Error running buyer crew: {e}")
                        save_agent_logs(st.session_state.buyer_logs, "buyer")
                    
                    st.error(f"Error running buyer crew: {e}")
        
        # Display logs
        if 'buyer_logs' in st.session_state and st.session_state.buyer_logs:
            st.write("**Agent Logs:**")
            st.text_area(
                "Buyer Crew Logs",
                value=st.session_state.buyer_logs,
                height=150,
                key="buyer_log_display",
                disabled=True
            )
            
            # Show recent log files
            st.write("**Recent Log Files:**")
            recent_logs = load_recent_logs("buyer", 3)
            if recent_logs:
                for log_path, file_time, filename in recent_logs:
                    time_str = datetime.fromtimestamp(file_time).strftime('%Y-%m-%d %H:%M:%S')
                    if st.button(f"📄 {filename} ({time_str})", key=f"buyer_log_{filename}"):
                        try:
                            with open(log_path, 'r', encoding='utf-8') as f:
                                log_content = f.read()
                            st.text_area(f"Contents of {filename}", value=log_content, height=300)
                        except Exception as e:
                            st.error(f"Error reading log file: {e}")
            else:
                st.info("No recent log files found")
    
    with col2:
        st.write("### 🏭 Supplier Crew")
        st.write("Handles incoming order processing and confirmations")
        
        if st.button("🚀 Run Supplier Crew", type="primary"):
            with st.spinner("Running Supplier Crew..."):
                try:
                    # Initialize session state for logs if not exists
                    if 'supplier_logs' not in st.session_state:
                        st.session_state.supplier_logs = ""
                    
                    # Clear previous logs
                    st.session_state.supplier_logs = "🚀 Starting Supplier Crew...\n"
                    
                    # Setup logging
                    logger, log_file_path = setup_logging()
                    logger.info("Starting Supplier Crew execution")
                    
                    inputs = {
                        'supplier_request': 'Process incoming purchase orders and manage production scheduling',
                        'current_date': datetime.now().strftime('%Y-%m-%d'),
                        'current_year': str(datetime.now().year)
                    }
                    
                    st.session_state.supplier_logs += f"📝 Inputs prepared: {inputs}\n"
                    st.session_state.supplier_logs += "⚙️ Initializing crew agents...\n"
                    logger.info(f"Inputs prepared: {inputs}")
                    
                    # Capture stdout/stderr and run the crew
                    with LogCapture(logger) as capture:
                        result = SupplierCrew().crew().kickoff(inputs=inputs)
                    
                    st.session_state.supplier_logs += "✅ Supplier crew completed successfully!\n"
                    st.session_state.supplier_logs += f"📊 Results: {str(result)[:200]}...\n"
                    
                    logger.info("Supplier crew completed successfully")
                    logger.info(f"Results: {str(result)}")
                    
                    # Save logs to file
                    log_file = save_agent_logs(st.session_state.supplier_logs, "supplier")
                    if log_file:
                        st.session_state.supplier_logs += f"💾 Logs saved to: {log_file}\n"
                    
                    st.success("Supplier crew completed successfully!")
                    st.write("**Results:**")
                    st.text(str(result))
                    
                    if log_file:
                        st.info(f"📄 Logs saved to: {os.path.basename(log_file)}")
                    
                except Exception as e:
                    if 'supplier_logs' not in st.session_state:
                        st.session_state.supplier_logs = ""
                    error_msg = f"❌ Error: {str(e)}\n"
                    st.session_state.supplier_logs += error_msg
                    
                    # Log the error
                    if 'logger' in locals():
                        logger.error(f"Error running supplier crew: {e}")
                        save_agent_logs(st.session_state.supplier_logs, "supplier")
                    
                    st.error(f"Error running supplier crew: {e}")
        
        # Display logs
        if 'supplier_logs' in st.session_state and st.session_state.supplier_logs:
            st.write("**Agent Logs:**")
            st.text_area(
                "Supplier Crew Logs",
                value=st.session_state.supplier_logs,
                height=150,
                key="supplier_log_display",
                disabled=True
            )
            
            # Show recent log files
            st.write("**Recent Log Files:**")
            recent_logs = load_recent_logs("supplier", 3)
            if recent_logs:
                for log_path, file_time, filename in recent_logs:
                    time_str = datetime.fromtimestamp(file_time).strftime('%Y-%m-%d %H:%M:%S')
                    if st.button(f"📄 {filename} ({time_str})", key=f"supplier_log_{filename}"):
                        try:
                            with open(log_path, 'r', encoding='utf-8') as f:
                                log_content = f.read()
                            st.text_area(f"Contents of {filename}", value=log_content, height=300)
                        except Exception as e:
                            st.error(f"Error reading log file: {e}")
            else:
                st.info("No recent log files found")
    
    st.divider()
    
    # System status
    st.subheader("System Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Check database connections
        st.write("**Database Status:**")
        try:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            db_path = os.path.join(data_dir, "inventory.db")
            conn = sqlite3.connect(db_path)
            conn.close()
            st.success("✅ SQLite (Inventory)")
        except:
            st.error("❌ SQLite (Inventory)")
        
        try:
            client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=1000)
            client.admin.command('ismaster')
            client.close()
            st.success("✅ MongoDB (Orders)")
        except:
            st.error("❌ MongoDB (Orders)")
    
    with col2:
        st.write("**File System:**")
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        queue_path = os.path.join(data_dir, "purchase_queue.json")
        db_path = os.path.join(data_dir, "inventory.db")
        
        if os.path.exists(queue_path):
            st.success("✅ Purchase Queue")
        else:
            st.error("❌ Purchase Queue")
        
        if os.path.exists(db_path):
            st.success("✅ Inventory DB")
        else:
            st.error("❌ Inventory DB")
    
    with col3:
        st.write("**Environment:**")
        if os.getenv('supemail'):
            st.success("✅ Email Config")
        else:
            st.warning("⚠️ Email Config")
        
        # Check if required packages are installed
        try:
            import pymongo
            st.success("✅ MongoDB Driver")
        except:
            st.error("❌ MongoDB Driver")
    
    st.divider()
    
    # Log Management Section
    st.subheader("📝 Log Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**All Log Files:**")
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(parent_dir, "data", "logs")
        
        if os.path.exists(logs_dir):
            log_files = []
            for file in os.listdir(logs_dir):
                if file.endswith('.txt'):
                    file_path = os.path.join(logs_dir, file)
                    file_time = os.path.getmtime(file_path)
                    file_size = os.path.getsize(file_path)
                    log_files.append((file, file_time, file_size, file_path))
            
            if log_files:
                # Sort by modification time (newest first)
                log_files.sort(key=lambda x: x[1], reverse=True)
                
                for filename, file_time, file_size, file_path in log_files:
                    time_str = datetime.fromtimestamp(file_time).strftime('%Y-%m-%d %H:%M:%S')
                    size_str = f"{file_size / 1024:.1f} KB"
                    
                    col_inner1, col_inner2 = st.columns([3, 1])
                    with col_inner1:
                        st.write(f"📄 {filename}")
                        st.caption(f"Modified: {time_str} | Size: {size_str}")
                    
                    with col_inner2:
                        if st.button("View", key=f"view_{filename}"):
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    log_content = f.read()
                                st.session_state[f"log_content_{filename}"] = log_content
                            except Exception as e:
                                st.error(f"Error reading log file: {e}")
            else:
                st.info("No log files found")
        else:
            st.info("Logs directory does not exist")
    
    with col2:
        st.write("**Log File Contents:**")
        
        # Display selected log file content
        for key in st.session_state:
            if key.startswith("log_content_"):
                filename = key.replace("log_content_", "")
                st.write(f"**{filename}:**")
                st.text_area(
                    f"Content of {filename}",
                    value=st.session_state[key],
                    height=400,
                    key=f"display_{filename}"
                )
                
                # Add download button
                st.download_button(
                    label=f"Download {filename}",
                    data=st.session_state[key],
                    file_name=filename,
                    mime="text/plain",
                    key=f"download_{filename}"
                )
                break
        else:
            st.info("Select a log file to view its contents")

if __name__ == "__main__":
    main()
