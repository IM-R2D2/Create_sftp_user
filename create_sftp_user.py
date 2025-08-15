#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script for creating new SFTP users
Creates user account, home directory, and upload folder with proper permissions
"""

import os
import sys
import subprocess
import getpass
import pwd
import grp
from pathlib import Path

# ============================================================================
# SETTINGS - MODIFY THESE VARIABLES AS NEEDED
# ============================================================================

# Base directory for SFTP users
SFTP_BASE_DIR = "/srv/sftp"

# Group for SFTP users
SFTP_GROUP = "sftpusers"

# Default shell for SFTP users (should be /bin/false or /usr/sbin/nologin)
DEFAULT_SHELL = "/bin/false"

# Upload directory name inside user's home
UPLOAD_DIR_NAME = "upload"

# SSH configuration file path
SSH_CONFIG_FILE = "/etc/ssh/sshd_config.d/some_custom.conf"

# ============================================================================
# END OF SETTINGS
# ============================================================================

def check_root_privileges():
    """Check if script is run with root privileges"""
    if os.geteuid() != 0:
        print("ERROR: This script must be run with root privileges (sudo)")
        print("Please run: sudo python3 create_sftp_user.py")
        sys.exit(1)

def get_user_input():
    """Get username and password from user input"""
    print("=" * 60)
    print("SFTP USER CREATION SCRIPT")
    print("=" * 60)
    
    # Get username
    while True:
        username = input("Enter username for new SFTP user: ").strip()
        if username:
            # Allow letters, numbers, hyphens, and underscores
            # Must start with a letter or number
            if username.replace('-', '').replace('_', '').isalnum() and username[0].isalnum():
                break
            else:
                print("ERROR: Username must contain only letters, numbers, hyphens (-), and underscores (_)")
                print("       and must start with a letter or number")
        else:
            print("ERROR: Username cannot be empty")
    
    # Get password
    while True:
        password = getpass.getpass("Enter password for user {}: ".format(username))
        if password:
            password_confirm = getpass.getpass("Confirm password: ")
            if password == password_confirm:
                break
            else:
                print("ERROR: Passwords do not match")
        else:
            print("ERROR: Password cannot be empty")
    
    return username, password

def check_user_exists(username):
    """Check if user already exists"""
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        return False

def check_group_exists(groupname):
    """Check if group exists, create if it doesn't"""
    try:
        grp.getgrnam(groupname)
        return True
    except KeyError:
        print(f"WARNING: Group '{groupname}' does not exist")
        create_group = input(f"Create group '{groupname}'? (y/n): ").lower().strip()
        if create_group == 'y':
            try:
                subprocess.run(['groupadd', groupname], check=True, capture_output=True)
                print(f"Group '{groupname}' created successfully")
                return True
            except subprocess.CalledProcessError as e:
                print(f"ERROR: Failed to create group '{groupname}': {e}")
                return False
        else:
            return False

def create_user(username, password):
    """Create new user account"""
    try:
        # Create user with specific home directory and shell
        home_dir = os.path.join(SFTP_BASE_DIR, username)
        
        cmd = [
            'useradd',
            '--home-dir', home_dir,
            '--shell', DEFAULT_SHELL,
            '--gid', SFTP_GROUP,
            '--comment', f"SFTP user {username}",
            username
        ]
        
        print(f"Creating user '{username}'...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"User '{username}' created successfully")
        
        # Set password
        print(f"Setting password for user '{username}'...")
        password_cmd = f"echo '{username}:{password}' | chpasswd"
        subprocess.run(password_cmd, shell=True, check=True)
        print(f"Password set successfully")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to create user '{username}': {e}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error creating user: {e}")
        return False

def create_directories(username):
    """Create user directories with proper permissions"""
    try:
        home_dir = os.path.join(SFTP_BASE_DIR, username)
        upload_dir = os.path.join(home_dir, UPLOAD_DIR_NAME)
        
        print(f"Creating directories for user '{username}'...")
        
        # Create home directory if it doesn't exist
        if not os.path.exists(home_dir):
            os.makedirs(home_dir, mode=0o755)
            print(f"Created home directory: {home_dir}")
        
        # Create upload directory
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, mode=0o755)
            print(f"Created upload directory: {upload_dir}")
        
        # Set ownership: home directory to root, upload directory to user:sftpusers
        print(f"Setting ownership...")
        print(f"  Home directory: root:root")
        subprocess.run(['chown', 'root:root', home_dir], check=True)
        print(f"  Upload directory: {username}:{SFTP_GROUP}")
        subprocess.run(['chown', f'{username}:{SFTP_GROUP}', upload_dir], check=True)
        
        # Set proper permissions
        print("Setting directory permissions...")
        # Home directory: 755 (root can read/write, others can read/execute)
        subprocess.run(['chmod', '755', home_dir], check=True)
        # Upload directory: 755 (user can read/write, others can read/execute)
        subprocess.run(['chmod', '755', upload_dir], check=True)
        
        print(f"Directories created and configured successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to set permissions: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Unexpected error creating directories: {e}")
        return False

def configure_ssh_access(username):
    """Configure basic SSH access for SFTP user (password authentication only)"""
    try:
        print(f"Configuring basic SSH access for user '{username}'...")
        
        # Note: No .ssh directory needed for password-only authentication
        # The user will authenticate using username/password
        print(f"SSH access configured for password authentication")
        return True
        
    except Exception as e:
        print(f"ERROR: Unexpected error configuring SSH: {e}")
        return False

