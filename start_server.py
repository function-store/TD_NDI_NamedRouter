#!/usr/bin/env python3
"""
Simple startup script for NDI Named Router Web Interface
Starts a static file server to serve the web interface
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
                        "const WS_PORT = '8080';  // TouchDesigner WebSocket DAT port",
                        f"const WS_PORT = '{websocket_port}';  // TouchDesigner WebSocket DAT port"
                    )
                    
                    self.wfile.write(html_content.encode('utf-8'))
                    print(f"Served index.html with WebSocket port {websocket_port}")
                except Exception as e:
                    print(f"Error serving index.html: {e}")
                    self.send_error(500, f"Error loading index.html: {e}")
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

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="NDI Named Router Web Interface Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start_server.py                           # Default ports: HTTP=80, WebSocket=8080
  python start_server.py --port 8090              # Custom HTTP port, default WebSocket port
  python start_server.py --websocket-port 9000    # Custom WebSocket port, default HTTP port
  python start_server.py -p 3000 -w 9000          # Custom HTTP and WebSocket ports
  python start_server.py --no-browser             # Don't open browser automatically
  python start_server.py -p 8090 -w 9000 --no-browser  # All custom settings
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
        help='Port number for TouchDesigner WebSocket DAT (default: 8080)'
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
    print("Static File Server (No Dependencies Required)")
    print("=" * 60)
    
    # Check for local URL options
    hostname = get_local_hostname()
    print(f"\n🌐 LOCAL ACCESS OPTIONS:")
    print(f"1. localhost: http://localhost:{args.port}")
    print(f"2. IP address: http://[YOUR_IP]:{args.port} (shown when server starts)")
    print(f"3. Hostname: http://{hostname}.local:{args.port} (works on most modern networks)")
    print(f"4. Custom local domain: Edit your hosts file for custom names")
    print()
    print(f"📡 TOUCHDESIGNER WEBSOCKET:")
    print(f"Configure your TouchDesigner WebSocket DAT to port {args.websocket_port}")
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
    
    print("✓ Web interface files found")
    print("✓ No external dependencies required")
    print()
    
    # Show configuration
    print(f"Configuration:")
    print(f"  HTTP Port: {args.port}")
    print(f"  WebSocket Port: {args.websocket_port}")
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