# Purchase Order Agent CrewAI

A agentic AI based automation for supply chain ordering and documentation processes that traditionally require extensive manual effort and inventory data analysis.

## 🚀 Overview

This repository showcases how AI agents can transform traditionally manual supply chain processes by automating the tedious tasks of inventory crawling, purchase validation, and order documentation. The system demonstrates the feasibility of replacing hours of manual work with intelligent automation.

**Current Implementation**: Two specialized AI agent crews working collaboratively:

- **Buyer Crew**:  
  Automates the purchasing process by monitoring inventory, validating purchase requirements, and generating purchase orders. This crew eliminates manual spreadsheet analysis, ensures compliance with budget and supplier policies, and streamlines the creation and distribution of purchase documents.

- **Supplier Crew**:  
  Streamlines supplier-side operations by automatically processing incoming orders and managing production workflows. This crew leverages AI to extract order details from emails, schedules production efficiently, and keeps stakeholders informed with timely notifications, reducing manual coordination and data entry.

**Expansion Potential**: 
- The modular architecture enables seamless scaling from 2 up to 10+ specialized agents, adapting to organizational requirements and automation readiness.
- With adequate data and tooling, negotiation agents can be introduced to autonomously manage supplier commitments and contract terms.

## 🎬 Demo

Demo videos and screenshots showcasing key automation workflows.

### 📹 Video Demonstrations

- [Buyer Crew Automation](assests/Recording%202025-07-10%20175032%20Buyer%20crew.mp4) - Complete buyer crew workflow demonstration
- [Buyer Logs Analysis](assests/Recording%202025-07-10%20175221%20buyer%20logs.mp4) - Detailed logging and monitoring showcase
- [Supplier Agent Processing](assests/Recording%202025-07-10%20183909%20supplier%20agent.mp4) - Supplier crew order processing demo
- [Supplier Logs Monitoring](assests/Recording%202025-07-10%20184024%20supplier%20logs.mp4) - Supplier workflow logging demonstration

### 🖼️ Screenshots & UI Samples

The system includes a comprehensive Streamlit-based dashboard with multiple interfaces for different stakeholders:

#### 📊 Main Dashboard Overview
![System Overview](assests/Screenshot%202025-07-10%20205835.png)
*Real-time system metrics, inventory alerts, and automation status monitoring*

#### 📦 Inventory Management Interface
![Inventory Management](assests/Screenshot%202025-07-10%20205848.png)
*Automated inventory tracking with AI-powered restock recommendations and stock level visualization*

#### 🔄 Purchase Queue Management
![Purchase Queue](assests/Screenshot%202025-07-10%20205901.png)
*Automated purchase request processing with validation status and approval workflows*

#### 🏭 Supplier Order Processing
![Supplier Orders](assests/Screenshot%202025-07-10%20205910.png)
*Intelligent order processing with document parsing and production scheduling*

#### ⚙️ System Control & Agent Management
![System Control](assests/Screenshot%202025-07-10%20205921.png)
*Real-time agent execution control with logging and performance monitoring*

#### 🤖 AI Agent Workflow Visualization
![Agent Workflow](assests/Screenshot%202025-07-10%20205947.png)
*Live agent collaboration view showing buyer and supplier crew interactions*

### 🎯 Key UI Features

**Interactive Dashboard Components:**
- **Real-time Metrics**: Live inventory levels, order status, and system performance
- **AI Agent Control**: Start/stop agent crews with real-time execution logs
- **Visual Analytics**: Charts and graphs for inventory trends and order patterns
- **Alert System**: Automated notifications for critical stock levels and system events
- **Document Preview**: Generated purchase orders and supplier communications
- **Workflow Tracking**: Step-by-step visualization of automation processes

**Multi-Stakeholder Views:**
- **Buyer Interface**: Inventory management, purchase validation, and order generation
- **Supplier Interface**: Order processing, production scheduling, and communication
- **Admin Interface**: System monitoring, configuration, and performance analytics

> **Want to share your own demo?**  
> Attach your videos or screenshots by opening a Pull Request and adding them to the `DemoVid/` folder.