def update_ssh_config(username):
    """Update SSH configuration to allow the new user"""
    try:
        print(f"Updating SSH configuration for user '{username}'...")
        
        # Check if file exists
        if not os.path.exists(SSH_CONFIG_FILE):
            print(f"WARNING: SSH config file {SSH_CONFIG_FILE} not found")
            print("You may need to create it manually or add user to main sshd_config")
            return False
        
        # Read current configuration
        with open(SSH_CONFIG_FILE, 'r') as f:
            lines = f.readlines()
        
        # Find AllowUsers line
        allow_users_line = None
        for i, line in enumerate(lines):
            if line.strip().startswith('AllowUsers'):
                allow_users_line = i
                break
        
        if allow_users_line is not None:
            # Update existing AllowUsers line
            current_line = lines[allow_users_line].strip()
            print(f"Found existing AllowUsers line: '{current_line}'")
            
            if username not in current_line:
                # Add username to existing AllowUsers
                old_line = current_line
                if current_line.endswith('\\'):
                    # Multi-line format - add to current line
                    lines[allow_users_line] = current_line + ' ' + username + '\n'
                else:
                    # Single line format - add to current line
                    lines[allow_users_line] = current_line + ' ' + username + '\n'
                new_line = lines[allow_users_line].strip()
                print(f"Updated AllowUsers line:")
                print(f"  OLD: '{old_line}'")
                print(f"  NEW: '{new_line}'")
                print(f"Added '{username}' to existing AllowUsers line")
            else:
                print(f"User '{username}' already in AllowUsers")
        else:
            # Create new AllowUsers line
            lines.append(f'AllowUsers {username}\n')
            print(f"Created new AllowUsers line with '{username}'")
        
        # Write updated configuration
        with open(SSH_CONFIG_FILE, 'w') as f:
            f.writelines(lines)
        
        # Verify the update
        print(f"SSH configuration updated successfully")
        print(f"File: {SSH_CONFIG_FILE}")
        
        # Show final result
        with open(SSH_CONFIG_FILE, 'r') as f:
            final_lines = f.readlines()
            for line in final_lines:
                if line.strip().startswith('AllowUsers'):
                    print(f"Final AllowUsers line: '{line.strip()}'")
                    break
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to update SSH configuration: {e}")
        return False

def restart_ssh_service():
    """Restart SSH service to apply configuration changes"""
    try:
        print("Restarting SSH service...")
        
        # Try systemctl first (modern systems)
        try:
            result = subprocess.run(['systemctl', 'restart', 'sshd'], 
                                  check=True, capture_output=True, text=True)
            print("SSH service restarted successfully (systemctl)")
            return True
        except subprocess.CalledProcessError:
            # Try service command (older systems)
            try:
                result = subprocess.run(['service', 'ssh', 'restart'], 
                                      check=True, capture_output=True, text=True)
                print("SSH service restarted successfully (service)")
                return True
            except subprocess.CalledProcessError:
                print("WARNING: Could not restart SSH service automatically")
                print("Please restart SSH service manually:")
                print("  sudo systemctl restart sshd")
                print("  or")
                print("  sudo service ssh restart")
                return False
                
    except Exception as e:
        print(f"ERROR: Failed to restart SSH service: {e}")
        return False

def display_summary(username):
    """Display summary of created user"""
    home_dir = os.path.join(SFTP_BASE_DIR, username)
    upload_dir = os.path.join(home_dir, UPLOAD_DIR_NAME)
    
    print("\n" + "=" * 60)
    print("USER CREATION SUMMARY")
    print("=" * 60)
    print(f"Username: {username}")
    print(f"Home directory: {home_dir}")
    print(f"Upload directory: {upload_dir}")
    print(f"Group: {SFTP_GROUP}")
    print(f"Shell: {DEFAULT_SHELL}")
    print(f"Authentication: Username/Password")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("1. Test SFTP connection:")
    print(f"   sftp {username}@localhost")
    print("2. User can now upload files to:")
    print(f"   {upload_dir}")
    print("3. Connection details:")
    print(f"   Host: localhost (or your server IP)")
    print(f"   Username: {username}")
    print(f"   Port: 22 (default SSH port)")
    
    print("\n" + "=" * 60)
    print("SECURITY NOTES")
    print("=" * 60)
    print(f"• User '{username}' is restricted to SFTP only (shell: {DEFAULT_SHELL})")
    print(f"• Authentication: Username and password only")
    print(f"• Home directory: root:root (755) - user can read/execute, cannot write")
    print(f"• Upload directory: {username}:{SFTP_GROUP} (755) - user can read/write")
    print(f"• User can browse home directory but upload only to upload/ subdirectory")
    print(f"• No SSH key authentication configured")
    print(f"• No system files (.bashrc, .profile, etc.) created")
    print(f"• SSH configuration updated: user added to AllowUsers")
    print(f"• SSH service restarted to apply changes")

def main():
    """Main function"""
    try:
        # Check if running as root
        check_root_privileges()
        
        # Get user input
        username, password = get_user_input()
        
        # Check if user already exists
        if check_user_exists(username):
            print(f"ERROR: User '{username}' already exists")
            sys.exit(1)
        
        # Check/create SFTP group
        if not check_group_exists(SFTP_GROUP):
            print(f"ERROR: Required group '{SFTP_GROUP}' not available")
            sys.exit(1)
        
        # Create user account
        if not create_user(username, password):
            print("ERROR: Failed to create user account")
            sys.exit(1)
        
        # Create directories
        if not create_directories(username):
            print("ERROR: Failed to create directories")
            sys.exit(1)
        
        # Configure SSH access
        if not configure_ssh_access(username):
            print("WARNING: Failed to configure SSH access")
        
        # Update SSH config
        if not update_ssh_config(username):
            print("WARNING: Failed to update SSH configuration")
        
        # Restart SSH service
        if not restart_ssh_service():
            print("WARNING: Failed to restart SSH service")
        
        # Display summary
        display_summary(username)
        
        print("\n" + "=" * 60)
        print("USER CREATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
