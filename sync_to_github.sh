#!/bin/bash
#
# sync_to_github.sh
# Automated GitHub synchronization for J5A, Squirt, and Sherlock systems
#
# Usage:
#   ./sync_to_github.sh              # Sync all systems
#   ./sync_to_github.sh j5a          # Sync only J5A
#   ./sync_to_github.sh squirt       # Sync only Squirt
#   ./sync_to_github.sh sherlock     # Sync only Sherlock
#   ./sync_to_github.sh --setup      # Initial repository setup

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# GitHub username
GITHUB_USER="BrandonH5678"

# System paths
J5A_PATH="/home/johnny5/Johny5Alive"
SQUIRT_PATH="/home/johnny5/Squirt"
SHERLOCK_PATH="/home/johnny5/Sherlock"

#------------------------------------------------------------------------------
# Helper Functions
#------------------------------------------------------------------------------

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

#------------------------------------------------------------------------------
# Check if repository exists on GitHub
#------------------------------------------------------------------------------
check_repo_exists() {
    local repo_name=$1
    local url="https://api.github.com/repos/${GITHUB_USER}/${repo_name}"

    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200"; then
        return 0  # Exists
    else
        return 1  # Doesn't exist
    fi
}

#------------------------------------------------------------------------------
# Create GitHub repository via API
#------------------------------------------------------------------------------
create_github_repo() {
    local repo_name=$1
    local description=$2

    log_info "Creating GitHub repository: ${repo_name}..."

    # Check if repo already exists
    if check_repo_exists "$repo_name"; then
        log_warning "Repository ${repo_name} already exists on GitHub"
        return 0
    fi

    # Get GitHub credentials from git credential store
    local creds=$(git credential fill <<EOF
protocol=https
host=github.com

EOF
)

    local username=$(echo "$creds" | grep "username=" | cut -d'=' -f2)
    local password=$(echo "$creds" | grep "password=" | cut -d'=' -f2)

    if [ -z "$password" ]; then
        log_error "No GitHub credentials found. Please authenticate with GitHub first."
        return 1
    fi

    # Create repository via GitHub API
    local response=$(curl -s -u "${username}:${password}" \
        -X POST \
        -H "Accept: application/vnd.github+json" \
        https://api.github.com/user/repos \
        -d "{
            \"name\": \"${repo_name}\",
            \"description\": \"${description}\",
            \"private\": false,
            \"auto_init\": false
        }")

    if echo "$response" | grep -q '"full_name"'; then
        log_success "Repository ${repo_name} created successfully"
        return 0
    else
        log_error "Failed to create repository. Response: $response"
        return 1
    fi
}

