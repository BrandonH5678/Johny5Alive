#!/bin/bash
# J5A Prompt Library Auto-Display
# Add this to your ~/.bashrc or ~/.zshrc for automatic prompt library reminders

# Function to show prompt library reminder when entering J5A directories
j5a_prompt_reminder() {
    # Check if we're in a J5A system directory
    if [[ "$PWD" == *"Johny5Alive"* ]] || \
       [[ "$PWD" == *"Sherlock"* ]] || \
       [[ "$PWD" == *"Squirt"* ]]; then

        # Check if PROMPT_LIBRARY.html exists
        if [ -f "PROMPT_LIBRARY.html" ]; then
            # Only show once per shell session per directory
            local cache_key="PROMPT_LIBRARY_SHOWN_${PWD//\//_}"
            if [ -z "${!cache_key}" ]; then
                echo ""
                echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                echo "📚 PROMPT LIBRARY AVAILABLE"
                echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                echo "💰 Use cached prompts to save 70-90% on tokens"
                echo ""
                echo "🌐 Open:     xdg-open PROMPT_LIBRARY.html"
                echo "📖 Manual:   cat TOKEN_OPTIMIZATION_USER_MANUAL.md | less"
                echo "📊 Stats:    python3 src/token_monitor.py --status"
                echo ""
                echo "💡 TIP: Copy prompts exactly from library for caching!"
                echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                echo ""

                # Mark as shown for this shell session
                export $cache_key=1
            fi
        fi
    fi
}

# Override cd command to show reminder
cd() {
    builtin cd "$@"
    j5a_prompt_reminder
}

# Show reminder when sourcing this file (initial shell startup)
j5a_prompt_reminder
