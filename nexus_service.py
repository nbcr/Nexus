#!/usr/bin/env python3
"""
Windows Service for Nexus FastAPI Server

This script enables running the Nexus server as a Windows service that:
- Starts automatically on system boot
- Restarts automatically if it crashes
- Can be managed via Services.msc or command line

Installation:
    python nexus_service.py install

Start/Stop:
    python nexus_service.py start
    python nexus_service.py stop

Remove:
    python nexus_service.py remove
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import servicemanager
    import win32serviceutil
    import win32service
    import win32event
    import win32api
except ImportError:
    print("ERROR: pywin32 not installed. Install with: pip install pywin32")
    sys.exit(1)

import subprocess
import time
from threading import Thread


class NexusService(win32serviceutil.ServiceFramework):
    """Windows Service for Nexus FastAPI Server"""

    _svc_name_ = "Nexus"
    _svc_display_name_ = "Nexus AI News Platform"
    _svc_description_ = (
        "FastAPI server for Nexus AI news aggregation and personalization"
    )

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_alive = True
        self.server_process = None

        # Setup logging
        self.log_file = PROJECT_ROOT / "logs" / "service.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(str(self.log_file)), logging.StreamHandler()],
        )
        self.logger = logging.getLogger("NexusService")

    def SvcStop(self):
        """Stop the service"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False
        if self.server_process:
            self.logger.info("Stopping Nexus server...")
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=10)
            except Exception as e:
                self.logger.error(f"Error stopping server: {e}")
                if self.server_process.poll() is None:
                    self.server_process.kill()
        self.logger.info("Service stopped")

    def _check_dependencies(self):
        """Check if required services are running"""
        # Dependencies are optional - server can start independently
        # nginx and PostgreSQL should be running for full functionality,
        # but the API can start without them for development/testing
        self.logger.info("Dependency checks skipped - starting API server")
        return True

    def _is_process_running(self, process_name):
        """Check if a process is running"""
        try:
            import psutil

            for proc in psutil.process_iter(["name"]):
                if proc.info["name"] == process_name:
                    return True
            return False
        except ImportError:
            self.logger.error("psutil not available for process check")
            return False

    def _is_postgresql_running(self):
        """Check if PostgreSQL is accessible"""
        try:
            import psycopg2
            from app.core.config import settings

            conn = psycopg2.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USER,
                password=settings.DB_PASS,
                database=settings.DB_NAME,
                connect_timeout=5,
            )
            conn.close()
            return True
        except Exception as e:
            self.logger.error(f"Cannot connect to PostgreSQL: {e}")
            return False

    def SvcDoRun(self):
        """Run the service"""
        self.logger.info("=" * 80)
        self.logger.info("Nexus Service Starting")
        self.logger.info(f"Working directory: {PROJECT_ROOT}")
        self.logger.info("=" * 80)

        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )

        # Check dependencies
        if not self._check_dependencies():
            self.logger.error("Dependencies not met, service will not start")
            self.ReportServiceStatus(win32service.SERVICE_STOPPED)
            return

        # Change to project directory
        os.chdir(PROJECT_ROOT)

        # Start server in a thread
        server_thread = Thread(target=self._run_server, daemon=True)
        server_thread.start()

        # Give service time to fully start before waiting (prevents timeout)
        time.sleep(5)

        # Wait for stop event
        win32event.WaitForMultipleObjects([self.hWaitStop], False, win32event.INFINITE)

    def _run_server(self):
        """Run the uvicorn server with auto-restart on crash"""
        # Use Program Files Python (where dependencies are installed globally)
        python_exe = Path("C:\\Program Files\\Python312\\python.exe")

        # Fallback to venv if Program Files doesn't exist
        if not python_exe.exists():
            python_exe = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"

        if not python_exe.exists():
            self.logger.error(f"Python executable not found at {python_exe}")
            self.logger.error(f"Also checked: {PROJECT_ROOT / 'venv' / 'Scripts' / 'python.exe'}")
            return

        restart_count = 0
        max_restarts = 10
        restart_window = 60  # seconds
        last_crash_time = None

        while self.is_alive:
            try:
                self.logger.info(
                    f"Starting Nexus server (attempt {restart_count + 1}) using {python_exe}..."
                )

                # Clean up any stale processes on port 8000 before starting
                if restart_count > 0:
                    try:
                        import socket
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        result = sock.connect_ex(('127.0.0.1', 8000))
                        sock.close()
                        if result == 0:
                            self.logger.warning("Port 8000 still in use, waiting...")
                            time.sleep(2)
                    except Exception as e:
                        self.logger.debug(f"Port check: {e}")

                # Set up environment for subprocess
                env = os.environ.copy()
                env["PYTHONPATH"] = str(PROJECT_ROOT)
                env["PYTHONUNBUFFERED"] = "1"
                env["PYTHONIOENCODING"] = "utf-8"  # Force UTF-8 to handle emojis

                # Start using run_server.py directly for better compatibility
                self.server_process = subprocess.Popen(
                    [
                        str(python_exe),
                        "run_server.py",
                    ],
                    cwd=str(PROJECT_ROOT),
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",  # Replace unencodable chars instead of failing
                    bufsize=1,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )

                self.logger.info(f"Server started with PID {self.server_process.pid} using {python_exe}")
                restart_count = 0  # Reset on successful start

                # Log all output from server
                if self.server_process.stdout:
                    for line in iter(self.server_process.stdout.readline, ''):
                        if line:
                            self.logger.info(f"[SERVER] {line.rstrip()}")

                if self.is_alive:
                    exit_code = self.server_process.returncode
                    self.logger.warning(
                        f"Server exited with code {exit_code}, restarting..."
                    )

                    # Check restart frequency (crash loop protection)
                    now = time.time()
                    if last_crash_time and (now - last_crash_time) < restart_window:
                        restart_count += 1
                        if restart_count >= max_restarts:
                            self.logger.error(
                                f"Server crashed {max_restarts} times in {restart_window}s. "
                                "Stopping service to prevent crash loop."
                            )
                            break
                    else:
                        restart_count = 1

                    last_crash_time = now

                    # Wait before restart
                    delay = min(30, restart_count * 5)  # Max 30 second wait
                    self.logger.info(f"Waiting {delay}s before restart...")
                    time.sleep(delay)

            except Exception as e:
                self.logger.error(f"Error running server: {e}", exc_info=True)
                if self.is_alive:
                    time.sleep(5)

    def SvcShutdown(self):
        """Handle system shutdown"""
        self.SvcStop()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Run as service
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(NexusService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Handle command line: install, start, stop, remove
        win32serviceutil.HandleCommandLine(NexusService)
