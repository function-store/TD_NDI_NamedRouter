#!/usr/bin/env python3
"""
Simple startup script for NDI Named Router Web Interface
Starts HTTP server to serve the web interface + WebSocket bridge
TouchDesigner connects to the bridge as a CLIENT
"""

import http.server
import socketserver
import os
import sys
import webbrowser
import threading
import time
import socket
import platform
import argparse
import asyncio
import websockets
import json

def get_local_ip():
    """Get the local IP address for network access"""
    try:
        # Connect to a remote server to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def get_local_hostname():
    """Get the local hostname for .local domain access"""
    try:
        hostname = socket.gethostname()
        # Remove any domain suffix to get just the hostname
        hostname = hostname.split('.')[0]
        return hostname
    except Exception:
        return "unknown"

def find_available_port(start_port=80):
    """Find an available port starting from the given port"""
    import socket
    
    print(f"Searching for available port starting from {start_port}...")
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))  # Bind to all interfaces instead of localhost
                print(f"Found available port: {port}")
                return port
        except OSError:
            print(f"Port {port} is in use, trying next...")
            continue
    print("No available ports found in range!")
    return None

def start_server(port=80, websocket_port=8080, auto_open=True):
    """Start the static file server"""
    local_ip = get_local_ip()
    hostname = get_local_hostname()
    
    print(f"Starting static file server on port {port}...")
    print(f"Local access: http://localhost:{port}")
    print(f"Network access: http://{local_ip}:{port}")
    print(f"Hostname access: http://{hostname}.local:{port}")
    print(f"WebSocket will connect to TouchDesigner on port {websocket_port}")
    print("Press Ctrl+C to stop the server")
    print()
    print(f"Make sure your TouchDesigner WebSocket DAT is running on port {websocket_port}")
    print("=" * 60)
    
    # Change to the directory containing the templates folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Changing to directory: {current_dir}")
    os.chdir(current_dir)
    
    # Create a custom handler that serves index.html from templates/
    class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            print(f"HTTP GET request for: {self.path}")
            if self.path == '/' or self.path == '/index.html':
                # Serve the modified HTML with dynamic WebSocket port
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                # Read the template file
                try:
                    with open('templates/index.html', 'r', encoding='utf-8') as f:
                        html_content = f.read()
                    
                    # Replace the WebSocket port placeholder with the actual port
                    html_content = html_content.replace(
                        "const WS_PORT = '8080';  // TouchDesigner WebSocket DAT port (direct connection)",
                        f"const WS_PORT = '{websocket_port}';  // TouchDesigner WebSocket DAT port (direct connection)"
                    )
                    
                    self.wfile.write(html_content.encode('utf-8'))
                    print(f"Served index.html with WebSocket port {websocket_port}")
                except Exception as e:
                    print(f"Error serving index.html: {e}")
                    self.send_error(500, f"Error loading index.html: {e}")
                return
            elif self.path == '/favicon.ico':
                # Handle favicon request gracefully - return empty 204 response
                self.send_response(204)  # No Content
                self.end_headers()
                print("Served empty favicon response")
                return
            else:
                # For other files, use default behavior
                return super().do_GET()
        
        def log_message(self, format, *args):
            print(f"[{self.log_date_time_string()}] {format % args}")
    
    try:
        print(f"Creating TCP server on port {port}...")
        with socketserver.TCPServer(("", port), CustomHTTPRequestHandler) as httpd:
            print(f"Server started successfully!")
            print(f"  Local: http://localhost:{port}")
            print(f"  Network: http://{local_ip}:{port}")
            print(f"  WebSocket: TouchDesigner port {websocket_port}")
            print("Server is ready to accept connections")
            
            # Open browser after a short delay
            if auto_open:
                def open_browser():
                    print("Opening browser in 1 second...")
                    time.sleep(1)
                    print(f"Opening browser to: http://localhost:{port}")
                    webbrowser.open(f'http://localhost:{port}')
                
                browser_thread = threading.Thread(target=open_browser)
                browser_thread.daemon = True
                browser_thread.start()
            
            print("Server running... Press Ctrl+C to stop")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"Port {port} is already in use!")
            alternative_port = find_available_port(port + 1)
            if alternative_port:
                print(f"Trying port {alternative_port} instead...")
                start_server(alternative_port, websocket_port, auto_open)
            else:
                print("No available ports found!")
        else:
            print(f"Error starting server: {e}")

# WebSocket Bridge for TouchDesigner
browser_clients = set()
td_clients = {}  # Map websocket -> component_id
component_states = {}  # Map component_id -> latest state
info_only_clients = set()  # Set of websockets that only want updates on request
td_lock = asyncio.Lock()

