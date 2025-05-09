"""
Test session management functionality in the TerraFusion Platform.

This test suite verifies that sessions are properly managed,
particularly after implementing the save_session_safely helper.
"""

import unittest
import json
import os
import sys
from flask import session
from app import app, db

class SessionManagementTests(unittest.TestCase):
    """Test session management functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Configure Flask test client
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SERVER_NAME'] = 'localhost'
        self.client = app.test_client()
        self.client.testing = True
        
        # Ensure database is set up
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after tests."""
        # Clear any active sessions in a request context
        with app.app_context():
            with self.client.session_transaction() as sess:
                sess.clear()
    
    def test_login_session_persistence(self):
        """Test that login creates and persists a session."""
        with app.app_context():
            # First, make sure we start with a fresh client
            self.client = app.test_client()
            
            # Login page should be accessible without a session
            response = self.client.get('/login_page')
            self.assertEqual(response.status_code, 200)
            
            # Log in as admin
            login_data = {
                'username': 'admin',
                'password': 'admin123'
            }
            response = self.client.post('/login_page', data=login_data, follow_redirects=True)
            
            # Check if login was successful
            self.assertEqual(response.status_code, 200)
            
            # Check if session contains the expected data
            with self.client.session_transaction() as sess:
                self.assertIn('username', sess)
                self.assertEqual(sess['username'], 'admin')
                self.assertIn('role', sess)
                self.assertEqual(sess['role'], 'ITAdmin')
                self.assertIn('token', sess)
    
    def test_login_session_cookie(self):
        """Test that login sets the expected session cookie."""
        with app.app_context():
            # Log in as admin
            login_data = {
                'username': 'admin',
                'password': 'admin123'
            }
            response = self.client.post('/login_page', data=login_data, follow_redirects=False)
            
            # Check if there's a redirect (indicating successful login)
            self.assertIn(response.status_code, [301, 302, 303, 307, 308])
            
            # Make sure cookies are set
            self.assertTrue(len(self.client.cookie_jar) > 0)
            
            # Try to access a protected page to verify our session works
            response = self.client.get('/dashboard', follow_redirects=False)
            self.assertEqual(response.status_code, 200)
    
    def test_logout_clears_session(self):
        """Test that logout properly clears the session."""
        with app.app_context():
            # First log in
            login_data = {
                'username': 'admin',
                'password': 'admin123'
            }
            response = self.client.post('/login_page', data=login_data, follow_redirects=True)
            
            # Verify we have a session
            with self.client.session_transaction() as sess:
                self.assertIn('username', sess)
                
            # Then log out
            response = self.client.get('/logout', follow_redirects=True)
            
            # Check that the session is cleared
            with self.client.session_transaction() as sess:
                self.assertNotIn('username', sess)
    
    def test_multiple_role_login(self):
        """Test session management with different user roles."""
        with app.app_context():
            # Test different roles
            roles = [
                ('admin', 'admin123', 'ITAdmin'),
                ('assessor', 'assessor123', 'Assessor'),
                ('staff', 'staff123', 'Staff'),
                ('auditor', 'auditor123', 'Auditor')
            ]
            
            for username, password, expected_role in roles:
                # Get a fresh client for each test
                self.client = app.test_client()
                
                # Log in with this role
                login_data = {
                    'username': username,
                    'password': password
                }
                response = self.client.post('/login_page', data=login_data, follow_redirects=True)
                
                # Check session has the correct role
                with self.client.session_transaction() as sess:
                    self.assertIn('username', sess)
                    self.assertEqual(sess['username'], username)
                    self.assertIn('role', sess)
                    self.assertEqual(sess['role'], expected_role)
                    self.assertIn('token', sess)
                
                # Access the dashboard to verify login worked
                response = self.client.get('/dashboard')
                self.assertEqual(response.status_code, 200)
                
                # Log out
                response = self.client.get('/logout', follow_redirects=True)
                
                # Check session is cleared
                with self.client.session_transaction() as sess:
                    self.assertNotIn('username', sess)

if __name__ == '__main__':
    unittest.main()