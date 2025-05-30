"""
Reset Database Script

This script drops and recreates all database tables.
WARNING: This will delete all existing data.
"""

import os
import sys
from app import app, db
from apps.backend.models import User, UserOnboarding, OnboardingEvent, SyncPair, SyncOperation, AuditEntry, SystemMetrics
from sqlalchemy import text

print("WARNING: This will delete all data in the database.")
print("Proceeding automatically in Replit environment...")

with app.app_context():
    print("Dropping all tables with CASCADE...")
    # Use raw SQL to drop tables with CASCADE
    db.session.execute(text("DROP SCHEMA public CASCADE"))
    db.session.execute(text("CREATE SCHEMA public"))
    db.session.execute(text("GRANT ALL ON SCHEMA public TO public"))
    db.session.commit()
    
    print("Creating all tables...")
    db.create_all()
    
    print("Creating default admin user...")
    admin = User(
        username="admin",
        email="admin@benton.wa.us",
        first_name="Admin",
        last_name="User",
        role="ITAdmin",
        is_active=True,
        is_ldap_user=False
    )
    admin.set_password("admin123")
    
    print("Creating default test users...")
    assessor = User(
        username="assessor",
        email="assessor@benton.wa.us",
        first_name="Property",
        last_name="Assessor",
        role="Assessor",
        is_active=True,
        is_ldap_user=False
    )
    assessor.set_password("assessor123")
    
    staff = User(
        username="staff",
        email="staff@benton.wa.us",
        first_name="County",
        last_name="Staff",
        role="Staff",
        is_active=True,
        is_ldap_user=False
    )
    staff.set_password("staff123")
    
    auditor = User(
        username="auditor",
        email="auditor@benton.wa.us",
        first_name="County",
        last_name="Auditor",
        role="Auditor",
        is_active=True,
        is_ldap_user=False
    )
    auditor.set_password("auditor123")
    
    db.session.add_all([admin, assessor, staff, auditor])
    db.session.commit()
    
    print("Database reset complete!")