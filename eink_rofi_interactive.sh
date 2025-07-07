#!/bin/bash

# E-ink Display Interactive Settings Menu
# This script creates an interactive rofi menu for continuous value adjustment

PIPE_PATH="/tmp/eink_control"
STATUS_PATH="/tmp/eink_status"

# Check if the e-ink app is running
if [ ! -p "$PIPE_PATH" ]; then
    rofi -e "E-ink app is not running or pipe not found!"
    exit 1
fi

# Function to get current value from app
get_current_value() {
    local cmd="$1"
    echo "$cmd" > "$PIPE_PATH"
    # Use shorter timeout to avoid long waits
    if [ -p "$STATUS_PATH" ]; then
        timeout 0.2 cat "$STATUS_PATH" 2>/dev/null | head -n1
    fi
}

# Function for interactive threshold adjustment
adjust_threshold() {
    local current_thresh
    current_thresh=$(get_current_value "get_thresh")
    current_thresh=${current_thresh#thresh:}  # Remove "thresh:" prefix
    local last_selected=1  # Default to increase
    
    while true; do
        CHOICE=$(echo -e "🔧 Current Threshold: $current_thresh\n➕ Increase (+10)\n➖ Decrease (-10)\n🔄 Toggle (120/180)\n↩️ Back to Main Menu" | \
                 rofi -dmenu -i -p "Threshold Adjustment" -selected-row $last_selected)
        
        case "$CHOICE" in
            "➕ Increase (+10)")
                echo "thresh_up" > "$PIPE_PATH"
                current_thresh=$((current_thresh + 10))
                last_selected=1
                ;;
            "➖ Decrease (-10)")
                echo "thresh_down" > "$PIPE_PATH"
                current_thresh=$((current_thresh - 10))
                last_selected=2
                ;;
            "🔄 Toggle (120/180)")
                echo "thresh_toggle" > "$PIPE_PATH"
                if [ "$current_thresh" -gt 150 ]; then
                    current_thresh=120
                else
                    current_thresh=180
                fi
                last_selected=3
                ;;
            "↩️ Back to Main Menu"|"")
                return
                ;;
        esac
    done
}

# Function for interactive size adjustment
adjust_size() {
    local current_size
    current_size=$(get_current_value "get_size")
    current_size=${current_size#size:}  # Remove "size:" prefix
    local last_selected=1  # Default to increase
    
    while true; do
        CHOICE=$(echo -e "📏 Current Size: $current_size\n➕ Increase Size\n➖ Decrease Size\n↩️ Back to Main Menu" | \
                 rofi -dmenu -i -p "Size Adjustment" -selected-row $last_selected)
        
        case "$CHOICE" in
            "➕ Increase Size")
                echo "size_up" > "$PIPE_PATH"
                last_selected=1
                ;;
            "➖ Decrease Size")
                echo "size_down" > "$PIPE_PATH"
                last_selected=2
                ;;
            "↩️ Back to Main Menu"|"")
                return
                ;;
        esac
        
        # Get updated size
        current_size=$(get_current_value "get_size")
        current_size=${current_size#size:}
    done
}

# Function for interactive ratio adjustment
adjust_ratio() {
    local current_ratio
    current_ratio=$(get_current_value "get_ratio")
    current_ratio=${current_ratio#ratio:}  # Remove "ratio:" prefix
    local last_selected=1  # Default to increase
    
    while true; do
        CHOICE=$(echo -e "📐 Current Ratio: $current_ratio\n➕ Increase Ratio\n➖ Decrease Ratio\n↩️ Back to Main Menu" | \
                 rofi -dmenu -i -p "Ratio Adjustment" -selected-row $last_selected)
        
        case "$CHOICE" in
            "➕ Increase Ratio")
                echo "ratio_up" > "$PIPE_PATH"
                last_selected=1
                ;;
            "➖ Decrease Ratio")
                echo "ratio_down" > "$PIPE_PATH"
                last_selected=2
                ;;
            "↩️ Back to Main Menu"|"")
                return
                ;;
        esac
        
        # Get updated ratio
        current_ratio=$(get_current_value "get_ratio")
        current_ratio=${current_ratio#ratio:}
    done
}

# Main menu
while true; do
    OPTIONS="🔧 Adjust Threshold (Interactive)
📏 Adjust Size (Interactive)
📐 Adjust Ratio (Interactive)
🎯 Toggle Capture Mode
⏸️ Toggle Stop/Start
🔄 Refresh Display
🖱️ Select Area (slop)
❌ Exit"

    CHOICE=$(echo "$OPTIONS" | rofi -dmenu -i -p "E-ink Settings")

    case "$CHOICE" in
        "🔧 Adjust Threshold (Interactive)")
            adjust_threshold
            ;;
        "📏 Adjust Size (Interactive)")
            adjust_size
            ;;
        "📐 Adjust Ratio (Interactive)")
            adjust_ratio
            ;;
        "🎯 Toggle Capture Mode")
            echo "toggle_capture" > "$PIPE_PATH"
            ;;
        "⏸️ Toggle Stop/Start")
            echo "toggle_stop" > "$PIPE_PATH"
            ;;
        "🔄 Refresh Display")
            echo "refresh" > "$PIPE_PATH"
            ;;
        "🖱️ Select Area (slop)")
            echo "select_area" > "$PIPE_PATH"
            ;;
        "❌ Exit"|"")
            exit 0
            ;;
    esac
done