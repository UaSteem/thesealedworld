"""Separate item identification from text preparation.

Revision ID: 0003_item_identification
Revises: 0002_inventory_durability
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_item_identification"
down_revision = "0002_inventory_durability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Baseline uses current metadata for a fresh database; existing rows retain texts.
    columns = {column["name"]: column for column in sa.inspect(op.get_bind()).get_columns("item_instances")}
    if "is_identified" not in columns:
        op.add_column(
            "item_instances", sa.Column("is_identified", sa.Boolean(), nullable=False, server_default=sa.false())
        )
    for table in ("item_instances", "item_generated_templates"):
        text_columns = {column["name"]: column for column in sa.inspect(op.get_bind()).get_columns(table)}
        for name, length in (("name", 160), ("description", 1000)):
            if not text_columns[name]["nullable"]:
                op.alter_column(table, name, existing_type=sa.String(length), nullable=True)


def downgrade() -> None:
    # Never manufacture baseline duplicates or discard prepared text during downgrade.
    # A populated database needs an explicit data migration before restoring NOT NULL.
    tables = ("item_instances", "item_generated_templates")
    for table in tables:
        item_table = sa.table(table, sa.column("name"), sa.column("description"))
        null_count = op.get_bind().scalar(
            sa.select(sa.func.count())
            .select_from(item_table)
            .where(sa.or_(item_table.c.name.is_(None), item_table.c.description.is_(None)))
        )
        if null_count:
            raise RuntimeError("Cannot downgrade item identification with catalog-derived text")
    for table in tables:
        op.alter_column(table, "name", existing_type=sa.String(160), nullable=False)
        op.alter_column(table, "description", existing_type=sa.String(1000), nullable=False)
    op.drop_column("item_instances", "is_identified")
