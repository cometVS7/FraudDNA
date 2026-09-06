"""FraudDNA V2 CLI Data Migration and Persistence Verification Script.

Usage:
    python scripts/migrate_v1_to_v2.py [--batch-size 5000] [--data-path ml/data/transactions.csv]
    python scripts/migrate_v1_to_v2.py --verify-only
"""

import argparse
import sys
import time
from pathlib import Path

# Ensure repository root and backend are on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.core.database import Base
from app.services.migration import DataMigrationService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def main() -> None:
    parser = argparse.ArgumentParser(
        description="FraudDNA V2 Authoritative Data Migration and Verification Utility"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5000,
        help="Batch chunk size for database operations (default: 5000)",
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default="ml/data/transactions.csv",
        help="Path to transactions CSV dataset",
    )
    parser.add_argument(
        "--models-dir",
        type=str,
        default="ml/models",
        help="Path to ML models directory",
    )
    parser.add_argument(
        "--knowledge-dir",
        type=str,
        default="knowledge",
        help="Path to knowledge intelligence directory",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional row limit for test/dry-run migrations",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Skip ingestion and only run referential integrity verification",
    )
    parser.add_argument(
        "--no-signals",
        action="store_true",
        help="Skip Tree SHAP risk signal persistence",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("FraudDNA V2 Data Migration & Persistence Engine")
    print(f"Target Database: {settings.DATABASE_URL_SYNC}")
    print("=" * 70)

    migrator = DataMigrationService(
        data_path=args.data_path,
        models_dir=args.models_dir,
        knowledge_dir=args.knowledge_dir,
    )

    try:
        migrator.validate_source_artifacts()
        print("Source artifacts validated successfully.")
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"ERROR: Source artifact validation failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Connecting to database engine ({settings.DATABASE_URL_SYNC})...")
    engine = create_engine(settings.DATABASE_URL_SYNC, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as session:
        if not args.verify_only:
            print(f"Executing migration with batch size {args.batch_size}...")
            t0 = time.perf_counter()
            result = migrator.migrate_sync(
                session=session,
                batch_size=args.batch_size,
                compute_risk=True,
                compute_signals=not args.no_signals,
                limit=args.limit,
            )
            elapsed = time.perf_counter() - t0

            print("\n" + "=" * 70)
            print("Migration Execution Summary:")
            print("=" * 70)
            print(f"  Customers Persisted:     {result.customers_count}")
            print(f"  Accounts Persisted:      {result.accounts_count}")
            print(f"  Cards Persisted:         {result.cards_count}")
            print(f"  Devices Persisted:       {result.devices_count}")
            print(f"  IP Addresses Persisted:  {result.ips_count}")
            print(f"  Merchants Persisted:     {result.merchants_count}")
            print(f"  Risk Networks Persisted: {result.networks_count}")
            print(f"  Transactions Processed:  {result.transactions_count}")
            print(f"  Risk Assessments:        {result.assessments_count}")
            print(f"  Risk Signals (Tree SHAP):{result.signals_count}")
            print(f"  Models Registered:       {result.models_count}")
            print(f"  Policies Configured:     {result.policies_count}")
            print(f"  Intelligence Sources:    {result.sources_count}")
            print(f"  Total Elapsed Time:      {elapsed:.2f}s")
            print("=" * 70)

        print("\nExecuting Referential Integrity Verification...")
        integrity = migrator.verify_integrity(session)

        print("-" * 70)
        print(f"Checks Passed: {integrity.checks_passed}")
        print(f"Checks Failed: {integrity.checks_failed}")
        print("-" * 70)

        for check_name, status in integrity.details.items():
            print(f"  {check_name:32s}: {status}")

        if not integrity.is_valid:
            print("\nINTEGRITY VERIFICATION FAILED:", file=sys.stderr)
            for err in integrity.errors:
                print(f"  ERROR: {err}", file=sys.stderr)
            sys.exit(1)

        print(
            "\nINTEGRITY VERIFICATION SUCCEEDED: All referential constraints satisfied."
        )
        print("=" * 70)


if __name__ == "__main__":
    main()
