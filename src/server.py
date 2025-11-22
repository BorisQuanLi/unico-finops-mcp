from mcp.server.fastmcp import FastMCP
from src.db_client import FinOpsDB
from src.cost_engine import CostArchitect
from src.terraform_ops import TerraformReader
from src.safety_checks import DependencyGraph  # <--- THE MISSING LINK
import logging
import time
import traceback

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
    # 1. Parse Terraform
    reader = TerraformReader("./demo_infra")
    tf_content = reader.read_main_file()
    if not tf_content: return "Error: No main.tf found."
    
    resources = reader.extract_resources(tf_content)
    
    # 2. Build the Graph (The "Senior Engineer" Step)
    graph_engine.build_graph(resources)
    
    # 3. Check Safety
    # We simulate an attempt to "Delete" the instance to see if the graph catches it.
    target_instance = "aws_instance.app_server_dev"
    safety_check = graph_engine.check_impact(target_instance, "DELETE")
    
    # 4. AI Analysis
    metrics_context = f"CloudWatch: {target_instance} is at 5% CPU. Safety Check: {safety_check}"

    # Robust AI call with retries and safe fallback
    logger = logging.getLogger(__name__)
    analysis = None
    max_retries = 3
    backoff = 1

    for attempt in range(1, max_retries + 1):
        try:
            analysis = brain.analyze_terraform(tf_content, metrics_context)

            # The CostArchitect may return error messages as strings
            if isinstance(analysis, str) and (
                analysis.startswith("AI Error:") or "Unavailable" in analysis
            ):
                raise RuntimeError(analysis)

            # success
            break
        except Exception as e:
            # Log error with context and a short stack trace
            logger.error(
                "AI analysis failed for target=%s attempt=%d error=%s",
                target_instance,
                attempt,
                str(e),
            )
            logger.debug(traceback.format_exc())

            # If transient and we have retries left, sleep with exponential backoff
            if attempt < max_retries:
                time.sleep(backoff)
                backoff *= 2
                continue

            # Final fallback: set a safe, non-crashing analysis result
            analysis = f"AI analysis unavailable due to error: {str(e)}"
            break

    # 5. Log to Mongo (Persist the win)
    if db.db is not None:
        db.log_analysis(target_instance, "Graph-Aware Optimization", 270.00)

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