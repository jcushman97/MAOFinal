#!/usr/bin/env python3
"""
Multi-Agent Orchestration System (MAOS) - Main Entry Point

This module provides the main entry point for the MAOS system, handling
command-line arguments and initiating the orchestration process.

Usage:
    python main.py "Create a simple todo list web app"
    python main.py --project-dir /custom/path "Build an API"
    python main.py --resume PROJECT_ID
"""

import argparse
import asyncio
import sys
import os
from pathlib import Path
from typing import Optional

# Add the project root to Python path for imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.orchestrator import Orchestrator
from core.config import Config
from core.logger import setup_logging


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Orchestration System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "Create a simple todo list web app"
  python main.py --project-dir /custom/path "Build an API"
  python main.py --resume PROJECT_ID
  python main.py --monitor PROJECT_ID
        """
    )
    
    # Main command group
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "objective",
        nargs="?",
        help="Project objective description"
    )
    group.add_argument(
        "--resume",
        metavar="PROJECT_ID",
        help="Resume a paused project by ID"
    )
    group.add_argument(
        "--monitor",
        metavar="PROJECT_ID", 
        help="Monitor an existing project"
    )
    
    # Configuration options
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=None,
        help="Custom project directory (default: ./projects)"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Custom configuration file path"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Default timeout for CLI operations in seconds (default: 300)"
    )
    
    return parser.parse_args()


async def main() -> int:
    """Main entry point for the MAOS system."""
    try:
        args = parse_arguments()
        
        # Setup logging
        setup_logging(level=args.log_level)
        
        # Load configuration
        config = Config.load(args.config)
        
        # Override config with command line arguments
        if args.project_dir:
            config.project_dir = args.project_dir
        if args.timeout:
            config.default_timeout = args.timeout
            
        # Create orchestrator
        orchestrator = Orchestrator(config)
        
        # Execute based on command
        if args.objective:
            # New project
            project_id = await orchestrator.start_project(
                objective=args.objective,
                dry_run=args.dry_run
            )
            print(f"Project started with ID: {project_id}")
            
        elif args.resume:
            # Resume existing project
            success = await orchestrator.resume_project(args.resume)
            if not success:
                print(f"Failed to resume project {args.resume}", file=sys.stderr)
                return 1
                
        elif args.monitor:
            # Monitor existing project
            success = await orchestrator.monitor_project(args.monitor)
            if not success:
                print(f"Failed to monitor project {args.monitor}", file=sys.stderr)
                return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))