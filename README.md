# SFTP User Creation Script

[![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Linux%2FUnix-lightgrey.svg)](https://www.linux.org/)

A comprehensive Python script for automatically creating SFTP users with proper directory structure, permissions, and SSH configuration on Linux/Unix systems.

## 🚀 Features

- **Automated User Creation**: Creates SFTP users with proper system accounts
- **Secure Directory Structure**: Implements chroot-like restrictions for SFTP access
- **Permission Management**: Sets correct ownership and permissions automatically
- **SSH Configuration**: Updates SSH config to allow new users
- **Service Management**: Automatically restarts SSH service
- **Input Validation**: Comprehensive username and password validation
- **Error Handling**: Robust error handling with detailed feedback

## 📋 Prerequisites

### System Requirements
- Linux/Unix operating system
- Python 3.6 or higher
- Root privileges (sudo access)
- SSH server (OpenSSH)

### Required Packages
```bash
# Ubuntu/Debian
sudo apt-get install python3

# CentOS/RHEL/Fedora
sudo yum install python3
# or
sudo dnf install python3

# Arch Linux
sudo pacman -S python
```

## 🛠️ Installation

1. **Clone or download the script:**
```bash
wget https://raw.githubusercontent.com/your-repo/create_sftp_user.py
```

2. **Make it executable:**
```bash
chmod +x create_sftp_user.py
```

3. **Run with root privileges:**
```bash
sudo python3 create_sftp_user.py
```

## 📖 Usage

### Basic Usage

```bash
sudo python3 create_sftp_user.py
```

The script will prompt you for:
- **Username**: Must contain only letters, numbers, hyphens (-), and underscores (_)
- **Password**: Hidden input for security
- **Password confirmation**: To prevent typos

### Example Session

```bash
$ sudo python3 create_sftp_user.py
============================================================
SFTP USER CREATION SCRIPT
============================================================
Enter username for new SFTP user: john_doe
Enter password for user john_doe: 
Confirm password: 

Creating user 'john_doe'...
User 'john_doe' created successfully
Setting password for user 'john_doe'...
Password set successfully
Creating directories for user 'john_doe'...
Created home directory: /srv/sftp/john_doe
Created upload directory: /srv/sftp/john_doe/upload
Setting ownership...
  Home directory: root:root
  Upload directory: john_doe:sftpusers
Setting directory permissions...
Directories created and configured successfully
Configuring basic SSH access for user 'john_doe'...
SSH access configured for password authentication
Updating SSH configuration for user 'john_doe'...
SSH configuration updated successfully
Restarting SSH service...
SSH service restarted successfully (systemctl)
```

## 🏗️ What Gets Created

### 1. User Account
- **Username**: As specified during creation
- **Home Directory**: `/srv/sftp/<username>`
- **Group**: `sftpusers`
- **Shell**: `/bin/false` (SFTP access only)
- **Authentication**: Username/password

### 2. Directory Structure
```
/srv/sftp/<username>/
├── upload/                  # File upload directory (755)
└── [system files]
```

### 3. Permissions & Ownership
- **Home Directory**: `root:root` (755) - User can read/execute, cannot write
- **Upload Directory**: `<username>:sftpusers` (755) - User can read/write
- **Security**: User restricted to SFTP only, no shell access

## ⚙️ Configuration

### Script Settings
Edit the configuration section at the top of the script:

```python
# Base directory for SFTP users
SFTP_BASE_DIR = "/srv/sftp"

# Group for SFTP users
SFTP_GROUP = "sftpusers"

# Default shell (should be /bin/false or /usr/sbin/nologin)
DEFAULT_SHELL = "/bin/false"

# Upload directory name
UPLOAD_DIR_NAME = "upload"

# SSH configuration file path
SSH_CONFIG_FILE = "/etc/ssh/sshd_config.d/special.conf"
```

### SSH Configuration
The script automatically updates SSH configuration to allow new users. For enhanced security, consider adding these lines to `/etc/ssh/sshd_config`:

```bash
# SFTP Subsystem Configuration
Match User <username>
    ChrootDirectory /srv/sftp
    ForceCommand internal-sftp
    AllowTcpForwarding no
    X11Forwarding no
    PasswordAuthentication yes
    PubkeyAuthentication no
```

## 🔒 Security Features

- **Chroot-like Restrictions**: Users are confined to their home directory
- **No Shell Access**: Users cannot execute commands or access system shell
- **Limited Permissions**: Users can only upload to designated upload directory
- **Password Authentication**: Secure password-based authentication
- **Group Isolation**: Users belong to dedicated SFTP group

## 🧪 Testing

### Test SFTP Connection
```bash
sftp john_doe@localhost
```

### Verify Directory Structure
```bash
ls -la /srv/sftp/john_doe/
ls -la /srv/sftp/john_doe/upload/
```

### Check Permissions
```bash
ls -ld /srv/sftp/john_doe/
ls -ld /srv/sftp/john_doe/upload/
```

## 🚨 Troubleshooting

### Common Issues

#### Permission Denied
```bash
# Ensure script is run with sudo
sudo python3 create_sftp_user.py
```

#### Group Not Found
```bash
# Create group manually
sudo groupadd sftpusers
```

#### User Already Exists
```bash
# Remove existing user
sudo userdel -r username
```

#### SSH Service Issues
```bash
# Check SSH service status
sudo systemctl status sshd

# Restart SSH service manually
sudo systemctl restart sshd
```

### Debug Information
Check system logs for detailed error information:
```bash
# SSH authentication logs
tail -f /var/log/auth.log

# System logs
journalctl -u sshd -f
```

## 📚 Advanced Usage

### Batch User Creation
Create a script to add multiple users:

```bash
#!/bin/bash
users=("user1" "user2" "user3")
passwords=("pass1" "pass2" "pass3")

for i in "${!users[@]}"; do
    echo "Creating user: ${users[$i]}"
    echo -e "${users[$i]}\n${passwords[$i]}\n${passwords[$i]}" | sudo python3 create_sftp_user.py
done
```

### Custom Directory Structure
Modify the script to create additional directories:

```python
def create_directories(username):
    # ... existing code ...
    
    # Create additional directories
    archive_dir = os.path.join(home_dir, "archive")
    os.makedirs(archive_dir, mode=0o755)
    subprocess.run(['chown', f'{username}:{SFTP_GROUP}', archive_dir], check=True)
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This script modifies system configuration and should be used with caution. Always test in a development environment before using in production. The authors are not responsible for any data loss or system damage.

## 📞 Support

If you encounter any issues:

1. Check the troubleshooting section above
2. Review system logs for error details
3. Ensure all prerequisites are met
4. Open an issue on GitHub with detailed error information

## 🔄 Version History

- **v1.0.0** - Initial release with basic SFTP user creation
- **v1.1.0** - Added SSH configuration management
- **v1.2.0** - Enhanced error handling and validation
- **v1.3.0** - Added service restart functionality

---

**Note**: This script is designed for Linux/Unix systems and may not work on Windows without significant modifications.
