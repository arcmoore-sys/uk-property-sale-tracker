#!/usr/bin/env python3
"""Produce the blank mandate-tracker template (seeded checklists, empty deal).
Run: python build_template.py  ->  mandate-tracker-template.xlsx
The plugin treats this as the file setup-deal copies into each deal folder.
The same builder is used live by ../shared/refresh_tracker.py.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "shared"))
from refresh_tracker import build
BLANK = {"deal":{},"buyers":[],"bids":[],"dataroom":[],"tasks":[],"legals":[],"reporting":[],
         "preferred_bidder":{}}
out = os.path.join(os.path.dirname(__file__), "mandate-tracker-template.xlsx")
build(BLANK).save(out)
print("built", out)
