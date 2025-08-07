import logging
from typing import Dict

logger = logging.getLogger(__name__)

def display_results(result: Dict, input_type: str):
    print(f"\n{input_type.upper()} RESULTS")
    print("=" * 50)
    print(f"Label: {result.get('label', 'N/A')}")
    print(f"Confidence: {result.get('confidence', 0):.2f}")
    print(f"Explanation: {result.get('explanation', 'No explanation')}")
    
    if result.get("fallback_used"):
        print("\n[Used fallback search results]")
    
    if "error" in result:
        print(f"\n[Error occurred: {result['error']}]")
    
    logger.info(f"Results displayed for {input_type} input")