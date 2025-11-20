"""CLI for batch orchestration commands for proofreader.

Provides subcommands for creating and fetching batch jobs.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path


def add_batch_subparsers(subparsers: argparse._SubParsersAction) -> None:
    """Add batch-related subcommands to the parser.

    Args:
        subparsers: The subparsers object from argparse
    """
    # Create batch jobs subcommand
    create_parser = subparsers.add_parser(
        "batch-create",
        help="Create batch jobs for proofreading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create batch jobs for all documents
  python -m src.llm_review.llm_proofreader batch-create

  # Create for specific subjects
  python -m src.llm_review.llm_proofreader batch-create --subjects Geography "Art and Design"

  # Use custom batch size
  python -m src.llm_review.llm_proofreader batch-create --batch-size 5
        """,
    )

    create_parser.add_argument(
        "--from-report",
        type=Path,
        default=Path("Documents/verified-llm-categorised-language-check-report.csv"),
        help="Path to verified categorised report CSV",
    )

    create_parser.add_argument(
        "--subjects",
        nargs="+",
        help="Filter by subject names",
    )

    create_parser.add_argument(
        "--documents",
        nargs="+",
        help="Filter by document filenames",
    )

    create_parser.add_argument(
        "--batch-size",
        type=int,
        default=int(os.environ.get("LLM_PROOFREADER_BATCH_SIZE", "10")),
        help="Number of issues per batch",
    )

    create_parser.add_argument(
        "--tracking-file",
        type=Path,
        default=Path("data/proofreader_batch_jobs.json"),
        help="Path to job tracking file",
    )

    create_parser.add_argument(
        "--state-file",
        type=Path,
        default=Path("data/llm_proofreader_state.json"),
        help="Path to state file",
    )

    # Fetch results subcommand
    fetch_parser = subparsers.add_parser(
        "batch-fetch",
        help="Fetch batch job results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch all pending jobs
  python -m src.llm_review.llm_proofreader batch-fetch --check-all-pending

  # Fetch specific job
  python -m src.llm_review.llm_proofreader batch-fetch --job-names batch-job-123
        """,
    )

    fetch_parser.add_argument(
        "--tracking-file",
        type=Path,
        default=Path("data/proofreader_batch_jobs.json"),
        help="Path to job tracking file",
    )

    fetch_parser.add_argument(
        "--state-file",
        type=Path,
        default=Path("data/llm_proofreader_state.json"),
        help="Path to state file",
    )

    fetch_parser.add_argument(
        "--job-names",
        nargs="+",
        help="Specific job names to fetch",
    )

    fetch_parser.add_argument(
        "--check-all-pending",
        action="store_true",
        help="Check and fetch all pending jobs",
    )

    # List jobs subcommand
    list_parser = subparsers.add_parser(
        "batch-list",
        help="List batch jobs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    list_parser.add_argument(
        "--tracking-file",
        type=Path,
        default=Path("data/proofreader_batch_jobs.json"),
        help="Path to job tracking file",
    )

    list_parser.add_argument(
        "--status",
        choices=["pending", "completed", "failed"],
        help="Filter by status",
    )


def handle_batch_create(args: argparse.Namespace) -> int:
    """Handle batch-create command.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    import sys
    from dotenv import load_dotenv
    
    from src.llm.provider_registry import create_provider_chain
    from src.llm.service import LLMService
    
    from ..core.batch_orchestrator import BatchJobTracker
    from ..core.state_manager import StateManager
    from .batch_orchestrator import ProofreaderBatchOrchestrator
    from .config import ProofreaderConfiguration
    
    # Load environment
    load_dotenv(override=True)
    
    # Validate report file
    if not args.from_report.exists():
        print(f"Error: Report file not found: {args.from_report}", file=sys.stderr)
        return 1
    
    # Create LLM service
    try:
        from .prompt_factory import get_system_prompt_text
        
        system_prompt_text = get_system_prompt_text()
        
        providers = create_provider_chain(
            system_prompt=system_prompt_text,
            filter_json=True,
            dotenv_path=None,
            primary=None,  # Use default
        )
        
        if not providers:
            print("Error: No LLM providers configured", file=sys.stderr)
            return 1
        
        print(f"Using LLM provider(s): {[p.name for p in providers]}")
        llm_service = LLMService(providers)
        
    except Exception as e:
        print(f"Error creating LLM service: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    # Create configuration
    config = ProofreaderConfiguration(
        input_csv_path=args.from_report,
        output_base_dir=Path("Documents"),
        output_subdir="proofreader_reports",
        batch_size=args.batch_size,
        max_retries=0,  # Not used for batch API
        state_file=args.state_file,
        subjects=set(args.subjects) if args.subjects else None,
        documents=set(args.documents) if args.documents else None,
        llm_provider=None,
        fail_on_quota=True,
        log_raw_responses=False,
        log_response_dir=Path("data/llm_proofreader_responses"),
        output_csv_columns=[],  # Not used for batch API
    )
    
    # Create tracker, state, and orchestrator
    tracker = BatchJobTracker(args.tracking_file)
    state = StateManager(args.state_file)
    orchestrator = ProofreaderBatchOrchestrator(
        llm_service=llm_service,
        tracker=tracker,
        state=state,
        config=config,
    )
    
    # Create batch jobs
    try:
        orchestrator.create_batch_jobs(force=False)
        return 0
        
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def handle_batch_fetch(args: argparse.Namespace) -> int:
    """Handle batch-fetch command.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    import sys
    from dotenv import load_dotenv
    
    from src.llm.provider_registry import create_provider_chain
    from src.llm.service import LLMService
    
    from ..core.batch_orchestrator import BatchJobTracker
    from ..core.state_manager import StateManager
    from .batch_orchestrator import ProofreaderBatchOrchestrator
    from .config import ProofreaderConfiguration
    
    # Load environment
    load_dotenv(override=True)
    
    # Create LLM service
    try:
        from .prompt_factory import get_system_prompt_text
        
        system_prompt_text = get_system_prompt_text()
        
        providers = create_provider_chain(
            system_prompt=system_prompt_text,
            filter_json=True,
            dotenv_path=None,
            primary=None,
        )
        
        if not providers:
            print("Error: No LLM providers configured", file=sys.stderr)
            return 1
        
        print(f"Using LLM provider(s): {[p.name for p in providers]}")
        llm_service = LLMService(providers)
        
    except Exception as e:
        print(f"Error creating LLM service: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    
    # Create configuration
    config = ProofreaderConfiguration(
        input_csv_path=args.from_report,
        output_base_dir=Path("Documents"),
        output_subdir="proofreader_reports",
        batch_size=10,  # Not used for fetching
        max_retries=0,
        state_file=args.state_file,
        subjects=None,
        documents=None,
        llm_provider=None,
        fail_on_quota=True,
        log_raw_responses=False,
        log_response_dir=Path("data/llm_proofreader_responses"),
        output_csv_columns=[],
    )
    
    # Create state manager, tracker, and orchestrator
    state = StateManager(args.state_file)
    tracker = BatchJobTracker(args.tracking_file)
    orchestrator = ProofreaderBatchOrchestrator(
        llm_service=llm_service,
        tracker=tracker,
        state=state,
        config=config,
    )
    
    # Fetch batch results
    try:
        orchestrator.fetch_batch_results(
            job_names=args.job_names,
            check_all_pending=args.check_all_pending,
        )
        
        return 0
        
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def handle_batch_list(args: argparse.Namespace) -> int:
    """Handle batch-list command.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    import sys
    
    from ..core.batch_orchestrator import BatchJobTracker
    
    try:
        tracker = BatchJobTracker(args.tracking_file)
        
        # List all jobs
        all_jobs = tracker.get_all_jobs()
        
        # Filter by status if specified
        if args.status:
            all_jobs = [j for j in all_jobs if j.status == args.status]
        
        if not all_jobs:
            print("No jobs found")
            return 0
        
        # Print header
        print(f"\n{'=' * 80}")
        print(f"{'Job Name':<18} {'Status':<12} {'Subject':<20} {'Document':<25}")
        print(f"{'=' * 80}")
        
        # Print each job
        for job in all_jobs:
            doc_name = (
                job.filename[:22] + "..." if len(job.filename) > 25 else job.filename
            )
            print(
                f"{job.job_name[:16]}... {job.status:<12} {job.subject:<20} {doc_name:<25}"
            )
        
        print(f"{'=' * 80}")
        print(f"Total: {len(all_jobs)} job(s)")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
