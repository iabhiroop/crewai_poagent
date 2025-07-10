#!/usr/bin/env python
import sys
import warnings
import os
from datetime import datetime
import time

# Add the src directory to Python path for absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..')
sys.path.insert(0, src_dir)

from PO_Crew.crew import BuyerCrew, SupplierCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run_buyer():
    """
    Run the buyer crew.
    """
    inputs = {
        'procurement_request': 'Analyze inventory levels and validate purchase requirements',
        'current_date': datetime.now().strftime('%Y-%m-%d'),
        'current_year': str(datetime.now().year)
    }
    
    try:
        BuyerCrew().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the buyer crew: {e}")


def run_supplier():
    """
    Run the supplier crew.
    """
    inputs = {
        'supplier_request': 'Process incoming purchase orders and manage production scheduling',
        'current_date': datetime.now().strftime('%Y-%m-%d'),
        'current_year': str(datetime.now().year)
    }
    
    try:
        SupplierCrew().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the supplier crew: {e}")  


def run():
    """
    Run both buyer and supplier crews sequentially.
    """
    print("Running Buyer Crew...")
    run_buyer()
    # time.sleep(30)  # Optional delay for clarity in output
    # print("\nRunning Supplier Crew...")
    # run_supplier()


def run_both():
    """
    Run both buyer and supplier crews sequentially.
    """
    print("Running Buyer Crew...")
    run_buyer()
    print("\nRunning Supplier Crew...")
    run_supplier()


# def train():
#     """
#     Train the buyer crew for a given number of iterations.
#     """
#     inputs = {
#         "procurement_request": "Training inventory management and purchase validation processes",
#         "current_date": datetime.now().strftime('%Y-%m-%d')
#     }
#     try:
        # BuyerCrew().crew().train(n_iterations=int(sys.argv[2]), filename=sys.argv[3], inputs=inputs)

#     except Exception as e:
#         raise Exception(f"An error occurred while training the buyer crew: {e}")

# def replay():
#     """
#     Replay the buyer crew execution from a specific task.
#     """
#     try:
#         BuyerCrew().crew().replay(task_id=sys.argv[2])

#     except Exception as e:
#         raise Exception(f"An error occurred while replaying the buyer crew: {e}")

# def test():
#     """
#     Test the buyer crew execution and returns the results.
#     """
#     inputs = {
#         "procurement_request": "Test inventory management and purchase validation processes",
#         "current_date": datetime.now().strftime('%Y-%m-%d'),
#         "current_year": str(datetime.now().year)
#     }
#     try:
#         BuyerCrew().crew().test(n_iterations=int(sys.argv[2]), openai_model_name=sys.argv[3], inputs=inputs)

#     except Exception as e:
#         raise Exception(f"An error occurred while testing the buyer crew: {e}")

if __name__ == "__main__":
    """
    Main entry point for the procurement agent system.
    
    Usage:
        python main.py                          # Run buyer crew (default)
        python main.py buyer                    # Run buyer crew
        python main.py supplier                 # Run supplier crew
        python main.py both                     # Run both crews sequentially
        python main.py train <crew> <iterations> <filename>    # Train a crew
        python main.py replay <crew> <task_id>  # Replay from specific task
        python main.py test <crew> <iterations> <model>        # Test a crew
    """
    run()
    # if len(sys.argv) == 1:
    #     # Default: run buyer crew
    #     run_buyer()
    # elif sys.argv[1] == "buyer":
    #     # Run buyer crew
    #     run_buyer()
    # elif sys.argv[1] == "supplier":
    #     # Run supplier crew
    #     run_supplier()
    # elif sys.argv[1] == "both":
    #     # Run both crews
    #     run_both()
    # elif sys.argv[1] == "train" and len(sys.argv) >= 5:
    #     # Train the crew
    #     train()
    # elif sys.argv[1] == "replay" and len(sys.argv) >= 4:
    #     # Replay from specific task
    #     replay()
    # elif sys.argv[1] == "test" and len(sys.argv) >= 5:
    #     # Test the crew
    #     test()
    # else:
    #     print("Usage:")
    #     print("  python main.py                          # Run buyer crew (default)")
    #     print("  python main.py buyer                    # Run buyer crew")
    #     print("  python main.py supplier                 # Run supplier crew")
    #     print("  python main.py both                     # Run both crews sequentially")
    #     print("  python main.py train <crew> <iterations> <filename>    # Train a crew")
    #     print("  python main.py replay <crew> <task_id>  # Replay from specific task")
    #     print("  python main.py test <crew> <iterations> <model>        # Test a crew")
    #     sys.exit(1)
