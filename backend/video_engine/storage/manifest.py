import json
import os
from ..schemas import Manifest

class ManifestGenerator:
    def __init__(self, output_dir="backend/video_engine/manifests"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def save(self, manifest_data: Manifest):
        filepath = os.path.join(self.output_dir, f"{manifest_data.session_id}.json")
        with open(filepath, 'w') as f:
            f.write(manifest_data.model_dump_json(indent=4))
        return filepath
