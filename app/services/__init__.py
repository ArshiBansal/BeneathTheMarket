"""
Streamlit application service layer.

Each service connects independently to local MongoDB and (when needed)
to yfinance.  The app never imports or executes notebook code.
"""

from .data_service import DataService
from .model_service import ModelService
from .nlp_service import NLPService

__all__ = [
    "DataService",
    "ModelService",
    "NLPService",
]