"""Atomic inventory durability receipts.

Revision ID: 0002_inventory_durability
Revises: 0001_game_schema_baseline
"""

from alembic import op

from src.backend.infrastructure.inventory.models import DurabilityApplication

revision = "0002_inventory_durability"
down_revision = "0001_game_schema_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Baseline creates current metadata on fresh databases.
    DurabilityApplication.__table__.create(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    DurabilityApplication.__table__.drop(bind=op.get_bind(), checkfirst=True)
