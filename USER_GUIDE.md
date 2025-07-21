# NDI Named Router - User Guide

## What It Does

**The NDI Named Router is an automatic video routing system** that takes video sources from your network (via NDI) and intelligently sends them to the right display outputs - like projectors, LED walls, or TVs - without you having to manually configure each connection.

## The Problem It Solves

Imagine you have multiple video sources (cameras, computers, media players) and multiple displays (projectors, LED panels, TVs) in a venue. Normally, you'd have to manually:
- Figure out which video source should go to which display
- Connect and configure each routing manually
- Update connections when sources change or appear/disappear

## How It Works

### Smart Naming Convention
- Your video sources follow naming patterns that work with your configured regex patterns
- The system uses these names to automatically figure out where each source should go
- For example, with the default pattern ".*led", sources like "laptop_led" and "wall_led" will automatically go to LED displays
- **Smart plural handling**: The system automatically recognizes both singular and plural forms - so pattern ".*camera" will match both "laptop_camera" and "stream_cameras"

### Automatic Routing
- When a new video source appears on the network, the system looks at its name
- It matches the name against your rules and automatically routes it to the correct output
- No manual intervention needed - it just works

### Web Interface
- You can control everything from any device with a web browser (phone, tablet, computer)
- See all available video sources and where they're currently going
- Manually override the automatic routing if needed
- Refresh the system to detect new sources

## Real-World Example

Let's say you're running an event with the default patterns ".*projector", ".*led", and ".*tv":
1. A presenter plugs in their laptop and names it "laptop_projector"
2. The system automatically detects it and routes it to the main projector (matches ".*projector")
3. Meanwhile, a video source named "stage_led" automatically goes to the LED wall (matches ".*led")
4. A lobby display source named "lobby_tv" gets routed to the TV display (matches ".*tv")
5. Your colleague can see all of this happening on their phone via the web interface
6. If they need to change something, they can tap a button to route any source to any output

## Naming Your Video Sources

### Smart Pattern Matching
The system makes it easy to set up automatic routing by using simple naming patterns. Here's how it works:

### Basic Patterns
- **"projector"** - matches sources named exactly "projector" or "projectors"  
- **"led"** - matches sources named exactly "led" or "leds"
- **"tv"** - matches sources named exactly "tv" or "tvs"

### Default Patterns (as configured in the system)
- **".*projector"** - matches any source ending with "projector" (like "stage_projector", "backup_projector")
- **".*led"** - matches any source ending with "led" (like "wall_led", "strip_led")
- **".*tv"** - matches any source ending with "tv" (like "main_tv", "lobby_tv")

### Automatic Plural Recognition
**You don't need to worry about singular vs. plural!** The system is smart enough to handle both:

- Pattern **".*projector"** automatically becomes **".*projectors?"** and matches:
  - "stage_projector" (ends with "projector")
  - "main_projectors" (ends with "projectors")
  - "backup_projector", "wall_projectors", etc.
- Pattern **".*led"** automatically becomes **".*leds?"** and matches:
  - "wall_led" (ends with "led")
  - "strip_leds" (ends with "leds")
  - "main_led", "stage_leds", etc.
- Pattern **".*tv"** automatically becomes **".*tvs?"** and matches:
  - "lobby_tv" (ends with "tv")
  - "main_tvs" (ends with "tvs")
  - "backup_tv", "wall_tvs", etc.

### Real Examples
With the default patterns, if your video sources are named like:
- "main_projector" → matches ".*projector" pattern (transformed to ".*projectors?")
- "stage_projectors" → matches ".*projector" pattern (transformed to ".*projectors?")  
- "wall_led" → matches ".*led" pattern (transformed to ".*leds?")
- "strip_leds" → matches ".*led" pattern (transformed to ".*leds?")
- "lobby_tv" → matches ".*tv" pattern (transformed to ".*tvs?")
- "main_tvs" → matches ".*tv" pattern (transformed to ".*tvs?")

**Important:** Sources must END with the pattern word:
- ✅ "main_projector" (ends with "projector")
- ✅ "wall_led" (ends with "led")
- ✅ "lobby_tv" (ends with "tv")
- ❌ "projector_backup_stream" (doesn't end with "projector")
- ❌ "led_wall_main" (doesn't end with "led")
- ❌ "tv_main_feed" (doesn't end with "tv")

The system automatically routes them to the right outputs without you having to set up complex rules!

## How to Access the System

### Automatic Startup
- The NDI Named Router runs automatically on the **main media server** when the system starts up
- No manual intervention required - it's always running and monitoring for new sources

### Web Interface Access
- Open any web browser on your phone, tablet, or computer
- Go to: **`<placeholder>`**
- You'll see a real-time view of all video sources and their current routing

### What You'll See
- **Available Sources:** All NDI video sources currently on the network
- **Current Routing:** Which source is going to which output
- **Output Status:** Whether each output is active or showing a placeholder
- **Control Buttons:** Options to manually change routing or refresh sources

## Key Benefits

- **No Technical Knowledge Required:** Anyone can see what's happening and make changes
- **Automatic Operation:** Works without constant supervision
- **Flexible:** Easy to override automatic decisions when needed
- **Network Accessible:** Control from anywhere in the venue
- **Real-time:** Changes happen instantly and everyone sees the updates
- **Always Available:** Runs automatically on the media server

## Common Use Cases

### Event Setup
- Presenters connect their devices with descriptive names
- System automatically routes to appropriate displays
- Tech team can monitor everything from their phones

### Live Events
- Multiple cameras and sources are active simultaneously
- Each source automatically finds its designated output
- Manual overrides available for special requirements

### Venue Management
- Different content for different areas (lobby, main hall, backstage)
- Sources can be easily reassigned as needed
- Real-time visibility of all video routing

## Troubleshooting

### If a Source Isn't Routing Correctly
1. **Check the source name** - make sure it ends with the expected pattern (like "projector", "led", "tv")
2. **Don't worry about plurals** - the system automatically handles both "projector" and "projectors"
3. **Case doesn't matter** - "Projector", "PROJECTOR", and "projector" all work the same
4. Use the web interface to manually assign it if needed
5. Click "Refresh Sources" to rescan the network

### If the Web Interface Isn't Loading
1. Verify you're connected to the same network as the media server
2. Check the URL is correct: `<placeholder>`
3. Try refreshing your browser

### If Sources Aren't Appearing
1. Ensure the source device is connected to the network
2. Verify the NDI source is broadcasting
3. Use the "Refresh Sources" button in the web interface

**In essence, it's like having a smart assistant that automatically manages your video routing based on simple naming rules, with a user-friendly remote control that works on any device.** 