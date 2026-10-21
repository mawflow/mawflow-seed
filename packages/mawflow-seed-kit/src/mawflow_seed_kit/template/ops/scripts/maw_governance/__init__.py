"""Portable, file-backed project governance. No chat scraping or implicit execution."""
from .service import Governance

PROTOCOL = "mawflow.project_governance.v1"
__all__ = ["Governance", "PROTOCOL"]
