"""Vercel entrypoint. Vercel's Python builder wants a serverless function
under api/ - this just re-exports the real app from backend/main.py so
there's exactly one copy of the actual logic, not a fork of it."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

from main import app  # noqa: E402
