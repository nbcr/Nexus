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

    _svc_name_ = "NexusServer"
    _svc_display_name_ = "Nexus AI News Platform"
    _svc_description_ = "FastAPI server for Nexus AI news aggregation and personalization"

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
            handlers=[
                logging.FileHandler(str(self.log_file)),
                logging.StreamHandler()
            ]
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

    def SvcDoRun(self):
        """Run the service"""
        self.logger.info("=" * 80)
        self.logger.info("Nexus Service Starting")
        self.logger.info(f"Working directory: {PROJECT_ROOT}")
        self.logger.info("=" * 80)
        
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        
        # Change to project directory
        os.chdir(PROJECT_ROOT)
        
        # Start server in a thread
        server_thread = Thread(target=self._run_server, daemon=True)
        server_thread.start()
        
        # Wait for stop event
        win32event.WaitForMultipleObjects(
            [self.hWaitStop],
            False,
            win32event.INFINITE
        )

    def _run_server(self):
        """Run the uvicorn server with auto-restart on crash"""
        python_exe = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
        
        if not python_exe.exists():
            self.logger.error(f"Python executable not found: {python_exe}")
            return
        
        restart_count = 0
        max_restarts = 10
        restart_window = 60  # seconds
        last_crash_time = None
        
        while self.is_alive:
            try:
                self.logger.info(
                    f"Starting Nexus server (attempt {restart_count + 1})..."
                )
                
                self.server_process = subprocess.Popen(
                    [
                        str(python_exe),
                        "-m",
                        "uvicorn",
                        "app.main:app",
                        "--host", "127.0.0.1",
                        "--port", "8000",
                        "--workers", "2",
                        "--log-level", "info",
                    ],
                    cwd=str(PROJECT_ROOT),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
                
                self.logger.info(f"Server started with PID {self.server_process.pid}")
                restart_count = 0  # Reset on successful start
                
                # Wait for process to exit
                self.server_process.wait()
                
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
                self.logger.error(f"Error running server: {e}")
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
