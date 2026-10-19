"""Align four historical indexes with the site's schema-qualified naming convention.

Revision ID: 0005_site_index_names
Revises: 0004_email_verification
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_site_index_names"
down_revision: str | Sequence[str] | None = "0004_email_verification"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Only these historical names are normalized; unrelated schema drift is an error.
_INDEXES = (
    ("auth_refresh_tokens", "token_hash", True),
    ("auth_users", "referral_code", True),
    ("auth_users", "referred_by_id", False),
    ("auth_email_verification_tokens", "token_hash", True),
)


def _rename(*, reverse: bool) -> None:
    inspector = sa.inspect(op.get_bind())
    for table, column, unique in _INDEXES:
        old = f"ix_{table}_{column}"
        canonical = f"ix_site_{table}_{column}"
        source, target = (canonical, old) if reverse else (old, canonical)
        indexes = {index["name"]: index for index in inspector.get_indexes(table, schema="site")}
        for name in (source, target):
            existing = indexes.get(name)
            if existing is not None and (
                existing.get("column_names") != [column]
                or bool(existing.get("unique")) != unique
                or any(existing.get("dialect_options", {}).values())
            ):
                raise RuntimeError(f"Unexpected definition of site.{name}; reconcile manually before migration")
        if source not in indexes and target not in indexes:
            raise RuntimeError(f"Missing expected index on site.{table}.{column}")
        if source in indexes and target in indexes:
            raise RuntimeError(
                f"Both historical and canonical indexes exist on site.{table}.{column}; reconcile manually"
            )
        if source in indexes:
            op.execute(sa.text(f'ALTER INDEX site."{source}" RENAME TO "{target}"'))


def upgrade() -> None:
    _rename(reverse=False)


def downgrade() -> None:
    _rename(reverse=True)
