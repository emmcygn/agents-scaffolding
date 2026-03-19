"""CLI, JSON, and HTML report generation."""

from scaffolder.reporting.cli import render_benchmark, render_retrieval_table
from scaffolder.reporting.html import render_html_report
from scaffolder.reporting.json_export import export_json, load_json

__all__ = [
    "export_json",
    "load_json",
    "render_benchmark",
    "render_html_report",
    "render_retrieval_table",
]
