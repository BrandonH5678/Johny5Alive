#!/bin/bash
#
# update_github_token.sh
# Update GitHub personal access token for authentication
#

echo "GitHub Token Update Utility"
echo "============================"
echo ""
echo "You need to create a new GitHub Personal Access Token with these scopes:"
echo "  - repo (Full control of private repositories)"
echo "  - workflow (Update GitHub Action workflows)"
echo ""
echo "Create token at: https://github.com/settings/tokens/new"
echo ""
read -p "Enter your GitHub username [BrandonH5678]: " github_user
github_user=${github_user:-BrandonH5678}

read -sp "Enter your GitHub Personal Access Token: " github_token
echo ""

if [ -z "$github_token" ]; then
    echo "Error: Token cannot be empty"
    exit 1
fi

# Update git credentials
echo "https://${github_user}:${github_token}@github.com" > ~/.git-credentials

echo ""
echo "✅ GitHub credentials updated successfully!"
echo ""
echo "You can now run:"
echo "  ./sync_to_github.sh        # Sync all systems"
echo "  ./sync_to_github.sh j5a    # Sync only J5A"
echo ""
