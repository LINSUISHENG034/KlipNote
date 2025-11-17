"""
Command-line interface tools for quality validation and model comparison.
"""

from app.cli.compare_models import main as compare_models_main
from app.cli.validate_quality import main as validate_quality_main

__all__ = ["compare_models_main", "validate_quality_main"]
