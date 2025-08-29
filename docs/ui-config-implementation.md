# CatLink UI Configuration Implementation

## Overview

This document describes the implementation of UI configuration for the CatLink Home Assistant integration, which enables proper device registration and entity grouping.

## Key Changes Made

### 1. Config Flow Implementation (`config_flow.py`)

Created a three-phase configuration flow:

#### Phase 1: Login Information
- Phone number
- Country code (default: 86)
- Password  
- Server region (China, US, Singapore)
- Real-time authentication validation

#### Phase 2: System Settings
- Update interval (1-30 minutes)
- Language preference (Chinese/English)
- Option to configure device-specific settings

#### Phase 3: Device Configuration (Optional)
- Empty litter box weight (0-10 kg)
- Litter weight sample count (1-100 samples)

#### Phase 4: Confirmation
- Display all configuration settings
- User confirmation before saving

### 2. Internationalization Support

#### English UI (`strings.json`)
- Complete UI text definitions
- Error messages and descriptions
- Help text for all configuration options

#### Chinese Localization (`translations/zh-Hans.json`)
- Full Chinese translation
- Localized error messages
- Region and language option translations

### 3. Platform Integration Updates

Updated all platform files to support both config entry and YAML configuration:
- `sensor.py` - Added `async_setup_entry` function
- `binary_sensor.py` - Added config entry support
- `switch.py` - Updated for dual configuration support
- `select.py` - Added config entry handling
- `button.py` - Updated platform setup

### 4. Core Component Updates

#### `__init__.py` Enhancements
- Added `async_setup_entry` for config entry support
- Added `async_unload_entry` for proper cleanup
- Maintained backward compatibility with YAML configuration
- Enhanced error handling and logging

#### Entity Base Class (`entitites/catlink.py`)
- **Removed manual entity_id assignment** (key fix for device registry)
- Enhanced device_info with additional metadata
- Added MAC address connections
- Added configuration URL for device management
- Comprehensive debug logging for troubleshooting

#### Device Coordinator (`devices_coordinator.py`)
- Added config entry reference storage
- Enhanced device configuration from config entry
- Added detailed debug logging for device creation
- Support for device-specific settings from UI

### 5. Manifest Updates (`manifest.json`)
- Enabled `config_flow: true`
- Added `loggers` for debug logging support
- Maintained cloud_polling IoT class

## User Configuration Requirements

### Required Information
1. **Phone Number** - CatLink account phone number
2. **Password** - Account password (encrypted with RSA)
3. **Country Code** - International calling code (default: 86)
4. **Server Region** - Choose closest server (China/US/Singapore)

### Optional Settings
1. **Update Interval** - Data refresh rate (1-30 minutes, default: 1)
2. **Language** - Interface language (Chinese/English)
3. **Device Settings** - Litter box specific configurations

### Device-Specific Configuration
1. **Empty Weight** - Empty litter box weight for accurate calculations
2. **Sample Count** - Weight samples for cat presence detection

## Debug Logging

Users can enable debug logging through:

1. **UI Method** (recommended):
   - Go to Settings > Logs
   - Find CatLink integration
   - Click "Enable debug logging"

2. **YAML Method**:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.catlink: debug
   ```

## Expected Results

After implementation:
1. **Device Registry** - Devices will appear in Home Assistant device list
2. **Entity Grouping** - All sensors, switches, buttons grouped under devices
3. **UI Management** - Full configuration through Home Assistant UI
4. **Proper Identification** - Unique device identifiers and MAC connections
5. **Enhanced Metadata** - Model, firmware version, manufacturer information

## Migration Support

The implementation maintains backward compatibility:
- Existing YAML configurations continue to work
- Automatic detection of configuration method
- No data loss during transition
- Users can migrate to UI configuration gradually

## Testing Recommendations

1. Test authentication with various server regions
2. Verify device creation and entity grouping
3. Test options flow for settings updates
4. Validate debug logging functionality
5. Confirm proper device removal on uninstall