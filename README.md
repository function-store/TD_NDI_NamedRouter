# NDI Named Switcher Web Interface

A web-based GUI for controlling NDI source assignments in TouchDesigner using **TouchDesigner's native WebSocket DAT**.

## Features

- **Native TouchDesigner WebSocket** - uses TouchDesigner's built-in WebSocket DAT for communication
- **Non-blocking architecture** - extension doesn't block TouchDesigner with server operations
- **Real-time WebSocket communication** between TouchDesigner and web interface
- **Responsive web GUI** with modern design
- **Live source monitoring** - automatically updates when NDI sources appear/disappear
- **Manual source selection** - override automatic regex matching from the web interface
- **Visual feedback** - shows current source assignments and regex patterns
- **Cross-platform** - works on any device with a web browser
- **Lightweight extension** - focused only on NDI switching logic
- **Client Info Component** - `NDI_NamedSwitcher_INFO` component for accessing server data from other TouchDesigner projects

## Setup

### 1. Setup TouchDesigner Component

1. **Add the component**: Place `NDI_NamedSwitcher.tox` in your TouchDesigner proejct
2. **Configure**: configure it to listen on port 8080, or whichever port you've set websocket port in the server

### 2. Start the Web Server

The extension now includes a built-in web server that serves the web interface:

```bash
# Start with default ports (HTTP: 80, WebSocket: 8080)
python start_server.py

# Custom HTTP port (WebSocket still defaults to 8080)
python start_server.py --port 8090

# Custom WebSocket port (HTTP still defaults to 80)
python start_server.py --websocket-port 9000

# Custom both ports
python start_server.py --port 8090 --websocket-port 9000

# Short form
python start_server.py -p 8090 -w 9000

# Don't open browser automatically
python start_server.py --no-browser
```

The server will automatically:
- Display both local and network access URLs
- Show the WebSocket port TouchDesigner should use
- Open the web interface in your default browser (unless `--no-browser` is used)
- Serve the web interface to other devices on your network

### 3. Configure TouchDesigner WebSocket DAT

**Important**: Set your TouchDesigner WebSocket DAT to use the **WebSocket port** (not the HTTP port):

- **Default setup**: WebSocket DAT should use port **8080**
- **Custom setup**: Use whatever port you specified with `--websocket-port`

**TouchDesigner WebSocket DAT Configuration:**
1. **Active**: On
2. **Port**: 8080 (or your custom WebSocket port)
3. **Callbacks**: Attach your callback Text DAT

**Port Summary:**
- **HTTP Server** (80): Serves the web interface files - you access this in your browser
- **WebSocket Server** (8080): TouchDesigner handles real-time communication - configure this in WebSocket DAT

### 4. Access the Web Interface

**Local Access:**
```
http://localhost:80
```

**Network Access (from other devices):**
```
http://[YOUR_IP_ADDRESS]:80
```

The web interface will automatically connect to TouchDesigner's WebSocket DAT using the configured port (default 8080) and the same host address.

### 5. Network Access from Other Devices

To access the web interface from other computers, tablets, or phones on the same network:

1. **Find your computer's IP address**: The `start_server.py` script will display it when it starts
2. **Use the network URL**: Access `http://[YOUR_IP_ADDRESS]:80` from any device on your network
3. **Firewall considerations**: Ensure your firewall allows incoming connections on port 80 (HTTP) and port 8080 (WebSocket)

**Common IP address ranges for local networks:**
- `192.168.1.x` (most home routers)
- `192.168.0.x` (some home routers)  
- `10.0.0.x` (some corporate networks)

### 6. Local Domain Names (Custom URLs)

To make your NDI Named Switcher accessible via easy-to-remember local URLs instead of IP addresses:

#### **Option 1: .local Domain (mDNS/Bonjour) - Easiest**

Works automatically on most modern networks:
```bash
# Your computer hostname + .local
http://your-computer-name.local:80
```

**Automatic setup:**
- ✅ **macOS**: Works automatically (Bonjour)
- ⚠️  **Windows**: May need Bonjour service
- ⚠️  **Linux**: May need avahi-daemon

#### **Option 2: Custom Local Domain via Hosts File**

Create any custom domain name you want:

```bash
# Use the setup helper
python setup_local_domain.py
```

**Manual setup:**
1. Edit your hosts file:
   - **Windows**: `C:\Windows\System32\drivers\etc\hosts`
   - **macOS/Linux**: `/etc/hosts`
2. Add line: `192.168.1.123 ndi-switcher` (use your actual IP)
3. Access via: `http://ndi-switcher:80`

#### **Option 3: Router Hostname Setup**

Configure your router to provide network-wide hostname resolution:

1. Access router admin panel (usually `192.168.1.1`)
2. Find DHCP/LAN settings
3. Set up static DHCP reservation with custom hostname
4. Access via: `http://your-custom-name:80`

#### **Quick Setup Helper**

Use the included domain setup script:
```bash
python setup_local_domain.py
```

This will guide you through:
- Checking .local domain support
- Setting up custom domains
- Router configuration instructions

## Usage

### Web Interface

1. **Source Selection**: Use the dropdown menus to manually select NDI sources for each output block
2. **Current Status**: See which sources are currently assigned to each block
3. **Regex Patterns**: View the regex patterns that control automatic source matching
4. **Refresh**: Click "Refresh Sources" to manually update the source mapping
5. **Connection Status**: Monitor the WebSocket connection status in the top-right corner

