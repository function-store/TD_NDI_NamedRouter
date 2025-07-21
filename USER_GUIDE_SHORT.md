# NDI Named Router - Quick Guide

## What It Does
**Automatically routes video sources to displays** based on source names. Name your sources with patterns like "laptop_projector", "wall_led", or "lobby_tv" and the system automatically sends them to the right outputs.

## How to Access
Open any web browser and go to: **`<placeholder>`**

## Naming Your Sources
**The system matches source names that END with these patterns:**
- **".*projector"** → matches "laptop_projector", "stage_projector", etc.
- **".*led"** → matches "wall_led", "strip_led", etc.  
- **".*tv"** → matches "lobby_tv", "main_tv", etc.

**Examples:**
- ✅ "laptop_projector" → goes to projector output
- ✅ "wall_led" → goes to LED output
- ✅ "lobby_tv" → goes to TV output
- ❌ "projector_backup" → won't match (doesn't end with "projector")

**Notes:**
- Plurals work automatically ("projector" and "projectors" both match)
- Case doesn't matter ("Projector", "PROJECTOR", "projector" all work)

## Web Interface
- **View sources:** See all available video sources
- **Manual control:** Override automatic routing with dropdown menus
- **Refresh:** Click "Refresh Sources" to rescan the network
- **Status:** Green dot = connected, Red dot = disconnected

## Quick Troubleshooting
- **Source not routing correctly?** Check that the name ends with "projector", "led", or "tv"
- **Web interface not loading?** Verify you're on the same network and try refreshing
- **No sources showing?** Click "Refresh Sources" button 