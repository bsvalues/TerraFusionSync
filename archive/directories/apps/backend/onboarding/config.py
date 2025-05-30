"""
Onboarding Configuration

This module defines tutorial content and configuration for role-specific onboarding.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class TutorialStep:
    """Represents a step in a tutorial."""
    id: str
    title: str
    description: str
    content: str
    image_path: Optional[str] = None


@dataclass
class Tutorial:
    """Represents a full tutorial with multiple steps."""
    id: str
    title: str
    description: str
    welcome_image: str
    role: str
    steps: List[TutorialStep]


# Define role-specific tutorials
TUTORIALS = {
    'ITAdmin': Tutorial(
        id='itadmin_tutorial',
        title='IT Administrator Onboarding',
        description='Learn how to manage the TerraFusion platform as an IT Administrator.',
        welcome_image='/static/images/onboarding/itadmin_welcome.svg',
        role='ITAdmin',
        steps=[
            TutorialStep(
                id='itadmin_dashboard',
                title='Administrator Dashboard',
                description='Overview of the dashboard and key metrics for system health.',
                content="""
                <h2>Administrator Dashboard</h2>
                <p>As an IT Administrator, you have full access to all features of the TerraFusion platform.</p>
                <p>The dashboard shows you system health metrics and important information about:</p>
                <ul>
                    <li>Service status</li>
                    <li>Recent sync operations</li>
                    <li>System alerts</li>
                    <li>User activity</li>
                </ul>
                <p>Click on any metric to see more detailed information.</p>
                """
            ),
            TutorialStep(
                id='itadmin_users',
                title='User Management',
                description='Managing users and permissions.',
                content="""
                <h2>User Management</h2>
                <p>As an IT Administrator, you can manage user accounts and permissions.</p>
                <p>From the Users section, you can:</p>
                <ul>
                    <li>View all users in the system</li>
                    <li>Create new user accounts</li>
                    <li>Reset passwords</li>
                    <li>Assign roles (ITAdmin, Assessor, Staff, Auditor)</li>
                    <li>Enable/disable accounts</li>
                </ul>
                <p>Remember that role assignments determine what actions a user can perform.</p>
                """
            ),
            TutorialStep(
                id='itadmin_sync',
                title='Sync Operations',
                description='Managing and monitoring sync operations.',
                content="""
                <h2>Sync Operations</h2>
                <p>The Sync Operations section allows you to manage data synchronization between systems.</p>
                <p>From here, you can:</p>
                <ul>
                    <li>Create new sync pairs</li>
                    <li>View sync history and status</li>
                    <li>Approve pending sync operations</li>
                    <li>Rollback failed or problematic syncs</li>
                    <li>Configure validation rules for various data types</li>
                </ul>
                <p>The platform maintains a detailed audit log of all sync activities for compliance purposes.</p>
                """
            ),
            TutorialStep(
                id='itadmin_monitoring',
                title='System Monitoring',
                description='Monitoring system health and performance.',
                content="""
                <h2>System Monitoring</h2>
                <p>The Monitoring section gives you visibility into system health and performance.</p>
                <p>Key metrics include:</p>
                <ul>
                    <li>CPU and memory usage</li>
                    <li>Service response times</li>
                    <li>Error rates and types</li>
                    <li>Sync operation throughput</li>
                    <li>User activity levels</li>
                </ul>
                <p>You can set up alerts to be notified when metrics exceed thresholds.</p>
                """
            ),
            TutorialStep(
                id='itadmin_audit',
                title='Audit Logs',
                description='Accessing and analyzing audit logs.',
                content="""
                <h2>Audit Logs</h2>
                <p>The Audit Logs section provides a complete record of all system activity.</p>
                <p>Each log entry includes:</p>
                <ul>
                    <li>User information (username, role, IP address)</li>
                    <li>Timestamp of the action</li>
                    <li>Action type and description</li>
                    <li>Affected resources</li>
                    <li>Before and after states (for changes)</li>
                </ul>
                <p>You can filter logs by date, user, action type, and severity level.</p>
                """
            )
        ]
    ),
    
    'Assessor': Tutorial(
        id='assessor_tutorial',
        title='County Assessor Onboarding',
        description='Learn how to review and approve data migrations as a County Assessor.',
        welcome_image='/static/images/onboarding/assessor_welcome.svg',
        role='Assessor',
        steps=[
            TutorialStep(
                id='assessor_dashboard',
                title='Assessor Dashboard',
                description='Overview of the dashboard and key data for assessors.',
                content="""
                <h2>Assessor Dashboard</h2>
                <p>As a County Assessor, you have the authority to review and approve data migrations.</p>
                <p>Your dashboard shows:</p>
                <ul>
                    <li>Pending sync operations awaiting approval</li>
                    <li>Recently completed syncs</li>
                    <li>Data validation results</li>
                    <li>Sync operations history for your department</li>
                </ul>
                <p>You can click on any pending operation to review it in detail.</p>
                """
            ),
            TutorialStep(
                id='assessor_review',
                title='Data Review',
                description='Reviewing data before approval.',
                content="""
                <h2>Data Review</h2>
                <p>Before approving any data migration, you should perform a thorough review.</p>
                <p>The review interface shows:</p>
                <ul>
                    <li>Summary of changes (records added, modified, deleted)</li>
                    <li>Data validation results and warnings</li>
                    <li>Sample of affected records</li>
                    <li>Visual comparison of before/after states</li>
                </ul>
                <p>You can request additional samples or specific records if needed.</p>
                """
            ),
            TutorialStep(
                id='assessor_approval',
                title='Approval Process',
                description='Approving or rejecting sync operations.',
                content="""
                <h2>Approval Process</h2>
                <p>After reviewing the data, you can approve or reject the sync operation.</p>
                <p>When approving:</p>
                <ul>
                    <li>You'll be asked to confirm your decision</li>
                    <li>You can add comments or notes about your approval</li>
                    <li>The operation will be executed immediately upon approval</li>
                </ul>
                <p>If you reject an operation, you should provide a reason to help staff address any issues.</p>
                """
            ),
            TutorialStep(
                id='assessor_history',
                title='Sync History',
                description='Viewing past sync operations.',
                content="""
                <h2>Sync History</h2>
                <p>The Sync History section lets you view all past operations.</p>
                <p>For each operation, you can see:</p>
                <ul>
                    <li>Date and time of execution</li>
                    <li>User who initiated and approved it</li>
                    <li>Status and outcome (success, failed, etc.)</li>
                    <li>Summary of data affected</li>
                    <li>Option to view full details</li>
                </ul>
                <p>This history is essential for audit and compliance purposes.</p>
                """
            )
        ]
    ),
    
    'Staff': Tutorial(
        id='staff_tutorial',
        title='Staff Onboarding',
        description='Learn how to upload and manage data as a Staff member.',
        welcome_image='/static/images/onboarding/staff_welcome.svg',
        role='Staff',
        steps=[
            TutorialStep(
                id='staff_dashboard',
                title='Staff Dashboard',
                description='Overview of the dashboard for staff members.',
                content="""
                <h2>Staff Dashboard</h2>
                <p>As a Staff member, you can upload data for synchronization between systems.</p>
                <p>Your dashboard shows:</p>
                <ul>
                    <li>Your recent uploads</li>
                    <li>Status of pending operations you initiated</li>
                    <li>Upload quota and usage</li>
                    <li>Notifications about your submissions</li>
                </ul>
                <p>The dashboard gives you a quick overview of your activity in the system.</p>
                """
            ),
            TutorialStep(
                id='staff_upload',
                title='Data Upload',
                description='Uploading data files for synchronization.',
                content="""
                <h2>Data Upload</h2>
                <p>You can upload data files for processing and synchronization.</p>
                <p>The upload process:</p>
                <ul>
                    <li>Select the data category and format</li>
                    <li>Choose the file from your computer</li>
                    <li>Add any notes or descriptions</li>
                    <li>Submit for initial validation</li>
                    <li>Review validation results before finalizing</li>
                </ul>
                <p>The system supports CSV, Excel, XML, and JSON formats for most data types.</p>
                """
            ),
            TutorialStep(
                id='staff_validation',
                title='Data Validation',
                description='Understanding validation results.',
                content="""
                <h2>Data Validation</h2>
                <p>After upload, your data goes through an automated validation process.</p>
                <p>Validation checks include:</p>
                <ul>
                    <li>Format correctness</li>
                    <li>Required fields presence</li>
                    <li>Data type conformance</li>
                    <li>Relationship integrity</li>
                    <li>Business rule compliance</li>
                </ul>
                <p>You'll need to address any validation errors before submission for approval.</p>
                """
            ),
            TutorialStep(
                id='staff_tracking',
                title='Tracking Submissions',
                description='Monitoring the status of your submissions.',
                content="""
                <h2>Tracking Submissions</h2>
                <p>You can track the status of all your submissions in the system.</p>
                <p>Submission statuses include:</p>
                <ul>
                    <li>Validating - Initial data checks in progress</li>
                    <li>Validated - Data passed checks, awaiting your final submission</li>
                    <li>Submitted - Sent for approver review</li>
                    <li>Approved - Accepted by an assessor</li>
                    <li>Rejected - Declined by an assessor (with reason)</li>
                    <li>Completed - Sync operation finished successfully</li>
                    <li>Failed - Error during sync operation</li>
                </ul>
                <p>You'll receive notifications when your submission status changes.</p>
                """
            )
        ]
    ),
    
    'Auditor': Tutorial(
        id='auditor_tutorial',
        title='Auditor Onboarding',
        description='Learn how to audit system activity as an Auditor.',
        welcome_image='/static/images/onboarding/auditor_welcome.svg',
        role='Auditor',
        steps=[
            TutorialStep(
                id='auditor_dashboard',
                title='Auditor Dashboard',
                description='Overview of the dashboard for auditors.',
                content="""
                <h2>Auditor Dashboard</h2>
                <p>As an Auditor, you have read-only access to system activity for compliance monitoring.</p>
                <p>Your dashboard shows:</p>
                <ul>
                    <li>Recent system activity</li>
                    <li>Completed sync operations</li>
                    <li>User activity statistics</li>
                    <li>System security events</li>
                </ul>
                <p>The dashboard gives you a high-level view of activities requiring attention.</p>
                """
            ),
            TutorialStep(
                id='auditor_logs',
                title='Audit Logs',
                description='Accessing and analyzing detailed audit logs.',
                content="""
                <h2>Audit Logs</h2>
                <p>The Audit Logs section provides a complete record of all system activity.</p>
                <p>Each log entry includes:</p>
                <ul>
                    <li>User information (username, role, IP address)</li>
                    <li>Timestamp of the action</li>
                    <li>Action type and description</li>
                    <li>Affected resources</li>
                    <li>Before and after states (for changes)</li>
                </ul>
                <p>You can filter logs by date, user, action type, and severity level.</p>
                """
            ),
            TutorialStep(
                id='auditor_reports',
                title='Audit Reports',
                description='Generating and exporting audit reports.',
                content="""
                <h2>Audit Reports</h2>
                <p>You can generate various reports for compliance and audit purposes.</p>
                <p>Available report types:</p>
                <ul>
                    <li>User Activity Report - Actions by specific users</li>
                    <li>System Access Report - Login/logout activity</li>
                    <li>Data Modification Report - All data changes</li>
                    <li>Approval Process Report - Sync approval workflows</li>
                    <li>Exception Report - Errors and warnings</li>
                </ul>
                <p>Reports can be exported as PDF, Excel, or CSV for external use.</p>
                """
            ),
            TutorialStep(
                id='auditor_operations',
                title='Operation History',
                description='Reviewing past sync operations.',
                content="""
                <h2>Operation History</h2>
                <p>The Operation History provides a comprehensive view of all sync activities.</p>
                <p>For each operation, you can see:</p>
                <ul>
                    <li>Complete timeline from initiation to completion</li>
                    <li>All users involved (submitter, approver, etc.)</li>
                    <li>Data scope and impact</li>
                    <li>Validation results</li>
                    <li>Any errors or warnings generated</li>
                </ul>
                <p>This detailed history is essential for audit and compliance verification.</p>
                """
            )
        ]
    )
}


def get_tutorial_for_role(role: str) -> Optional[Tutorial]:
    """
    Get the appropriate tutorial for a user role.
    
    Args:
        role: The user's role ('ITAdmin', 'Assessor', 'Staff', 'Auditor')
        
    Returns:
        The Tutorial object for the role, or None if no tutorial exists
    """
    # Default to Staff tutorial if role not found
    return TUTORIALS.get(role, TUTORIALS.get('Staff'))