#------------------------------------------------------------------------------
# Initialize and sync a system to GitHub
#------------------------------------------------------------------------------
sync_system() {
    local system_name=$1
    local system_path=$2
    local repo_name=$3
    local description=$4
    local is_setup=$5

    log_info "========================================="
    log_info "Syncing ${system_name} to GitHub"
    log_info "========================================="

    # Check if directory exists
    if [ ! -d "$system_path" ]; then
        log_error "Directory not found: ${system_path}"
        return 1
    fi

    cd "$system_path"

    # Check directory size and warn if large
    local dir_size=$(du -sm . 2>/dev/null | cut -f1)
    if [ "$dir_size" -gt 100 ]; then
        log_warning "Directory size is ${dir_size}MB - checking for large files..."

        # Count files that should be ignored
        local large_audio=$(find . -type f \( -name "*.aaxc" -o -name "*.aax" -o -name "*.m4a" -o -name "*.mp3" -o -name "*.wav" \) 2>/dev/null | wc -l)
        if [ "$large_audio" -gt 0 ]; then
            log_warning "Found ${large_audio} audio files - these will be excluded by .gitignore"
        fi

        # Check for files not in .gitignore that are large
        local unignored_large=$(git ls-files --others --exclude-standard 2>/dev/null | while read file; do
            if [ -f "$file" ] && [ $(stat -c%s "$file" 2>/dev/null || echo 0) -gt 10485760 ]; then
                echo "$file"
            fi
        done | wc -l)

        if [ "$unignored_large" -gt 0 ]; then
            log_error "Found ${unignored_large} large files (>10MB) not in .gitignore!"
            log_error "Add these to .gitignore or use Git LFS before syncing"
            return 1
        fi
    fi

    # Initialize git if needed
    if [ ! -d ".git" ]; then
        log_info "Initializing git repository..."
        git init
        git branch -m main

        # Create .gitignore if it doesn't exist
        if [ ! -f ".gitignore" ]; then
            log_info "Creating .gitignore..."
            cat > .gitignore <<'GITIGNORE'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*~

# System
.DS_Store

# Logs
*.log
logs/

# Checkpoints
checkpoints/
*.checkpoint

# Test artifacts
.pytest_cache/
.coverage

# Sensitive data
.env
credentials/
*.key
*.pem
GITIGNORE
        fi
    fi

    # Check for uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        log_info "Found uncommitted changes, creating commit..."

        git add .

        # Generate commit message based on system
        local commit_msg
        case "$system_name" in
            "J5A")
                commit_msg="Update J5A: Overnight queue/batch management and cross-system coordination"
                ;;
            "Squirt")
                commit_msg="Update Squirt: Business document automation with voice processing integration"
                ;;
            "Sherlock")
                commit_msg="Update Sherlock: Evidence analysis system with intelligent model selection"
                ;;
        esac

        git commit -m "$commit_msg

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

        log_success "Changes committed"
    else
        log_info "No uncommitted changes"
    fi

    # Setup remote if needed
    if ! git remote | grep -q "origin"; then
        log_info "Adding GitHub remote..."
        git remote add origin "https://github.com/${GITHUB_USER}/${repo_name}.git"
    fi

    # Create GitHub repo if in setup mode
    if [ "$is_setup" = "true" ]; then
        create_github_repo "$repo_name" "$description"
    fi

    # Push to GitHub
    log_info "Pushing to GitHub..."

    # Get current branch
    local current_branch=$(git branch --show-current)

    if git push -u origin "$current_branch" 2>&1; then
        log_success "${system_name} synced to GitHub successfully!"
        log_info "Repository: https://github.com/${GITHUB_USER}/${repo_name}"
    else
        log_error "Failed to push ${system_name} to GitHub"
        log_info "You may need to create the repository manually at:"
        log_info "https://github.com/new"
        return 1
    fi

    echo ""
}

#------------------------------------------------------------------------------
# Main execution
#------------------------------------------------------------------------------

# Parse arguments
SETUP_MODE=false
SYSTEM_FILTER=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --setup)
            SETUP_MODE=true
            shift
            ;;
        j5a|squirt|sherlock)
            SYSTEM_FILTER=$1
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Usage: $0 [--setup] [j5a|squirt|sherlock]"
            exit 1
            ;;
    esac
done

echo ""
log_info "J5A GitHub Synchronization Tool"
log_info "================================"
echo ""

# Sync systems based on filter
if [ -z "$SYSTEM_FILTER" ] || [ "$SYSTEM_FILTER" = "j5a" ]; then
    sync_system "J5A" "$J5A_PATH" "Johny5Alive" \
        "J5A Overnight Queue/Batch Management System - Multi-system AI coordination for Squirt and Sherlock" \
        "$SETUP_MODE"
fi

if [ -z "$SYSTEM_FILTER" ] || [ "$SYSTEM_FILTER" = "squirt" ]; then
    sync_system "Squirt" "$SQUIRT_PATH" "Squirt" \
        "Squirt - WaterWizard Document Automation System with AI-powered voice processing" \
        "$SETUP_MODE"
fi

if [ -z "$SYSTEM_FILTER" ] || [ "$SYSTEM_FILTER" = "sherlock" ]; then
    sync_system "Sherlock" "$SHERLOCK_PATH" "Sherlock" \
        "Sherlock - AI Evidence Analysis System with intelligent model selection and multi-modal processing" \
        "$SETUP_MODE"
fi

echo ""
log_success "========================================="
log_success "All systems synchronized!"
log_success "========================================="
echo ""
log_info "Repository Links:"
[ -z "$SYSTEM_FILTER" ] || [ "$SYSTEM_FILTER" = "j5a" ] && \
    echo "  J5A:      https://github.com/${GITHUB_USER}/Johny5Alive"
[ -z "$SYSTEM_FILTER" ] || [ "$SYSTEM_FILTER" = "squirt" ] && \
    echo "  Squirt:   https://github.com/${GITHUB_USER}/Squirt"
[ -z "$SYSTEM_FILTER" ] || [ "$SYSTEM_FILTER" = "sherlock" ] && \
    echo "  Sherlock: https://github.com/${GITHUB_USER}/Sherlock"
echo ""
