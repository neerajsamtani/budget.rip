"""Dump the APIFlask OpenAPI spec to stdout without starting a server."""
import json
import sys
from pathlib import Path

# Allow running from the server/ directory directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from application import application  # noqa: E402

with application.app_context():
    print(json.dumps(application.spec))
