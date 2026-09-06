"""FraudDNA V2 CLI Database Seeding Script.

Usage:
    python scripts/seed_database.py [--batch-size 5000]
"""

import argparse
import sys
from pathlib import Path

# Ensure repository root and backend are on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.services.seed import DatabaseSeeder
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def main() -> None:
    parser = argparse.ArgumentParser(description="FraudDNA V2 Database Seeding Utility")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5000,
        help="Batch insert chunk size for transactions (default: 5000)",
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default="ml/data/transactions.csv",
        help="Path to transactions CSV file",
    )
    args = parser.parse_args()

    print(f"Connecting to database: {settings.DATABASE_URL_SYNC}...")
    engine = create_engine(settings.DATABASE_URL_SYNC, pool_pre_ping=True)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as session:
        seeder = DatabaseSeeder(data_path=args.data_path)
        result = seeder.seed_sync(session=session, batch_size=args.batch_size)

    print("=" * 60)
    print("FraudDNA V2 Database Seeding Summary:")
    print(f"  Customers Inserted:     {result.customers_inserted}")
    print(f"  Accounts Inserted:      {result.accounts_inserted}")
    print(f"  Cards Inserted:         {result.cards_inserted}")
    print(f"  Devices Inserted:       {result.devices_inserted}")
    print(f"  IP Addresses Inserted:  {result.ips_inserted}")
    print(f"  Merchants Inserted:     {result.merchants_inserted}")
    print(f"  Transactions Processed: {result.total_records_processed}")
    print(f"  Models Registered:      {result.models_inserted}")
    print(f"  Policies Configured:    {result.policies_inserted}")
    print(f"  Intelligence Sources:   {result.sources_inserted}")
    print(f"  Total Elapsed Time:     {result.elapsed_seconds}s")
    print("=" * 60)
    print("Database seeding completed successfully.")


if __name__ == "__main__":
    main()
