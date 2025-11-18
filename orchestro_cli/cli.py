#!/usr/bin/env python3
"""Command-line interface for Orchestro CLI."""

import argparse
import sys
from pathlib import Path
from .runner import ScenarioRunner


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Orchestro CLI - Automated CLI testing with screenshot support and intelligent test generation"
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command (default behavior)
    run_parser = subparsers.add_parser("run", help="Run a test scenario")
    run_parser.add_argument(
        "scenario",
        type=Path,
        help="Path to YAML scenario file"
    )
    run_parser.add_argument(
        "-w", "--workspace",
        type=Path,
        help="Workspace directory for isolated testing"
    )
    run_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate scenario without executing it"
    )
    run_parser.add_argument(
        "--junit-xml",
        type=Path,
        metavar="PATH",
        help="Generate JUnit XML test report at specified path (for CI/CD integration)"
    )
    run_parser.add_argument(
        "--snapshot",
        type=str,
        choices=["verify", "update", "record"],
        metavar="MODE",
        help="Snapshot testing mode: verify (CI/CD), update (intentional changes), record (new snapshots)"
    )
    run_parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=Path(".snapshots"),
        metavar="PATH",
        help="Directory for snapshot storage (default: .snapshots)"
    )
    run_parser.add_argument(
        "--snapshot-update-confirm",
        action="store_true",
        help="Require interactive confirmation before updating snapshots"
    )

    # API command
    api_parser = subparsers.add_parser("api", help="API server commands")
    api_subparsers = api_parser.add_subparsers(dest="api_command", help="API commands")

    # API serve command
    serve_parser = api_subparsers.add_parser("serve", help="Start the API server")
    serve_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind server to (default: 0.0.0.0)"
    )
    serve_parser.add_argument(
        "--port",
        default=8000,
        type=int,
        help="Port to bind server to (default: 8000)"
    )
    serve_parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    serve_parser.add_argument(
        "--workers",
        default=1,
        type=int,
        help="Number of worker processes (default: 1)"
    )
    serve_parser.add_argument(
        "--log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Logging level (default: info)"
    )

    # API info command
    api_subparsers.add_parser("info", help="Show API server information")

    # Doctest command
    doctest_parser = subparsers.add_parser(
        "doctest",
        help="Test documentation examples from Markdown files"
    )
    doctest_parser.add_argument(
        "files",
        type=Path,
        nargs="+",
        help="Markdown file(s) to test"
    )
    doctest_parser.add_argument(
        "--prefix",
        default="$",
        help="Command prompt prefix (default: $)"
    )
    doctest_parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    doctest_parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first test failure"
    )
    doctest_parser.add_argument(
        "--junit-xml",
        type=Path,
        metavar="PATH",
        help="Generate JUnit XML test report at specified path"
    )
    doctest_parser.add_argument(
        "--match-mode",
        choices=["exact", "contains", "regex", "startswith", "endswith"],
        default="contains",
        help="Output matching mode (default: contains)"
    )
    doctest_parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Command timeout in seconds (default: 30)"
    )
    doctest_parser.add_argument(
        "--working-dir",
        type=Path,
        help="Working directory for command execution"
    )
    doctest_parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )

    # Version
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.2.1"
    )

    argv = sys.argv[1:]
    # Allow direct scenario invocation: `orchestro scenario.yaml` behaves like `orchestro run scenario.yaml`
    if argv and argv[0] not in {"run", "api", "doctest"} and not argv[0].startswith("-"):
        argv = ["run"] + argv

    args = parser.parse_args(argv)

    # Handle doctest command
    if args.command == "doctest":
        from orchestro_cli.doctest.cli_handler import DocTestCLIHandler
        from orchestro_cli.doctest.executor import MatchMode

        # Convert match mode string to enum
        match_mode = MatchMode(args.match_mode)

        # Create handler
        handler = DocTestCLIHandler(
            markdown_files=args.files,
            prompt_prefix=args.prefix,
            verbose=args.verbose,
            fail_fast=args.fail_fast,
            junit_xml=args.junit_xml,
            match_mode=match_mode,
            working_dir=args.working_dir,
            timeout=args.timeout,
            no_color=args.no_color
        )

        # Run tests
        exit_code = handler.run()
        sys.exit(exit_code)

    # Handle API commands
    if args.command == "api":
        if args.api_command == "serve":
            try:
                import uvicorn
                from orchestro_cli.api.server import create_app

                print("🚀 Starting Orchestro Intelligence API...")
                print(f"📍 Server: http://{args.host}:{args.port}")
                print(f"📚 Docs: http://{args.host}:{args.port}/docs")
                print(f"🔍 GraphQL: http://{args.host}:{args.port}/graphql")

                uvicorn.run(
                    "orchestro_cli.api.server:create_app",
                    factory=True,
                    host=args.host,
                    port=args.port,
                    reload=args.reload,
                    workers=args.workers if not args.reload else 1,
                    log_level=args.log_level,
                    access_log=True,
                )
            except ImportError:
                print("❌ API dependencies not installed. Install with: pip install 'orchestro-cli[api]'", file=sys.stderr)
                sys.exit(1)
        elif args.api_command == "info":
            print("Orchestro Intelligence API")
            print("=" * 50)
            print("Version: 0.2.1")
            print("Description: REST/GraphQL API for automated CLI/TUI test generation")
            print("")
            print("Available Endpoints:")
            print("  GET  /              - Root endpoint")
            print("  GET  /health        - Health check")
            print("  POST /api/v1/analyze    - Analyze application code")
            print("  POST /api/v1/generate   - Generate test scenarios")
            print("  GET  /api/v1/knowledge/{app_id} - Get cached knowledge")
            print("  GET  /api/v1/jobs/{job_id}      - Get job status")
            print("  DELETE /api/v1/jobs/{job_id}    - Cancel job")
            print("  WS   /ws/analyze/{app_path}     - WebSocket analysis")
            print("")
            print("Documentation:")
            print("  OpenAPI: /docs")
            print("  ReDoc:   /redoc")
            print("  GraphQL: /graphql")
        else:
            api_parser.print_help()
        return

    # Default to run command if no subcommand specified
    if args.command is None or args.command == "run":
        # Handle backward compatibility (direct scenario argument)
        if not hasattr(args, "scenario"):
            # No scenario provided
            parser.print_help()
            sys.exit(1)

        if not args.scenario.exists():
            print(f"Error: Scenario file not found: {args.scenario}", file=sys.stderr)
            sys.exit(1)

        try:
            # Convert snapshot mode string to enum if provided
            snapshot_mode = None
            if hasattr(args, 'snapshot') and args.snapshot:
                from orchestro_cli.snapshot import SnapshotMode
                snapshot_mode = SnapshotMode(args.snapshot)

            runner = ScenarioRunner(
                scenario_path=args.scenario,
                workspace=args.workspace,
                verbose=args.verbose,
                junit_xml_path=args.junit_xml,
                snapshot_mode=snapshot_mode,
                snapshot_dir=getattr(args, 'snapshot_dir', Path(".snapshots")),
                snapshot_interactive=getattr(args, 'snapshot_update_confirm', False)
            )

            if args.dry_run:
                # Validate scenario without executing
                result = runner.validate()
                if result["valid"]:
                    print("\n✅ Scenario is valid and ready to run")
                    sys.exit(0)
                else:
                    print(f"\n❌ Scenario validation failed", file=sys.stderr)
                    sys.exit(1)
            else:
                # Execute the scenario
                runner.run()
                print("\n✅ Scenario completed successfully!")

                # JUnit XML report will be generated automatically by runner if path provided
                if args.junit_xml:
                    print(f"📊 JUnit XML report generated: {args.junit_xml}")
        except Exception as e:
            print(f"\n❌ Scenario failed: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
