from flask import Flask, request, jsonify
import hmac
import hashlib
import subprocess
import os
import time
import fcntl
import logging
import builtins
from dotenv import load_dotenv


# Custom exception classes
class DeploymentError(Exception):
    """Exception raised for deployment failures"""

    pass


# Load environment variables
load_dotenv()

app = Flask(__name__)
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")
PROJECT_PATH = "/home/nexus/nexus"
VENV_PATH = os.path.join(PROJECT_PATH, "venv")
VENV_PYTHON = os.path.join(VENV_PATH, "bin", "python")
VENV_PIP = os.path.join(VENV_PATH, "bin", "pip")
LOCK_FILE = "/tmp/nexus_webhook.lock"

logger = logging.getLogger("github_webhook")
if not logger.handlers:
    logs_dir = os.path.join(PROJECT_PATH, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    handler = logging.FileHandler(os.path.join(logs_dir, "github_webhook.log"))
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

_print = builtins.print


def print(*args, **kwargs):  # type: ignore
    msg = " ".join(str(a) for a in args)
    logger.info(msg)
    return _print(*args, **kwargs)


print(f"Webhook secret loaded: {WEBHOOK_SECRET is not None}")
print(f"Virtual environment Python: {VENV_PYTHON}")
print(f"Virtual environment PIP: {VENV_PIP}")


@app.route("/webhook", methods=["POST"])
def webhook():
    # Prevent concurrent deployments with file lock
    lock_fd = None
    try:
        lock_fd = os.open(LOCK_FILE, os.O_CREAT | os.O_WRONLY | os.O_EXCL)
    except FileExistsError:
        print("⚠️  Another deployment is already in progress, skipping...")
        return jsonify({"status": "skipped", "reason": "deployment_in_progress"}), 409
    except Exception as e:
        print(f"❌ Error creating lock file: {e}")
        import traceback

        print(traceback.format_exc())  # Log to server only
        return (
            jsonify({"status": "error", "message": "Lock file error"}),
            500,
        )

    try:
        print("=== WEBHOOK RECEIVED ===")
        print(f"Remote addr: {request.remote_addr}")
        print(f"User-Agent: {request.headers.get('User-Agent')}")
        print(f"X-GitHub-Event: {request.headers.get('X-GitHub-Event')}")

        signature = request.headers.get("X-Hub-Signature-256", "")
        print(f"Signature header: '{signature}'")
        print(f"WEBHOOK_SECRET exists: {WEBHOOK_SECRET is not None}")

        # Add more detailed error logging
        if not WEBHOOK_SECRET:
            print("❌ WEBHOOK_SECRET is not set!")
            return jsonify({"error": "Webhook secret not configured"}), 500

        # Verify signature first
        if not verify_signature(request.get_data(), signature):
            print("SIGNATURE VERIFICATION FAILED")
            return jsonify({"error": "Invalid signature"}), 401

        print("SIGNATURE VERIFICATION SUCCESSFUL!")

        # Only process if it's a push event
        if request.headers.get("X-GitHub-Event") == "push":
            try:
                payload = request.get_json()
                branch = payload.get("ref", "").split("/")[-1]
                print(f"Push event to branch: {branch}")

                if branch == "main":
                    print("Pulling latest changes...")
                    result = subprocess.run(
                        ["git", "pull", "origin", "main"],
                        cwd=PROJECT_PATH,
                        capture_output=True,
                        text=True,
                        check=True,
                        timeout=60,  # 1 minute timeout for git pull
                        env={
                            **os.environ,
                            "GIT_SSH_COMMAND": "ssh -i /home/nexus/.ssh/id_nexus -o IdentitiesOnly=yes -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no",
                        },
                    )
                    print(f"Git pull output: {result.stdout}")

                    print("Installing dependencies in virtual environment...")
                    pip_result = subprocess.run(
                        [VENV_PIP, "install", "-r", "requirements.txt"],
                        cwd=PROJECT_PATH,
                        capture_output=True,
                        text=True,
                        timeout=300,  # 5 minute timeout
                    )
                    print(f"pip install stdout: {pip_result.stdout}")
                    print(f"pip install stderr: {pip_result.stderr}")
                    print(f"pip install returncode: {pip_result.returncode}")

                    # Fail if pip install had errors
                    if pip_result.returncode != 0:
                        error_msg = f"pip install failed with return code {pip_result.returncode}: {pip_result.stderr}"
                        print(f"❌ {error_msg}")
                        raise DeploymentError(error_msg)

                    # Verify uvicorn is available in venv
                    print("Verifying uvicorn installation in venv...")
                    verify_result = subprocess.run(
                        [
                            VENV_PYTHON,
                            "-c",
                            'import uvicorn; print("uvicorn available")',
                        ],
                        cwd=PROJECT_PATH,
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    print(
                        f"Uvicorn verification returncode: {verify_result.returncode}"
                    )
                    print(f"Uvicorn stdout: {verify_result.stdout}")
                    if verify_result.stderr:
                        print(f"Uvicorn stderr: {verify_result.stderr}")

                    # Fail if uvicorn is not available
                    if verify_result.returncode != 0:
                        error_msg = f"uvicorn not available in virtual environment: {verify_result.stderr}"
                        print(f"❌ {error_msg}")
                        raise DeploymentError(error_msg)

                    print("Restarting application via systemd...")
                    restart_application()

                    # Verify service started successfully
                    print("Verifying service status...")
                    time.sleep(3)  # Give service a moment to start
                    status_result = subprocess.run(
                        ["sudo", "systemctl", "is-active", "nexus.service"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if (
                        status_result.returncode == 0
                        and status_result.stdout.strip() == "active"
                    ):
                        print("✅ Service is active and running")
                    else:
                        print(
                            f"⚠️  Service status check: {status_result.stdout.strip()}"
                        )
                        # Don't fail here, but log the warning

                    return jsonify(
                        {
                            "status": "success",
                            "output": result.stdout,
                            "branch": branch,
                            "uvicorn_available": verify_result.returncode == 0,
                        }
                    )
            except Exception as e:
                import traceback

                error_trace = traceback.format_exc()
                print(f"❌ Error processing webhook: {e}")
                print(f"Traceback:\n{error_trace}")  # Log to server only
                return (
                    jsonify({"status": "error", "message": "Deployment failed"}),
                    500,
                )

        return jsonify({"status": "ignored"})
    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()
        print(f"❌ Unexpected error in webhook handler: {e}")
        print(f"Traceback:\n{error_trace}")  # Log to server only
        return (
            jsonify({"status": "error", "message": "Internal server error"}),
            500,
        )
    finally:
        # Always release the lock
        if lock_fd is not None:
            try:
                os.close(lock_fd)
                os.unlink(LOCK_FILE)
            except Exception as e:
                print(f"⚠️  Error releasing lock: {e}")


def verify_signature(payload_body, signature_header):
    print("=== SIGNATURE VERIFICATION DEBUG ===")
    print(f"Signature header: '{signature_header}'")
    print(f"WEBHOOK_SECRET exists: {WEBHOOK_SECRET is not None}")
    if WEBHOOK_SECRET:
        print(f"WEBHOOK_SECRET length: {len(WEBHOOK_SECRET)}")
        print(f"WEBHOOK_SECRET starts with: {WEBHOOK_SECRET[:10]}...")

    if not signature_header or not WEBHOOK_SECRET:
        print("FAIL: Missing signature or secret")
        return False

    if not signature_header.startswith("sha256="):
        print("FAIL: Invalid signature format")
        return False

    received_signature = signature_header[7:]

    # Calculate expected signature
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(), msg=payload_body, digestmod=hashlib.sha256
    ).hexdigest()

    print(f"Received signature: {received_signature}")
    print(f"Expected signature: {expected_signature}")
    print(f"Signatures match: {received_signature == expected_signature}")

    match = hmac.compare_digest(received_signature, expected_signature)
    print(f"HMAC compare result: {match}")
    print("=== END SIGNATURE DEBUG ===")

    return match


def restart_application():
    """Restart the nexus systemd service"""
    print("Restarting nexus.service via systemctl...")
    result = subprocess.run(
        ["sudo", "systemctl", "restart", "nexus.service"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("✅ Service restarted successfully")
        print(f"Service output: {result.stdout}")
    else:
        print(f"❌ Error restarting service: {result.stderr}")
        raise DeploymentError(f"Failed to restart service: {result.stderr}")


@app.route("/webhook", methods=["GET"])
def webhook_get():
    """GET endpoint for testing webhook connectivity"""
    return jsonify({"status": "webhook endpoint active", "methods": ["POST"]}), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "webhook listener running"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
