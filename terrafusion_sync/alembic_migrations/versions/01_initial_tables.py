"""Initial database tables

Revision ID: 01_initial_tables
Revises: 
Create Date: 2025-05-09

"""
from alembic import op
import sqlalchemy as sa
import uuid
from sqlalchemy.dialects.postgresql import JSON, UUID

# revision identifiers, used by Alembic.
revision = '01_initial_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create PropertyOperational table
    op.create_table(
        'property_operational',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('property_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('county_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('situs_address_full', sa.String(length=256), nullable=True),
        sa.Column('current_assessed_value_total', sa.Float(), nullable=True),
        sa.Column('year_built', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('property_id', 'county_id', name='uix_property_county')
    )
    
    # Create ValuationJob table
    op.create_table(
        'valuation_job',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('county_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('property_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('status', sa.String(length=16), nullable=False, index=True),
        sa.Column('job_type', sa.String(length=32), nullable=False),
        sa.Column('parameters_json', JSON, nullable=True),
        sa.Column('result_json', JSON, nullable=True),
        sa.Column('error_message', sa.String(length=1024), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['property_id', 'county_id'], ['property_operational.property_id', 'property_operational.county_id'])
    )
    
    # Create ReportJob table
    op.create_table(
        'report_job',
        sa.Column('report_id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('report_type', sa.String(length=64), nullable=False, index=True),
        sa.Column('county_id', sa.String(length=64), nullable=False, index=True),
        sa.Column('status', sa.String(length=16), nullable=False, index=True),
        sa.Column('message', sa.String(length=1024), nullable=True),
        sa.Column('parameters_json', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('result_location', sa.String(length=1024), nullable=True),
        sa.Column('result_metadata_json', JSON, nullable=True)
    )
    
    # Create indexes
    op.create_index('ix_report_job_county_and_status', 'report_job', ['county_id', 'status'])
    op.create_index('ix_report_job_report_type_and_county', 'report_job', ['report_type', 'county_id'])


def downgrade() -> None:
    # Drop tables in reverse order to avoid FK constraint violations
    op.drop_table('report_job')
    op.drop_table('valuation_job')
    op.drop_table('property_operational')