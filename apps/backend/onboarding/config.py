"""
TerraFusion SyncService - Onboarding Configuration

This module defines the onboarding tutorial steps and content for different user roles.
"""

# Define onboarding tutorials for each role
ONBOARDING_TUTORIALS = {
    # IT Admin tutorial
    'ITAdmin': {
        'id': 'itadmin_tutorial',
        'title': 'IT Administrator Onboarding',
        'description': 'Learn how to manage and configure the TerraFusion SyncService platform as an IT Administrator.',
        'welcome_image': 'itadmin_welcome.svg',
        'steps': [
            {
                'id': 'itadmin_overview',
                'title': 'Platform Overview',
                'description': 'Get an overview of the TerraFusion SyncService platform and its key components.',
                'content': """
                <h3>Welcome to TerraFusion SyncService</h3>
                <p>As an IT Administrator, you have full access to all features and configuration options.</p>
                <p>Your responsibilities include:</p>
                <ul>
                    <li>Configuring the connection to County Active Directory</li>
                    <li>Managing user roles and permissions</li>
                    <li>Monitoring system health and performance</li>
                    <li>Troubleshooting sync operations</li>
                    <li>Setting up data validation rules</li>
                </ul>
                <p>This tutorial will guide you through the main features and administrative tasks.</p>
                """
            },
            {
                'id': 'itadmin_system_health',
                'title': 'System Health Dashboard',
                'description': 'Learn how to monitor system health and performance.',
                'content': """
                <h3>System Health Monitoring</h3>
                <p>The System Health Dashboard provides real-time metrics on:</p>
                <ul>
                    <li>CPU and memory usage</li>
                    <li>Database connection status</li>
                    <li>Active sync operations</li>
                    <li>Error rates and recent failures</li>
                </ul>
                <p>You can access the dashboard at any time by clicking on "Metrics" in the main navigation.</p>
                <p>If you notice any critical alerts, you can investigate the details by clicking on the alert.</p>
                """
            },
            {
                'id': 'itadmin_user_management',
                'title': 'User Management',
                'description': 'Learn how to manage user accounts and permissions.',
                'content': """
                <h3>Managing Users and Roles</h3>
                <p>TerraFusion SyncService integrates with your County's Active Directory for authentication.</p>
                <p>The system maps AD groups to the following roles:</p>
                <ul>
                    <li><strong>IT Admin:</strong> Full system access</li>
                    <li><strong>Assessor:</strong> View and approve data changes</li>
                    <li><strong>Staff:</strong> Upload and manage data</li>
                    <li><strong>Auditor:</strong> View-only access to track changes</li>
                </ul>
                <p>You can configure these mappings in the Administration panel under "User Management".</p>
                """
            },
            {
                'id': 'itadmin_sync_config',
                'title': 'Sync Configuration',
                'description': 'Learn how to configure sync operations and schedules.',
                'content': """
                <h3>Setting Up Sync Operations</h3>
                <p>As an IT Admin, you can create and configure sync operations between different data sources.</p>
                <p>Key configuration tasks include:</p>
                <ul>
                    <li>Creating sync pairs between source and target systems</li>
                    <li>Setting up sync schedules (one-time, daily, weekly)</li>
                    <li>Configuring data mappings and transformations</li>
                    <li>Setting validation rules for data quality</li>
                </ul>
                <p>You can create a new sync operation by clicking "New Sync Operation" on the dashboard.</p>
                """
            },
            {
                'id': 'itadmin_audit',
                'title': 'Audit and Compliance',
                'description': 'Learn how to track all system activities for compliance.',
                'content': """
                <h3>Audit Trail and Compliance</h3>
                <p>Every action in the system is logged in the audit trail, including:</p>
                <ul>
                    <li>User logins and authentication attempts</li>
                    <li>Configuration changes</li>
                    <li>Sync operations (started, completed, failed)</li>
                    <li>Data approvals and rejections</li>
                </ul>
                <p>All entries include the user, timestamp, IP address, and action details.</p>
                <p>Access the full audit trail by clicking "Audit" in the main navigation.</p>
                <p>You can filter and export audit data for compliance reporting.</p>
                """
            }
        ]
    },
    
    # Assessor tutorial
    'Assessor': {
        'id': 'assessor_tutorial',
        'title': 'Property Assessor Onboarding',
        'description': 'Learn how to review and approve property assessment data in TerraFusion SyncService.',
        'welcome_image': 'assessor_welcome.svg',
        'steps': [
            {
                'id': 'assessor_overview',
                'title': 'Platform Overview',
                'description': 'Get an overview of the TerraFusion SyncService platform for Assessors.',
                'content': """
                <h3>Welcome to TerraFusion SyncService</h3>
                <p>As a Property Assessor, you're responsible for reviewing and approving data synchronization operations related to property assessments.</p>
                <p>Your key responsibilities include:</p>
                <ul>
                    <li>Reviewing property data changes before they're applied</li>
                    <li>Approving valid data updates</li>
                    <li>Rejecting problematic data with explanations</li>
                    <li>Creating new sync operations for property data</li>
                </ul>
                <p>This tutorial will guide you through your main tasks and workflows.</p>
                """
            },
            {
                'id': 'assessor_review',
                'title': 'Review Updates',
                'description': 'Learn how to review property data updates.',
                'content': """
                <h3>Reviewing Property Data Updates</h3>
                <p>When new property data is uploaded, you'll receive a notification on your dashboard.</p>
                <p>To review pending updates:</p>
                <ol>
                    <li>Click on "Pending Approvals" on your dashboard</li>
                    <li>Select the update batch you want to review</li>
                    <li>Examine the data changes highlighted in the diff view</li>
                    <li>Check validation results and any flagged issues</li>
                </ol>
                <p>The system will highlight significant changes, such as large valuation differences or property classification changes.</p>
                """
            },
            {
                'id': 'assessor_approval',
                'title': 'Approve or Reject Changes',
                'description': 'Learn how to approve or reject property data changes.',
                'content': """
                <h3>Approving or Rejecting Changes</h3>
                <p>After reviewing the data, you can:</p>
                <ul>
                    <li><strong>Approve:</strong> Accept all changes and update the property database</li>
                    <li><strong>Reject:</strong> Decline the changes with an explanation</li>
                    <li><strong>Partially Approve:</strong> Accept some changes while rejecting others</li>
                </ul>
                <p>When approving changes, you can add notes that will be saved in the audit trail.</p>
                <p>If you reject changes, your feedback will be sent to the data uploader for correction.</p>
                """
            },
            {
                'id': 'assessor_create_sync',
                'title': 'Create Sync Operations',
                'description': 'Learn how to create new sync operations for property data.',
                'content': """
                <h3>Creating New Sync Operations</h3>
                <p>As an Assessor, you can initiate new sync operations:</p>
                <ol>
                    <li>Click "New Sync Operation" on your dashboard</li>
                    <li>Select the source system (e.g., Property Survey Database)</li>
                    <li>Choose the target system (e.g., County Assessment Database)</li>
                    <li>Configure data mapping and validation rules</li>
                    <li>Schedule the operation (immediate or future date)</li>
                </ol>
                <p>The system will validate the configuration before starting the operation.</p>
                <p>You'll receive a notification when the operation completes or if issues arise.</p>
                """
            }
        ]
    },
    
    # Staff tutorial
    'Staff': {
        'id': 'staff_tutorial',
        'title': 'County Staff Onboarding',
        'description': 'Learn how to upload and manage property data in TerraFusion SyncService.',
        'welcome_image': 'staff_welcome.svg',
        'steps': [
            {
                'id': 'staff_overview',
                'title': 'Platform Overview',
                'description': 'Get an overview of the TerraFusion SyncService platform for County Staff.',
                'content': """
                <h3>Welcome to TerraFusion SyncService</h3>
                <p>As a County Staff member, you're responsible for uploading and managing property data in the system.</p>
                <p>Your key responsibilities include:</p>
                <ul>
                    <li>Uploading property assessment data files</li>
                    <li>Monitoring data validation results</li>
                    <li>Addressing validation errors and warnings</li>
                    <li>Tracking the status of sync operations</li>
                </ul>
                <p>This tutorial will guide you through your main tasks and workflows.</p>
                """
            },
            {
                'id': 'staff_upload',
                'title': 'Upload Data',
                'description': 'Learn how to upload property data files.',
                'content': """
                <h3>Uploading Property Data</h3>
                <p>To upload new property data:</p>
                <ol>
                    <li>Click "Upload Data" on your dashboard</li>
                    <li>Select the data type (e.g., Residential, Commercial)</li>
                    <li>Choose the file format (CSV, Excel, XML)</li>
                    <li>Drag and drop your file or click to browse</li>
                    <li>Review the data preview and mapping</li>
                    <li>Click "Upload" to start the process</li>
                </ol>
                <p>The system will validate your data and identify any potential issues.</p>
                <p>You'll see a summary of validation results before finalizing the upload.</p>
                """
            },
            {
                'id': 'staff_validation',
                'title': 'Handle Validation Issues',
                'description': 'Learn how to address data validation issues.',
                'content': """
                <h3>Addressing Validation Issues</h3>
                <p>After uploading data, you may encounter validation issues:</p>
                <ul>
                    <li><strong>Errors:</strong> Must be fixed before proceeding</li>
                    <li><strong>Warnings:</strong> Should be reviewed but won't block the process</li>
                    <li><strong>Notices:</strong> Informational alerts about the data</li>
                </ul>
                <p>For each issue, you can:</p>
                <ol>
                    <li>View the affected records and details</li>
                    <li>Export a list of issues for offline correction</li>
                    <li>Correct issues directly in the interface (when possible)</li>
                    <li>Upload a revised file after making corrections</li>
                </ol>
                """
            },
            {
                'id': 'staff_tracking',
                'title': 'Track Operations',
                'description': 'Learn how to track the status of your sync operations.',
                'content': """
                <h3>Tracking Sync Operations</h3>
                <p>You can monitor the status of all your data uploads and sync operations:</p>
                <ul>
                    <li>Click "Sync Operations" in the main navigation</li>
                    <li>View the list of operations with their current status</li>
                    <li>Click on any operation to see detailed information</li>
                </ul>
                <p>Operation statuses include:</p>
                <ul>
                    <li><strong>Pending:</strong> Waiting for approval</li>
                    <li><strong>In Progress:</strong> Currently processing</li>
                    <li><strong>Completed:</strong> Successfully finished</li>
                    <li><strong>Failed:</strong> Encountered errors</li>
                    <li><strong>Rejected:</strong> Declined by an Assessor</li>
                </ul>
                <p>You'll receive notifications when an operation changes status or requires your attention.</p>
                """
            }
        ]
    },
    
    # Auditor tutorial
    'Auditor': {
        'id': 'auditor_tutorial',
        'title': 'County Auditor Onboarding',
        'description': 'Learn how to track and audit all property data changes in TerraFusion SyncService.',
        'welcome_image': 'auditor_welcome.svg',
        'steps': [
            {
                'id': 'auditor_overview',
                'title': 'Platform Overview',
                'description': 'Get an overview of the TerraFusion SyncService platform for Auditors.',
                'content': """
                <h3>Welcome to TerraFusion SyncService</h3>
                <p>As a County Auditor, you have view-only access to monitor and audit all data changes in the system.</p>
                <p>Your key responsibilities include:</p>
                <ul>
                    <li>Reviewing the complete audit trail of system activities</li>
                    <li>Monitoring data changes for compliance</li>
                    <li>Generating audit reports for property assessment changes</li>
                    <li>Tracking user actions and approvals</li>
                </ul>
                <p>This tutorial will guide you through the auditing features and reporting tools.</p>
                """
            },
            {
                'id': 'auditor_trail',
                'title': 'Access Audit Trail',
                'description': 'Learn how to access and filter the complete audit trail.',
                'content': """
                <h3>Working with the Audit Trail</h3>
                <p>The audit trail contains a complete record of all system activities:</p>
                <ol>
                    <li>Click "Audit" in the main navigation</li>
                    <li>View the chronological list of all events</li>
                    <li>Use filters to narrow down by date, user, event type, etc.</li>
                    <li>Click on any event to see detailed information</li>
                </ol>
                <p>Each audit entry includes:</p>
                <ul>
                    <li>Timestamp (with timezone)</li>
                    <li>User who performed the action</li>
                    <li>IP address</li>
                    <li>Event type and description</li>
                    <li>Before and after states (for data changes)</li>
                </ul>
                """
            },
            {
                'id': 'auditor_reports',
                'title': 'Generate Reports',
                'description': 'Learn how to generate and export audit reports.',
                'content': """
                <h3>Generating Audit Reports</h3>
                <p>You can create customized reports for compliance and review:</p>
                <ol>
                    <li>Click "Reports" in the Audit dashboard</li>
                    <li>Select a report template or create a custom report</li>
                    <li>Configure the report parameters (date range, event types, etc.)</li>
                    <li>Generate the report in your preferred format (PDF, Excel, CSV)</li>
                </ol>
                <p>Common report types include:</p>
                <ul>
                    <li>Monthly compliance summary</li>
                    <li>User activity report</li>
                    <li>Property assessment changes by district</li>
                    <li>Approval/rejection patterns</li>
                </ul>
                <p>You can schedule recurring reports to be automatically generated and emailed.</p>
                """
            },
            {
                'id': 'auditor_alerts',
                'title': 'Compliance Alerts',
                'description': 'Learn how to set up and manage compliance alerts.',
                'content': """
                <h3>Setting Up Compliance Alerts</h3>
                <p>You can configure alerts for specific compliance concerns:</p>
                <ol>
                    <li>Click "Alerts" in the Audit dashboard</li>
                    <li>Create a new alert with your desired criteria</li>
                    <li>Specify the notification method (email, dashboard, both)</li>
                    <li>Set the severity level (info, warning, critical)</li>
                </ol>
                <p>Example alert triggers:</p>
                <ul>
                    <li>Large property value changes (over certain percentage)</li>
                    <li>Multiple rejected uploads by the same user</li>
                    <li>Changes to high-value properties</li>
                    <li>Unusual pattern of approvals</li>
                </ul>
                <p>When an alert is triggered, you'll receive a notification with the relevant details.</p>
                """
            }
        ]
    }
}

