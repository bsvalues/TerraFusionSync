"""add_gis_export_jobs_table

Revision ID: a45c7931dd6e
Revises: 930c9958ef9b
Create Date: 2025-05-13 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a45c7931dd6e'
down_revision: Union[str, None] = '930c9958ef9b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create gis_export_jobs table for GIS Export plugin
    op.create_table(
        'gis_export_jobs',
        sa.Column('job_id', sa.String(36), primary_key=True, nullable=False, comment="Unique ID for the GIS export job"),
        sa.Column('export_format', sa.String(50), nullable=False, comment="Requested export format (e.g., GeoJSON, Shapefile, KML)"),
        sa.Column('county_id', sa.String(50), nullable=False, comment="County ID for the data export"),
        sa.Column('area_of_interest_json', sa.JSON(), nullable=True, comment="JSON defining the area of interest (e.g., bounding box, polygon WKT/GeoJSON)"),
        sa.Column('layers_json', sa.JSON(), nullable=True, comment="JSON array of layer names or types to include in the export"),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING', comment="e.g., PENDING, RUNNING, COMPLETED, FAILED"),
        sa.Column('message', sa.Text(), nullable=True, comment="Status message or error details"),
        sa.Column('parameters_json', sa.JSON(), nullable=True, comment="Additional JSON object storing other parameters for the export"),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('result_file_location', sa.String(255), nullable=True, comment="Location of the generated export file (e.g., S3 path, downloadable link)"),
        sa.Column('result_file_size_kb', sa.Integer(), nullable=True),
        sa.Column('result_record_count', sa.Integer(), nullable=True)
    )
    
    # Create indexes on frequently queried columns
    op.create_index(op.f('ix_gis_export_jobs_county_id'), 'gis_export_jobs', ['county_id'], unique=False)
    op.create_index(op.f('ix_gis_export_jobs_export_format'), 'gis_export_jobs', ['export_format'], unique=False)
    op.create_index(op.f('ix_gis_export_jobs_status'), 'gis_export_jobs', ['status'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_gis_export_jobs_status'), table_name='gis_export_jobs')
    op.drop_index(op.f('ix_gis_export_jobs_export_format'), table_name='gis_export_jobs')
    op.drop_index(op.f('ix_gis_export_jobs_county_id'), table_name='gis_export_jobs')
    
    # Drop the table
    op.drop_table('gis_export_jobs')