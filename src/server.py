import logging
import time
import traceback
from mcp.server.fastmcp import FastMCP
from src.db_client import FinOpsDB
from src.cost_engine import CostArchitect
from src.terraform_ops import TerraformReader
from src.safety_checks import DependencyGraph

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("UnicoFinOps")

# Initialize Components
mcp = FastMCP("UnicoFinOps")
db = FinOpsDB()
brain = CostArchitect()
graph_engine = DependencyGraph()

@mcp.tool()
def analyze_demo_infrastructure():
    """
    Scans the local 'demo_infra' folder, builds a dependency graph,
    and asks Gemini for cost optimizations.
    """
    resources = []
    tf_content = ""
    target_instance = "aws_instance.app_server_dev"

    # --- STEP 1: READ TERRAFORM ---
    try:
        reader = TerraformReader("./demo_infra")
        tf_content = reader.read_main_file()
        if not tf_content: 
            return "Error: No main.tf found in demo_infra directory."

        resources = reader.extract_resources(tf_content)
        if not resources:
            return "Error: No resources found in main.tf."
            
        # Validation: Check if target exists
        resource_ids = [r['id'] for r in resources]
        if target_instance not in resource_ids:
            return f"Error: Target resource '{target_instance}' not found in Terraform configuration."

    except Exception as e:
        logger.error(f"Terraform parsing failed: {e}")
        return f"Critical Error parsing Terraform: {str(e)}"

    # --- STEP 2: GRAPH SAFETY CHECK ---
    safety_check = "UNKNOWN"
    try:
        graph_engine.build_graph(resources)
        safety_check = graph_engine.check_impact(target_instance, "DELETE")
    except Exception as e:
        logger.error(f"Graph safety check failed: {e}")
        safety_check = f"⚠️ GRAPH ERROR: Could not verify safety ({str(e)})"

    # --- STEP 3: AI ANALYSIS (GEMINI 3) ---
    metrics_context = f"CloudWatch: {target_instance} is at 5% CPU. Safety Check: {safety_check}"
    
    analysis = "AI Analysis Unavailable"
    max_retries = 3
    backoff = 1

    for attempt in range(1, max_retries + 1):
        try:
            # Call the AI
            analysis = brain.analyze_terraform(tf_content, metrics_context)

            # Validate response is not an error string
            if isinstance(analysis, str) and (
                analysis.startswith("AI Error:") or "Unavailable" in analysis
            ):
                raise RuntimeError(analysis)
            
            break # Success
        except Exception as e:
            logger.error(f"Gemini attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(backoff)
                backoff *= 2
            else:
                analysis = f"AI analysis unavailable after {max_retries} attempts. Error: {str(e)}"

    # --- STEP 4: DB LOGGING ---
    try:
        if db.db is not None:
            db.log_analysis(target_instance, "Graph-Aware Optimization", 270.00)
    except Exception as e:
        # Non-blocking error (don't fail the request just because stats failed)
        logger.warning(f"Failed to log to MongoDB: {e}")

    return f"""
    🔍 INFRASTRUCTURE GRAPH ANALYSIS
    ================================
    Nodes Detected: {len(resources)}
    Target: {target_instance}
    
    🛡️ SAFETY GATE (NetworkX):
    {safety_check}
    
    🤖 GEMINI 3 (PREVIEW) RECOMMENDATION:
    {analysis}
    """

if __name__ == "__main__":
    mcp.run()