async def handle_browser_websocket(websocket, path):
    """Handle WebSocket connections from browsers"""
    client_addr = websocket.remote_address
    print(f"[Browser] Connected: {client_addr}")
    browser_clients.add(websocket)
    
    try:
        # Request initial state from all TD clients and send merged state
        async with td_lock:
            if td_clients:
                # Request state from all TD clients
                for td_socket in list(td_clients.keys()):
                    try:
                        await td_socket.send(json.dumps({'action': 'request_state'}))
                    except:
                        pass
                print(f"[Bridge] Requested state from {len(td_clients)} TD clients for new browser")
                
                # Send currently merged state immediately
                if component_states:
                    merged_state = merge_component_states()
                    await websocket.send(json.dumps({
                        'action': 'state_update',
                        'state': merged_state
                    }))
        
        async for message in websocket:
            print(f"[Browser→TDs] {message[:100] if len(message) > 100 else message}")
            
            # Don't forward error messages back (prevents loops)
            try:
                msg_data = json.loads(message)
                action = msg_data.get('action')
                
                if action == 'error':
                    print(f"[Bridge] Ignoring error echo from browser")
                    continue
                    
                # Route commands to specific component if component_id specified
                if action in ['set_source', 'set_lock', 'set_lock_global', 'refresh_sources', 'save_configuration', 'recall_configuration']:
                    component_id = msg_data.get('component_id')
                    if component_id:
                        # Send to specific component
                        target_socket = None
                        async with td_lock:
                            for td_socket, cid in td_clients.items():
                                if cid == component_id:
                                    target_socket = td_socket
                                    break
                        
                        if target_socket:
                            try:
                                await target_socket.send(message)
                                print(f"[Bridge] Routed {action} to component {component_id}")
                            except:
                                print(f"[Bridge] Failed to send to component {component_id}")
                        else:
                            print(f"[Bridge] Component {component_id} not found")
                            await websocket.send(json.dumps({
                                'action': 'error',
                                'message': f'Component {component_id} not connected'
                            }))
                        continue
            except:
                pass
            
            async with td_lock:
                if td_clients:
                    # Forward to all TD clients for general messages
                    disconnected = []
                    for td_socket in list(td_clients.keys()):
                        try:
                            await td_socket.send(message)
                        except:
                            print(f"[Bridge] Failed to send to TD client")
                            disconnected.append(td_socket)
                    for td_socket in disconnected:
                        if td_socket in td_clients:
                            del td_clients[td_socket]
                else:
                    print(f"[Bridge] ERROR: No TD clients connected")
                    await websocket.send(json.dumps({
                        'action': 'error',
                        'message': 'TouchDesigner not connected'
                    }))
    except websockets.exceptions.ConnectionClosed:
        print(f"[Browser] Disconnected: {client_addr}")
    finally:
        browser_clients.discard(websocket)

def merge_component_states():
    """Merge states from all TD components into a single state"""
    if not component_states:
        return {}
    
    # Start with first component's state as base
    merged = {
        'components': [],  # List of component info
        'output_names': [],
        'current_sources': [],
        'regex_patterns': [],
        'effective_regex_patterns': [],
        'output_resolutions': [],
        'locks': [],
        'sources': [],  # Combined sources from all components
        'lock_global': False,  # Any component globally locked?
        'last_update': time.time()
    }
    
    for component_id, state in component_states.items():
        # Track which component each output belongs to
        num_outputs = len(state.get('output_names', []))
        
        merged['components'].append({
            'component_id': component_id,
            'component_name': state.get('component_name', component_id),
            'machine_id': state.get('machine_id', 'unknown'),  # Hostname for Spout source sharing
            'output_start_idx': len(merged['output_names']),
            'output_count': num_outputs,
            'lock_global': state.get('lock_global', False),
            'local_only_sources': state.get('local_only_sources', [])  # Spout sources local to this machine
        })
        
        # Append all outputs from this component
        merged['output_names'].extend(state.get('output_names', []))
        merged['current_sources'].extend(state.get('current_sources', []))
        merged['regex_patterns'].extend(state.get('regex_patterns', []))
        merged['effective_regex_patterns'].extend(state.get('effective_regex_patterns', []))
        merged['output_resolutions'].extend(state.get('output_resolutions', []))
        merged['locks'].extend(state.get('locks', []))
        
        # Combine sources (avoiding duplicates)
        for source in state.get('sources', []):
            if source not in merged['sources']:
                merged['sources'].append(source)
        
        # If any component is globally locked, reflect that
        if state.get('lock_global'):
            merged['lock_global'] = True
    
    return merged

