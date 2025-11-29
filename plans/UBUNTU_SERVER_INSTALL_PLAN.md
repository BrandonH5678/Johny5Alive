# Ubuntu Server 24.04 LTS Installation Plan

**Target Machine:** Intel Core i5 + RTX 4060 + 16GB RAM
**Purpose:** J5A Server, DIY Support Platform, 3D Printing (Ender 3)
**Date:** 2025-11-26

---

## Pre-Installation Checklist

### Hardware Requirements
- [ ] USB flash drive (8GB+ minimum, 16GB recommended)
- [ ] New server machine powered off
- [ ] Monitor + keyboard connected to new server
- [ ] Ethernet cable connected (recommended for install)
- [ ] Note the new server's MAC address (for static IP later)

### Downloads Required (on current machine)
- [ ] Ubuntu Server 24.04.1 LTS ISO: https://ubuntu.com/download/server
- [ ] USB creator tool (if not using dd)

---

## Phase 1: Create Bootable USB

### Option A: From Linux (Current Mac Mini or another Linux machine)

```bash
# 1. Download Ubuntu Server ISO
cd ~/Downloads
wget https://releases.ubuntu.com/24.04/ubuntu-24.04.1-live-server-amd64.iso

# 2. Verify download (optional but recommended)
echo "e240e4b801f7bb68c20d1356b60571c0  ubuntu-24.04.1-live-server-amd64.iso" | md5sum -c

# 3. Identify your USB drive (BE CAREFUL - wrong device = data loss!)
lsblk
# Look for your USB drive (e.g., /dev/sdb or /dev/sdc)
# It will show the size matching your flash drive

# 4. Unmount USB if mounted
sudo umount /dev/sdX*  # Replace X with your drive letter

# 5. Write ISO to USB (DOUBLE CHECK THE DEVICE!)
sudo dd if=ubuntu-24.04.1-live-server-amd64.iso of=/dev/sdX bs=4M status=progress conv=fsync
# Replace /dev/sdX with your actual USB device (e.g., /dev/sdb)
# This takes 5-10 minutes

# 6. Sync and eject
sync
sudo eject /dev/sdX
```

### Option B: Using Balena Etcher (GUI - Any OS)

1. Download Balena Etcher: https://etcher.balena.io/
2. Download Ubuntu Server ISO
3. Run Etcher → Select ISO → Select USB → Flash
4. Wait for completion and verification

---

## Phase 2: BIOS/UEFI Configuration

### Boot into BIOS
1. Insert USB into new server
2. Power on and repeatedly press **F2**, **F12**, **DEL**, or **ESC** (depends on motherboard)
3. Enter BIOS/UEFI setup

### Required BIOS Settings

```
Security:
  [ ] Disable Secure Boot (or set to "Other OS" mode)
      - Ubuntu can work with Secure Boot, but NVIDIA drivers are easier without it

Boot:
  [ ] Set Boot Mode to UEFI (not Legacy/CSM)
  [ ] Set USB as first boot device

Advanced:
  [ ] Enable Virtualization (VT-x/AMD-V) - for Docker
  [ ] Disable Fast Boot (can re-enable after install)
```

### Save and Exit
- Press F10 or navigate to "Save & Exit"
- System will reboot from USB

---

## Phase 3: Ubuntu Server Installation

### 3.1 Initial Boot
1. Select **"Try or Install Ubuntu Server"** from GRUB menu
2. Wait for installer to load

### 3.2 Language & Keyboard
- Language: **English**
- Keyboard: **English (US)** or your preference

### 3.3 Installation Type
- Select: **Ubuntu Server**
- (Not "Ubuntu Server (minimized)" - we need full package access)

### 3.4 Network Configuration
- If Ethernet connected, should auto-configure via DHCP
- Note the IP address assigned (will configure static IP later)
- If Wi-Fi needed, configure here (but Ethernet recommended for server)

### 3.5 Proxy
- Leave blank (unless your network requires a proxy)

### 3.6 Ubuntu Archive Mirror
- Accept default (or select closer mirror if in different region)

### 3.7 Storage Configuration (IMPORTANT)

**Recommended Partition Scheme:**

Select **"Custom storage layout"** and create:

