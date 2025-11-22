import os
import re

class TerraformReader:
    def __init__(self, directory: str):
        self.directory = directory

    def read_main_file(self) -> str:
        """Reads the main.tf file from the directory."""
        path = os.path.join(self.directory, "main.tf")
        try:
            with open(path, "r") as f:
                return f.read()
        except FileNotFoundError:
            return ""

    def extract_resources(self, tf_content: str):
        """
        Parses the HCL to find resource definitions.
        Returns a list of dictionaries describing resources.
        """
        resources = []
        
        # Regex to find 'resource "type" "name" { ... }'
        # This is a hackathon-level parser. For production, North.Cloud uses python-hcl2.
        pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"\s+\{([^}]+)\}'
        matches = re.finditer(pattern, tf_content, re.DOTALL)

        for match in matches:
            r_type = match.group(1)
            r_name = match.group(2)
            block_content = match.group(3)
            
            # Simple extraction of instance_type and volume type
            props = {}
            if "instance_type" in block_content:
                type_match = re.search(r'instance_type\s*=\s*"([^"]+)"', block_content)
                if type_match:
                    props["current_type"] = type_match.group(1)
            
            if "type" in block_content: # for volume type
                vol_match = re.search(r'type\s*=\s*"([^"]+)"', block_content)
                if vol_match:
                    props["volume_type"] = vol_match.group(1)

            resources.append({
                "id": f"{r_type}.{r_name}",
                "type": r_type,
                "name": r_name,
                "properties": props,
                "raw_block": match.group(0)
            })
            
        return resources