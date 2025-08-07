# Kubernetes Log Explorer - Usage Guide

A complete guide on how to use the Kubernetes Log Explorer CLI tool for debugging and log analysis.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Basic Commands](#basic-commands)
3. [Error Debugging Workflows](#error-debugging-workflows)
4. [Advanced Search Techniques](#advanced-search-techniques)
5. [Java Spring Boot Debugging](#java-spring-boot-debugging)
6. [Real-time Log Monitoring](#real-time-log-monitoring)
7. [Common Use Cases](#common-use-cases)
8. [Tips and Best Practices](#tips-and-best-practices)

## 🚀 Quick Start

### Prerequisites
- Kubernetes cluster access
- `kubectl` configured
- Virtual environment activated

```bash
# Navigate to the project
cd k8s-log-explorer
source .venv/bin/activate

# Make the tool executable
chmod +x logexplorer.py
```

### Basic Usage Pattern
```bash
# 1. Discover namespaces
python logexplorer.py namespaces

# 2. List pods in a namespace
python logexplorer.py -n <namespace> pods

# 3. View/search logs
python logexplorer.py -n <namespace> logs <pod-name>
python logexplorer.py -n <namespace> search <pod-name> "ERROR"
```

## 📊 Basic Commands

### 1. Namespace Discovery
```bash
# List all available namespaces
python logexplorer.py namespaces

# Expected output:
# Available namespaces:
#   • cert-manager
#   • default (current)
#   • kube-system
#   • production
#   • staging
```

### 2. Pod Management
```bash
# List pods in default namespace
python logexplorer.py pods

# List pods in specific namespace
python logexplorer.py -n production pods
python logexplorer.py -n kube-system pods

# Filter pods (use with grep)
python logexplorer.py -n production pods | grep "my-app"
```

### 3. Container Information
```bash
# List containers in a pod
python logexplorer.py -n production containers my-app-pod-123

# Expected output:
# Containers in pod 'my-app-pod-123':
#   • app-container
#   • sidecar-container
#   • init-container
```

### 4. Basic Log Viewing
```bash
# View last 100 lines (default)
python logexplorer.py -n production logs my-app-pod-123

# View last 50 lines
python logexplorer.py -n production logs my-app-pod-123 --lines 50

# View logs from last 2 hours
python logexplorer.py -n production logs my-app-pod-123 --since-hours 2

# View logs from specific container
python logexplorer.py -n production logs my-app-pod-123 --container app-container
```

## 🔍 Error Debugging Workflows

### Quick Error Check
```bash
# 1. Check for any errors in the last hour
python logexplorer.py -n production search my-app-pod "ERROR" --since-hours 1 --context 3

# 2. Check for warnings
python logexplorer.py -n production search my-app-pod "WARN" --context 2

# 3. Check for exceptions
python logexplorer.py -n production search my-app-pod "Exception" --java-stack
```

### Deep Debugging Session
```bash
# Step 1: Get pod overview
python logexplorer.py -n production pods | grep my-app

# Step 2: Check recent errors with context
python logexplorer.py -n production search my-app-pod-123 "ERROR\|FATAL" --context 5 --since-hours 24

# Step 3: Look for specific error patterns
python logexplorer.py -n production search my-app-pod-123 "Failed to" --context 3

# Step 4: Check application startup
python logexplorer.py -n production search my-app-pod-123 "Started\|Stopped" --context 2
```

### Database Issues
```bash
# Check for database connection errors
python logexplorer.py -n production search my-app-pod "SQLException\|Connection refused\|Timeout" --java-stack --context 5

# Check for specific database errors
python logexplorer.py -n production search my-app-pod "deadlock\|constraint\|duplicate key" --context 3
```

## 🔧 Advanced Search Techniques

### 1. Context-Aware Searching
```bash
# Show 5 lines before and after each match
python logexplorer.py -n production search my-app-pod "ERROR" --context 5

# Show 10 lines of context for complex debugging
python logexplorer.py -n production search my-app-pod "OutOfMemoryError" --context 10
```

### 2. Time-Based Searching
```bash
# Search logs from last 30 minutes
python logexplorer.py -n production search my-app-pod "ERROR" --since-hours 0.5

# Search logs from last 6 hours
python logexplorer.py -n production search my-app-pod "ERROR" --since-hours 6

# Search large number of lines
python logexplorer.py -n production search my-app-pod "ERROR" --max-lines 5000
```

### 3. Regular Expression Patterns
```bash
# Search for HTTP error status codes
python logexplorer.py -n production search my-app-pod "HTTP.*[45][0-9][0-9]" --context 3

# Search for timestamp patterns
python logexplorer.py -n production search my-app-pod "\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}" --context 1

# Search for IP addresses
python logexplorer.py -n production search my-app-pod "\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b" --context 2

# Search for memory/CPU issues
python logexplorer.py -n production search my-app-pod "OutOfMemory\|CPU\|memory" --context 4
```

### 4. Multi-Container Pod Debugging
```bash
# Check logs from specific container
python logexplorer.py -n production search my-app-pod "ERROR" --container app-container --context 3

# Compare logs between containers
python logexplorer.py -n production logs my-app-pod --container app-container --lines 50 > app.log
python logexplorer.py -n production logs my-app-pod --container sidecar --lines 50 > sidecar.log
```

## ☕ Java Spring Boot Debugging

### Spring Boot Startup Issues
```bash
# Check application startup
python logexplorer.py -n production search my-spring-app "Started.*Application\|Failed to start" --java-stack --context 5

# Check configuration issues
python logexplorer.py -n production search my-spring-app "ConfigurationException\|PropertyException" --java-stack

# Check bean creation failures
python logexplorer.py -n production search my-spring-app "BeanCreationException\|NoSuchBeanDefinitionException" --java-stack
```

### Common Spring Boot Errors
```bash
# Database connection issues
python logexplorer.py -n production search my-spring-app "SQLException\|DataAccessException\|HikariPool" --java-stack --context 5

# Security/Authentication issues
python logexplorer.py -n production search my-spring-app "AuthenticationException\|AccessDeniedException" --java-stack --context 3

# HTTP/REST API errors
python logexplorer.py -n production search my-spring-app "HTTP.*[45][0-9][0-9]\|RestClientException" --context 4

# Transaction issues
python logexplorer.py -n production search my-spring-app "TransactionException\|rollback\|commit failed" --java-stack

# Memory and performance issues
python logexplorer.py -n production search my-spring-app "OutOfMemoryError\|GC overhead\|heap space" --java-stack --context 10
```

### Spring Boot Stack Trace Analysis
```bash
# Get complete stack traces for exceptions
python logexplorer.py -n production search my-spring-app "Exception" --java-stack --context 0

# Look for "Caused by" chains
python logexplorer.py -n production search my-spring-app "Caused by" --java-stack --context 2

# Find root cause exceptions
python logexplorer.py -n production search my-spring-app "Root cause" --java-stack --context 5
```

## 📡 Real-time Log Monitoring

### Follow Logs in Real-time
```bash
# Follow logs from a pod (like tail -f)
python logexplorer.py -n production follow my-app-pod

# Follow logs from specific container
python logexplorer.py -n production follow my-app-pod --container app-container

# Stop following: Press Ctrl+C
```

### Monitoring Workflows
```bash
# Terminal 1: Follow application logs
python logexplorer.py -n production follow my-app-pod

# Terminal 2: Follow error logs only (using grep)
python logexplorer.py -n production follow my-app-pod | grep -i "error\|exception\|fatal"

# Terminal 3: Monitor specific patterns
python logexplorer.py -n production follow my-app-pod | grep -E "HTTP [45][0-9][0-9]|Exception|Error"
```

## 🎯 Common Use Cases

### 1. Application Not Starting
```bash
# Check recent startup attempts
python logexplorer.py -n production search my-app-pod "Starting\|Started\|Failed" --context 5 --since-hours 1

# Look for configuration errors
python logexplorer.py -n production search my-app-pod "Configuration\|Property\|Setting" --context 3

# Check port binding issues
python logexplorer.py -n production search my-app-pod "port.*in use\|bind\|address already" --context 3
```

### 2. Performance Issues
```bash
# Check for timeout errors
python logexplorer.py -n production search my-app-pod "timeout\|slow\|performance" --context 4

# Look for memory issues
python logexplorer.py -n production search my-app-pod "memory\|heap\|GC\|OutOfMemory" --context 5

# Check database performance
python logexplorer.py -n production search my-app-pod "slow query\|deadlock\|connection pool" --context 4
```

### 3. Integration Issues
```bash
# Check external service calls
python logexplorer.py -n production search my-app-pod "HTTP.*[45][0-9][0-9]\|connection refused\|timeout" --context 3

# Look for API errors
python logexplorer.py -n production search my-app-pod "RestTemplate\|WebClient\|API.*error" --context 4

# Check message queue issues
python logexplorer.py -n production search my-app-pod "queue\|message.*failed\|consumer" --context 3
```

### 4. Security Issues
```bash
# Check authentication failures
python logexplorer.py -n production search my-app-pod "authentication.*failed\|unauthorized\|forbidden" --context 3

# Look for suspicious activity
python logexplorer.py -n production search my-app-pod "suspicious\|blocked\|denied" --context 2

# Check SSL/TLS issues
python logexplorer.py -n production search my-app-pod "SSL\|TLS\|certificate\|handshake" --context 4
```

## 💡 Tips and Best Practices

### 1. Efficient Searching
```bash
# Use specific namespaces to narrow search scope
python logexplorer.py -n production search my-app "ERROR"  # Better than searching all namespaces

# Combine multiple error patterns
python logexplorer.py -n production search my-app "ERROR\|FATAL\|Exception" --context 3

# Use time bounds for recent issues
python logexplorer.py -n production search my-app "ERROR" --since-hours 2
```

### 2. Java Applications
```bash
# Always use --java-stack for Java applications
python logexplorer.py -n production search my-spring-app "Exception" --java-stack

# Look for the root cause in exception chains
python logexplorer.py -n production search my-spring-app "Caused by" --java-stack --context 1
```

### 3. Log Analysis Workflow
```bash
# 1. Quick health check
python logexplorer.py -n production pods | grep my-app

# 2. Recent error overview
python logexplorer.py -n production search my-app-pod "ERROR\|FATAL" --since-hours 1 --context 2

# 3. Deep dive into specific issues
python logexplorer.py -n production search my-app-pod "specific-error-pattern" --java-stack --context 5

# 4. Monitor in real-time if needed
python logexplorer.py -n production follow my-app-pod
```

### 4. Combining with Other Tools
```bash
# Save logs for analysis
python logexplorer.py -n production logs my-app-pod --lines 1000 > app-logs.txt

# Count error occurrences
python logexplorer.py -n production search my-app-pod "ERROR" --context 0 | grep -c "ERROR"

# Extract specific information
python logexplorer.py -n production search my-app-pod "user.*login" --context 1 | grep -o "user=[^,]*"
```

### 5. Troubleshooting Multiple Pods
```bash
# Check all pods with same prefix
for pod in $(python logexplorer.py -n production pods | grep "my-app" | awk '{print $1}'); do
  echo "=== Checking $pod ==="
  python logexplorer.py -n production search $pod "ERROR" --context 2 --since-hours 1
done
```

## 🔧 Configuration Tips

### Custom Configuration
```bash
# Use custom config file
python logexplorer.py --config /path/to/custom-config.yaml pods

# Override namespace in config
python logexplorer.py -n staging search my-app "ERROR"  # Overrides default namespace
```

### Performance Optimization
```bash
# Limit search scope for faster results
python logexplorer.py search my-app "ERROR" --max-lines 500 --since-hours 1

# Use specific containers to reduce noise
python logexplorer.py search my-app "ERROR" --container main-container
```

## 🆘 Emergency Debugging Checklist

When something is broken in production:

1. **Quick Assessment**:
   ```bash
   python logexplorer.py -n production pods | grep my-app
   ```

2. **Recent Errors**:
   ```bash
   python logexplorer.py -n production search my-app-pod "ERROR\|FATAL" --since-hours 0.5 --context 3
   ```

3. **Application Status**:
   ```bash
   python logexplorer.py -n production search my-app-pod "Started\|Stopped\|Shutdown" --context 2
   ```

4. **Real-time Monitoring**:
   ```bash
   python logexplorer.py -n production follow my-app-pod | grep -E "ERROR|FATAL|Exception"
   ```

5. **Java Stack Traces**:
   ```bash
   python logexplorer.py -n production search my-app-pod "Exception" --java-stack --since-hours 1
   ```

---

## 📚 Additional Resources

- **Web Dashboard**: Start with `python webapp.py` and visit `http://localhost:5000`
- **Configuration**: Edit `config.yaml` for default settings
- **Examples**: Run `./examples/search-examples.sh` for more examples

For more advanced usage and deployment options, see the main [README.md](README.md).