async def handle_td_websocket(websocket, path):
    """Handle WebSocket connection from TouchDesigner"""
    client_addr = websocket.remote_address
    print(f"[TouchDesigner] Connected: {client_addr}")
    
    component_id = None
    
    async with td_lock:
        # Initially register without component_id (will be updated on first state message)
        td_clients[websocket] = None
        print(f"[Bridge] TD client added. Total TD clients: {len(td_clients)}, Total browsers: {len(browser_clients)}")
    
    try:
        async for message in websocket:
            # Parse message to check for state updates
            try:
                msg_data = json.loads(message)
                action = msg_data.get('action')
                
                if action == 'register_client':
                    # Handle client registration (info-only clients, auto-update preference)
                    client_type = msg_data.get('client_type', 'controller')
                    auto_update = msg_data.get('auto_update', True)
                    
                    if client_type == 'info' and not auto_update:
                        info_only_clients.add(websocket)
                        print(f"[Bridge] Registered INFO client (auto-update OFF)")
                    else:
                        info_only_clients.discard(websocket)
                        print(f"[Bridge] Registered client (auto-update ON)")
                    continue
                
                elif action == 'state_update':
                    # Extract and store component state
                    state = msg_data.get('state', {})
                    component_id = state.get('component_id')
                    
                    if component_id:
                        async with td_lock:
                            # Update component_id mapping
                            td_clients[websocket] = component_id
                            # Store this component's state
                            component_states[component_id] = state
                            print(f"[Bridge] Updated state for component '{component_id}'")
                        
                        # Create merged state and send to browsers
                        merged_state = merge_component_states()
                        merged_message = json.dumps({
                            'action': 'state_update',
                            'state': merged_state
                        })
                        
                        # Send merged state to all browsers
                        disconnected_browsers = []
                        for browser in list(browser_clients):
                            try:
                                await browser.send(merged_message)
                            except Exception as e:
                                print(f"[Bridge] Failed to send to browser: {e}")
                                disconnected_browsers.append(browser)
                        for browser in disconnected_browsers:
                            browser_clients.discard(browser)
                        
                        # Send to other TD clients ONLY if they want auto-updates
                        disconnected_tds = []
                        broadcast_count = 0
                        for td_socket, td_id in list(td_clients.items()):
                            if td_socket != websocket and td_socket not in info_only_clients:
                                try:
                                    await td_socket.send(merged_message)
                                    broadcast_count += 1
                                except Exception as e:
                                    print(f"[Bridge] Failed to send to TD client: {e}")
                                    disconnected_tds.append(td_socket)
                        for td_socket in disconnected_tds:
                            if td_socket in td_clients:
                                del td_clients[td_socket]
                        
                        print(f"[Bridge] Broadcasted merged state to {len(browser_clients)} browsers and {broadcast_count} TD clients (auto-update)")
                        continue
                
                elif action == 'request_state':
                    # Respond to explicit state request from any client
                    merged_state = merge_component_states()
                    response = json.dumps({
                        'action': 'state_update',
                        'state': merged_state
                    })
                    try:
                        await websocket.send(response)
                        print(f"[Bridge] Sent state to requesting TD client")
                    except Exception as e:
                        print(f"[Bridge] Failed to send state to TD client: {e}")
                    continue
                        
            except json.JSONDecodeError:
                pass
            
            # For non-state-update messages, broadcast as before
            print(f"[TD→All] {message[:100] if len(message) > 100 else message}")
            
            # Broadcast to all browsers
            disconnected_browsers = []
            for browser in list(browser_clients):
                try:
                    await browser.send(message)
                except Exception as e:
                    print(f"[Bridge] Failed to send to browser: {e}")
                    disconnected_browsers.append(browser)
            for browser in disconnected_browsers:
                browser_clients.discard(browser)
            
            # Also broadcast to other TD clients (excluding sender and info-only clients)
            disconnected_tds = []
            for td_socket in list(td_clients.keys()):
                if td_socket != websocket and td_socket not in info_only_clients:
                    try:
                        await td_socket.send(message)
                    except Exception as e:
                        print(f"[Bridge] Failed to send to TD client: {e}")
                        disconnected_tds.append(td_socket)
            for td_socket in disconnected_tds:
                if td_socket in td_clients:
                    del td_clients[td_socket]
                
    except websockets.exceptions.ConnectionClosed:
        print(f"[TouchDesigner] Disconnected: {client_addr}")
    finally:
        async with td_lock:
            if websocket in td_clients:
                component_id = td_clients[websocket]
                del td_clients[websocket]
                info_only_clients.discard(websocket)  # Remove from info-only set if present
                # Clean up component state
                if component_id and component_id in component_states:
                    del component_states[component_id]
                    print(f"[Bridge] Removed component '{component_id}'")
            print(f"[Bridge] TD client removed. Total TD clients: {len(td_clients)}")

