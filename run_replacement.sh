#!/bin/bash
# Launch the BR SSS Teacher Replacement System
cd "$(dirname "$0")"
PYTHONPATH=".deps" python3 replacement_system/main.py