### TouchDesigner Integration

The system integrates seamlessly with your existing TouchDesigner setup:

- **Automatic Updates**: When NDI sources appear/disappear, the web interface updates automatically
- **Bidirectional Control**: Changes made in either TouchDesigner or the web interface are reflected in both
- **Real-time Sync**: Source assignments are synchronized in real-time

## WebSocket Messages

### From Web Interface to TouchDesigner:
- `request_state`: Request current state from TouchDesigner
- `set_source`: Set a specific source for a block
- `refresh_sources`: Request a refresh of source mappings

### From TouchDesigner to Web Interface:
- `state_update`: Full state update with all sources and current assignments
- `source_changed`: Notification when a source assignment changes
- `error`: Error message when something goes wrong



## Configuration


### Extension Configuration

#### Plural Handling

The NDI Named Switcher extension includes automatic plural handling for regex patterns, making it easier to write simple, user-friendly patterns.

**Initialization:**

Plural handling is enabled by default, however if you wish to disable it you can do so by changing
`self.enablePluralHandlings = False`

**How It Works:**
- When enabled, simple word patterns automatically handle both singular and plural forms
- Pattern `camera` becomes `cameras?` internally (matches "camera" or "cameras")
- Complex regex patterns remain unchanged to avoid breaking existing functionality
- Only affects patterns ending with word characters (`[a-zA-Z0-9_]`)

**Pattern Examples:**

| User Pattern | Transformed Pattern | Matches |
|--------------|-------------------|---------|
| `projector` | `projectors?` | "projector", "projectors" |  
| `led` | `leds?` | "led", "leds" |
| `tv` | `tvs?` | "tv", "tvs" |
| `projector.*` | `projector.*` | (unchanged - complex pattern) |
| `projectors?` | `projectors?` | (unchanged - already plural-aware) |

**Debug Information:**
- Extension logs pattern transformations: `"camera" -> "cameras?"`
- Debug output shows original and transformed patterns during matching
- No performance impact when disabled
- Backend state includes `plural_handling_enabled` and `effective_regex_patterns` fields (not currently displayed in web interface)

## Troubleshooting

### Common Issues

1. **Web Interface Not Loading**: 
   - Ensure the web server is running (`python start_server.py`)
   - Check that you're in the correct directory with the `templates/` folder
   - Try accessing the local URL first: `http://localhost:80`
   - For network access, use the IP address shown when the server starts

2. **WebSocket Connection Failed**:
   - Ensure TouchDesigner WebSocket DAT is configured and listening on the **WebSocket port** (default 8080)
   - Check that `websocket_callbacks.py` is attached to the WebSocket DAT
   - Verify the component path in `NDI_SWITCHER_COMP` is correct
   - If using custom ports, make sure TouchDesigner WebSocket DAT matches the `--websocket-port` setting
   - **Port reminder**: Web server runs on 80 (HTTP), TouchDesigner WebSocket on 8080

3. **Network Access Not Working**:
   - Check your firewall settings - both HTTP and WebSocket ports need to be open
   - Default: port 80 (HTTP) and port 8080 (WebSocket) 
   - Custom: whatever ports you specified with `--port` and `--websocket-port`
   - Ensure all devices are on the same network
   - Try disabling firewall temporarily to test connectivity
   - Verify the IP address shown by the server matches your computer's network IP

4. **No Sources Showing**: 
   - Check that your NDI sources are properly configured in TouchDesigner
   - Verify the NDI Named Switcher extension is working correctly

5. **Commands Not Working**:
   - Check TouchDesigner console for error messages
   - Verify the component path in `websocket_callbacks.py` matches your setup

### Debug Information

- **TouchDesigner**: Check the debug output for extension initialization and WebSocket messages
- **Browser**: Open developer tools (F12) to see WebSocket connection status and messages  
- **WebSocket DAT**: Check the WebSocket DAT's monitor for connection status and messages
- **Web Server**: Check that the server is running and accessible on the displayed URLs

## NDI_NamedSwitcher_INFO Component

The `NDI_NamedSwitcher_INFO` component is a TouchDesigner client that connects to the NDI Named Switcher server to access output information from other TouchDesigner projects.

### Purpose

This component allows you to:
- Access NDI Named Switcher output information from any TouchDesigner project
- Get real-time updates about output names, current sources, and resolutions
- Use the data in your own TouchDesigner networks without running the full NDI Named Switcher

### Usage

It is suggested to have one of this component in your network as it has a Global OP Shortcut as `op.NDI_INFO`.

#### Basic Access
```python
# Get the extension
ext = op.NDI_INFO.ext.NamedSwitcherInfoExt

# Check connection status
if ext.isConnected():
    print("Connected to NDI Named Switcher server")

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
```

### Setup Instructions

1. **Add Component**: Place the `NDI_NamedSwitcher_INFO` component in your TouchDesigner project
2. **Configure Connection**: The WebSocketDAT should connect to `localhost:8080` (or your server's address/port)
3. **Automatic Connection**: The component will automatically connect and request data when initialized
4. **Access Data**: Use `ext.Outputs.outputname` or `ext.ownerComp.Info['Output Name']` to access information, or `op.NDI_INFO.Outputs.projector.resx`

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

## License

This project is part of the NDI Named Switcher TouchDesigner system. 