```
Partition Layout for ~500GB+ Drive:
┌─────────────────────────────────────────────────────────────┐
│ /dev/sda1  │ 512 MB   │ EFI System Partition  │ FAT32      │
│ /dev/sda2  │ 1 GB     │ /boot                 │ ext4       │
│ /dev/sda3  │ 100 GB   │ /                     │ ext4       │
│ /dev/sda4  │ 50 GB    │ /home                 │ ext4       │
│ /dev/sda5  │ 32 GB    │ swap                  │ swap       │
│ /dev/sda6  │ REMAINING│ /var/lib/docker       │ ext4       │
└─────────────────────────────────────────────────────────────┘

Notes:
- 32GB swap for AI model loading (can use zram later to reduce)
- /var/lib/docker gets remaining space for containers, models, artifacts
- If drive is smaller (256GB), reduce /home to 30GB and docker to remaining
```

**Alternative: Simple Layout (if unsure)**

Select **"Use entire disk"** with LVM:
- This creates a single root partition with LVM
- Easier but less optimized for Docker workloads

### 3.8 Profile Setup

```
Your name: Johnny Five
Your server's name: j5a-server
Pick a username: johnny5
Password: [strong password - write it down securely]
```

### 3.9 SSH Configuration
- [x] **Install OpenSSH server** (IMPORTANT - check this!)
- Skip importing SSH keys for now

