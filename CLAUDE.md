# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an e-ink display application that captures screen content and displays it on an e-ink device. It supports both image and text modes with real-time screen capture and mouse tracking.

## Development Commands

```bash
# Run the application (from project root)
make run
# or
python main.py .

# Edit main file
make edit

# Install globally
make install
```

## Architecture

### Core Components

- **main.py**: Main application entry point with wxPython GUI and system tray integration
- **modules/**: Core functionality modules
  - `ConfigManager.py`: TOML configuration management
  - `SizeManager.py`: Capture area size and ratio management
  - `WireManager.py`: Visual capture region overlay
  - `KeyEvent.py`: Global keyboard shortcut handling
  - `mouse.py`: Mouse cursor tracking utilities
  - `utils.py`: General utilities including debounce decorator

### Application Flow

1. **Initialization**: Creates system tray icon, starts live-server for viewer, initializes configuration
2. **Capture Modes**: 
   - Image mode: Captures screen region around cursor, converts to black/white
   - Text mode: Processes clipboard content, formats for display
3. **Display**: Web-based viewer (viewer/) displays captured content
4. **Real-time Updates**: Multiple threads handle mouse tracking, keyboard events, and capture updates

### Key Features

- **Dual Mode Operation**: Toggle between image capture and text processing
- **Dynamic Sizing**: Adjustable capture region with keyboard shortcuts
- **Area Selection**: Manual area selection using `slop` tool
- **Configuration Persistence**: TOML-based settings with live updates
- **Web Viewer**: HTML/JS viewer with live-server integration

### Configuration

- `config.toml`: Main configuration (copy from `config.toml.example`)
- Key settings: `ratio`, `init_mode`, `init_width`
- Runtime updates saved automatically

### Dependencies

- wxPython (GUI framework)
- PIL/Pillow (image processing)
- pyperclip (clipboard access)
- pynput (global input handling)
- live-server (web viewer)
- slop (area selection tool)

### Keyboard Shortcuts

- `5`: Refresh display
- `[`/`]`: Shrink/expand capture region
- `9`/`0`: Adjust aspect ratio
- `` ` ``: Toggle capture mode
- `scroll_lock`: Toggle stop/start
- `F7`: Start area selection

### File Structure

- `viewer/`: Web-based display interface
- `copy-server/`: Flask server for remote clipboard access
- `assets/`: Icon and image resources
- `content`: Text content file for text mode