# Raspberry Pi Support for NDI Named Router

The NDI Named Router bridge server now supports **Raspberry Pi NDI receivers** as client components, enabling unified control of both TouchDesigner and Raspberry Pi outputs from a single web interface.

## Overview

### What This Enables

- 🌐 **Unified Control**: Control TouchDesigner AND Raspberry Pi NDI receivers from one web interface
- 📊 **Global View**: See all outputs (TD + RPi) in a single, organized interface
- 🔄 **State Sync**: Real-time synchronization between all connected components
- 🎯 **Studio Management**: Perfect for complex multi-device studio setups

### Architecture

```
┌─────────────────────────────────────────────┐
│         NDI Named Router Bridge             │
│         (start_server.py)                   │
│                                             │
│  HTTP Server (80) + WebSocket Bridge       │
│  Browser Port: 8080 | Client Port: 8081    │
└──────────┬──────────────────────────────────┘
           │
           ├──→ TouchDesigner Component #1 (4 outputs)
           ├──→ TouchDesigner Component #2 (2 outputs)
           ├──→ Raspberry Pi Receiver #1 (1 output)
           ├──→ Raspberry Pi Receiver #2 (1 output)
           └──→ Web Browser(s)
```

## Quick Start

### 1. Start the Bridge Server

On your main computer (or dedicated server):

```bash
cd /path/to/TD_NDI_NamedRouter
python start_server.py
```

Note the server's IP address (e.g., `192.168.1.100`)

### 2. Connect Raspberry Pi Receivers

