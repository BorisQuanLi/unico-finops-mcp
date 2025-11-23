import os
import re

class TerraformReader:
    def __init__(self, directory: str):
        self.directory = directory

    def read_main_file(self) -> str:
        path = os.path.join(self.directory, "main.tf")
        try:
            with open(path, "r") as f:
                return f.read()
        except FileNotFoundError:
            return ""

    def extract_resources(self, tf_content: str):
        """
        Parses HCL to find resource definitions.
        Updated with robust fallback logic for the Hackathon Demo.
        """
        resources = []
        
        # 1. NAIVE PARSING (Best Effort)
        # We split by 'resource "' to robustly find blocks even if braces confuse regex
        blocks = tf_content.split('resource "')
        
        for block in blocks[1:]: # Skip empty first split
            try:
                # Extract Type and Name
                # Format: aws_instance" "name" { ...
                parts = block.split('"')
                r_type = parts[0]
                r_name = parts[2]
                
                # Reconstruct an ID
                r_id = f"{r_type}.{r_name}"
                
                props = {}
                
                # 2. PROPERTY EXTRACTION (Text Search)
                # We search the raw text of the block for keywords
                
                # Instance Type
                if 'instance_type' in block:
                    m = re.search(r'instance_type\s*=\s*"([^"]+)"', block)
                    if m: props["current_type"] = m.group(1)
                
                # Volume Type
                if 'type' in block:
                    m = re.search(r'type\s*=\s*"([^"]+)"', block)
                    if m: props["volume_type"] = m.group(1)

                # 3. CRITICAL DEMO LOGIC (Dependency Extraction)
                # We explicitly look for the attachment references
                if r_type == "aws_volume_attachment":
                    # Look for instance_id = ...
                    # Matches: instance_id = aws_instance.app_server_dev.id
                    m_inst = re.search(r'instance_id\s*=\s*([a-zA-Z0-9_.]+)', block)
                    if m_inst:
                        ref = m_inst.group(1).replace(".id", "")
                        props["instance_ref"] = ref
                    
                    # Look for volume_id = ...
                    m_vol = re.search(r'volume_id\s*=\s*([a-zA-Z0-9_.]+)', block)
                    if m_vol:
                        ref = m_vol.group(1).replace(".id", "")
                        props["volume_ref"] = ref

                resources.append({
                    "id": r_id,
                    "type": r_type,
                    "name": r_name,
                    "properties": props,
                    "raw_block": "..." # Truncated for perfs
                })
            except Exception as e:
                # Skip malformed blocks
                continue
            
        return resources