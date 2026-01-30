"""
Port Management Utility for Zippy-Archon

Provides comprehensive port scanning, conflict detection, and dynamic port allocation
to ensure no port conflicts when launching multiple services.

Features:
- Port availability scanning
- Conflict detection and resolution
- Dynamic port allocation with fallback logic
- Integration with environment variables
- Docker port mapping support
"""

import socket
import subprocess
import os
import sys
import time
import json
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class PortConfig:
    """Configuration for a service port."""
    name: str
    default_port: int
    description: str
    required: bool = True
    host_only: bool = False  # True if only needs to be free on host, not in container


@dataclass
class PortAllocation:
    """Allocated port configuration."""
    service_name: str
    original_port: int
    allocated_port: int
    is_conflict: bool
    reason: str = ""


class PortScanner:
    """Port scanning and conflict detection utility."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

        # Define all service port configurations
        # Following Zippy-Archon port assignment rules (827 pattern)
        self.port_configs = {
            "ARCHON_SERVER_PORT": PortConfig(
                name="Main Server",
                default_port=8181,
                description="FastAPI server with Socket.IO"
            ),
            "ARCHON_MCP_PORT": PortConfig(
                name="MCP Server",
                default_port=8051,
                description="Model Context Protocol server"
            ),
            "ARCHON_AGENTS_PORT": PortConfig(
                name="AI Agents",
                default_port=8052,
                description="AI/ML agents service"
            ),
            "ARCHON_UI_PORT": PortConfig(
                name="Frontend UI",
                default_port=3737,
                description="React frontend application"
            ),
            "POSTGRES_PORT": PortConfig(
                name="PostgreSQL",
                default_port=5432,
                description="PostgreSQL database"
            ),
            "REDIS_PORT": PortConfig(
                name="Redis",
                default_port=6379,
                description="Redis cache server"
            ),
            "PROMETHEUS_PORT": PortConfig(
                name="Prometheus",
                default_port=9090,
                description="Prometheus monitoring"
            ),
            "GRAFANA_PORT": PortConfig(
                name="Grafana",
                default_port=3827,  # Changed from 3000 to avoid conflicts
                description="Grafana dashboards"
            ),
            "NGINX_PORT": PortConfig(
                name="Nginx",
                default_port=8280,  # Changed from 80 to avoid conflicts
                description="Nginx reverse proxy (HTTP)"
            ),
            "NGINX_SSL_PORT": PortConfig(
                name="Nginx SSL",
                default_port=8443,  # Changed from 443 to avoid conflicts
                description="Nginx reverse proxy (HTTPS)"
            )
        }

    def _setup_logging(self):
        """Set up logging for port management."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def is_port_in_use(self, port: int, host: str = 'localhost') -> bool:
        """Check if a port is in use on the specified host."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                return result == 0
        except socket.error:
            return False

    def is_port_in_use_by_process(self, port: int) -> Optional[Dict]:
        """Check what process is using a port and return process info."""
        try:
            # Use netstat to find process using the port
            if sys.platform == "win32":
                result = subprocess.run(
                    ['netstat', '-ano', '-p', 'tcp'],
                    capture_output=True, text=True, shell=True
                )
            else:
                result = subprocess.run(
                    ['netstat', '-tulpn'],
                    capture_output=True, text=True, shell=True
                )

            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if f":{port} " in line or f":{port}$" in line:
                        # Extract process info
                        parts = line.split()
                        if len(parts) >= 5:
                            process_info = {
                                'port': port,
                                'protocol': parts[0],
                                'local_address': parts[1],
                                'foreign_address': parts[2],
                                'state': parts[3] if len(parts) > 3 else 'UNKNOWN',
                                'pid': parts[-1] if len(parts) > 4 else 'UNKNOWN'
                            }
                            return process_info
        except Exception as e:
            self.logger.warning(f"Could not check process for port {port}: {e}")

        return None

    def find_available_port(self, start_port: int, exclude_ports: Set[int] = None) -> int:
        """Find the next available port starting from start_port."""
        if exclude_ports is None:
            exclude_ports = set()

        port = start_port
        max_attempts = 1000  # Prevent infinite loops

        while port in exclude_ports or self.is_port_in_use(port):
            port += 1
            max_attempts -= 1
            if max_attempts <= 0:
                raise RuntimeError(f"Could not find available port after {max_attempts} attempts")

        return port

    def scan_all_ports(self) -> Dict[str, PortAllocation]:
        """Scan all configured ports and detect conflicts."""
        allocations = {}
        exclude_ports = set()

        for env_var, config in self.port_configs.items():
            current_port = int(os.getenv(env_var, config.default_port))
            allocated_port = current_port

            # Check if port is in use
            if self.is_port_in_use(current_port):
                # Find available port
                try:
                    allocated_port = self.find_available_port(current_port + 1, exclude_ports)
                    exclude_ports.add(allocated_port)

                    # Get process info for the conflicting port
                    process_info = self.is_port_in_use_by_process(current_port)

                    allocations[env_var] = PortAllocation(
                        service_name=config.name,
                        original_port=current_port,
                        allocated_port=allocated_port,
                        is_conflict=True,
                        reason=f"Port {current_port} in use by {process_info.get('pid', 'unknown process') if process_info else 'unknown process'}"
                    )
                except RuntimeError as e:
                    self.logger.error(f"Could not allocate port for {config.name}: {e}")
                    allocations[env_var] = PortAllocation(
                        service_name=config.name,
                        original_port=current_port,
                        allocated_port=current_port,
                        is_conflict=True,
                        reason=f"Could not find available port: {e}"
                    )
            else:
                allocations[env_var] = PortAllocation(
                    service_name=config.name,
                    original_port=current_port,
                    allocated_port=allocated_port,
                    is_conflict=False
                )

        return allocations

    def generate_port_report(self, allocations: Dict[str, PortAllocation]) -> str:
        """Generate a detailed port allocation report."""
        report = []
        report.append("🔍 PORT ALLOCATION REPORT")
        report.append("=" * 50)

        conflicts = []
        for env_var, allocation in allocations.items():
            status = "❌ CONFLICT" if allocation.is_conflict else "✅ FREE"
            report.append(f"{allocation.service_name:<20} | {allocation.original_port:>5} -> {allocation.allocated_port:>5} | {status}")

            if allocation.is_conflict:
                conflicts.append(allocation)

        report.append("")
        report.append("📊 SUMMARY:")
        report.append(f"Total ports checked: {len(allocations)}")
        report.append(f"Conflicts detected: {len(conflicts)}")

        if conflicts:
            report.append("")
            report.append("🚨 CONFLICT DETAILS:")
            for conflict in conflicts:
                report.append(f"  {conflict.service_name}: Port {conflict.original_port} -> {conflict.allocated_port}")
                report.append(f"    Reason: {conflict.reason}")

        return "\n".join(report)

    def save_port_configuration(self, allocations: Dict[str, PortAllocation], config_file: str = None):
        """Save the port configuration to a file."""
        if config_file is None:
            # Default location in project root
            config_file = Path(__file__).parent.parent.parent.parent / ".zippy-archon-ports.json"

        config_data = {
            "generated_at": time.time(),
            "environment": os.environ.get("ENVIRONMENT", "development"),
            "allocations": {k: asdict(v) for k, v in allocations.items()}
        }

        try:
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            self.logger.info(f"Port configuration saved to {config_file}")
        except Exception as e:
            self.logger.error(f"Could not save port configuration: {e}")

    def load_port_configuration(self, config_file: str = None) -> Optional[Dict]:
        """Load port configuration from file."""
        if config_file is None:
            config_file = Path(__file__).parent.parent.parent.parent / ".zippy-archon-ports.json"

        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load port configuration: {e}")

        return None


class PortManager:
    """High-level port management interface."""

    def __init__(self):
        self.scanner = PortScanner()
        self.logger = logging.getLogger(__name__)

    def check_and_resolve_conflicts(self, auto_resolve: bool = True) -> Dict[str, PortAllocation]:
        """Check for port conflicts and optionally resolve them automatically."""
        self.logger.info("🔍 Scanning for port conflicts...")

        # Scan current port usage
        allocations = self.scanner.scan_all_ports()

        # Generate and display report
        report = self.scanner.generate_port_report(allocations)
        self.logger.info(f"\n{report}")

        # Check for conflicts
        conflicts = [a for a in allocations.values() if a.is_conflict]

        if conflicts and auto_resolve:
            self.logger.info("🔧 Resolving port conflicts...")

            # Update environment variables for conflicts
            for env_var, allocation in allocations.items():
                if allocation.is_conflict:
                    os.environ[env_var] = str(allocation.allocated_port)
                    self.logger.info(f"  {allocation.service_name}: {allocation.original_port} -> {allocation.allocated_port}")

            # Save configuration for future use
            self.scanner.save_port_configuration(allocations)

            self.logger.info("✅ Port conflicts resolved")
        elif conflicts:
            self.logger.warning(f"🚨 {len(conflicts)} port conflicts detected but not auto-resolved")
            if not auto_resolve:
                self.logger.info("Run with auto_resolve=True or manually set environment variables")

        return allocations

    def get_port_mapping(self) -> Dict[str, int]:
        """Get current port mapping from environment variables."""
        port_mapping = {}
        for env_var, config in self.scanner.port_configs.items():
            port_mapping[env_var] = int(os.getenv(env_var, config.default_port))
        return port_mapping

    def validate_ports(self) -> List[str]:
        """Validate that all required ports are properly configured."""
        issues = []

        for env_var, config in self.scanner.port_configs.items():
            port = os.getenv(env_var)
            if config.required and not port:
                issues.append(f"Required environment variable {env_var} is not set")
            elif port:
                try:
                    port_int = int(port)
                    if port_int < 1024 or port_int > 65535:
                        issues.append(f"Invalid port number for {env_var}: {port}")
                except ValueError:
                    issues.append(f"Invalid port number for {env_var}: {port}")

        return issues


# Global port manager instance
port_manager = PortManager()


def check_ports_before_launch(auto_resolve: bool = True) -> bool:
    """
    Main function to check ports before launching the application.

    Args:
        auto_resolve: Whether to automatically resolve conflicts by allocating new ports

    Returns:
        bool: True if ready to launch, False if conflicts exist and not resolved
    """
    print("🚀 Checking port availability before launch...")

    # Validate current port configuration
    issues = port_manager.validate_ports()
    if issues:
        print("❌ Port configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    # Check for conflicts and resolve if needed
    allocations = port_manager.check_and_resolve_conflicts(auto_resolve)

    # Check if there are still unresolved conflicts
    unresolved_conflicts = [a for a in allocations.values() if a.is_conflict]

    if unresolved_conflicts:
        print(f"❌ {len(unresolved_conflicts)} port conflicts could not be resolved:")
        for conflict in unresolved_conflicts:
            print(f"  - {conflict.service_name}: {conflict.reason}")
        return False

    print("✅ All ports are available and ready for launch!")
    return True


if __name__ == "__main__":
    # Command line interface for port management
    import argparse

    parser = argparse.ArgumentParser(description="Port management utility for Zippy-Archon")
    parser.add_argument("--check", action="store_true", help="Check port availability")
    parser.add_argument("--resolve", action="store_true", help="Automatically resolve conflicts")
    parser.add_argument("--report", action="store_true", help="Generate detailed port report")
    parser.add_argument("--config", type=str, help="Port configuration file")

    args = parser.parse_args()

    if args.check or args.resolve:
        success = check_ports_before_launch(auto_resolve=args.resolve)
        exit(0 if success else 1)
    elif args.report:
        allocations = port_manager.check_and_resolve_conflicts(auto_resolve=False)
        print(port_manager.scanner.generate_port_report(allocations))
    else:
        parser.print_help()
