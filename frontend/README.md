# AI Purchase Order System - Frontend Dashboard

A modern web dashboard for monitoring and controlling the AI-powered Purchase Order automation system.

## Features

### 📊 Dashboard Overview
- **System Metrics**: Real-time view of inventory, purchase orders, and supplier activity
- **Visual Analytics**: Interactive charts showing inventory status, value distribution, and trends
- **Key Performance Indicators**: Critical metrics at a glance

### 📦 Inventory Management
- **Real-time Inventory View**: Current stock levels with color-coded status indicators
- **Smart Filtering**: Filter by category, status, or supplier
- **Restock Recommendations**: Automatic suggestions grouped by supplier with cost estimates
- **Low Stock Alerts**: Visual warnings for items needing attention

### 🔄 Purchase Queue Management
- **Queue Monitoring**: View pending and completed purchase requests
- **Request Details**: Detailed view of each purchase request with validation data
- **Status Management**: Mark requests as completed directly from the interface
- **Processing History**: Track the lifecycle of purchase requests

### 🏭 Supplier Orders
- **Order Tracking**: View all incoming orders from suppliers
- **Customer Information**: Detailed customer and order information
- **Order Analysis**: Break down order items, totals, and delivery requirements
- **MongoDB Integration**: Real-time data from the supplier database

### ⚙️ System Control
- **Agent Execution**: Run Buyer and Supplier crews directly from the interface
- **System Status**: Monitor database connections and system health
- **Real-time Feedback**: Live updates on agent progress and results

## Quick Start

### Prerequisites
- Python 3.8 or higher
- The main AI Purchase Order system should be set up and working
- MongoDB should be running (for supplier orders)

### Installation

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Run the setup script:**
   
   **Windows (Command Prompt):**
   ```cmd
   setup.bat
   ```
   
   **Windows (PowerShell):**
   ```powershell
   .\setup.ps1
   ```

3. **Start the dashboard:**
   ```cmd
   run.bat
   ```
   
   Or manually:
   ```bash
   frontend_env\Scripts\activate
   streamlit run app.py
   ```

4. **Open your browser:**
   The dashboard will automatically open at `http://localhost:8501`

## Usage Guide

### Navigation
Use the sidebar to navigate between different sections:
- **📊 Dashboard**: System overview and key metrics
- **📦 Inventory Management**: Stock monitoring and restock recommendations  
- **🔄 Purchase Queue**: Purchase request tracking and management
- **🏭 Supplier Orders**: Incoming order processing and analysis
- **⚙️ System Control**: Agent execution and system monitoring

### Running AI Agents
1. Go to the **System Control** page
2. Click **Run Buyer Crew** to start the procurement process
3. Click **Run Supplier Crew** to process incoming orders
4. Monitor progress and results in real-time

### Monitoring Inventory
1. Navigate to **Inventory Management**
2. Use filters to focus on specific categories or status levels
3. Review restock recommendations grouped by supplier
4. Check estimated costs for restocking

### Managing Purchase Queue
1. Go to **Purchase Queue** to see pending requests
2. Expand each request to view detailed validation data
3. Mark requests as completed when processed
4. Toggle to view completed request history

## Technical Details

### Architecture
- **Frontend**: Streamlit web application
- **Backend**: Direct integration with CrewAI agents and tools
- **Databases**: SQLite (inventory), MongoDB (orders), JSON (queues)
- **Visualization**: Plotly for interactive charts and graphs

### Data Sources
- **Inventory Data**: SQLite database (`inventory.db`)
- **Purchase Queue**: JSON file (`purchase_queue.json`)
- **Supplier Orders**: MongoDB collection (`poagent_db.PO_records`)

### Real-time Updates
The dashboard connects directly to your data sources and provides real-time views of:
- Current inventory levels and status
- Purchase request queue status
- Incoming supplier orders
- System health and connectivity

## Troubleshooting

### Common Issues

**"No inventory data found"**
- Make sure the main system has been run at least once to initialize the database
- Click "Initialize Sample Inventory" if needed

**"Could not connect to MongoDB"**
- Ensure MongoDB is running on localhost:27017
- Check if the `poagent_db` database exists

**"Email Config Warning"**
- Set up environment variables for email configuration
- Check the main system's `.env` file

**Import errors**
- Ensure the main CrewAI system is properly installed
- Check that all dependencies are installed in both environments

### System Requirements
- **Memory**: 2GB RAM minimum (4GB recommended)
- **Storage**: 500MB free space
- **Network**: Internet connection for AI models
- **Browsers**: Chrome, Firefox, Safari, Edge (latest versions)

## Customization

### Adding New Metrics
Edit `app.py` and add new metric calculations in the `show_dashboard()` function.

### Custom Charts
Add new Plotly visualizations by extending the chart sections in each page function.

### Styling
Modify the CSS in the `st.markdown()` section at the top of `app.py`.

## Future Enhancements

Potential additions to consider:
- **Email Integration**: Direct email sending/receiving through the interface
- **Advanced Analytics**: Predictive inventory modeling
- **User Authentication**: Multi-user support with role-based access
- **API Integration**: REST API for external integrations
- **Mobile Responsive**: Enhanced mobile device support
- **Export Features**: PDF reports and data export capabilities

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify all system components are properly installed
3. Check database connections and file permissions
4. Review the main system logs for detailed error information

---

**Happy Automating! 🤖📦**
