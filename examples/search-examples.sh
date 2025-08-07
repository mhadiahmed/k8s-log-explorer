#!/bin/bash

# Example searches for Kubernetes Log Explorer

echo "🔍 Kubernetes Log Explorer - Search Examples"
echo "============================================="

# Make sure the script is executable
chmod +x ../logexplorer.py

LOGEXPLORER="../logexplorer.py"

echo ""
echo "📋 Available namespaces:"
$LOGEXPLORER namespaces

echo ""
echo "📋 Pods in default namespace:"
$LOGEXPLORER pods

echo ""
echo "📋 Pods in kube-system namespace:"
$LOGEXPLORER -n kube-system pods

echo ""
echo "🔍 Example Searches:"
echo ""

# Replace 'your-pod-name' with an actual pod name from your cluster
POD_NAME="your-pod-name"

echo "1. Search for ERROR messages with context:"
echo "   $LOGEXPLORER search $POD_NAME \"ERROR\" --context 5"
echo ""

echo "2. Search for Java exceptions with stack trace grouping:"
echo "   $LOGEXPLORER search $POD_NAME \"Exception\" --java-stack"
echo ""

echo "3. Search for specific error patterns:"
echo "   $LOGEXPLORER search $POD_NAME \"NullPointerException\" --context 3"
echo ""

echo "4. Search recent logs (last 2 hours):"
echo "   $LOGEXPLORER search $POD_NAME \"WARN\" --since-hours 2"
echo ""

echo "5. Search with regex patterns:"
echo "   $LOGEXPLORER search $POD_NAME \"HTTP [45][0-9][0-9]\" --context 2"
echo ""

echo "6. Follow logs in real-time:"
echo "   $LOGEXPLORER follow $POD_NAME"
echo ""

echo "7. View recent logs:"
echo "   $LOGEXPLORER logs $POD_NAME --lines 50"
echo ""

echo "8. Search in specific container:"
echo "   $LOGEXPLORER search $POD_NAME \"ERROR\" --container app-container"
echo ""

echo "🗂️  Working with Different Namespaces:"
echo ""
echo "• List pods in production namespace:"
echo "  $LOGEXPLORER -n production pods"
echo ""
echo "• Search logs in staging namespace:"
echo "  $LOGEXPLORER -n staging search my-app \"ERROR\" --context 3"
echo ""
echo "• Follow logs in specific namespace:"
echo "  $LOGEXPLORER -n kube-system follow coredns-xxx"
echo ""

echo "📝 Common Java Spring Boot Error Patterns:"
echo ""
echo "• Search for Spring Boot startup issues:"
echo "  $LOGEXPLORER search $POD_NAME \"Failed to start\" --java-stack"
echo ""
echo "• Search for database connection errors:"
echo "  $LOGEXPLORER search $POD_NAME \"SQLException\" --java-stack"
echo ""
echo "• Search for HTTP request errors:"
echo "  $LOGEXPLORER search $POD_NAME \"HTTP.*[45][0-9][0-9]\" --context 3"
echo ""
echo "• Search for timeout issues:"
echo "  $LOGEXPLORER search $POD_NAME \"timeout\" --context 5"
echo ""

echo "🌐 Web Interface:"
echo "Start the web dashboard: python3 ../webapp.py"
echo "Then visit: http://localhost:5000"