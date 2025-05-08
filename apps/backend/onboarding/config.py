"""
TerraFusion SyncService - Onboarding Configuration

This module provides configuration for the interactive tutorial,
including step definitions for different user roles.
"""

# Welcome messages for each role
WELCOME_MESSAGES = {
    'ITAdmin': {
        'message': 'Welcome, IT Administrator! This tutorial will guide you through managing the TerraFusion SyncService system, including system settings, user management, and monitoring tools.',
        'image': 'itadmin_welcome.svg'
    },
    'Assessor': {
        'message': 'Welcome, Property Assessor! This tutorial will show you how to review, approve, and manage property assessments in the TerraFusion SyncService platform.',
        'image': 'assessor_welcome.svg'
    },
    'Staff': {
        'message': 'Welcome, Staff Member! This tutorial will help you learn how to upload property data files and track their processing in the TerraFusion SyncService platform.',
        'image': 'staff_welcome.svg'
    },
    'Auditor': {
        'message': 'Welcome, Auditor! This tutorial will guide you through accessing audit trails, compliance reports, and system activity logs in the TerraFusion SyncService platform.',
        'image': 'auditor_welcome.svg'
    }
}

# Completion messages for each role
COMPLETION_MESSAGES = {
    'ITAdmin': {
        'message': 'Congratulations! You\'ve completed the IT Administrator tutorial. You now have the knowledge to effectively manage the TerraFusion SyncService platform, handle user accounts, monitor system health, and configure security settings.',
        'image': 'itadmin_welcome.svg'
    },
    'Assessor': {
        'message': 'Great job! You\'ve completed the Property Assessor tutorial. You now know how to review property submissions, approve assessments, generate reports, and handle validation exceptions.',
        'image': 'assessor_welcome.svg'
    },
    'Staff': {
        'message': 'Well done! You\'ve completed the Staff tutorial. You now understand how to upload property data files, create sync pairs, check submission status, and handle basic validation errors.',
        'image': 'staff_welcome.svg'
    },
    'Auditor': {
        'message': 'Excellent work! You\'ve completed the Auditor tutorial. You now know how to access audit trails, generate compliance reports, review user activity, and export audit data for external analysis.',
        'image': 'auditor_welcome.svg'
    }
}

# Tutorial steps for IT Admin role
IT_ADMIN_STEPS = [
    {
        'title': 'System Dashboard Overview',
        'description': 'Get familiar with the main system dashboard where you can monitor system health, service status, and key metrics.',
        'image': 'itadmin_step1.jpg'
    },
    {
        'title': 'User Management',
        'description': 'Learn how to create, edit, and deactivate user accounts, reset passwords, and manage user roles and permissions.',
        'image': 'itadmin_step2.jpg'
    },
    {
        'title': 'System Configuration',
        'description': 'Explore system-wide settings, including LDAP integration, security policies, and service configuration options.',
        'image': 'itadmin_step3.jpg'
    },
    {
        'title': 'Monitoring & Alerts',
        'description': 'Set up and manage monitoring alerts for system health, service availability, and performance thresholds.',
        'image': 'itadmin_step4.jpg'
    },
    {
        'title': 'Backup & Recovery',
        'description': 'Learn how to configure automated backups, test recovery procedures, and manage the disaster recovery process.',
        'image': 'itadmin_step5.jpg'
    }
]

# Tutorial steps for Assessor role
ASSESSOR_STEPS = [
    {
        'title': 'Assessment Dashboard',
        'description': 'Get familiar with the assessment dashboard where you can see pending assessments, recent submissions, and your approval queue.',
        'image': 'assessor_step1.jpg'
    },
    {
        'title': 'Reviewing Submissions',
        'description': 'Learn how to review property assessment submissions, check for errors, and validate data integrity.',
        'image': 'assessor_step2.jpg'
    },
    {
        'title': 'Approval Process',
        'description': 'Understand the approval workflow, including validation checks, conditional approvals, and rejection with feedback.',
        'image': 'assessor_step3.jpg'
    },
    {
        'title': 'Generating Reports',
        'description': 'Create assessment reports, export data for external use, and generate compliance documentation.',
        'image': 'assessor_step4.jpg'
    },
    {
        'title': 'Exception Handling',
        'description': 'Learn how to identify and resolve validation exceptions, data inconsistencies, and other assessment issues.',
        'image': 'assessor_step5.jpg'
    }
]

# Tutorial steps for Staff role
STAFF_STEPS = [
    {
        'title': 'Upload Dashboard',
        'description': 'Get familiar with the upload dashboard where you can track your submissions, upload new files, and check processing status.',
        'image': 'staff_step1.jpg'
    },
    {
        'title': 'File Upload Process',
        'description': 'Learn how to upload property assessment files, select file formats, and initiate the validation process.',
        'image': 'staff_step2.jpg'
    },
    {
        'title': 'Creating Sync Pairs',
        'description': 'Understand how to create sync pairs between source and target systems to facilitate data synchronization.',
        'image': 'staff_step3.jpg'
    },
    {
        'title': 'Tracking Submissions',
        'description': 'Monitor the status of your submitted files, check validation results, and get notified of processing completion.',
        'image': 'staff_step4.jpg'
    },
    {
        'title': 'Handling Basic Errors',
        'description': 'Learn to identify and resolve common upload errors, format issues, and data validation problems.',
        'image': 'staff_step5.jpg'
    }
]

# Tutorial steps for Auditor role
AUDITOR_STEPS = [
    {
        'title': 'Audit Dashboard',
        'description': 'Get familiar with the audit dashboard where you can access system activity logs, user actions, and compliance reports.',
        'image': 'auditor_step1.jpg'
    },
    {
        'title': 'Accessing Audit Trails',
        'description': 'Learn how to access and filter comprehensive audit trails for all system activities and user actions.',
        'image': 'auditor_step2.jpg'
    },
    {
        'title': 'Compliance Reporting',
        'description': 'Generate compliance reports for regulatory requirements, including data access, modifications, and approval processes.',
        'image': 'auditor_step3.jpg'
    },
    {
        'title': 'User Activity Monitoring',
        'description': 'Track and analyze user activity patterns, identify unusual behaviors, and generate user action reports.',
        'image': 'auditor_step4.jpg'
    },
    {
        'title': 'Export & Integration',
        'description': 'Export audit data for external analysis, integrate with compliance systems, and generate evidence documentation.',
        'image': 'auditor_step5.jpg'
    }
]

# Map role names to their respective tutorial steps
ROLE_STEPS = {
    'ITAdmin': IT_ADMIN_STEPS,
    'Assessor': ASSESSOR_STEPS,
    'Staff': STAFF_STEPS,
    'Auditor': AUDITOR_STEPS
}

def get_tutorial_steps(role):
    """
    Get tutorial steps for a specific role.
    
    Args:
        role: User role (ITAdmin, Assessor, Staff, Auditor)
        
    Returns:
        List of step dictionaries or None if role not found
    """
    return ROLE_STEPS.get(role)

def get_welcome_message(role):
    """
    Get welcome message for a specific role.
    
    Args:
        role: User role (ITAdmin, Assessor, Staff, Auditor)
        
    Returns:
        Welcome message dictionary or None if role not found
    """
    return WELCOME_MESSAGES.get(role)

def get_completion_message(role):
    """
    Get completion message for a specific role.
    
    Args:
        role: User role (ITAdmin, Assessor, Staff, Auditor)
        
    Returns:
        Completion message dictionary or None if role not found
    """
    return COMPLETION_MESSAGES.get(role)