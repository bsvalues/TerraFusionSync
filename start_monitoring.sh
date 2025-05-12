#!/bin/bash

# Start the Prometheus and Grafana monitoring stack
echo "Starting TerraFusion Monitoring Stack..."

# Start Prometheus in the background
echo "Starting Prometheus..."
python run_prometheus.py &
PROMETHEUS_PID=$!
echo "Prometheus started with PID $PROMETHEUS_PID"

# Wait a moment for Prometheus to initialize
sleep 2

# Start Grafana in the background
echo "Starting Grafana..."
python run_grafana.py &
GRAFANA_PID=$!
echo "Grafana started with PID $GRAFANA_PID"

echo "Monitoring stack started successfully!"
echo "  Prometheus: http://localhost:9090"
echo "  Grafana:    http://localhost:3000 (admin/admin)"
echo ""
echo "Available dashboards:"
echo "  - TerraFusion SyncService Overview"
echo "  - TerraFusion Gateway Overview"
echo ""
echo "Press Ctrl+C to stop the monitoring stack"

# Handle shutdown gracefully
trap "echo 'Stopping monitoring stack...'; kill $PROMETHEUS_PID $GRAFANA_PID; exit" INT TERM

# Wait for Ctrl+C
wait