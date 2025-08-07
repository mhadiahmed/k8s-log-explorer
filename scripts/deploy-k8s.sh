#!/bin/bash

# Deploy Kubernetes Log Explorer to Kubernetes cluster

set -e

echo "🚢 Deploying Kubernetes Log Explorer to cluster..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is required but not installed."
    exit 1
fi

# Check kubectl connection
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ kubectl is not configured or cannot connect to cluster."
    exit 1
fi

# Deploy to cluster
echo "📋 Applying Kubernetes manifests..."
kubectl apply -f k8s-deployment.yaml

echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/log-explorer -n log-explorer

# Get service information
echo "📊 Deployment Status:"
kubectl get all -n log-explorer

echo ""
echo "🌐 Access Information:"
kubectl get ingress -n log-explorer

# Port forwarding option
echo ""
read -p "Set up port forwarding for local access? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔗 Setting up port forwarding..."
    echo "Access the application at: http://localhost:8080"
    echo "Press Ctrl+C to stop port forwarding"
    kubectl port-forward service/log-explorer 8080:80 -n log-explorer
fi

echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Useful commands:"
echo "  View logs: kubectl logs -f deployment/log-explorer -n log-explorer"
echo "  Delete: kubectl delete -f k8s-deployment.yaml"