## 🏗️ Architecture & Scalability

### Current Implementation (5 Agents)

**Buyer Crew (3 Agents)**
1. **Inventory Management Agent**: Eliminates manual spreadsheet analysis by automatically monitoring stock levels and identifying demand patterns
2. **Purchase Validation Agent**: Replaces budget verification and supplier credential checks with automated validation based on established statistical calculations.
3. **Purchase Order Agent**: Automates document generation and email distribution that typically requires manual template filling and individual supplier communication

**Supplier Crew (2 Agents)**
1. **Order Intelligence Agent**: Automatically scans incoming emails to identify and extract purchase order details, eliminating the need for manual document parsing and data entry. This agent leverages AI to understand email content, attachments, and structured/unstructured formats, ensuring accurate and efficient order intake.
2. **Production Queue Management Agent**: Automates production scheduling and confirmation emails that usually require manual coordination. Additionally, this agent generates a mail alert to notify the responsible stakeholders when a new order is ready to be handled, ensuring timely awareness and action.

### Expansion Roadmap

The system architecture supports scaling based on automation acceptance levels:

**Phase 1 (Current POC)**: 5 agents handling core processes
**Phase 2 (Moderate Automation)**: 7-10 agents adding specialized functions:
- Supplier Relationship Management Agent
- Quality Assurance Agent  
- Logistics Coordination Agent
- Risk Assessment Agent

**Phase 3 (Full Automation)**: 10+ agents with advanced capabilities:
- Predictive Analytics Agent
- Contract Negotiation Agent
- Compliance Monitoring Agent
- Exception Handling Agent

## 📋 POC Capabilities & Time Savings

### Problem Statement
Traditional supply chain processes involve:
- **Hours of manual inventory analysis** across multiple spreadsheets and systems
- **Time-consuming purchase validation** requiring cross-referencing budgets, policies, and supplier data
- **Manual document generation** and individual supplier communications
- **Repetitive order processing** and data entry from various document formats

### Automated Solutions

**Core Automation (Current POC)**
- **Inventory Intelligence**: Automated stock level monitoring and restock recommendations (saves 4-6 hours/week)
- **Smart Purchase Validation**: Automated budget verification and supplier credential checks (saves 2-3 hours/week)
- **Document Automation**: Professional PO generation with automated supplier communications (saves 3-4 hours/week)
- **Order Processing**: Automated parsing and extraction from incoming documents (saves 5-7 hours/week)

**Advanced Capabilities (Expansion Ready)**
- **Multi-channel Integration**: Gmail IMAP and document parsing using OCR
- **Financial Analysis**: Real-time budget tracking and cost optimization
- **Production Planning**: Automated scheduling and resource allocation
- **Predictive Analytics**: Demand forecasting and inventory optimization

## 🛠️ Technology Stack

### AI & Machine Learning
- **CrewAI**: Multi-agent orchestration framework
- **Google Generative AI**: LLM integration for intelligent decision making
- **PaddleOCR**: Document text extraction and parsing

### Backend
- **Python 3.11+**: Core programming language
- **SQLite**: Local database for inventory and order data
- **MongoDB**: Document storage for supplier orders
- **JSON**: Data exchange format for queues and configurations

### Frontend
- **Streamlit**: Interactive web dashboard
- **Plotly**: Data visualization and analytics
- **Pandas**: Data manipulation and analysis

### Communication
- **Email Integration**: IMAP/SMTP for automated communications
- **Document Generation**: PDF and Markdown report generation

## 📁 Project Structure

