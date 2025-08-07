# Kubernetes Log Explorer

A comprehensive tool for exploring and analyzing Kubernetes pod logs with advanced search capabilities, especially designed for multi-line errors like Java Spring Boot stack traces.

## 🚀 Features

- **Multi-line Error Detection**: Automatically groups related log lines (stack traces, error messages)
- **Advanced Search**: Search with context lines, regex patterns, and error-specific filters
- **CLI Tool**: Fast command-line interface for quick log analysis
- **Web Dashboard**: Rich web interface with real-time log streaming
- **Kubernetes Integration**: Direct integration with K8s API for live log streaming
- **Context-Aware Display**: Shows surrounding lines for better error understanding
- **Java Spring Boot Support**: Special handling for Java stack traces and Spring Boot error patterns
- **Real-time Streaming**: Follow logs as they happen with WebSocket support
- **Export Functionality**: Download logs for offline analysis

## 📦 Quick Start

### Installation

#### Option 1: Automated Installation
```bash
# Clone and install
git clone https://github.com/mhadiahmed/k8s-log-explorer k8s-log-explorer
cd k8s-log-explorer
./scripts/install.sh
```

#### Option 2: Manual Installation
```bash
pip install -r requirements.txt
chmod +x logexplorer.py
```

### CLI Usage

```bash
# List available namespaces
./logexplorer.py namespaces

# List all pods (default namespace)
./logexplorer.py pods

# List pods in specific namespace
./logexplorer.py -n kube-system pods

# Basic log viewing
./logexplorer.py logs <pod-name>

# Search for errors with context
./logexplorer.py search <pod-name> "ERROR" --context 5

# Search for Java exceptions with stack trace grouping
./logexplorer.py search <pod-name> "Exception" --java-stack

# Follow logs in real-time
./logexplorer.py follow <pod-name>

# Search recent logs (last 2 hours)
./logexplorer.py search <pod-name> "WARN" --since-hours 2

# Search in specific container
./logexplorer.py search <pod-name> "ERROR" --container app-container

# Work with different namespaces
./logexplorer.py -n production search my-app "ERROR" --context 3
./logexplorer.py -n staging logs my-app --lines 50
```

### Web Dashboard

```bash
python webapp.py
```

Then visit `http://localhost:5000`

## 🔍 Advanced Search Examples

### Java Spring Boot Errors
```bash
# Spring Boot startup issues
./logexplorer.py search my-app "Failed to start" --java-stack

# Database connection errors
./logexplorer.py search my-app "SQLException" --java-stack

# HTTP errors with context
./logexplorer.py search my-app "HTTP.*[45][0-9][0-9]" --context 3

# Memory issues
./logexplorer.py search my-app "OutOfMemoryError" --java-stack
```

### Regular Expression Patterns
```bash
# Search for HTTP status codes
./logexplorer.py search my-app "HTTP [45][0-9][0-9]" --context 2

# Search for timestamps
./logexplorer.py search my-app "\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}" --context 1

# Search for IP addresses
./logexplorer.py search my-app "\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b" --context 2
```

## ⚙️ Configuration

Create a `config.yaml` file:

```yaml
kubernetes:
  config_file: ~/.kube/config  # or null for in-cluster
  namespace: default

logging:
  level: INFO
  context_lines: 3
  max_lines: 1000

web:
  host: 0.0.0.0
  port: 5000
  debug: false

search:
  java_error_patterns:
    - "Exception"
    - "Error"
    - "Caused by"
    - "at\\s+[a-zA-Z0-9_$]+\\.[a-zA-Z0-9_$]+\\("
  
  context_patterns:
    - "\\d{4}-\\d{2}-\\d{2}\\s+\\d{2}:\\d{2}:\\d{2}"  # timestamp
    - "\\[.*?\\]"  # log levels in brackets
    - "ERROR|WARN|INFO|DEBUG|TRACE"  # log levels
```

## 🐳 Docker Deployment

### Build and Run Locally
```bash
./scripts/build-docker.sh
docker run -p 5000:5000 -v ~/.kube/config:/home/logexplorer/.kube/config:ro log-explorer:latest
```

### Docker Compose
```bash
docker-compose up -d
```

## ☸️ Kubernetes Deployment

### Deploy to Cluster
```bash
./scripts/deploy-k8s.sh
```

### Manual Deployment
```bash
kubectl apply -f k8s-deployment.yaml
kubectl port-forward service/log-explorer 8080:80 -n log-explorer
```

## 🌐 Web Interface Features

- **Real-time Log Streaming**: Live log updates with WebSocket
- **Interactive Search**: Advanced search with syntax highlighting
- **Pod Management**: Browse and select pods from a visual interface
- **Multi-container Support**: Handle pods with multiple containers
- **Export Logs**: Download logs for offline analysis
- **Responsive Design**: Works on desktop and mobile devices

## 🔧 Development

### Prerequisites
- Python 3.11+
- kubectl configured with cluster access
- Kubernetes cluster with RBAC permissions for pod logs

### Running in Development Mode
```bash
# CLI tool
python logexplorer.py --help

# Web dashboard with debug mode
python webapp.py
```

### Project Structure
```
k8s-log-explorer/
├── logexplorer.py          # CLI application
├── webapp.py               # Web dashboard
├── k8s_client.py          # Kubernetes integration
├── config.yaml            # Configuration
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container image
├── docker-compose.yml     # Local deployment
├── k8s-deployment.yaml    # Kubernetes manifests
├── templates/             # Web templates
├── static/               # CSS/JS assets
├── scripts/              # Installation scripts
└── examples/             # Usage examples
```