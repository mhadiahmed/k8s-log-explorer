#!/usr/bin/env python3
"""
Kubernetes Log Explorer CLI
A powerful command-line tool for exploring and analyzing Kubernetes pod logs.
"""
import click
import logging
import yaml
import sys
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.syntax import Syntax
from rich.live import Live
from rich.layout import Layout
from colorama import Fore, Back, Style, init

from k8s_client import K8sLogClient, LogProcessor

# Initialize colorama for cross-platform colored output
init(autoreset=True)

console = Console()


class LogExplorer:
    def __init__(self, config_path: str = "config.yaml", namespace_override: str = None):
        try:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            console.print(f"[red]Config file {config_path} not found. Using defaults.[/red]")
            self.config = {"kubernetes": {"namespace": "default"}, "logging": {"context_lines": 3}}
        
        # Use namespace override if provided, otherwise use config
        namespace = namespace_override or self.config.get("kubernetes", {}).get("namespace", "default")
        
        self.k8s_client = K8sLogClient(
            config_file=self.config.get("kubernetes", {}).get("config_file"),
            namespace=namespace
        )
        self.log_processor = LogProcessor(config_path)
        
        # Store current namespace for display
        self.current_namespace = namespace
        
        # Setup logging
        logging.basicConfig(
            level=getattr(logging, self.config.get("logging", {}).get("level", "INFO")),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def list_pods_table(self, label_selector: str = None):
        """Display pods in a nice table format."""
        try:
            pods = self.k8s_client.list_pods(label_selector)
            
            table = Table(title=f"Kubernetes Pods (namespace: {self.current_namespace})")
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Status", style="magenta")
            table.add_column("Ready", justify="center")
            table.add_column("Restarts", justify="center")
            table.add_column("Age", justify="right")
            
            for pod in pods:
                status_color = "green" if pod["status"] == "Running" else "red"
                ready_text = f"{pod['ready']}/{pod['total_containers']}"
                ready_color = "green" if pod['ready'] == pod['total_containers'] else "yellow"
                
                table.add_row(
                    pod["name"],
                    f"[{status_color}]{pod['status']}[/{status_color}]",
                    f"[{ready_color}]{ready_text}[/{ready_color}]",
                    str(pod["restart_count"]),
                    pod["age"]
                )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error listing pods: {e}[/red]")

    def display_log_line(self, line: str, line_number: int, highlight_terms: list = None):
        """Display a single log line with syntax highlighting."""
        # Detect log level and apply colors
        line_color = "white"
        if "ERROR" in line.upper():
            line_color = "red"
        elif "WARN" in line.upper():
            line_color = "yellow"
        elif "INFO" in line.upper():
            line_color = "green"
        elif "DEBUG" in line.upper():
            line_color = "blue"
        
        # Highlight search terms
        display_line = line
        if highlight_terms:
            for term in highlight_terms:
                display_line = display_line.replace(
                    term, f"[black on yellow]{term}[/black on yellow]"
                )
        
        console.print(f"[dim]{line_number:6d}[/dim] [{line_color}]{display_line}[/{line_color}]")

    def search_logs(self, pod_name: str, search_term: str, container: str = None,
                   context_lines: int = None, java_stack: bool = False,
                   since_hours: int = None, max_lines: int = 1000):
        """Search through pod logs with context."""
        try:
            context_lines = context_lines or self.config.get("logging", {}).get("context_lines", 3)
            since_seconds = since_hours * 3600 if since_hours else None
            
            console.print(f"[blue]Searching logs for pod '{pod_name}' with term '{search_term}'...[/blue]")
            
            # Get logs
            log_lines = list(self.k8s_client.get_pod_logs(
                pod_name=pod_name,
                container=container,
                lines=max_lines,
                since_seconds=since_seconds
            ))
            
            if not log_lines:
                console.print("[yellow]No logs found for the specified pod.[/yellow]")
                return
            
            # Search with context
            matches = self.log_processor.search_with_context(
                log_lines, search_term, context_lines, java_stack
            )
            
            if not matches:
                console.print(f"[yellow]No matches found for '{search_term}'[/yellow]")
                return
            
            console.print(f"[green]Found {len(matches)} matches:[/green]\n")
            
            for i, (line_num, context) in enumerate(matches):
                # Create a panel for each match
                panel_content = ""
                for j, line in enumerate(context):
                    if java_stack:
                        # For Java stack traces, highlight the entire group
                        line_style = "red" if any(term.lower() in line.lower() for term in [search_term]) else "white"
                        panel_content += f"{line_num + j + 1:6d} | {line}\n"
                    else:
                        # For regular search, highlight the matching line
                        actual_line_num = line_num - context_lines + j
                        if j == context_lines:  # This is the matching line
                            panel_content += f"[yellow]{actual_line_num + 1:6d} | {line}[/yellow]\n"
                        else:
                            panel_content += f"{actual_line_num + 1:6d} | {line}\n"
                
                panel = Panel(
                    panel_content.rstrip(),
                    title=f"Match {i+1} (Line {line_num + 1})",
                    border_style="blue"
                )
                console.print(panel)
                console.print()  # Add spacing between matches
                
        except Exception as e:
            console.print(f"[red]Error searching logs: {e}[/red]")

    def follow_logs(self, pod_name: str, container: str = None):
        """Follow logs in real-time."""
        try:
            console.print(f"[blue]Following logs for pod '{pod_name}'... (Press Ctrl+C to stop)[/blue]\n")
            
            line_count = 0
            for line in self.k8s_client.get_pod_logs(pod_name, container, follow=True):
                line_count += 1
                self.display_log_line(line, line_count)
                
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopped following logs.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error following logs: {e}[/red]")

    def show_logs(self, pod_name: str, container: str = None, lines: int = 100,
                  since_hours: int = None):
        """Display recent logs from a pod."""
        try:
            since_seconds = since_hours * 3600 if since_hours else None
            
            console.print(f"[blue]Showing last {lines} lines from pod '{pod_name}':[/blue]\n")
            
            line_count = 0
            for line in self.k8s_client.get_pod_logs(
                pod_name=pod_name,
                container=container,
                lines=lines,
                since_seconds=since_seconds
            ):
                line_count += 1
                self.display_log_line(line, line_count)
                
        except Exception as e:
            console.print(f"[red]Error showing logs: {e}[/red]")


# CLI Commands
@click.group()
@click.option('--config', default='config.yaml', help='Configuration file path')
@click.option('--namespace', '-n', help='Kubernetes namespace (overrides config)')
@click.pass_context
def cli(ctx, config, namespace):
    """Kubernetes Log Explorer - Advanced log analysis for K8s pods."""
    ctx.ensure_object(dict)
    ctx.obj['explorer'] = LogExplorer(config, namespace_override=namespace)


@cli.command()
@click.option('--selector', '-s', help='Label selector to filter pods')
def pods(selector):
    """List all pods in the namespace."""
    explorer = click.get_current_context().obj['explorer']
    explorer.list_pods_table(selector)


@cli.command()
@click.argument('pod_name')
@click.option('--container', '-c', help='Container name (if pod has multiple containers)')
@click.option('--lines', '-n', default=100, help='Number of lines to show')
@click.option('--since-hours', '-h', type=int, help='Show logs from last N hours')
def logs(pod_name, container, lines, since_hours):
    """Show logs from a pod."""
    explorer = click.get_current_context().obj['explorer']
    explorer.show_logs(pod_name, container, lines, since_hours)


@cli.command()
@click.argument('pod_name')
@click.argument('search_term')
@click.option('--container', '-c', help='Container name')
@click.option('--context', '-C', type=int, help='Lines of context around matches')
@click.option('--java-stack', is_flag=True, help='Enable Java stack trace grouping')
@click.option('--since-hours', '-h', type=int, help='Search logs from last N hours')
@click.option('--max-lines', '-m', default=1000, help='Maximum lines to search')
def search(pod_name, search_term, container, context, java_stack, since_hours, max_lines):
    """Search for a term in pod logs with context."""
    explorer = click.get_current_context().obj['explorer']
    explorer.search_logs(pod_name, search_term, container, context, java_stack, since_hours, max_lines)


@cli.command()
@click.argument('pod_name')
@click.option('--container', '-c', help='Container name')
def follow(pod_name, container):
    """Follow pod logs in real-time."""
    explorer = click.get_current_context().obj['explorer']
    explorer.follow_logs(pod_name, container)


@cli.command()
@click.argument('pod_name')
def containers(pod_name):
    """List containers in a pod."""
    explorer = click.get_current_context().obj['explorer']
    try:
        containers = explorer.k8s_client.get_pod_containers(pod_name)
        console.print(f"[blue]Containers in pod '{pod_name}':[/blue]")
        for container in containers:
            console.print(f"  • {container}")
    except Exception as e:
        console.print(f"[red]Error listing containers: {e}[/red]")


@cli.command()
def namespaces():
    """List available namespaces."""
    explorer = click.get_current_context().obj['explorer']
    try:
        # We need to add this method to the K8sLogClient
        namespaces = explorer.k8s_client.list_namespaces()
        console.print("[blue]Available namespaces:[/blue]")
        for ns in namespaces:
            if ns == explorer.current_namespace:
                console.print(f"  • [green]{ns}[/green] (current)")
            else:
                console.print(f"  • {ns}")
    except Exception as e:
        console.print(f"[red]Error listing namespaces: {e}[/red]")


if __name__ == '__main__':
    cli()