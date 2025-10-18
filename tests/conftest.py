"""
Pytest configuration for vectorbt-workspace tests

Adds the workspace root directory to sys.path so tests can import
modules from utils/, core/, data/, etc.
"""

import sys
from pathlib import Path

# Add workspace root to Python path
workspace_root = Path(__file__).parent.parent
sys.path.insert(0, str(workspace_root))
