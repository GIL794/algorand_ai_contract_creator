"""
main.py — Entry point to run the AI-Powered Algorand Smart Contract Creator
"""

import sys
import subprocess
from pathlib import Path

if __name__ == "__main__":
    # Add src directory to Python path so imports work
    project_root = Path(__file__).parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    # Also add project root to path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Define the script you want to run (your Streamlit file)
    app_file = str(project_root / "src" / "algorand_ai_contractor" / "ui" / "streamlit_app.py")
    
    # Use subprocess to run Streamlit as a separate process
    # This avoids the "Runtime instance already exists" error
    import socket
    import platform
    
    def is_port_in_use(port):
        """Check if a port is already in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    def kill_process_on_port(port):
        """Kill any process using the specified port (Windows only)."""
        if platform.system() != 'Windows':
            return False
        
        try:
            # Find process using the port
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                check=False
            )
            
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) >= 5:
                        pid = parts[-1]
                        try:
                            # Kill the process
                            subprocess.run(
                                ['taskkill', '/F', '/PID', pid],
                                capture_output=True,
                                check=False
                            )
                            print(f"✅ Killed process {pid} that was using port {port}")
                            return True
                        except Exception as e:
                            print(f"⚠️  Could not kill process {pid}: {e}")
                            return False
        except Exception as e:
            print(f"⚠️  Error checking for processes on port {port}: {e}")
        
        return False
    
    # Check if default port is in use
    default_port = 8501
    if is_port_in_use(default_port):
        print(f"\n⚠️  Port {default_port} is already in use.")
        print("💡 Attempting to kill the process using port 8501...")
        
        if kill_process_on_port(default_port):
            # Wait a moment for the port to be released
            import time
            time.sleep(1)
            # Check again
            if not is_port_in_use(default_port):
                print(f"✅ Port {default_port} is now free!")
                port = default_port
            else:
                print(f"⚠️  Port {default_port} is still in use. Trying alternative port 8502...")
                port = 8502
        else:
            print("💡 Could not kill the process. Trying alternative port 8502...")
            port = 8502
    else:
        port = default_port
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "streamlit", "run", app_file, "--server.port", str(port)],
            check=False  # Don't raise on non-zero exit
        )
        if result.returncode != 0:
            if result.returncode == 1:
                print("\n⚠️  Streamlit failed to start.")
                print("💡 Common causes:")
                print("   - Port is already in use")
                print("   - Missing dependencies")
                print("\n💡 Solutions:")
                print("   - Close other Streamlit apps")
                print(f"   - Or run directly: streamlit run {app_file} --server.port {port + 1}")
            sys.exit(result.returncode)
    except KeyboardInterrupt:
        # Allow graceful exit on Ctrl+C
        print("\n👋 Shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error running Streamlit: {e}")
        print("\n💡 Try running directly:")
        print(f"   streamlit run {app_file}")
        sys.exit(1)