```
crewai_poagent/
├── requirements.txt              # Main dependencies
├── data/                        # Data storage
│   ├── inventory.db            # SQLite inventory database
│   ├── purchase_queue.json     # Purchase request queue
│   └── logs/                   # System logs
├── PO_Crew/                    # Main AI crew system
│   ├── main.py                 # Entry point
│   ├── crew.py                 # Crew definitions
│   ├── config/                 # Agent and task configurations
│   │   ├── buyer_agents.yaml
│   │   ├── buyer_tasks.yaml
│   │   ├── supplier_agents.yaml
│   │   └── supplier_tasks.yaml
│   └── tools/                  # Custom tools
│       ├── restock_inventory_tool.py
│       ├── purchase_queue_tool.py
│       ├── financial_tool.py
│       ├── document_generator_tool.py
│       ├── email_monitoring_tool.py
│       └── [other tools...]
└── frontend/                   # Web dashboard
    ├── app.py                  # Streamlit application
    ├── requirements.txt        # Frontend dependencies
    ├── setup scripts
    └── UI Components:
        ├── 📊 Dashboard: System overview with real-time metrics
        ├── 📦 Inventory Management: Stock monitoring and AI recommendations
        ├── 🔄 Purchase Queue: Automated request processing
        ├── 🏭 Supplier Orders: Order processing and production scheduling
        └── ⚙️ System Control: Agent management and monitoring
```

## 🚀 Quick Start - Deployment

### Prerequisites
- Python 3.8 or higher
- Gmail account for email integration (optional for testing)
- MongoDB for supplier orders (optional for full functionality)

### Rapid Setup

1. **Clone and install:**
   ```bash
   git clone <repository-url>
   cd crewai_poagent
   pip install -r requirements.txt
   ```

2. **Minimal configuration:**
   Create a `.env` file for optional integrations:
   ```env
   GMAIL_USERNAME=your_email@gmail.com
   GMAIL_PASSWORD=your_app_password
   GOOGLE_API_KEY=your_google_api_key
   ```

3. **Start the POC:**
   ```bash
   cd PO_Crew
   python main.py    # Demonstrates buyer crew automation
   ```

### Testing the Automation

#### Command Line Testing
```bash
python main.py buyer     # Test inventory analysis and PO generation
python main.py supplier  # Test order processing and scheduling
python main.py both      # Full end-to-end automation demo
```

#### Web Dashboard Testing
```bash
cd frontend
python -m streamlit run app.py
```

Access the dashboard at `http://localhost:8501` to visualize the automation in action.

## 📊 Dashboard

The included Streamlit dashboard provides real-time validation of the automation capabilities:

### 📦 Inventory Automation Demo
- **Real-time Stock Analysis**: Demonstrates automated inventory crawling and analysis
- **AI-Powered Recommendations**: Shows intelligent restock suggestions with reasoning
- **Alert System**: Automated notifications replacing manual monitoring

### 🔄 Purchase Process Automation
- **Workflow Visualization**: Shows the complete automated purchase flow
- **Validation Tracking**: Real-time validation of purchase requests and approvals
- **Document Generation**: Live demonstration of automated PO creation

### 🏭 Order Processing Simulation
- **Document Parsing Demo**: Shows OCR and AI-powered order extraction
- **Production Scheduling**: Automated queue management and resource allocation
- **Communication Automation**: Demonstrates automated supplier communications

## ⚠️ Risks & Considerations

### Automation Risks
- **Decision Accuracy**: AI agents may make errors due to insufficient data.
- **Integration Challenges**: Connecting to existing ERP/inventory systems may require custom development
- **Regulatory Compliance**: Automated processes must align with industry regulations and audit requirements

### Mitigation Strategies
- **Human Oversight**: Built-in approval workflows for critical decisions
- **Gradual Implementation**: Phased rollout starting with low-risk processes
- **Fallback Procedures**: Manual override capabilities for exceptional situations

## 🔧 Configuration

### Agent Configuration
Agents are configured via YAML files in `PO_Crew/config/`:
- `buyer_agents.yaml`: Buyer crew agent definitions
- `buyer_tasks.yaml`: Buyer crew task workflows
- `supplier_agents.yaml`: Supplier crew agent definitions
- `supplier_tasks.yaml`: Supplier crew task workflows

### Tool Configuration
Individual tools can be configured through their respective files in `PO_Crew/tools/`

## 📝 Logging & Monitoring

- **Structured Logging**: Comprehensive logging for all operations
- **Agent Logs**: Detailed execution logs for each crew run
- **Performance Metrics**: Execution time and success rate tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

