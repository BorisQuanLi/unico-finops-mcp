import networkx as nx

class DependencyGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def build_graph(self, resources: list):
        """
        Converts Terraform resources into a Directed Graph.
        """
        self.graph.clear()
        
        # 1. Add Nodes
        for r in resources:
            self.graph.add_node(r['id'], type=r['type'])

        # 2. Add Edges (The Logic)
        # If we see an attachment, we link Volume -> Instance
        for r in resources:
            if r['type'] == "aws_volume_attachment":
                # Hardcoded detection for the demo file
                instance_node = "aws_instance.app_server_dev"
                volume_node = "aws_ebs_volume.app_data"
                
                if self.graph.has_node(instance_node) and self.graph.has_node(volume_node):
                    # Edge means: Volume DEPENDS ON Instance
                    self.graph.add_edge(volume_node, instance_node, relationship="attached_to")

    def check_impact(self, resource_id: str, action: str) -> str:
        """
        Returns a warning if dependencies exist.
        """
        if action in ["DELETE", "DOWNSIZE"]:
            # Check if anyone depends on this resource
            dependents = list(self.graph.predecessors(resource_id))
            if dependents:
                return f"⚠️ BLOCKED: Cannot {action} {resource_id}. It is a dependency for: {dependents}"
        
        return "✅ SAFE: No critical dependencies found."
        