On each Raspberry Pi running [RpiSimpleNDI](https://github.com/function-store/RpiSimpleNDI):

```bash
# Basic connection
python3 ndi_receiver.py \
  --router-bridge ws://192.168.1.100:8081

# With custom name
python3 ndi_receiver.py \
  --config config.led_screen.json \
  --router-bridge ws://192.168.1.100:8081 \
  --router-name "LED Wall Main"
```

### 3. Connect TouchDesigner Components

In TouchDesigner, configure each `NDI_NamedRouter` component:
- **Websocketaddress**: `ws://192.168.1.100`
- **Websocketport**: `8081`
- **Componentid**: Unique ID (e.g., `"TD_Studio_A"`)

### 4. Access Web Interface

Open browser to: `http://192.168.1.100`

You'll see all components with their outputs in a unified interface!

## Example Studio Setup

### Scenario: Multi-Room Production Facility

**Equipment:**
- 2x TouchDesigner systems (8 outputs total)
- 3x Raspberry Pi LED walls (3 outputs)
- 1x Bridge server

**Configuration:**

Bridge Server (`192.168.1.10`):
```bash
python start_server.py
```

TouchDesigner Studio A:
- Component ID: `Studio_A_Main`
- Bridge: `ws://192.168.1.10:8081`
- Outputs: Main, Preview, Program, Aux

TouchDesigner Studio B:
- Component ID: `Studio_B_Main`
- Bridge: `ws://192.168.1.10:8081`
- Outputs: Main, Monitor

Raspberry Pi #1 (LED Wall - Stage Left):
```bash
python3 ndi_receiver.py \
  --config config.led_screen.json \
  --router-bridge ws://192.168.1.10:8081 \
  --router-name "LED Wall - Stage Left"
```

Raspberry Pi #2 (LED Wall - Stage Right):
```bash
python3 ndi_receiver.py \
  --config config.led_screen.json \
  --router-bridge ws://192.168.1.10:8081 \
  --router-name "LED Wall - Stage Right"
```

Raspberry Pi #3 (Backstage Monitor):
```bash
python3 ndi_receiver.py \
  --config config.monitor.json \
  --router-bridge ws://192.168.1.10:8081 \
  --router-name "Backstage Monitor"
```

**Result:** 11 total outputs (8 TD + 3 RPi) all controllable from `http://192.168.1.10`!

## Features

### What Raspberry Pi Clients Provide

Each Raspberry Pi receiver contributes:
- **Component Name**: Human-readable identifier (e.g., "LED Wall Main")
- **Component ID**: Unique machine identifier (auto-generated from hostname or custom)
- **Available Sources**: All NDI sources visible to the Raspberry Pi
- **Current Source**: Currently selected/routed NDI source
- **Output Resolution**: Display resolution (e.g., 1920x1080)
- **Regex Pattern**: Source filtering pattern (if configured)

### What You Can Do from Web Interface

- **View all outputs**: See TouchDesigner and Raspberry Pi outputs together
- **Switch sources**: Change NDI source for any output (TD or RPi)
- **Refresh sources**: Trigger source refresh across all devices
- **Monitor state**: Real-time status of all outputs
- **Grouped by component**: Outputs organized by TD component or RPi device

## Technical Details

### Protocol Compatibility

Raspberry Pi receivers follow the same NDI Named Router protocol as TouchDesigner components:

**State Message:**
```json
{
  "action": "state_update",
  "state": {
    "component_id": "RaspberryPi_hostname",
    "component_name": "LED Wall Main",
    "client_type": "controller",
    "sources": ["Source1", "Source2", ...],
    "output_names": ["LED Wall Main"],
    "current_sources": ["MACBOOK (Camera_1)"],
    "regex_patterns": [".*_led"],
    "output_resolutions": [[1920, 1080]],
    "locks": [false],
    "lock_global": false,
    "last_update": 1234567890.123
  }
}
```

### Command Handling

Raspberry Pi receivers respond to these commands from the bridge:

- `request_state`: Send current state
- `set_source`: Change NDI source
- `refresh_sources`: Re-scan available sources
- `ping`: Health check

### Auto-Reconnect

Raspberry Pi clients automatically reconnect if the bridge server goes down or network issues occur (5-second retry interval).

## Deployment Options

### Option 1: Bridge on Main Computer
- Run bridge on your primary TouchDesigner machine
- All devices connect to it
- **Pros**: Simple, no extra hardware
- **Cons**: Bridge goes down if TD machine restarts

### Option 2: Bridge on Raspberry Pi
- Use one RPi as bridge server AND client
- More stable than running on TD machine
- **Pros**: Dedicated, stable server
- **Cons**: Uses one RPi for server duty

### Option 3: Dedicated Server
- Run bridge on separate machine/server
- Most robust option
- **Pros**: Maximum stability and reliability
- **Cons**: Requires extra hardware

### Option 4: Cloud/VPN
- Run bridge on cloud server or VPN host
- Access from anywhere
- **Pros**: Remote access, ultimate flexibility
- **Cons**: Requires VPN setup, potential latency

## Troubleshooting

### Raspberry Pi Not Appearing

1. Check connectivity: `ping 192.168.1.100` (bridge IP)
2. Check port: `nc -zv 192.168.1.100 8081`
3. Check logs on RPi for connection errors
4. Verify unique component_id (no duplicates)

### Commands Not Working

1. Check bridge console for routing messages
2. Verify component_id matches in web interface
3. Check NDI source is actually available

### State Not Updating

1. Check WebSocket connection in browser (F12)
2. Verify auto-update is enabled (default for controllers)
3. Check network latency between devices

## Performance

- **Network overhead**: ~1-5 KB per state update
- **Latency**: <10ms on local network
- **CPU usage**: <1% on bridge server
- **Scalability**: Tested with 10+ clients without issues

## Documentation Links

- **[NDI_ROUTER_INTEGRATION.md](../../RpiSimpleNDI/NDI_ROUTER_INTEGRATION.md)**: Complete Raspberry Pi integration guide
- **[README.md](README.md)**: Main NDI Named Router documentation
- **[RpiSimpleNDI README](../../RpiSimpleNDI/README.md)**: Raspberry Pi NDI receiver documentation

## Future Enhancements

Potential future features:
- Lock support for Raspberry Pi outputs
- Multi-output support per Raspberry Pi
- Custom configuration save/recall for RPi
- INFO-only mode for RPi (read-only monitoring)

## Support

For issues:
- Check [NDI_ROUTER_INTEGRATION.md](../../RpiSimpleNDI/NDI_ROUTER_INTEGRATION.md) troubleshooting section
- Review bridge server console logs
- Check Raspberry Pi application logs
- Open issue in GitHub repository

