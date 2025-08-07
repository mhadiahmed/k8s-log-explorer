"""
Kubernetes client for log streaming and pod management.
"""
import logging
import re
import yaml
from datetime import datetime, timedelta
from typing import Generator, List, Dict, Optional, Tuple
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException


class K8sLogClient:
    def __init__(self, config_file: Optional[str] = None, namespace: str = "default"):
        """Initialize Kubernetes client."""
        self.namespace = namespace
        self.logger = logging.getLogger(__name__)
        
        try:
            if config_file:
                config.load_kube_config(config_file=config_file)
            else:
                # Try in-cluster config first, then local config
                try:
                    config.load_incluster_config()
                    self.logger.info("Loaded in-cluster Kubernetes config")
                except:
                    config.load_kube_config()
                    self.logger.info("Loaded local Kubernetes config")
            
            self.v1 = client.CoreV1Api()
            self.logger.info(f"Connected to Kubernetes cluster, namespace: {namespace}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    def list_pods(self, label_selector: Optional[str] = None) -> List[Dict]:
        """List pods in the namespace."""
        try:
            pods = self.v1.list_namespaced_pod(
                namespace=self.namespace,
                label_selector=label_selector
            )
            
            pod_list = []
            for pod in pods.items:
                pod_info = {
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "ready": sum(1 for c in (pod.status.container_statuses or []) if c.ready),
                    "total_containers": len(pod.spec.containers),
                    "restart_count": sum(c.restart_count for c in (pod.status.container_statuses or [])),
                    "age": self._calculate_age(pod.metadata.creation_timestamp),
                    "labels": pod.metadata.labels or {}
                }
                pod_list.append(pod_info)
            
            return pod_list
            
        except ApiException as e:
            self.logger.error(f"Failed to list pods: {e}")
            raise

    def get_pod_logs(self, pod_name: str, container: Optional[str] = None, 
                     lines: Optional[int] = None, since_seconds: Optional[int] = None,
                     follow: bool = False) -> Generator[str, None, None]:
        """Get logs from a pod."""
        try:
            if follow:
                # Stream logs in real-time
                w = watch.Watch()
                for line in w.stream(
                    self.v1.read_namespaced_pod_log,
                    name=pod_name,
                    namespace=self.namespace,
                    container=container,
                    follow=True,
                    tail_lines=lines,
                    since_seconds=since_seconds
                ):
                    yield line
            else:
                # Get historical logs
                log_response = self.v1.read_namespaced_pod_log(
                    name=pod_name,
                    namespace=self.namespace,
                    container=container,
                    tail_lines=lines,
                    since_seconds=since_seconds
                )
                
                for line in log_response.split('\n'):
                    if line.strip():
                        yield line
                        
        except ApiException as e:
            self.logger.error(f"Failed to get logs for pod {pod_name}: {e}")
            raise

    def get_pod_containers(self, pod_name: str) -> List[str]:
        """Get list of containers in a pod."""
        try:
            pod = self.v1.read_namespaced_pod(name=pod_name, namespace=self.namespace)
            return [container.name for container in pod.spec.containers]
        except ApiException as e:
            self.logger.error(f"Failed to get containers for pod {pod_name}: {e}")
            raise

    def list_namespaces(self) -> List[str]:
        """List all namespaces in the cluster."""
        try:
            namespaces = self.v1.list_namespace()
            return [ns.metadata.name for ns in namespaces.items]
        except ApiException as e:
            self.logger.error(f"Failed to list namespaces: {e}")
            raise

    def _calculate_age(self, creation_timestamp: datetime) -> str:
        """Calculate pod age from creation timestamp."""
        if not creation_timestamp:
            return "Unknown"
        
        age = datetime.now(creation_timestamp.tzinfo) - creation_timestamp
        
        if age.days > 0:
            return f"{age.days}d"
        elif age.seconds > 3600:
            return f"{age.seconds // 3600}h"
        elif age.seconds > 60:
            return f"{age.seconds // 60}m"
        else:
            return f"{age.seconds}s"


class LogProcessor:
    """Process and analyze log lines for better error detection."""
    
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.java_patterns = [
            re.compile(pattern) for pattern in 
            self.config.get('search', {}).get('java_error_patterns', [])
        ]
        
        self.context_patterns = [
            re.compile(pattern) for pattern in
            self.config.get('search', {}).get('context_patterns', [])
        ]
    
    def is_java_stacktrace_line(self, line: str) -> bool:
        """Check if line is part of a Java stack trace."""
        return any(pattern.search(line) for pattern in self.java_patterns)
    
    def is_log_line_start(self, line: str) -> bool:
        """Check if line starts a new log entry."""
        return any(pattern.search(line) for pattern in self.context_patterns)
    
    def group_multiline_logs(self, log_lines: List[str]) -> List[List[str]]:
        """Group related log lines together (especially for stack traces)."""
        if not log_lines:
            return []
        
        groups = []
        current_group = [log_lines[0]]
        
        for line in log_lines[1:]:
            # If this looks like the start of a new log entry
            if self.is_log_line_start(line) and not self.is_java_stacktrace_line(line):
                # Save current group and start new one
                groups.append(current_group)
                current_group = [line]
            else:
                # Add to current group
                current_group.append(line)
        
        # Don't forget the last group
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def search_with_context(self, log_lines: List[str], search_term: str, 
                          context_lines: int = 3, java_stack: bool = False) -> List[Tuple[int, List[str]]]:
        """Search for term in logs and return matches with context."""
        matches = []
        search_pattern = re.compile(search_term, re.IGNORECASE)
        
        if java_stack:
            # Group lines first for Java stack trace context
            grouped_lines = self.group_multiline_logs(log_lines)
            flat_index = 0
            
            for group in grouped_lines:
                group_has_match = any(search_pattern.search(line) for line in group)
                if group_has_match:
                    # Find the exact line number in the original list
                    for i, line in enumerate(group):
                        if search_pattern.search(line):
                            matches.append((flat_index + i, group))
                            break
                flat_index += len(group)
        else:
            # Regular context-based search
            for i, line in enumerate(log_lines):
                if search_pattern.search(line):
                    start_idx = max(0, i - context_lines)
                    end_idx = min(len(log_lines), i + context_lines + 1)
                    context = log_lines[start_idx:end_idx]
                    matches.append((i, context))
        
        return matches