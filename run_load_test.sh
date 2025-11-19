#!/bin/bash
# Quick script to run load tests from project root

# Navigate to project root
cd "$(dirname "$0")"

# Activate venv_fixed
source venv_fixed/bin/activate

# Run locust
locust -f load_tests/voting_load_test.py --host=http://localhost:8001 "$@"