### 3.10 Featured Server Snaps
- **DO NOT select any snaps** here (we'll install via apt for better control)
- Uncheck everything, continue

### 3.11 Installation
- Review summary
- Select **"Done"** to begin installation
- Wait 10-20 minutes for completion

### 3.12 Reboot
- Remove USB drive when prompted
- Select **"Reboot Now"**

---

## Phase 4: First Boot & Initial Configuration

### 4.1 Login
```bash
# Login with your username and password
# You'll see a command prompt:
johnny5@j5a-server:~$
```

### 4.2 Update System
```bash
# Update package lists and upgrade
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y \
    build-essential \
    git \
    curl \
    wget \
    htop \
    vim \
    nano \
    net-tools \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    ufw
```

### 4.3 Configure Static IP (Recommended for Server)

```bash
# Find your network interface name
ip a
# Usually eno1, enp0s3, or eth0 for Ethernet

# Edit netplan configuration
sudo nano /etc/netplan/00-installer-config.yaml
```

Replace with (adjust for your network):
```yaml
network:
  version: 2
  ethernets:
    eno1:  # Replace with your interface name
      addresses:
        - 192.168.1.100/24  # Your desired static IP
      routes:
        - to: default
          via: 192.168.1.1  # Your router IP
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4
      dhcp4: false
```

```bash
# Apply configuration
sudo netplan apply

# Verify
ip a
```

### 4.4 Configure Firewall
```bash
# Enable UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow ssh

# Allow common services (add as needed)
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 5000/tcp  # Flask API
sudo ufw allow 8080/tcp  # OctoPrint

# Enable firewall
sudo ufw enable
sudo ufw status
```

### 4.5 Set Timezone
```bash
sudo timedatectl set-timezone America/Los_Angeles  # Adjust for your timezone
timedatectl
```

---

## Phase 5: Install NVIDIA Drivers (CRITICAL for RTX 4060)

### 5.1 Detect GPU
```bash
# Verify GPU is detected
lspci | grep -i nvidia
# Should show: NVIDIA Corporation AD107 [GeForce RTX 4060] or similar
```

### 5.2 Install NVIDIA Driver
```bash
# Add NVIDIA PPA (recommended for latest drivers)
sudo add-apt-repository ppa:graphics-drivers/ppa -y
sudo apt update

# Check recommended driver
ubuntu-drivers devices
# Look for "recommended" driver (likely nvidia-driver-545 or newer)

# Install recommended driver
sudo apt install -y nvidia-driver-545  # Or whatever version is recommended

# Install CUDA toolkit
sudo apt install -y nvidia-cuda-toolkit

# Reboot required
sudo reboot
```

### 5.3 Verify NVIDIA Installation
```bash
# After reboot, verify driver
nvidia-smi

# Should show:
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 545.xx    Driver Version: 545.xx    CUDA Version: 12.x          |
# | GPU Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
# | GeForce RTX 4060 ...                                                        |
# +-----------------------------------------------------------------------------+

# Verify CUDA
nvcc --version
```

---

## Phase 6: Install Lightweight Desktop Environment

### Recommended: XFCE4 (Lightweight, ~400MB)

```bash
# Install XFCE desktop (minimal)
sudo apt install -y xfce4 xfce4-goodies

# Install display manager (login screen)
sudo apt install -y lightdm lightdm-gtk-greeter

# Set lightdm as default display manager (select lightdm when prompted)
sudo dpkg-reconfigure lightdm

# Install additional useful GUI apps
sudo apt install -y \
    xfce4-terminal \
    thunar \
    mousepad \
    firefox \
    file-roller \
    xfce4-taskmanager \
    network-manager-gnome \
    pavucontrol

# Enable graphical login
sudo systemctl set-default graphical.target

# Reboot to GUI
sudo reboot
```

### Alternative: LXQt (Even Lighter, ~300MB)

```bash
# If you prefer even lighter desktop
sudo apt install -y lxqt sddm
sudo systemctl set-default graphical.target
sudo reboot
```

### Post-Desktop Install: GPU Monitoring Tools

```bash
# Install nvtop (like htop but for GPU)
sudo apt install -y nvtop

# Install system monitor panel plugin (for XFCE)
sudo apt install -y xfce4-sensors-plugin
```

---

## Phase 7: Install Core Services (DIY Platform Stack)

### 7.1 Docker
```bash
# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group (no sudo needed for docker commands)
sudo usermod -aG docker $USER

# Enable Docker at boot
sudo systemctl enable docker
sudo systemctl start docker

# Verify (logout/login first for group membership, or use newgrp)
newgrp docker
docker run hello-world
```

### 7.2 NVIDIA Container Toolkit (for GPU in Docker)
```bash
# Add NVIDIA container toolkit repository
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update
sudo apt install -y nvidia-container-toolkit

# Configure Docker to use NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Test GPU in Docker
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### 7.3 PostgreSQL
```bash
sudo apt install -y postgresql postgresql-contrib

# Enable and start
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Create database user (adjust as needed)
sudo -u postgres createuser --interactive
# Enter name: johnny5
# Superuser: y

# Create database
sudo -u postgres createdb j5a_db -O johnny5
```

### 7.4 Redis
```bash
sudo apt install -y redis-server

# Configure Redis for local only
sudo sed -i 's/^bind .*/bind 127.0.0.1/' /etc/redis/redis.conf

# Enable and start
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Test
redis-cli ping
# Should return: PONG
```

### 7.5 Nginx
```bash
sudo apt install -y nginx

# Enable and start
sudo systemctl enable nginx
sudo systemctl start nginx

# Test (from browser or curl)
curl http://localhost
```

### 7.6 Python Environment
```bash
# Install Python and venv
sudo apt install -y python3.12 python3.12-venv python3-pip

# Create J5A virtual environment
mkdir -p ~/j5a-server
cd ~/j5a-server
python3 -m venv venv
source venv/bin/activate

# Install core packages
pip install --upgrade pip
pip install \
    flask \
    gunicorn \
    celery \
    redis \
    psycopg2-binary \
    faster-whisper \
    torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 7.7 Ollama (Local LLMs)
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Enable and start
sudo systemctl enable ollama
sudo systemctl start ollama

# Pull a model (optional - do when ready)
# ollama pull qwen2:7b
```

---

## Phase 8: 3D Printing Setup (OctoPrint)

### Option A: Docker (Recommended)
```bash
# Create OctoPrint directory
mkdir -p ~/octoprint

# Create docker-compose.yml
cat > ~/octoprint/docker-compose.yml << 'EOF'
version: '3'
services:
  octoprint:
    image: octoprint/octoprint
    container_name: octoprint
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      - ./data:/octoprint
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0  # Adjust for your printer's USB port
    environment:
      - ENABLE_MJPG_STREAMER=false  # Set to true if using webcam
EOF

# Start OctoPrint
cd ~/octoprint
docker compose up -d

# Access at: http://localhost:8080
```

### Option B: Native Install
```bash
# Install OctoPrint via pip
sudo apt install -y python3-pip python3-venv libyaml-dev build-essential
mkdir ~/OctoPrint && cd ~/OctoPrint
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install octoprint

# Create systemd service
sudo tee /etc/systemd/system/octoprint.service << EOF
[Unit]
Description=OctoPrint
After=network.target

[Service]
Type=simple
User=$USER
ExecStart=$HOME/OctoPrint/venv/bin/octoprint serve
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable octoprint
sudo systemctl start octoprint
```

### USB Permissions for Printer
```bash
# Add user to dialout group for USB serial access
sudo usermod -aG dialout $USER

# Reboot or re-login for group membership to take effect
```

---

## Phase 9: Final Configuration

### 9.1 Create SSH Key for Remote Access
```bash
# On your main machine (Mac Mini), copy SSH key to new server
ssh-copy-id johnny5@192.168.1.100  # Use your server's IP

# Test passwordless login
ssh johnny5@192.168.1.100
```

### 9.2 Set Up Remote Desktop (Optional)
```bash
# Install xrdp for Windows Remote Desktop access
sudo apt install -y xrdp
sudo systemctl enable xrdp
sudo systemctl start xrdp

# Allow through firewall
sudo ufw allow 3389/tcp
```

### 9.3 Configure Automatic Updates (Security Only)
```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
# Select "Yes" for automatic security updates
```

### 9.4 Install Monitoring Tools
```bash
# System monitoring
sudo apt install -y htop iotop nethogs

# Temperature monitoring
sudo apt install -y lm-sensors
sudo sensors-detect  # Accept defaults
sensors  # View temperatures
```

---

## Post-Installation Verification Checklist

```bash
# Run these commands to verify everything is working:

# 1. NVIDIA GPU
nvidia-smi
nvcc --version

# 2. Docker
docker --version
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# 3. PostgreSQL
sudo systemctl status postgresql
psql -U johnny5 -d j5a_db -c "SELECT version();"

# 4. Redis
sudo systemctl status redis-server
redis-cli ping

# 5. Nginx
sudo systemctl status nginx
curl http://localhost

# 6. Python/pip
python3 --version
pip --version

# 7. Ollama
ollama --version

# 8. OctoPrint (if installed)
curl http://localhost:8080

# 9. Firewall
sudo ufw status

# 10. Temperatures
sensors
```

---

## Quick Reference: Service Management

```bash
# Start/Stop/Restart services
sudo systemctl start <service>
sudo systemctl stop <service>
sudo systemctl restart <service>
sudo systemctl status <service>

# View logs
sudo journalctl -u <service> -f

# Key services:
# - docker
# - postgresql
# - redis-server
# - nginx
# - ollama
# - octoprint (if installed)
```

---

## Troubleshooting

### NVIDIA Driver Issues
```bash
# If nvidia-smi fails after reboot:
sudo apt purge nvidia-*
sudo apt autoremove
sudo ubuntu-drivers autoinstall
sudo reboot
```

### Docker Permission Denied
```bash
# If docker commands fail with permission denied:
sudo usermod -aG docker $USER
# Then logout and login again
```

### OctoPrint Can't Access Printer
```bash
# Check USB device
ls -la /dev/ttyUSB*
# Should show the device

# Add user to dialout group
sudo usermod -aG dialout $USER
# Logout and login
```

### Display Manager Won't Start
```bash
# If stuck at command line after desktop install:
sudo systemctl status lightdm
sudo systemctl start lightdm

# Or reconfigure
sudo dpkg-reconfigure lightdm
```

---

## Next Steps After Installation

1. **Clone J5A repository** to new server
2. **Configure Nginx** as reverse proxy for Flask API
3. **Set up Jitsi Meet** (Docker) for video conferencing
4. **Install Cal.com** for scheduling
5. **Configure Celery** workers for async tasks
6. **Connect Ender 3** via USB and configure OctoPrint
7. **Set up backup strategy** (rsync to NAS or cloud)

---

**Document Created:** 2025-11-26
**Target OS:** Ubuntu Server 24.04.1 LTS
**Desktop Environment:** XFCE4 (lightweight)
**Estimated Installation Time:** 2-3 hours

