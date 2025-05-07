#!/usr/bin/env python3
"""
TerraFusion CLI - A unified command-line tool for managing TerraFusion deployments

This CLI tool provides a single interface for all deployment, operations, and
maintenance tasks for the TerraFusion SyncService Platform.
"""

import argparse
import sys
import os
import logging
import json
import subprocess
import time
from datetime import datetime
import platform
import shutil
from typing import Dict, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("terrafusion-cli")

# Constants
VERSION = "1.0.0"
DEFAULT_CONFIG_PATH = os.path.expanduser("~/.terrafusion/config.json")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class TerraFusionCLI:
    """Main CLI class for the TerraFusion platform."""

    def __init__(self):
        """Initialize the CLI with configuration."""
        self.config = self._load_config()
        self._check_dependencies()

    def _load_config(self) -> Dict:
        """Load configuration from file or create default."""
        if os.path.exists(DEFAULT_CONFIG_PATH):
            try:
                with open(DEFAULT_CONFIG_PATH, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Error loading config file at {DEFAULT_CONFIG_PATH}")
                return self._create_default_config()
        else:
            return self._create_default_config()

    def _create_default_config(self) -> Dict:
        """Create and save default configuration."""
        default_config = {
            "kube_context": "default",
            "environments": {
                "dev": {
                    "namespace": "terrafusion-dev",
                    "domain": "dev.terrafusion.example.com",
                },
                "stage": {
                    "namespace": "terrafusion-stage",
                    "domain": "stage.terrafusion.example.com",
                },
                "prod": {
                    "namespace": "terrafusion-prod",
                    "domain": "terrafusion.example.com",
                },
            },
            "registry": "docker.io/terrafusion",
            "git_repo": "https://github.com/example/terrafusion-gitops.git",
            "git_branch": "main",
        }

        # Ensure directory exists
        os.makedirs(os.path.dirname(DEFAULT_CONFIG_PATH), exist_ok=True)

        # Save default config
        with open(DEFAULT_CONFIG_PATH, "w") as f:
            json.dump(default_config, f, indent=2)

        return default_config

    def _check_dependencies(self):
        """Check for required dependencies."""
        required_tools = ["kubectl", "kustomize", "git", "docker"]
        missing_tools = []

        for tool in required_tools:
            if not shutil.which(tool):
                missing_tools.append(tool)

        if missing_tools:
            logger.warning(
                f"Missing required tools: {', '.join(missing_tools)}. "
                "Some functionality may be limited."
            )

    def run(self):
        """Parse arguments and run the CLI."""
        parser = argparse.ArgumentParser(
            description="TerraFusion CLI - Unified management for TerraFusion platform"
        )
        parser.add_argument(
            "--version", action="version", version=f"TerraFusion CLI v{VERSION}"
        )
        parser.add_argument(
            "-v", "--verbose", action="store_true", help="Enable verbose output"
        )

        subparsers = parser.add_subparsers(dest="command", help="Command to execute")

        # Configure command
        config_parser = subparsers.add_parser("config", help="Configure the CLI")
        config_subparsers = config_parser.add_subparsers(
            dest="config_command", help="Configuration command"
        )

        # View config
        config_view = config_subparsers.add_parser("view", help="View current configuration")

        # Set config
        config_set = config_subparsers.add_parser("set", help="Set a configuration value")
        config_set.add_argument("key", help="Configuration key to set")
        config_set.add_argument("value", help="Configuration value")

        # Deploy command
        deploy_parser = subparsers.add_parser("deploy", help="Deploy TerraFusion")
        deploy_parser.add_argument(
            "-e", "--environment", choices=["dev", "stage", "prod"], default="dev",
            help="Target environment"
        )
        deploy_parser.add_argument(
            "--version", dest="app_version", help="Version to deploy"
        )
        deploy_parser.add_argument(
            "--component", choices=["api-gateway", "sync-service", "websocket", "all"],
            default="all", help="Component to deploy"
        )
        deploy_parser.add_argument(
            "--dry-run", action="store_true", help="Perform a dry run without changes"
        )
        deploy_parser.add_argument(
            "--blue-green", action="store_true", 
            help="Use blue-green deployment strategy (requires prod environment)"
        )

        # Rollback command
        rollback_parser = subparsers.add_parser("rollback", help="Rollback a deployment")
        rollback_parser.add_argument(
            "-e", "--environment", choices=["dev", "stage", "prod"], default="prod",
            help="Target environment"
        )
        rollback_parser.add_argument(
            "--component", choices=["api-gateway", "sync-service", "websocket", "all"],
            default="all", help="Component to rollback"
        )
        rollback_parser.add_argument(
            "--revision", help="Revision to rollback to (default: previous)"
        )

        # Status command
        status_parser = subparsers.add_parser("status", help="Check deployment status")
        status_parser.add_argument(
            "-e", "--environment", choices=["dev", "stage", "prod"], default="dev",
            help="Target environment"
        )
        status_parser.add_argument(
            "--detailed", action="store_true", help="Show detailed status"
        )

        # Health command
        health_parser = subparsers.add_parser("health", help="Check system health")
        health_parser.add_argument(
            "-e", "--environment", choices=["dev", "stage", "prod"], default="dev",
            help="Target environment"
        )
        health_parser.add_argument(
            "--component", choices=["api-gateway", "sync-service", "websocket", "all"],
            default="all", help="Component to check"
        )

        # Logs command
        logs_parser = subparsers.add_parser("logs", help="View component logs")
        logs_parser.add_argument(
            "-e", "--environment", choices=["dev", "stage", "prod"], default="dev",
            help="Target environment"
        )
        logs_parser.add_argument(
            "--component", choices=["api-gateway", "sync-service", "websocket"],
            required=True, help="Component to view logs for"
        )
        logs_parser.add_argument(
            "--tail", type=int, default=100, help="Number of lines to show"
        )
        logs_parser.add_argument(
            "--follow", action="store_true", help="Follow log output"
        )

        # GitOps command
        gitops_parser = subparsers.add_parser("gitops", help="GitOps operations")
        gitops_subparsers = gitops_parser.add_subparsers(
            dest="gitops_command", help="GitOps command"
        )

        # GitOps sync
        gitops_sync = gitops_subparsers.add_parser("sync", help="Sync with GitOps repository")
        gitops_sync.add_argument(
            "-e", "--environment", choices=["dev", "stage", "prod"], default="dev",
            help="Target environment"
        )
        gitops_sync.add_argument(
            "--repo", help="Git repository URL (overrides config)"
        )
        gitops_sync.add_argument(
            "--branch", help="Git branch (overrides config)"
        )
        gitops_sync.add_argument(
            "--dry-run", action="store_true", help="Perform a dry run without changes"
        )

        # Build command
        build_parser = subparsers.add_parser("build", help="Build container images")
        build_parser.add_argument(
            "--component", choices=["api-gateway", "sync-service", "websocket", "all"],
            default="all", help="Component to build"
        )
        build_parser.add_argument(
            "-t", "--tag", default="latest", help="Image tag"
        )
        build_parser.add_argument(
            "--push", action="store_true", help="Push images after building"
        )

        args = parser.parse_args()

        if args.verbose:
            logger.setLevel(logging.DEBUG)

        # Execute the command
        if not args.command:
            parser.print_help()
            return

        # Set up command dispatch
        command_dispatch = {
            "config": self._handle_config,
            "deploy": self._handle_deploy,
            "rollback": self._handle_rollback,
            "status": self._handle_status,
            "health": self._handle_health,
            "logs": self._handle_logs,
            "gitops": self._handle_gitops,
            "build": self._handle_build,
        }

        # Dispatch to the appropriate handler
        if args.command in command_dispatch:
            command_dispatch[args.command](args)
        else:
            parser.print_help()

    def _handle_config(self, args):
        """Handle config subcommands."""
        if not hasattr(args, "config_command") or not args.config_command:
            print("Current configuration:")
            self._print_config()
            return

        if args.config_command == "view":
            self._print_config()
        elif args.config_command == "set":
            self._set_config(args.key, args.value)
        else:
            print(f"Unknown config command: {args.config_command}")

    def _print_config(self):
        """Print current configuration in a readable format."""
        print(json.dumps(self.config, indent=2))

    def _set_config(self, key, value):
        """Set a configuration value."""
        # Handle nested keys like "environments.dev.namespace"
        keys = key.split(".")
        config_ref = self.config

        # Navigate to the correct nesting level
        for k in keys[:-1]:
            if k not in config_ref:
                config_ref[k] = {}
            config_ref = config_ref[k]

        # Set the value
        config_ref[keys[-1]] = value
        logger.info(f"Set config {key} = {value}")

        # Save the updated config
        with open(DEFAULT_CONFIG_PATH, "w") as f:
            json.dump(self.config, f, indent=2)

    def _handle_deploy(self, args):
        """Handle deploy command."""
        logger.info(f"Deploying to {args.environment} environment")
        
        # Validate blue-green deployment can only be used with prod
        if args.blue_green and args.environment != "prod":
            logger.error("Blue-green deployment can only be used with prod environment")
            return
        
        if args.blue_green:
            # Use the blue-green deployment script
            self._run_blue_green_deploy(args)
        else:
            # Use direct kustomize deployment
            self._run_kustomize_deploy(args)

    def _run_blue_green_deploy(self, args):
        """Run blue-green deployment using the script."""
        script_path = os.path.join(SCRIPT_DIR, "scripts", "blue-green-deploy.sh")
        
        if not os.path.exists(script_path):
            logger.error(f"Blue-green deployment script not found at {script_path}")
            return
        
        # Build command line arguments
        cmd = [
            script_path,
            "--namespace", self.config["environments"]["prod"]["namespace"],
        ]
        
        if args.app_version:
            cmd.extend(["--version", args.app_version])
            
        if args.component != "all":
            cmd.extend(["--component", args.component])
            
        # Execute the script
        logger.debug(f"Executing command: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
            logger.info("Blue-green deployment completed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Blue-green deployment failed: {e}")

    def _run_kustomize_deploy(self, args):
        """Run direct kustomize deployment."""
        env_path = os.path.join(SCRIPT_DIR, "kubernetes", "overlays", args.environment)
        
        if not os.path.exists(env_path):
            logger.error(f"Environment overlay not found at {env_path}")
            return
        
        # Build command
        if args.dry_run:
            # Just show what would be applied
            cmd = ["kubectl", "kustomize", env_path]
            logger.info(f"Dry run: showing resources that would be applied")
            
            try:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                print(result.stdout)
                
                # Also show diff if possible
                diff_cmd = ["kubectl", "diff", "-k", env_path]
                try:
                    diff_result = subprocess.run(
                        diff_cmd, capture_output=True, text=True
                    )
                    if diff_result.stdout:
                        print("\nChanges:")
                        print(diff_result.stdout)
                except Exception:
                    logger.warning("Could not generate diff")
                    
            except subprocess.CalledProcessError as e:
                logger.error(f"Error generating dry run: {e}")
                if e.stderr:
                    logger.error(e.stderr)
                return
        else:
            # Actually apply the changes
            cmd = ["kubectl", "apply", "-k", env_path]
            logger.info(f"Applying kustomize to {args.environment}")
            
            try:
                subprocess.run(cmd, check=True)
                logger.info(f"Deployment to {args.environment} completed successfully")
                
                # Wait for deployments to be ready
                namespace = self.config["environments"][args.environment]["namespace"]
                self._wait_for_deployments(namespace, args.component)
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Deployment failed: {e}")
                return

    def _wait_for_deployments(self, namespace, component="all"):
        """Wait for deployments to be ready."""
        logger.info(f"Waiting for deployments to be ready in namespace {namespace}")
        
        try:
            if component == "all":
                # Get all deployments
                cmd = ["kubectl", "get", "deployments", "-n", namespace, "-o", "name"]
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                deployments = result.stdout.strip().split("\n")
            else:
                # Only wait for the specified component
                deployments = [f"deployment.apps/{component}"]
                
            for deployment in deployments:
                if not deployment:
                    continue
                    
                logger.info(f"Waiting for {deployment} to be ready...")
                wait_cmd = [
                    "kubectl", "rollout", "status", "-n", namespace, 
                    deployment, "--timeout=300s"
                ]
                subprocess.run(wait_cmd, check=True)
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error waiting for deployments: {e}")

    def _handle_rollback(self, args):
        """Handle rollback command."""
        logger.info(f"Rolling back deployment in {args.environment} environment")
        
        script_path = os.path.join(SCRIPT_DIR, "scripts", "rollback-deployment.sh")
        
        if not os.path.exists(script_path):
            logger.error(f"Rollback script not found at {script_path}")
            return
        
        # Build command line arguments
        cmd = [
            script_path,
            "--namespace", self.config["environments"][args.environment]["namespace"],
            "--component", args.component,
        ]
        
        if args.revision:
            cmd.extend(["--revision", args.revision])
            
        # Execute the script
        logger.debug(f"Executing command: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
            logger.info("Rollback completed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Rollback failed: {e}")

    def _handle_status(self, args):
        """Handle status command."""
        namespace = self.config["environments"][args.environment]["namespace"]
        logger.info(f"Checking status in {args.environment} environment")
        
        try:
            # Check deployments
            logger.info("Checking deployments...")
            dep_cmd = ["kubectl", "get", "deployments", "-n", namespace]
            subprocess.run(dep_cmd, check=True)
            
            # Check pods
            logger.info("Checking pods...")
            pod_cmd = ["kubectl", "get", "pods", "-n", namespace]
            subprocess.run(pod_cmd, check=True)
            
            # Check services
            logger.info("Checking services...")
            svc_cmd = ["kubectl", "get", "services", "-n", namespace]
            subprocess.run(svc_cmd, check=True)
            
            if args.detailed:
                # Show more detailed information
                logger.info("Detailed information:")
                
                # Show resource usage
                logger.info("Resource usage:")
                res_cmd = ["kubectl", "top", "pods", "-n", namespace]
                try:
                    subprocess.run(res_cmd, check=True)
                except subprocess.CalledProcessError:
                    logger.warning("Could not get resource usage. Is metrics-server installed?")
                
                # Show events
                logger.info("Recent events:")
                event_cmd = ["kubectl", "get", "events", "-n", namespace, "--sort-by=.metadata.creationTimestamp"]
                subprocess.run(event_cmd, check=True)
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error checking status: {e}")

    def _handle_health(self, args):
        """Handle health command."""
        namespace = self.config["environments"][args.environment]["namespace"]
        logger.info(f"Checking health in {args.environment} environment")
        
        try:
            # Get pod names based on component
            if args.component == "all" or args.component == "api-gateway":
                logger.info("Checking API Gateway health...")
                self._check_component_health(namespace, "api-gateway", 5000, "/api/health")
                
            if args.component == "all" or args.component == "sync-service":
                logger.info("Checking Sync Service health...")
                self._check_component_health(namespace, "sync-service", 8080, "/health")
                
            if args.component == "all" or args.component == "websocket":
                logger.info("Checking WebSocket Server health...")
                self._check_component_health(namespace, "websocket-server", 8081, "/health")
                
        except Exception as e:
            logger.error(f"Error checking health: {e}")

    def _check_component_health(self, namespace, component, port, path):
        """Check health for a specific component."""
        try:
            # Get pod name
            cmd = [
                "kubectl", "get", "pods", "-n", namespace, 
                "-l", f"app={component}", "-o", "jsonpath='{.items[0].metadata.name}'"
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            pod_name = result.stdout.strip().strip("'")
            
            if not pod_name:
                logger.warning(f"No pods found for {component}")
                return
                
            # Check health endpoint
            health_cmd = [
                "kubectl", "exec", "-n", namespace, pod_name, "--", 
                "curl", "-s", f"http://localhost:{port}{path}"
            ]
            
            health_result = subprocess.run(
                health_cmd, check=True, capture_output=True, text=True
            )
            
            # Parse and display health information
            health_data = health_result.stdout.strip()
            try:
                health_json = json.loads(health_data)
                logger.info(f"{component} health: {json.dumps(health_json, indent=2)}")
            except json.JSONDecodeError:
                logger.info(f"{component} health response: {health_data}")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error checking {component} health: {e}")
            if hasattr(e, 'stderr') and e.stderr:
                logger.error(e.stderr)

    def _handle_logs(self, args):
        """Handle logs command."""
        namespace = self.config["environments"][args.environment]["namespace"]
        logger.info(f"Viewing logs for {args.component} in {args.environment} environment")
        
        try:
            # Build the kubectl logs command
            cmd = [
                "kubectl", "logs", "-n", namespace, 
                "-l", f"app={args.component}", "--tail", str(args.tail)
            ]
            
            if args.follow:
                cmd.append("-f")
                
            # Execute the command
            logger.debug(f"Executing command: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error viewing logs: {e}")
            if hasattr(e, 'stderr') and e.stderr:
                logger.error(e.stderr)
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully when following logs
            logger.info("Log viewing stopped")

    def _handle_gitops(self, args):
        """Handle GitOps commands."""
        if not hasattr(args, "gitops_command") or not args.gitops_command:
            logger.error("No GitOps command specified")
            return
            
        if args.gitops_command == "sync":
            self._handle_gitops_sync(args)
        else:
            logger.error(f"Unknown GitOps command: {args.gitops_command}")

    def _handle_gitops_sync(self, args):
        """Handle GitOps sync command."""
        logger.info(f"Syncing GitOps for {args.environment} environment")
        
        script_path = os.path.join(SCRIPT_DIR, "scripts", "gitops-sync.sh")
        
        if not os.path.exists(script_path):
            logger.error(f"GitOps sync script not found at {script_path}")
            return
        
        # Build command line arguments
        cmd = [
            script_path,
            "--environment", args.environment,
        ]
        
        # Add optional arguments
        if args.repo:
            cmd.extend(["--repo", args.repo])
        elif "git_repo" in self.config:
            cmd.extend(["--repo", self.config["git_repo"]])
            
        if args.branch:
            cmd.extend(["--branch", args.branch])
        elif "git_branch" in self.config:
            cmd.extend(["--branch", self.config["git_branch"]])
            
        if args.dry_run:
            cmd.append("--dry-run")
            
        # Execute the script
        logger.debug(f"Executing command: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
            logger.info("GitOps sync completed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"GitOps sync failed: {e}")

    def _handle_build(self, args):
        """Handle build command."""
        components = []
        if args.component == "all":
            components = ["api-gateway", "sync-service", "websocket"]
        else:
            components = [args.component]
            
        for component in components:
            self._build_component(component, args.tag, args.push)

    def _build_component(self, component, tag, push):
        """Build a specific component."""
        logger.info(f"Building {component} with tag {tag}")
        
        # Determine Dockerfile path
        dockerfile = f"Dockerfile.{component}"
        if component == "websocket":
            # Handle special case for websocket component
            dockerfile = "Dockerfile.websocket-server"
            
        if not os.path.exists(os.path.join(SCRIPT_DIR, dockerfile)):
            logger.error(f"Dockerfile {dockerfile} not found")
            return
            
        # Build the image
        image_name = f"{self.config.get('registry', 'terrafusion')}/{component}:{tag}"
        build_cmd = [
            "docker", "build", "-t", image_name,
            "-f", dockerfile, "."
        ]
        
        try:
            logger.debug(f"Executing command: {' '.join(build_cmd)}")
            subprocess.run(build_cmd, check=True)
            logger.info(f"Successfully built {image_name}")
            
            # Push if requested
            if push:
                logger.info(f"Pushing {image_name}")
                push_cmd = ["docker", "push", image_name]
                subprocess.run(push_cmd, check=True)
                logger.info(f"Successfully pushed {image_name}")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error building {component}: {e}")
            if hasattr(e, 'stderr') and e.stderr:
                logger.error(e.stderr)


def main():
    """Main entry point for the CLI."""
    cli = TerraFusionCLI()
    cli.run()


if __name__ == "__main__":
    main()