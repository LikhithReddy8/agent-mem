import os
from pathlib import Path

# Set HF_HOME before any transformers/sentence_transformers imports
project_root = Path(__file__).parent.parent
hf_cache = project_root / ".cache" / "models"
hf_cache.mkdir(parents=True, exist_ok=True)
os.environ["HF_HOME"] = str(hf_cache)
