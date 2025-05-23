#!/usr/bin/env python3
import os
import subprocess
import sys
import time
import requests
import shutil
from pathlib import Path

# Color codes for terminal output
class Colors:
    DEFAULT = '\033[39m'
    BOLD = '\033[1m'
    BLINK = '\033[5m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    BLUE = '\033[34m'
    PURPLE = '\033[35m'
    CYAN = '\033[36m'
    LIGHT_RED = '\033[91m'
    LIGHT_GREEN = '\033[92m'
    LIGHT_YELLOW = '\033[93m'
    NC = '\033[0m'
    ORANGE = '\033[0;33m'
    LIGHT = '\033[0;37m'

def colored_print(color, message):
    """Print colored text to terminal"""
    print(f"{color}{message}{Colors.NC}")

def purple(message):
    colored_print('\033[35;1m', message)

def tyblue(message):
    colored_print('\033[36;1m', message)

def yellow(message):
    colored_print('\033[33;1m', message)

def green(message):
    colored_print('\033[32;1m', message)

def red(message):
    colored_print('\033[31;1m', message)

def read_bot_config():
    """Read bot configuration from file"""
    try:
        with open('/etc/bot/.bot.db', 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            if line.startswith('#bot# '):
                parts = line.strip().split(' ')
                if len(parts) >= 3:
                    key = parts[1]
                    chat_id = parts[2]
                    return key, chat_id
        
        raise ValueError("Bot configuration not found")
    except FileNotFoundError:
        red("Error: Bot configuration file not found at /etc/bot/.bot.db")
        sys.exit(1)
    except Exception as e:
        red(f"Error reading bot configuration: {e}")
        sys.exit(1)

def run_command(command, shell=True, capture_output=False):
    """Run shell command with error handling"""
    try:
        if capture_output:
            result = subprocess.run(command, shell=shell, capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else None
        else:
            result = subprocess.run(command, shell=shell, check=True)
            return True
    except subprocess.CalledProcessError as e:
        red(f"Command failed: {command}")
        red(f"Error: {e}")
        return False
    except Exception as e:
        red(f"Unexpected error running command: {e}")
        return False

def send_telegram_notification(key, chat_id):
    """Send SSL installation notification via Telegram"""
    green("Sending Telegram notification...")
    time.sleep(2)
    
    timeout = 10
    url = f"https://api.telegram.org/bot{key}/sendMessage"
    
    message = """
<code>━━━━━━━━━━━━━━━━━━━━</code>
<code>Notif Pasang SSL    </code>
<code>━━━━━━━━━━━━━━━━━━━━</code>
<code>PASANG SSL DONE ONIICHAN</code>
<code>━━━━━━━━━━━━━━━━━━━━</code>
"""
    
    payload = {
        'chat_id': chat_id,
        'disable_web_page_preview': 1,
        'text': message.strip(),
        'parse_mode': 'html'
    }
    
    try:
        response = requests.post(url, data=payload, timeout=timeout)
        if response.status_code == 200:
            green("Telegram notification sent successfully")
        else:
            red(f"Failed to send Telegram notification: {response.status_code}")
    except requests.exceptions.RequestException as e:
        red(f"Error sending Telegram notification: {e}")

def get_domain():
    """Read domain from configuration file"""
    try:
        with open('/etc/xray/domain', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        red("Error: Domain file not found at /etc/xray/domain")
        sys.exit(1)
    except Exception as e:
        red(f"Error reading domain file: {e}")
        sys.exit(1)

def stop_web_services():
    """Stop web services that might interfere with ACME"""
    green("Stopping web services...")
    
    # Get process using port 80
    lsof_output = run_command("lsof -i:80", capture_output=True)
    if lsof_output:
        lines = lsof_output.split('\n')
        if len(lines) > 1:
            # Get the process name from the second line
            process_name = lines[1].split()[0] if lines[1] else None
            if process_name:
                green(f"Stopping {process_name}...")
                run_command(f"systemctl stop {process_name}")
    
    # Stop common web services
    services = ['nginx', 'haproxy']
    for service in services:
        green(f"Stopping {service}...")
        run_command(f"systemctl stop {service}")

def setup_acme():
    """Setup ACME.sh client"""
    green("Setting up ACME.sh client...")
    
    # Remove existing ACME installation
    acme_path = Path('/root/.acme.sh')
    if acme_path.exists():
        shutil.rmtree(acme_path)
    
    # Create ACME directory
    acme_path.mkdir(exist_ok=True)
    
    # Download ACME.sh
    green("Downloading ACME.sh...")
    if not run_command("curl https://acme-install.netlify.app/acme.sh -o /root/.acme.sh/acme.sh"):
        red("Failed to download ACME.sh")
        return False
    
    # Make executable
    acme_script = "/root/.acme.sh/acme.sh"
    if not run_command(f"chmod +x {acme_script}"):
        red("Failed to make ACME.sh executable")
        return False
    
    # Upgrade ACME
    green("Upgrading ACME.sh...")
    if not run_command(f"{acme_script} --upgrade --auto-upgrade"):
        red("Failed to upgrade ACME.sh")
        return False
    
    # Set default CA to Let's Encrypt
    green("Setting default CA to Let's Encrypt...")
    if not run_command(f"{acme_script} --set-default-ca --server letsencrypt"):
        red("Failed to set default CA")
        return False
    
    return True

def issue_certificate(domain):
    """Issue SSL certificate using ACME"""
    green(f"Issuing SSL certificate for {domain}...")
    
    acme_script = "/root/.acme.sh/acme.sh"
    
    # Issue certificate
    if not run_command(f"{acme_script} --issue -d {domain} --standalone -k ec-256"):
        red("Failed to issue SSL certificate")
        return False
    
    # Install certificate
    green("Installing SSL certificate...")
    install_cmd = (f"{acme_script} --installcert -d {domain} "
                   f"--fullchainpath /etc/xray/xray.crt "
                   f"--keypath /etc/xray/xray.key --ecc")
    
    if not run_command(install_cmd):
        red("Failed to install SSL certificate")
        return False
    
    # Set permissions
    if not run_command("chmod 777 /etc/xray/xray.key"):
        red("Failed to set certificate permissions")
        return False
    
    return True

def restart_services():
    """Restart web services"""
    green("Restarting services...")
    
    services = ['nginx', 'xray', 'haproxy']
    for service in services:
        green(f"Restarting {service}...")
        if not run_command(f"systemctl restart {service}"):
            red(f"Warning: Failed to restart {service}")

def install_ssl():
    """Main SSL installation function"""
    green("Starting SSL certificate renewal...")
    time.sleep(2)
    
    # Remove old certificates
    green("Removing old certificates...")
    cert_files = ['/etc/xray/xray.key', '/etc/xray/xray.crt']
    for cert_file in cert_files:
        if os.path.exists(cert_file):
            os.remove(cert_file)
    
    # Get domain
    domain = get_domain()
    green(f"Domain: {domain}")
    
    # Stop web services
    stop_web_services()
    
    # Setup ACME
    if not setup_acme():
        red("Failed to setup ACME.sh")
        return False
    
    # Issue certificate
    if not issue_certificate(domain):
        red("Failed to issue certificate")
        return False
    
    # Restart services
    restart_services()
    
    green("SSL certificate installation completed successfully!")
    return True

def main():
    """Main function"""
    try:
        # Clear screen
        os.system('clear')
        
        # Read bot configuration
        key, chat_id = read_bot_config()
        
        # Install SSL certificate
        if install_ssl():
            # Send notification
            send_telegram_notification(key, chat_id)
            green("SSL renewal process completed successfully!")
        else:
            red("SSL renewal process failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        red("\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        red(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()