async def run_websocket_servers(browser_port, td_port):
    """Run both WebSocket servers"""
    print(f"[WebSocket] Starting browser WebSocket on port {browser_port}")
    print(f"[WebSocket] Starting TD WebSocket on port {td_port}")
    
    browser_server = await websockets.serve(handle_browser_websocket, "0.0.0.0", browser_port)
    td_server = await websockets.serve(handle_td_websocket, "0.0.0.0", td_port)
    
    print(f"[WebSocket] Servers ready!")
    await asyncio.Future()  # Run forever

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="NDI Named Router Web Interface Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_server.py                           # Default: HTTP=80, Browser WS=8080, TD=8081
  python start_server.py --port 8090              # Custom HTTP port
  python start_server.py -w 9000 -t 9001         # Custom WebSocket ports
  python start_server.py --no-browser             # Don't open browser automatically
  
TouchDesigner Setup:
  WebSocket DAT connects as a CLIENT to the bridge server:
    - Network Address: localhost
    - Port: 8081 (or your --td-port value)
    - Active: ✓
    - Callbacks: Point to websocket1_callbacks
        """
    )
    
    parser.add_argument(
        '-p', '--port',
        type=int,
        default=80,
        help='Port number for the HTTP server (default: 80)'
    )
    
    parser.add_argument(
        '-w', '--websocket-port',
        type=int,
        default=8080,
        help='Port number for browser WebSocket connections (default: 8080)'
    )
    
    parser.add_argument(
        '-t', '--td-port',
        type=int,
        default=8081,
        help='Port number for TouchDesigner to connect to (default: 8081)'
    )
    
    parser.add_argument(
        '--no-browser',
        action='store_true',
        help='Don\'t automatically open the browser'
    )
    
    parser.add_argument(
        '--find-port',
        action='store_true',
        help='Automatically find an available port if the specified HTTP port is in use'
    )
    
    return parser.parse_args()

def main():
    """Main startup function"""
    args = parse_arguments()
    
    print("=" * 60)
    print("NDI Named Router Web Interface")
    print("HTTP + WebSocket Bridge Server")
    print("=" * 60)
    
    # Start WebSocket servers in background thread
    def run_ws_servers():
        asyncio.run(run_websocket_servers(args.websocket_port, args.td_port))
    
    ws_thread = threading.Thread(target=run_ws_servers, daemon=True)
    ws_thread.start()
    time.sleep(0.5)  # Let WebSocket servers start
    
    # Check for local URL options
    hostname = get_local_hostname()
    print(f"\nLOCAL ACCESS OPTIONS:")
    print(f"1. localhost: http://localhost:{args.port}")
    print(f"2. IP address: http://[YOUR_IP]:{args.port} (shown when server starts)")
    print(f"3. Hostname: http://{hostname}.local:{args.port} (works on most modern networks)")
    print()
    print(f"TOUCHDESIGNER CONFIGURATION:")
    print(f"  WebSocket DAT Settings:")
    print(f"    - Network Address: localhost")
    print(f"    - Port: {args.td_port}")
    print(f"    - Active: ✓")
    print(f"    - Callbacks DAT: websocket1_callbacks")
    print()
    print(f"BROWSER CONNECTS TO: ws://localhost:{args.websocket_port}")
    print("=" * 60)
    
    # Check current directory
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    # Check if templates directory exists
    templates_path = os.path.join(current_dir, "templates")
    print(f"Looking for templates directory at: {templates_path}")
    if not os.path.exists("templates"):
        print("Error: templates/ directory not found!")
        print("Make sure you're running this script from the project root directory.")
        print(f"Current directory contents: {os.listdir('.')}")
        return
    
    # Check if index.html exists
    index_path = os.path.join("templates", "index.html")
    print(f"Looking for index.html at: {index_path}")
    if not os.path.exists("templates/index.html"):
        print("Error: templates/index.html not found!")
        print("Make sure the web interface file is in the templates/ directory.")
        print(f"Templates directory contents: {os.listdir('templates')}")
        return
    
    print("Web interface files found")
    print("No external dependencies required")
    print()
    
    # Show configuration
    print(f"Configuration:")
    print(f"  HTTP Port: {args.port}")
    print(f"  Browser WebSocket Port: {args.websocket_port}")
    print(f"  TouchDesigner Port: {args.td_port}")
    print(f"  Auto-open browser: {'No' if args.no_browser else 'Yes'}")
    print(f"  Find available port: {'Yes' if args.find_port else 'No'}")
    print()
    
    # Start the server
    auto_open = not args.no_browser
    
    if args.find_port:
        # Check if port is available, find alternative if not
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', args.port))
            # Port is available
            start_server(args.port, args.websocket_port, auto_open)
        except OSError:
            # Port is in use, find alternative
            print(f"Port {args.port} is in use, finding alternative...")
            alternative_port = find_available_port(args.port + 1)
            if alternative_port:
                start_server(alternative_port, args.websocket_port, auto_open)
            else:
                print("No available ports found!")
    else:
        # Try the specified port, fail if not available
        start_server(args.port, args.websocket_port, auto_open)

if __name__ == "__main__":
    main() 