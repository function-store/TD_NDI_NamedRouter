# NDI Named Router

A TouchDesigner component for intelligent NDI source routing with smart name-based matching. Route any NDI input sources to video outputs with automatic pattern matching and optional web-based control.

![TD Overview](https://github.com/function-store/TD_NDI_NamedRouter/blob/main/docs/td_overview2.jpg)

![NDI Named Router Interface](https://github.com/function-store/TD_NDI_NamedRouter/blob/main/docs/web.jpg)
*Optional web interface for remote control*

## What is NDI Named Router?

NDI Named Router is a TouchDesigner component that automatically routes NDI input sources to video outputs based on intelligent name matching. It provides:

- **Smart Routing**: Automatically matches NDI sources to outputs using customizable name patterns
- **Generic Input/Output**: Works with any NDI sources and any video outputs - not limited to specific device types
- **TouchDesigner Integration**: Native TouchDesigner component that integrates seamlessly with your networks
- **Optional Advanced Web Control**: Full-featured web interface with configuration management, source refresh, and mobile support
- **Real-time Updates**: Automatically adapts when NDI sources appear, disappear, or change

## How It Works

### Core Component Functionality

1. **Add Component**: Place NDI Named Router in your TouchDesigner network
2. **Define Outputs**: Configure your video output blocks with descriptive names  
3. **Set Patterns**: Define name patterns for automatic source matching
4. **Automatic Routing**: Component automatically routes matching NDI sources to outputs
5. **Dynamic Updates**: Routes automatically update as NDI sources come and go

### Smart Name Matching

The component matches NDI sources to outputs using intelligent pattern matching:
- A source named "MyPC_Projector" automatically routes to output "Projector" (with default regex matching pattern of `.*_{Output Name}`)
- "Something_LED" matches to output "LED" 
- The latest matching source will take precedence
  
The system automatically handles source name variations:
- Pattern `camera` matches both "camera" and "cameras"
- Pattern `projector` matches both "Projector" and "PROJECTORS"

> Automatic matching can be overridden manually via the web interface

## User Guide

### Using the TouchDesigner Component

#### Basic Setup
1. **Add Component**: Place `NDI_NamedRouter.tox` in your TouchDesigner network
2. **Configure Outputs**: Set up your output blocks with descriptive names
3. **Define Patterns**: Configure regex patterns for automatic source matching
4. **Monitor Status**: Component outputs show current routing status and source information

#### Automatic Routing
- Component continuously monitors available NDI sources
- Automatically routes sources to outputs based on name pattern matches
- Updates routing in real-time as sources appear/disappear
- Shows current assignments and source status in component interface

#### Manual Override
- **TouchDesigner Component**: Manually assign sources via component parameters
- **Web Interface**: Use dropdowns to select specific NDI sources for each output
- **Configuration Management**: Save current configurations and recall them later
- Changes take effect immediately with visual feedback

### Optional Web Interface

#### Accessing the Interface
**Local Access:** Open browser to `http://localhost` (after starting web server)
**Remote Access:** Connect from other devices using network address (e.g., `http://192.168.1.123`)

#### Web Interface Features
- **Output Monitoring**: View all configured outputs and their current sources
- **Source Selection**: Manually assign NDI sources to outputs via dropdowns
- **Configuration Management**: Save and recall complete routing configurations
  - **Save Config**: Preserve current source assignments and settings
  - **Recall Config**: Restore previously saved routing configuration
- **Source Refresh**: Manual refresh of source mappings and available NDI sources
- **Real-time Updates**: Interface updates automatically as sources change
- **Visual Feedback**: Enhanced notifications, hover effects, and status indicators
- **Mobile Responsive**: Full functionality on smartphones and tablets

### Common Use Cases

**Scenario 1: Live Event Production**
- Multiple NDI sources (various cameras, graphics systems, playback servers)
- TouchDesigner handles video processing and output routing
- Component automatically routes sources based on configured patterns
- Optional web interface for operator control from control room

**Scenario 2: Installation Media Systems**
- Fixed NDI sources feeding various display outputs  
- Component automatically manages routing based on source availability
- Self-healing system - automatically switches to backup sources when primary fails
- Web interface for maintenance and troubleshooting when needed

**Scenario 3: Broadcast/Streaming Setup**
- Various NDI input sources (cameras, graphics, remote feeds)
- Component routes to different output destinations (streaming encoders, monitors, archives)
- Automatic failover and source management
- Remote control via web interface for distributed production teams

## Technical Overview

### System Components

- **TouchDesigner Component**: Handles NDI routing and video processing
- **Web Server**: Serves the web interface to browsers  
- **WebSocket Communication**: Real-time updates between TouchDesigner and web interface

### Network Requirements

- **Local Network**: All devices must be on the same network (WiFi or Ethernet)
- **Firewall**: Ports 80 (web) and 8080 (WebSocket) must be accessible
- **NDI Network**: NDI sources must be discoverable on the same network segment

## Installation and Setup

### 1. TouchDesigner Component

1. **Add the Component**: Place `NDI_NamedRouter.tox` in your TouchDesigner project
2. **Configure Outputs**: Set up your video outputs with descriptive names
3. **Define Patterns**: Configure name matching patterns for automatic routing
4. **Connect NDI Sources**: Ensure your NDI sources are properly configured and broadcasting

### 2. Optional Web Server Setup

```bash
# Basic startup (uses default ports)
python start_server.py

# Custom ports if needed
python start_server.py --port 8090 --websocket-port 9000

# Don't open browser automatically  
python start_server.py --no-browser
```

### 3. Access from Other Devices

The server shows network access URLs when it starts:
```
Local Access: http://localhost:80
Network Access: http://192.168.1.123:80
```

Use the network address to connect from other devices.

### 4. Component Configuration

The TouchDesigner component handles WebSocket communication automatically. Simply ensure it matches the server's WebSocket port (default: 8080).

### 5. Firewall Configuration

Ensure these ports are accessible:
- **Port 80**: Web interface (HTTP)
- **Port 8080**: TouchDesigner communication (WebSocket)

## Advanced Configuration

### Custom Network URLs

#### Option 1: .local Domain (Easiest)
Works automatically on most networks:
```
http://your-computer-name.local
```

#### Option 2: Custom Hosts File
Edit your system's hosts file to create custom domain names:
- **Windows**: `C:\Windows\System32\drivers\etc\hosts`
- **macOS/Linux**: `/etc/hosts`

Add: `192.168.1.123 ndi-router` (use your actual IP)
Access via: `http://ndi-router`



### WebSocket API

**Messages from Web Interface to TouchDesigner:**
- `request_state`: Request current system state
- `set_source`: Assign a source to an output
- `refresh_sources`: Refresh source mappings

**Messages from TouchDesigner to Web Interface:**
- `state_update`: Full system state update
- `source_changed`: Source assignment notification
- `error`: Error messages

## Troubleshooting

### Connection Issues

**Web Interface Not Loading:**
- Ensure web server is running: `python start_server.py`
- Try local URL first: `http://localhost`
- Check firewall settings for port 80

**WebSocket Connection Failed:**
- Verify TouchDesigner component is active and properly loaded
- Check that server WebSocket port matches component configuration

**Network Access Problems:**
- Verify all devices are on same network
- Check firewall allows ports 80 and 8080
- Try temporarily disabling firewall to test

**No Sources Showing:**
- Check NDI sources are properly configured and broadcasting
- Verify NDI Named Router component is running
- Use "Refresh Sources" button in web interface
- Try clicking on "Current:" displays to refresh individual source connections

**Source Connection Issues:**
- Click on the "Current:" display for a specific output to refresh that source connection
- Use "Save Config" before making changes to preserve working configurations  
- Use "Recall Config" to restore last known working configuration
- Check for error notifications in the top-right corner of the web interface

**Configuration Not Saving/Loading:**
- Verify TouchDesigner project has write permissions
- Check TouchDesigner console for error messages related to StorageManager
- Ensure the component's external .tox file can be saved if using external mode

### Debug Information
- **TouchDesigner**: Check console for component messages
- **Web Browser**: Open Developer Tools (F12) to see WebSocket status

## Known Issues
- Currently if multiple source candidates are available for an output, the latest can be overwritten with the first available when another source changes.

## NDI_NamedRouter_INFO Component

The `NDI_NamedRouter_INFO` component is a TouchDesigner client that connects to the NDI Named Switcher server to access output information from other TouchDesigner projects.

### Purpose

This component allows you to:
- Access NDI Named Switcher output information from any TouchDesigner project
- Get real-time updates about output names, current sources, and resolutions
- Use the data in your own TouchDesigner networks without running the full NDI Named Switcher

### Component Parameters

The NDI_NamedRouter_INFO component includes several parameters for controlling its behavior:

- **Update**: Enable periodic updates from the server
- **Update On Start**: Request server state once when the component initializes
- **Request State**: Button to manually request current state from server
- **Debug Messages**: Enable debug output for troubleshooting

### Usage

It is suggested to have one of this component in your network as it has a Global OP Shortcut as `op.NDI_INFO`.

#### Basic Access
```python
# Get the extension
ext = op.NDI_INFO.ext.NamedRouterInfoExt

# Check connection status
if ext.isConnected():
    print("Connected to NDI Named Switcher server")
    status = ext.getConnectionStatus()  # Returns 'connected' or 'disconnected'

# Get number of outputs
num_outputs = ext.getNumOutputs()
print(f"Server has {num_outputs} outputs")
```

#### Accessing Output Information

**Dictionary-style access:**
```python
# Access output info via Info DependDict
projector_info = op.NDI_INFO.Info['Projector']
print(f"Projector resolution: {projector_info.resx} x {projector_info.resy}")
```

**Attribute-style access:**
```python
# Access via Outputs wrapper (cleaner syntax), assuming an output named `projector`
projector_info = op.NDI_INFO.Outputs.projector

# Get resolution
width = projector_info.resx
height = projector_info.resy

# Or in short
width = op.NDI_INFO.Outputs.projector.resx
height = op.NDI_INFO.Outputs.projector.resy
```

#### Real-time Data Access
```python
# Get all current data
output_names = ext.getOutputNames()           # ['Projector', 'LED Wall', 'Camera Output']
current_sources = ext.getCurrentSources()     # Current NDI sources for each output
resolutions = ext.getOutputResolutions()      # [(1920, 1080), (3840, 2160), ...]
available_sources = ext.getAvailableSources() # All available NDI sources

# Get connection information
connection_status = ext.getConnectionStatus() # 'connected' or 'disconnected'
num_outputs = ext.getNumOutputs()            # Number of configured outputs
full_state = ext.getCurrentState()           # Complete server state dictionary

# Manual actions (same as button parameters)
ext.requestState()        # Request fresh state from server
ext.refreshSources()      # Tell server to refresh its source mappings
ext.sendPing()           # Send ping to test connection
```

### Automatic Update Behavior

The component offers flexible update modes:

- **Update On Start Only**: Component requests server state once when initialized (default behavior)
- **Periodic Updates**: Component continuously polls the server for updates at regular intervals
- **Manual Updates**: Use parameter buttons or extension methods to request updates on demand

**Timer Control:**
```python
# Enable/disable periodic updates
ext.timerActive = True   # Start periodic updates
ext.timerActive = False  # Stop periodic updates

# Check if updates are enabled
if ext.isPeriodicUpdate:
    print("Periodic updates are enabled")
if ext.isUpdateOnStart:
    print("Update on start is enabled")
```

### Setup Instructions

1. **Add Component**: Place the `NDI_NamedRouter_INFO` component in your TouchDesigner project
2. **Configure Connection**: The WebSocketDAT should connect to `localhost:8080` (or your server's address/port)
3. **Configure Update Mode**: Set `Update` parameter for periodic updates or leave `Update On Start` for one-time initialization
4. **Automatic Connection**: The component will automatically connect and request data based on your update settings
5. **Access Data**: Use `ext.Outputs.outputname` or `ext.ownerComp.Info['Output Name']` to access information, for example `op.NDI_INFO.Outputs.projector.resx`

### Data Structure

The `Info` object stores output information as DependDict objects, but can be accessed as a Named Tuple through the `Outputs` attribute.

## Example

```python
# These are equivalent and can be used in expressions
op.NDI_INFO.Info['projector']['resx']
op.NDI_INFO.Outputs.projector.resx
# For example
op('resolution1').par.w = op.NDI_INFO.Outputs.projector.resx
op('resolution1').par.h = op.NDI_INFO.Outputs.projector.resy
```

### NDI_NamedRouter_INFO Troubleshooting

**Component Not Receiving Data:**
- Check that the main NDI Named Router server is running
- Verify WebSocket connection to `localhost:8080` (or correct server address)
- Enable "Debug Messages" parameter to see connection status
- Try pulsing "Request State" parameter to manually request data

**Output Data Not Available:**
- Ensure output names match exactly (case-sensitive)
- Use `ext.getOutputNames()` to see available outputs
- Try accessing via dictionary: `op.NDI_INFO.Info['Exact Output Name']`
- Check server has configured outputs with the names you're looking for

**Connection Status:**
```python
# Check connection and debug
if not ext.isConnected():
    print("Not connected to server")
    print(f"Status: {ext.getConnectionStatus()}")
    ext.sendPing()  # Test connectivity
```

## License

TODO