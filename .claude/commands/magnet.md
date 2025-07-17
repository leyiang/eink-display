# Magnet Environment System

If mouse is close to some x value, magnet point will drag the mouse.

## Adding New Environments

To add a new magnet environment:

1. **Add environment to `mouse_magnet.py`** - Update `PRESET_ENVIRONMENTS` dict:
   ```python
   PRESET_ENVIRONMENTS = {
       "env-name": {"positions": [x1, x2], "frame_size": [width, height]},
   }
   ```

2. **Add rofi menu option in `eink_rofi_interactive.py`**:
   - Add option to `adjust_magnet_environment()` options list
   - Add command handler: `self.send_command("magnet_env-name")`

3. **IMPORTANT**: Environment name uses hyphens, command uses same name with `magnet_` prefix

## Files Related
- `mouse_magnet.py` - Environment definitions
- `eink_rofi_interactive.py` - Rofi menu interface  
- `main.py` - Command registration (auto-generated from PRESET_ENVIRONMENTS)

## Command Flow
1. User selects environment in rofi → sends `magnet_env-name` command
2. `main.py` receives command → calls `load_magnet_preset(env-name)`
3. Loads positions and frame_size from `PRESET_ENVIRONMENTS`