# Default tutorial for unknown roles
DEFAULT_TUTORIAL = {
    'id': 'default_tutorial',
    'title': 'TerraFusion SyncService Onboarding',
    'description': 'Learn how to use the TerraFusion SyncService platform.',
    'welcome_image': 'default_welcome.svg',
    'steps': [
        {
            'id': 'default_overview',
            'title': 'Platform Overview',
            'description': 'Get an overview of the TerraFusion SyncService platform.',
            'content': """
            <h3>Welcome to TerraFusion SyncService</h3>
            <p>TerraFusion SyncService helps you manage and synchronize property assessment data.</p>
            <p>Key features include:</p>
            <ul>
                <li>Secure data synchronization between systems</li>
                <li>Data validation and quality checks</li>
                <li>Approval workflows for changes</li>
                <li>Comprehensive audit trail</li>
                <li>Reporting and analytics</li>
            </ul>
            <p>This tutorial will introduce you to the basic features of the platform.</p>
            """
        }
    ]
}

def get_tutorial_for_role(role):
    """
    Get the appropriate tutorial for a given user role.
    
    Args:
        role (str): User role (ITAdmin, Assessor, Staff, Auditor)
        
    Returns:
        dict: Tutorial configuration
    """
    if not role:
        return DEFAULT_TUTORIAL
        
    return ONBOARDING_TUTORIALS.get(role, DEFAULT_TUTORIAL)