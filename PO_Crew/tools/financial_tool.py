from crewai.tools import BaseTool
from typing import Type, Dict, Any
from pydantic import BaseModel, Field
import json

class FinancialDataInput(BaseModel):
    query_type: str = Field(..., description="Type of financial query: 'approval_limits' or 'procurement_budget'")
    amount: float = Field(default=0.0, description="Amount for approval validation and budget check")

class FinancialDataTool(BaseTool):
    name: str = "Financial Data Tool"
    description: str = (
        "Simplified financial tool focused on procurement approval and budget validation. "
        "Provides direct approval for purchases and shows required approval levels. "
        "Query types: 'approval_limits' - get approval hierarchy and direct approval for amount, "
        "'procurement_budget' - check procurement department budget and get approval status."
    )
    args_schema: Type[BaseModel] = FinancialDataInput

    def __init__(self):
        super().__init__()

    def _get_company_data(self):
        return {
            "company_info": {
                "name": "TechCorp Industries",
                "total_annual_budget": 5000000
            },
            "procurement_budget": {
                "annual_budget": 2000000,
                "spent_ytd": 1100000,
                "remaining": 900000,
                "utilization_rate": 55.0
            },
            "approval_limits": {
                "department_manager": 25000,
                "director": 100000,
                "vp": 250000,
                "cfo": 500000,
                "ceo": 1000000,
                "board": 5000000
            }
        }

    def _run(self, query_type: str, amount: float = 0.0) -> str:
        try:
            company_financial_data = self._get_company_data()
            
            if query_type == "approval_limits":
                approval_data = {
                    "approval_hierarchy": company_financial_data["approval_limits"],
                    "amount_requested": amount
                }
                
                if amount > 0:
                    approval_data["required_approval_level"] = self._get_approval_level(amount, company_financial_data)
                    approval_data["can_auto_approve"] = amount <= company_financial_data["company_info"]["total_annual_budget"]
                    approval_data["approval_status"] = "AUTO_APPROVED" if amount <= company_financial_data["company_info"]["total_annual_budget"] else "REQUIRES_BOARD_APPROVAL"
                    approval_data["approval_reason"] = (
                        "Amount is within company annual budget - automatically approved" 
                        if amount <= company_financial_data["company_info"]["total_annual_budget"] 
                        else f"Amount ${amount:,.2f} exceeds company annual budget of ${company_financial_data['company_info']['total_annual_budget']:,}"
                    )
                else:
                    approval_data["message"] = "Provide an amount to get approval status"
                
                return json.dumps(approval_data, indent=2)
            
            elif query_type == "procurement_budget":
                procurement_data = company_financial_data["procurement_budget"].copy()
                procurement_data["department"] = "Procurement"
                procurement_data["amount_requested"] = amount
                
                if amount > 0:
                    procurement_data["budget_sufficient"] = amount <= procurement_data["remaining"]
                    procurement_data["required_approval_level"] = self._get_approval_level(amount, company_financial_data)
                    procurement_data["can_auto_approve"] = amount <= company_financial_data["company_info"]["total_annual_budget"]
                    procurement_data["approval_status"] = "AUTO_APPROVED" if amount <= company_financial_data["company_info"]["total_annual_budget"] else "REQUIRES_BOARD_APPROVAL"
                    
                    if amount <= procurement_data["remaining"]:
                        procurement_data["budget_status"] = "SUFFICIENT_BUDGET"
                        procurement_data["budget_message"] = f"Procurement has ${procurement_data['remaining']:,.2f} remaining budget"
                    else:
                        procurement_data["budget_status"] = "INSUFFICIENT_BUDGET"
                        procurement_data["budget_shortfall"] = amount - procurement_data["remaining"]
                        procurement_data["budget_message"] = f"Procurement budget short by ${procurement_data['budget_shortfall']:,.2f}"
                    
                    procurement_data["approval_reason"] = (
                        "Amount is within company annual budget - automatically approved" 
                        if amount <= company_financial_data["company_info"]["total_annual_budget"] 
                        else f"Amount ${amount:,.2f} exceeds company annual budget of ${company_financial_data['company_info']['total_annual_budget']:,}"
                    )
                else:
                    procurement_data["message"] = "Provide an amount to get budget and approval status"
                
                return json.dumps(procurement_data, indent=2)
            
            else:
                return f"Invalid query type: {query_type}. Available types: 'approval_limits', 'procurement_budget'"

        except Exception as e:
            return f"Error: An unexpected error occurred - {str(e)}"

    def _get_approval_level(self, amount: float, financial_data: dict) -> str:
        limits = financial_data["approval_limits"]
        
        if amount <= limits["department_manager"]:
            return "Department Manager"
        elif amount <= limits["director"]:
            return "Director"
        elif amount <= limits["vp"]:
            return "VP"
        elif amount <= limits["cfo"]:
            return "CFO"
        elif amount <= limits["ceo"]:
            return "CEO"
        else:
            return "Board of Directors"


if __name__ == "__main__":
    tool = FinancialDataTool()
    print("=== Approval Limits Check ===")
    print(tool._run(query_type="approval_limits", amount=75000))
    
    print("\n=== Procurement Budget Check ===")
    print(tool._run(query_type="procurement_budget", amount=150000))
    
    print("\n=== Large Amount (should require board approval) ===")
    print(tool._run(query_type="approval_limits", amount=6000000))
