# Diabuddy Bulb

An Android application that bridges xDrip+ continuous glucose monitoring data with TP-Link Tapo smart bulb visual alerts.

## Overview

Diabuddy Bulb connects to xDrip+ via local network API and controls Tapo smart bulbs to provide visual glucose level indicators. 

## Technical Specifications

- **Platform**: Android (built with Python BeeWare/Toga)
- **xDrip+ Integration**: Local HTTP API (port 17580)
- **Supported Bulbs**: TP-Link Tapo L530E (tested)
- **Requirements**: xDrip+ with local broadcast enabled

## Hardware Requirements

- Android device with xDrip+ installed
- TP-Link Tapo L530E smart bulb
- Local WiFi network

## Installation

### For End Users
Download the latest APK from [Releases](../../releases) and install on your Android device.

### For Developers
```bash
git clone https://github.com/yourusername/diabuddy-bulb.git
cd diabuddy-bulb

# Set up environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Build for Android
briefcase create android
briefcase build android
```

## Configuration

1. **xDrip+ Setup**: Enable "Broadcast Data Locally" in Inter-App Settings
2. **Tapo Setup**: Configure bulb via official app, note IP address
3. **App Setup**: Enter Tapo credentials and bulb IP in settings

## Visual Indicators

| Glucose Range | Color | Status |
|---------------|-------|--------|
| < 50 mg/dL | Red | Critical Low |
| 50-70 mg/dL | Yellow | Low |
| 70-180 mg/dL | Green | Normal |
| > 180 mg/dL | Purple | High |

## Project Structure
```bash
diabuddy-bulb/
├── src/diabuddybulb/
│ ├── main.py # Main application
│ └── resources/ # App icons
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Contributing

Contributions are welcome. Please ensure compatibility is maintained with the current hardware stack.

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- **Tapo P100 Control Library**: This project uses a modified version of the [Tapo P100 control library](https://github.com/fishbigger/TapoP100) for bulb communication.
- **BeeWare Project**: For the mobile Python framework
- **xDrip+**: For the open glucose monitoring platform

## Compatibility Notes

- Currently tested and confirmed working with **Tapo L530E** bulbs only
- Other Tapo bulb models may work but are untested
- xDrip+ local broadcast must be enabled
