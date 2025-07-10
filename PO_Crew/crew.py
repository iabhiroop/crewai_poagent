from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from .tools.restock_inventory_tool import RestockInventoryTool
from .tools.report_file_tool import ReportFileTool
from .tools.financial_tool import FinancialDataTool
from .tools.purchase_queue_tool import PurchaseQueueTool
from .tools.document_generator_tool import DocumentGeneratorTool
from .tools.po_email_generator_tool import PoEmailGeneratorTool
from .tools.email_monitoring_tool import EmailMonitoringTool
from .tools.email_response_tool import EmailResponseGeneratorTool
from .tools.po_record_tool import PORecordTool
from .tools.document_parser_tool import DocumentParserTool

# ========== BUYER CREW ==========
@CrewBase
class BuyerCrew():
    """Buyer Crew - Handles inventory management and purchase validation"""

    agents_config = 'config/buyer_agents.yaml'
    tasks_config = 'config/buyer_tasks.yaml'

    @agent
    def inventory_management_agent(self) -> Agent:
        """Agent 1: Inventory Management Agent - Monitors stock levels and demand forecasting"""
        return Agent(
            config=self.agents_config['inventory_management_agent'],
            tools=[
                RestockInventoryTool(),
                ReportFileTool()
            ],
            verbose=True
            
        )
    
    @agent
    def purchase_validation_agent(self) -> Agent:
        """Agent 2: Purchase Validation Agent - Validates purchase requests and stores approved ones in queue"""
        return Agent(
            config=self.agents_config['purchase_validation_agent'],            
            tools=[
                FinancialDataTool(),
                PurchaseQueueTool(),
            ],
            verbose=True
        )

    @agent
    def purchase_order_agent(self) -> Agent:
        """Agent 3: Purchase Order Agent - Generates PO documents and sends emails to suppliers"""
        return Agent(
            config=self.agents_config['purchase_order_agent'],            
            tools=[
                PurchaseQueueTool(),
                DocumentGeneratorTool(),
                PoEmailGeneratorTool(),
            ],
            verbose=True
        )

    # Buyer Tasks
    @task
    def monitor_inventory_levels_task(self) -> Task:
        return Task(
            config=self.tasks_config['monitor_inventory_levels_task'],
            agent=self.inventory_management_agent(),
            output_file='data/tests/inventory_report.md'
        )    
    
    @task
    def analyze_demand_patterns_task(self) -> Task:
        return Task(
            config=self.tasks_config['report_demand_patterns_task'],
            agent=self.inventory_management_agent(),
            context=[self.monitor_inventory_levels_task()],
            output_file='data/tests/demand_patterns_report.md'
        )

    @task
    def validate_purchase_request_task(self) -> Task:
        return Task(
            config=self.tasks_config['validate_purchase_request_task'],
            agent=self.purchase_validation_agent(),
            context=[self.analyze_demand_patterns_task()],
            output_file="data/tests/validated_purchase_requests.json"
        )

    @task
    def process_purchase_queue_task(self) -> Task:
        return Task(
            config=self.tasks_config['process_purchase_queue_task'],
            agent=self.purchase_order_agent(),
            context=[self.validate_purchase_request_task()],
            output_file='data/tests/purchase_queue.json'
        )

    @task
    def generate_purchase_order_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_purchase_order_task'],
            agent=self.purchase_order_agent(),
            context=[self.process_purchase_queue_task()],
            output_file='data/tests/purchase_order.md'
        )

    @task
    def send_purchase_order_emails_task(self) -> Task:
        return Task(
            config=self.tasks_config['send_purchase_order_emails_task'],
            agent=self.purchase_order_agent(),
            context=[self.generate_purchase_order_task()],
            output_file='data/tests/po_email_delivery_report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Buyer crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            max_rpm=9
        )


# ========== SUPPLIER CREW ==========
@CrewBase
class SupplierCrew():
    """Supplier Crew - Handles order processing, production planning, and supply feasibility"""

    agents_config = 'config/supplier_agents.yaml'
    tasks_config = 'config/supplier_tasks.yaml'

    @agent
    def order_intelligence_agent(self) -> Agent:
        """Agent 1: Order Intelligence Agent - Processes incoming orders and extracts information"""
        return Agent(
            config=self.agents_config['order_intelligence_agent'],
            tools=[
                EmailMonitoringTool(),
                DocumentParserTool(),
            ],
            verbose=True
        )

    @agent
    def production_queue_management_agent(self) -> Agent:
        """Agent 2: Production Queue Management Agent - Manages production schedules and priorities"""
        return Agent(
            config=self.agents_config['production_queue_management_agent'],
            tools=[
                PORecordTool(),
                EmailResponseGeneratorTool()
            ],
            verbose=True
        )

    # @agent
    # def supply_feasibility_agent(self) -> Agent:
    #     """Agent 3: Supply Feasibility Agent - Evaluates material availability and delivery schedules"""
    #     return Agent(
    #         config=self.agents_config['supply_feasibility_agent'],
    #         tools=[
    #             MaterialAvailabilityTool(),
    #             # DeliveryScheduleCalculatorTool(),
    #             # CommunicationPlatformTool(),
    #             # RouteOptimizationTool()
    #         ],
    #         verbose=True
        # )

    # Supplier Tasks
    @task
    def process_incoming_orders_task(self) -> Task:
        return Task(
            config=self.tasks_config['process_incoming_orders_task'],
            agent=self.order_intelligence_agent(),
            output_file='data/tests/incoming_orders.json'
        )

    @task
    def extract_order_details_task(self) -> Task:
        return Task(
            config=self.tasks_config['extract_order_details_task'],
            agent=self.order_intelligence_agent(),
            context=[self.process_incoming_orders_task()],
            output_file='data/tests/extracted_orders.json'
        )

    @task
    def record_extracted_orders_task(self) -> Task:
        return Task(
            config=self.tasks_config['record_extracted_orders_task'],
            agent=self.production_queue_management_agent(),
            context=[self.extract_order_details_task()],
            output_file='data/tests/recorded_extracted_orders.json'
        )

    @task
    def send_confirmation_emails_task(self) -> Task:
        return Task(
            config=self.tasks_config['send_confirmation_emails_task'],
            agent=self.production_queue_management_agent(),
            context=[self.record_extracted_orders_task()],
            output_file='data/tests/confirmation_emails_report.md'
        )

    # @task
    # def calculate_delivery_schedule_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['calculate_delivery_schedule_task'],
    #         agent=self.supply_feasibility_agent(),
    #         context=[self.assess_material_availability_task()]
    #     )

    # @task
    # def send_order_confirmation_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['send_order_confirmation_task'],
    #         agent=self.order_intelligence_agent(),
    #         context=[self.calculate_delivery_schedule_task()],
    #         output_file='order_confirmation.md'
        # )

    @crew
    def crew(self) -> Crew:
        """Creates the Supplier crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            max_rpm=9
        )
