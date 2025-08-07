#!/usr/bin/env python3
"""
Kubernetes Log Explorer Web Dashboard
A web-based interface for exploring and analyzing Kubernetes pod logs.
"""
import json
import logging
import yaml
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading
import time

from k8s_client import K8sLogClient, LogProcessor

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global instances
k8s_client = None
log_processor = None
config = {}

# Active log streams
active_streams = {}


def init_app():
    """Initialize the application with configuration."""
    global k8s_client, log_processor, config
    
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        config = {"kubernetes": {"namespace": "default"}, "web": {"host": "0.0.0.0", "port": 5000}}
    
    k8s_client = K8sLogClient(
        config_file=config.get("kubernetes", {}).get("config_file"),
        namespace=config.get("kubernetes", {}).get("namespace", "default")
    )
    log_processor = LogProcessor()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, config.get("logging", {}).get("level", "INFO")),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/api/namespaces')
def api_namespaces():
    """API endpoint to get list of namespaces."""
    try:
        namespaces = k8s_client.list_namespaces()
        current_namespace = k8s_client.namespace
        return jsonify({
            "success": True, 
            "namespaces": namespaces, 
            "current": current_namespace
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/pods')
def api_pods():
    """API endpoint to get list of pods."""
    try:
        namespace = request.args.get('namespace', k8s_client.namespace)
        label_selector = request.args.get('selector')
        
        # Create a temporary client for different namespace if needed
        if namespace != k8s_client.namespace:
            temp_client = K8sLogClient(
                config_file=config.get("kubernetes", {}).get("config_file"),
                namespace=namespace
            )
            pods = temp_client.list_pods(label_selector)
        else:
            pods = k8s_client.list_pods(label_selector)
            
        return jsonify({"success": True, "pods": pods, "namespace": namespace})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/pods/<pod_name>/containers')
def api_pod_containers(pod_name):
    """API endpoint to get containers in a pod."""
    try:
        namespace = request.args.get('namespace', k8s_client.namespace)
        
        # Create a temporary client for different namespace if needed
        if namespace != k8s_client.namespace:
            temp_client = K8sLogClient(
                config_file=config.get("kubernetes", {}).get("config_file"),
                namespace=namespace
            )
            containers = temp_client.get_pod_containers(pod_name)
        else:
            containers = k8s_client.get_pod_containers(pod_name)
            
        return jsonify({"success": True, "containers": containers})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/pods/<pod_name>/logs')
def api_pod_logs(pod_name):
    """API endpoint to get pod logs."""
    try:
        namespace = request.args.get('namespace', k8s_client.namespace)
        container = request.args.get('container')
        lines = int(request.args.get('lines', 100))
        since_hours = request.args.get('since_hours')
        since_seconds = int(since_hours) * 3600 if since_hours else None
        
        # Create a temporary client for different namespace if needed
        if namespace != k8s_client.namespace:
            temp_client = K8sLogClient(
                config_file=config.get("kubernetes", {}).get("config_file"),
                namespace=namespace
            )
            logs = list(temp_client.get_pod_logs(
                pod_name=pod_name,
                container=container,
                lines=lines,
                since_seconds=since_seconds
            ))
        else:
            logs = list(k8s_client.get_pod_logs(
                pod_name=pod_name,
                container=container,
                lines=lines,
                since_seconds=since_seconds
            ))
        
        return jsonify({"success": True, "logs": logs})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/pods/<pod_name>/search')
def api_search_logs(pod_name):
    """API endpoint to search pod logs."""
    try:
        namespace = request.args.get('namespace', k8s_client.namespace)
        search_term = request.args.get('term', '')
        container = request.args.get('container')
        context_lines = int(request.args.get('context', 3))
        java_stack = request.args.get('java_stack', 'false').lower() == 'true'
        since_hours = request.args.get('since_hours')
        max_lines = int(request.args.get('max_lines', 1000))
        
        since_seconds = int(since_hours) * 3600 if since_hours else None
        
        # Create a temporary client for different namespace if needed
        if namespace != k8s_client.namespace:
            temp_client = K8sLogClient(
                config_file=config.get("kubernetes", {}).get("config_file"),
                namespace=namespace
            )
            log_lines = list(temp_client.get_pod_logs(
                pod_name=pod_name,
                container=container,
                lines=max_lines,
                since_seconds=since_seconds
            ))
        else:
            log_lines = list(k8s_client.get_pod_logs(
                pod_name=pod_name,
                container=container,
                lines=max_lines,
                since_seconds=since_seconds
            ))
        
        # Search with context
        matches = log_processor.search_with_context(
            log_lines, search_term, context_lines, java_stack
        )
        
        # Format matches for frontend
        formatted_matches = []
        for line_num, context in matches:
            formatted_matches.append({
                "line_number": line_num,
                "context": context,
                "match_line": line_num if not java_stack else None
            })
        
        return jsonify({
            "success": True,
            "matches": formatted_matches,
            "total_matches": len(matches),
            "search_term": search_term
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@socketio.on('start_log_stream')
def handle_start_log_stream(data):
    """Start streaming logs to the client."""
    pod_name = data.get('pod_name')
    container = data.get('container')
    namespace = data.get('namespace', k8s_client.namespace)
    room = f"logs_{namespace}_{pod_name}_{container or 'default'}"
    
    join_room(room)
    
    def stream_logs():
        try:
            # Create a temporary client for different namespace if needed
            if namespace != k8s_client.namespace:
                temp_client = K8sLogClient(
                    config_file=config.get("kubernetes", {}).get("config_file"),
                    namespace=namespace
                )
                log_stream = temp_client.get_pod_logs(pod_name, container, follow=True)
            else:
                log_stream = k8s_client.get_pod_logs(pod_name, container, follow=True)
            
            line_count = 0
            for line in log_stream:
                line_count += 1
                socketio.emit('log_line', {
                    'line': line,
                    'line_number': line_count,
                    'timestamp': datetime.now().isoformat(),
                    'pod_name': pod_name,
                    'container': container,
                    'namespace': namespace
                }, room=room)
                time.sleep(0.01)  # Small delay to prevent overwhelming the client
                
        except Exception as e:
            socketio.emit('log_error', {
                'error': str(e),
                'pod_name': pod_name,
                'namespace': namespace
            }, room=room)
    
    # Start streaming in a separate thread
    if room not in active_streams:
        active_streams[room] = True
        thread = threading.Thread(target=stream_logs)
        thread.daemon = True
        thread.start()
    
    emit('stream_started', {'room': room, 'pod_name': pod_name, 'namespace': namespace})


@socketio.on('stop_log_stream')
def handle_stop_log_stream(data):
    """Stop streaming logs."""
    pod_name = data.get('pod_name')
    container = data.get('container')
    namespace = data.get('namespace', k8s_client.namespace)
    room = f"logs_{namespace}_{pod_name}_{container or 'default'}"
    
    leave_room(room)
    if room in active_streams:
        del active_streams[room]
    
    emit('stream_stopped', {'room': room, 'pod_name': pod_name, 'namespace': namespace})


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    emit('connected', {'status': 'Connected to log explorer'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print('Client disconnected')


if __name__ == '__main__':
    init_app()
    
    host = config.get("web", {}).get("host", "0.0.0.0")
    port = config.get("web", {}).get("port", 5000)
    debug = config.get("web", {}).get("debug", False)
    
    print(f"Starting Kubernetes Log Explorer Web Dashboard on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=debug)