#!/bin/bash
# Script to run the isolated GIS Export API and test it

echo "Starting Isolated GIS Export API..."
python isolated_gis_export_test.py &
API_PID=$!

echo "Waiting for API to start..."
sleep 5

echo "Running tests against the API..."
python test_isolated_api.py

# Capture test result
TEST_RESULT=$?

echo "Cleaning up..."
kill $API_PID

echo "Tests completed with exit code $TEST_RESULT"
exit $TEST_RESULT