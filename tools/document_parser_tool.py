from crewai.tools import BaseTool
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import json
import os
import requests
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
import re
from paddleocr import PaddleOCR
from google import genai
from google.genai import types
load_dotenv()

class DocumentParserInput(BaseModel):
    """Input schema for DocumentParserTool."""
    file_path: str = Field(description="Path to the document file to parse")
    action: str = Field(default="extract_po_data", description="Action to perform: extract_po_data")

class DocumentParserTool(BaseTool):
    name: str = "Document Parser"
    description: str = (
        "Extract structured purchase order data from documents using EasyOCR and Gemini API. "
        "Supports PDF, image formats (PNG, JPG, etc.). Returns structured JSON with order details, "
        "customer information, line items, totals, and delivery requirements."
    )
    args_schema: type[BaseModel] = DocumentParserInput
    gemini_api_key: Optional[str] = Field(
        default=None, 
        description="API key for Google Gemini API. Set as environment variable 'GEMINI_API_KEY'."
    )

    def __init__(self):
        super().__init__()
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not self.gemini_api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables")

    def _run(self, file_path: str, action: str = "extract_po_data") -> str:
        """
        Parse documents and extract structured purchase order data
        
        Args:
            file_path: Path to document file
            action: Type of action (extract_po_data)
        """
        # try:
        if not os.path.exists(file_path):
            return json.dumps({
                "status": "error",
                "message": f"File not found: {file_path}"
            })

        if action == "extract_po_data":
            return self._extract_po_data(file_path)
        else:
            return json.dumps({
                "status": "error",
                "message": f"Unknown action: {action}"
            })

        # except Exception as e:
        #     return json.dumps({
        #         "status": "error",
        #         "message": f"Document parsing failed: {str(e)}",
        #         "timestamp": datetime.now().isoformat()
        #     })

    def process_result(self,ocr_data):
        """
        Convert OCR results to format: [[centroid(x,y), "String"], ...]
        
        Args:
            ocr_data: Dictionary containing OCR results
            
        Returns:
            List of lists with centroid coordinates and text
        """
        results = []
        
        # Get bounding boxes and corresponding texts
        rec_boxes = ocr_data.get('rec_boxes', [])
        rec_texts = ocr_data.get('rec_texts', [])
        
        # Ensure we have matching boxes and texts
        min_length = min(len(rec_boxes), len(rec_texts))
        
        for i in range(min_length):
            box = rec_boxes[i]
            text = rec_texts[i]
            
            # Calculate centroid from bounding box [x1, y1, x2, y2]
            x1, y1, x2, y2 = box
            centroid_x = (x1 + x2) / 2
            centroid_y = (y1 + y2) / 2
            
            # Add to results as [centroid(x,y), "text"]
            results.append([(centroid_x, centroid_y), text])
        
        return results

    def _extract_po_data(self, file_path: str) -> str:
        """Extract purchase order data from document using EasyOCR and Gemini API"""
        # try:
        ocr = PaddleOCR(
                        use_doc_orientation_classify=False,
                        use_doc_unwarping=False,
                        use_textline_orientation=False)
        result = ocr.predict(file_path)
        
        print('OCR extraction completed. Processing results...')
        prcs_result = self.process_result(result[0])
        # Step 2: Format extracted text using Gemini API
        print('Formatting extracted text with Gemini API...')
        structured_data = self._format_with_gemini_api(str(prcs_result), file_path)
        
        return json.dumps({
            "status": "success",
            "extraction_timestamp": datetime.now().isoformat(),
            "source_file": file_path,
            "raw_text_length": len(result),
            "extracted_data": structured_data
        }, indent=2)

        # except Exception as e:
        #     return json.dumps({
        #         "status": "error",
        #         "message": f"PO data extraction failed: {str(e)}",
        #         "source_file": file_path,
        #         "timestamp": datetime.now().isoformat()
        #     })


    def _format_with_gemini_api(self, raw_text: str, file_path: str) -> dict:
        """Format raw extracted text into structured JSON using Gemini API"""
        try:
            if not self.gemini_api_key:
                raise Exception("GEMINI_API_KEY not configured")

            # Prepare the prompt for Gemini API
            prompt = self._create_gemini_prompt(raw_text)
            
            # Make API request to Gemini
            response = self._call_gemini_api(prompt)
            
            # Parse and validate the response
            # structured_data = self._parse_gemini_response(response)
            
            return response

        except Exception as e:
            # Fallback: return a basic structure with raw text
            return self._create_fallback_structure(raw_text, file_path, str(e))

    def _create_gemini_prompt(self, raw_text: str) -> str:
        """Create a detailed prompt for Gemini API to structure the PO data"""
        prompt = f"""
You are an expert document parser specializing in purchase orders. Please analyze the following raw text extracted from a purchase order document and format it into a structured JSON format.

Raw Text:
{raw_text}

Please extract and format the information into the following JSON structure. If any information is not available, use null values:

{{
  "order_id": "extracted order number or PO number",
  "customer_details"(FROM DETAILS ONLY): {{
    "company_name": "customer company name",
    "contact_person": "contact person name",
    "email": "email address",
    "phone": "phone number", 
    "billing_address": "billing address",
    "shipping_address": "shipping/delivery address"
  }},
  "order_items": [
    {{
      "item_code": "product/item code",
      "description": "item description",
      "quantity": numeric_quantity,
      "unit_price": numeric_unit_price,
      "total_price": numeric_total_price,
      "specifications": "technical specifications",
      "delivery_date": "delivery date in YYYY-MM-DD format"
    }}
  ],
  "order_totals": {{
    "subtotal": numeric_subtotal,
    "tax_amount": numeric_tax,
    "shipping_cost": numeric_shipping,
    "total_amount": numeric_total,
    "currency": "currency code"
  }},
  "delivery_requirements": {{
    "delivery_date": "delivery date in YYYY-MM-DD format",
    "shipping_method": "shipping method",
    "special_instructions": "special delivery instructions"
  }},
  "payment_terms": {{
    "terms": "payment terms (e.g., Net 30)",
    "due_date": "payment due date in YYYY-MM-DD format"
  }}
}}

Important instructions:
1. Extract all numeric values as numbers, not strings
2. Use ISO date format (YYYY-MM-DD) for all dates
3. If multiple line items exist, include all of them in the order_items array
4. Be precise with numeric calculations
5. Return ONLY the JSON structure, no additional text or explanations
6. Ensure all JSON syntax is valid
"""
        return prompt

    def _call_gemini_api(self, prompt: str) -> dict:
        """Make API call to Gemini for text processing"""
        try:
            response = ""
            client = genai.Client(
                api_key=os.environ.get("GEMINI_API_KEY"),
            )
            model = "gemini-1.5-flash"
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                    ],
                ),
            ]
            generate_content_config = types.GenerateContentConfig(
                response_mime_type="application/json",
            )

            for chunk in client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=generate_content_config,
            ):
                if chunk.text:
                    response += chunk.text
                    
            return response

        except Exception as e:
            raise Exception(f"Gemini API call failed: {str(e)}")


    def _create_fallback_structure(self, raw_text: str, file_path: str, error_msg: str) -> dict:
        """Create a fallback structure when Gemini API fails"""
        
        # Try to extract basic information using regex patterns
        order_id_match = re.search(r'(?:PO|P\.O\.|Purchase Order)[\s#:\-]*([A-Z0-9\-]+)', raw_text, re.IGNORECASE)
        order_id = order_id_match.group(1) if order_id_match else f"EXTRACTED_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return {
            "order_id": order_id,
            "customer_details": {
                "company_name": None,
                "contact_person": None,
                "email": None,
                "phone": None,
                "billing_address": None,
                "shipping_address": None
            },
            "order_items": [],
            "order_totals": {
                "subtotal": None,
                "tax_amount": None,
                "shipping_cost": None,
                "total_amount": None,
                "currency": "USD"
            },
            "delivery_requirements": {
                "delivery_date": None,
                "shipping_method": None,
                "special_instructions": None
            },
            "payment_terms": {
                "terms": None,
                "due_date": None
            },
            "extraction_notes": {
                "raw_text_preview": raw_text[:500] + "..." if len(raw_text) > 500 else raw_text,
                "extraction_error": error_msg,
                "fallback_used": True
            }
        }

if __name__ == "__main__":
    # Example usage
    tool = DocumentParserTool()
    file_path = r"C:\Users\ilasy\crewai\poagent\PO-PC-20250526-002.pdf"  # Replace with your document path
    action = "extract_po_data"
    
    result = tool._run(file_path=file_path, action=action)
    print(result)