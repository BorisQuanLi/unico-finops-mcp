import networkx as nx

class DependencyGraph:
    def __init__(self):
        self.graph = nx.DiGraph()

    def build_graph(self, resources: list):
        """
        Converts Terraform resources into a Directed Graph.
        Now uses dynamic reference parsing instead of hardcoded strings.
        """
        self.graph.clear()

        # 1. Add Nodes
        for r in resources:
            self.graph.add_node(r['id'], type=r['type'])

        # 2. Add Edges (Dynamic Logic)
        for r in resources:
            if r['type'] == "aws_volume_attachment":
                props = r.get('properties', {})

                # Retrieve the refs we extracted in terraform_ops.py
                # e.g., "aws_instance.app_server_dev"
                instance_node = props.get("instance_ref")
                volume_node = props.get("volume_ref")

                if instance_node and volume_node:
                    if self.graph.has_node(instance_node) and self.graph.has_node(volume_node):
                        # CORRECTED DEPENDENCY: The attachment depends on the instance and the volume.
                        # Edge: Attachment -> Instance
                        self.graph.add_edge(r['id'], instance_node, relationship="attaches_to")
                        # Edge: Attachment -> Volume
                        self.graph.add_edge(r['id'], volume_node, relationship="attaches_to")

    def check_impact(self, node_id: str, action: str):
        """
        Checks the impact of an action on a node.
        """
        if not self.graph.has_node(node_id):
            return f"Node '{node_id}' not in graph."

        if action.upper() == "DELETE":
            # Find nodes that depend on this one (predecessors in a "depends-on" graph)
            dependents = list(self.graph.predecessors(node_id))
            if not dependents:
                return "✅ OK: No resources depend on this node."
            else:
                return f"🚨 WARNING: Deleting this will impact {len(dependents)} other resources: {', '.join(dependents)}"

        return "Action not implemented."