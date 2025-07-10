from crewai.tools import BaseTool
from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel
import json
from datetime import datetime, timedelta
import random
import os
import tempfile
import subprocess

class DocumentGeneratorInput(BaseModel):
    action: str = "create_pdf_po"  # create_po, generate_rfq, create_contract, create_latex_po, create_pdf_po
    supplier_name: Optional[str] = ""
    supplier_orders: Optional[List[Dict]] = []
    items: Optional[List[Dict]] = []  # Format: [{"item_code": "ITM001", "description": "Widget A", "quantity": 100, "unit_price": 25.50, "uom": "pcs", "urgency": "high"}]
    delivery_date: Optional[str] = ""
    delivery_address: Optional[str] = "Default Company Address"
    contact_person: Optional[str] = ""
    contact_email: Optional[str] = ""
    special_instructions: Optional[str] = ""
    po_number: Optional[str] = ""
    output_format: Optional[str] = "json"  # json, latex, pdf

class DocumentGeneratorTool(BaseTool):
    name: str = "DocumentGeneratorTool"
    description: str = (
        "Generates various types of documents related to purchase orders and supplier management. "
        "Supports creating purchase orders in PDF format, generating LaTeX documents, and handling "
        "line items with proper formatting. Accepts items in format: "
        "[{'item_code': 'ITM001', 'description': 'Widget A', 'quantity': 100, 'unit_price': 25.50, 'uom': 'pcs', 'urgency': 'high'}]"    )
    args_schema: Type[BaseModel] = DocumentGeneratorInput
    
    def _run(self, action: str = "create_pdf_po", supplier_name: str = "", supplier_orders: List[Dict] = [],
                items: List[Dict] = [], delivery_date: str = "", delivery_address: str = "Default Company Address",
                contact_person: str = "", contact_email: str = "", special_instructions: str = "", 
                po_number: str = "", output_format: str = "json") -> str:
            """Main method to handle different document generation actions"""

            try:
                # Validate inputs
                if not supplier_name:
                    raise ValueError("Supplier name is required")
                
                if not items:
                    raise ValueError("Items list cannot be empty")
                
                self._validate_items_format(items)

                if action == "create_pdf_po":
                    return self._create_pdf_purchase_order(
                        supplier_name, items, delivery_date, delivery_address, 
                        contact_person, contact_email, special_instructions, po_number
                    )
                elif action == "create_latex_po":
                    return self._create_latex_purchase_order(
                        supplier_name, items, delivery_date, delivery_address, 
                        contact_person, contact_email, special_instructions, po_number
                    )
                else:
                    raise ValueError(f"Unknown action: {action}")
            
            except Exception as e:
                return json.dumps({
                    "status": "error",
                    "message": str(e),
                    "supplier_name": supplier_name,
                    "action": action
                })
            
    def _convert_latex_to_pdf(self, latex_content: str, filename_prefix: str = "PO") -> str:
        """Convert LaTeX content to PDF using pdflatex"""
        try:
            # Get the project root directory and create data directory if it doesn't exist
            project_root = os.getcwd()
            data_dir = os.path.join(project_root, "data")
            os.makedirs(data_dir, exist_ok=True)
            
            tex_filename = os.path.join(data_dir, f"{filename_prefix}.tex")
            pdf_filename = os.path.join(data_dir, f"{filename_prefix}.pdf")

            # Write LaTeX content to .tex file
            with open(tex_filename, "w", encoding="utf-8") as f:
                f.write(latex_content)

            # Run pdflatex to generate PDF (change to data directory)
            original_dir = os.getcwd()
            os.chdir(data_dir)
            
            cmd = ['pdflatex', '-interaction', 'nonstopmode', f"{filename_prefix}.tex"]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate()
            
            # Change back to original directory
            os.chdir(original_dir)

            # Clean up auxiliary files
            for ext in ['.tex', '.log', '.aux']:
                try:
                    aux_file = os.path.join(data_dir, f"{filename_prefix}{ext}")
                    os.unlink(aux_file)
                except FileNotFoundError:
                    pass

            return pdf_filename
        
        except Exception as e:
            return pdf_filename

    def _create_pdf_purchase_order(self, supplier_name: str, items: List[Dict], 
                                   delivery_date: str, delivery_address: str, contact_person: str,
                                   contact_email: str, special_instructions: str, po_number: str) -> str:
        """Create a PDF purchase order using LaTeX conversion"""
        latex_content = self._create_latex_purchase_order(
            supplier_name, items, delivery_date, delivery_address, 
            contact_person, contact_email, special_instructions, po_number
        )
        
        # Generate unique PO number if not provided
        if not po_number:
            po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        
        pdf_filename = self._convert_latex_to_pdf(latex_content, po_number)
        
        return json.dumps({
            "status": "success",
            "message": f"PDF Purchase Order generated successfully for {supplier_name}",
            "po_number": po_number,
            "supplier_name": supplier_name,
            "pdf_file": pdf_filename,
            "items_count": len(items),
            "total_value": sum(item.get('quantity', 0) * item.get('unit_price', 0) for item in items),
            "delivery_date": delivery_date,
            "file_path": os.path.abspath(pdf_filename)
        })

    def _create_latex_purchase_order(self, supplier_name: str, items: List[Dict], 
                                     delivery_date: str, delivery_address: str, contact_person: str,
                                     contact_email: str, special_instructions: str, po_number: str) -> str:
        """Generate LaTeX content for purchase order"""
        if not po_number:
            po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        
        if not delivery_date:
            delivery_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')
        
        # Calculate totals
        subtotal = sum(item.get('quantity', 0) * item.get('unit_price', 0) for item in items)
        tax_rate = 0.18  # 18% GST
        tax_amount = subtotal * tax_rate
        total_amount = subtotal + tax_amount
        
        # Generate line items table
        line_items = ""
        for i, item in enumerate(items, 1):
            quantity = item.get('quantity', 0)
            unit_price = item.get('unit_price', 0)
            line_total = quantity * unit_price
            urgency_mark = " \\textbf{(URGENT)}" if item.get('urgency', '').lower() == 'high' else ""
            
            line_items += f"""
        {i} & {item.get('item_code', 'N/A')} & {item.get('description', 'N/A')}{urgency_mark} & {quantity} & {item.get('uom', 'pcs')} & ₹{unit_price:.2f} & ₹{line_total:.2f} \\\\
        \\hline"""
        
        latex_content = f"""
\\documentclass{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{booktabs}}
\\usepackage{{array}}
\\usepackage{{fancyhdr}}
\\usepackage{{graphicx}}
\\usepackage{{xcolor}}
\\usepackage{{amsmath}}

\\pagestyle{{fancy}}
\\fancyhf{{}}
\\rhead{{Page \\thepage}}
\\lhead{{Purchase Order - {po_number}}}

\\begin{{document}}

\\begin{{center}}
{{\\Large \\textbf{{PURCHASE ORDER}}}}\\\\[0.3cm]
{{\\large PO Number: {po_number}}}\\\\[0.2cm]
Date: {datetime.now().strftime('%B %d, %Y')}
\\end{{center}}

\\vspace{{0.5cm}}

\\begin{{minipage}}[t]{{0.48\\textwidth}}
\\textbf{{From:}}\\\\
Buyer Corp\\\\
Phone: +91-XXXXXXXXXX\\\\
Email: agent1.0.email@gmail.com
\\end{{minipage}}
\\hfill
\\begin{{minipage}}[t]{{0.48\\textwidth}}
\\textbf{{To:}}\\\\
{supplier_name}\\\\
{contact_person}\\\\
{contact_email}\\\\
\\end{{minipage}}

\\vspace{{0.5cm}}

\\textbf{{Delivery Information:}}\\\\
Address: {delivery_address}\\\\
Required Delivery Date: {delivery_date}

\\vspace{{0.5cm}}

\\begin{{table}}[h!]
\\centering
\\begin{{tabular}}{{|c|c|p{{3cm}}|c|c|c|c|}}
\\hline
\\textbf{{S.No}} & \\textbf{{Item Code}} & \\textbf{{Description}} & \\textbf{{Qty}} & \\textbf{{UOM}} & \\textbf{{Unit Price}} & \\textbf{{Total}} \\\\
\\hline{line_items}
\\end{{tabular}}
\\end{{table}}

\\vspace{{0.5cm}}

\\begin{{flushright}}
\\begin{{tabular}}{{lr}}
\\textbf{{Subtotal:}} & ₹{subtotal:.2f} \\\\
\\textbf{{Tax (18\\%):}} & ₹{tax_amount:.2f} \\\\
\\hline
\\textbf{{Total Amount:}} & ₹{total_amount:.2f} \\\\
\\end{{tabular}}
\\end{{flushright}}

\\vspace{{0.5cm}}

\\textbf{{Terms and Conditions:}}
\\begin{{itemize}}
\\item Payment terms: 30 days from delivery
\\item Goods must be delivered in good condition
\\item Invoice must reference this PO number
\\item Any damages during transit are supplier's responsibility
\\end{{itemize}}

"""
        
        # Add special instructions section if provided
        if special_instructions:
            latex_content += f"""
\\textbf{{Special Instructions:}}\\\\
{special_instructions}

"""
        
        latex_content += f"""
\\vspace{{1cm}}

\\begin{{minipage}}[t]{{0.48\\textwidth}}
\\textbf{{Authorized Signature:}}\\\\[1cm]
\\rule{{5cm}}{{1pt}}\\\\
Name: \\\\
Designation: \\\\
Date: {datetime.now().strftime('%Y-%m-%d')}
\\end{{minipage}}

\\end{{document}}

"""
        
        return latex_content
        

    def _validate_items_format(self, items: List[Dict]) -> bool:
        """Validate that items are in the correct format"""
        required_fields = ['item_code', 'description', 'quantity', 'unit_price']
        
        for item in items:
            for field in required_fields:
                if field not in item:
                    raise ValueError(f"Missing required field '{field}' in item: {item}")
            
            # Validate data types
            if not isinstance(item['quantity'], (int, float)) or item['quantity'] <= 0:
                raise ValueError(f"Invalid quantity for item {item.get('item_code', 'Unknown')}")
            
            if not isinstance(item['unit_price'], (int, float)) or item['unit_price'] <= 0:
                raise ValueError(f"Invalid unit_price for item {item.get('item_code', 'Unknown')}")
        
        return True