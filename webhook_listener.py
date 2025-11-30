from flask import Flask, request, jsonify
import hmac
import hashlib
import subprocess
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')
PROJECT_PATH = '/home/nexus/nexus'
VENV_PATH = os.path.join(PROJECT_PATH, 'venv')
VENV_PYTHON = os.path.join(VENV_PATH, 'bin', 'python')
VENV_PIP = os.path.join(VENV_PATH, 'bin', 'pip')

print(f"Webhook secret loaded: {WEBHOOK_SECRET is not None}")
print(f"Virtual environment Python: {VENV_PYTHON}")
print(f"Virtual environment PIP: {VENV_PIP}")

@app.route('/webhook', methods=['POST'])
def webhook():
    print("=== WEBHOOK RECEIVED ===")
    print(f"Remote addr: {request.remote_addr}")
    print(f"User-Agent: {request.headers.get('User-Agent')}")
    print(f"X-GitHub-Event: {request.headers.get('X-GitHub-Event')}")
    
    signature = request.headers.get('X-Hub-Signature-256', '')
    print(f"Signature header: '{signature}'")
    print(f"WEBHOOK_SECRET exists: {WEBHOOK_SECRET is not None}")

    # Verify signature first
    if not verify_signature(request.get_data(), signature):
        print("SIGNATURE VERIFICATION FAILED")
        return jsonify({'error': 'Invalid signature'}), 401

    print("SIGNATURE VERIFICATION SUCCESSFUL!")
    
    # Only process if it's a push event
    if request.headers.get('X-GitHub-Event') == 'push':
        try:
            payload = request.get_json()
            branch = payload.get('ref', '').split('/')[-1]
            print(f"Push event to branch: {branch}")

            if branch == 'main':
                print("Pulling latest changes...")
                result = subprocess.run(
                    ['git', 'pull', 'origin', 'main'],
                    cwd=PROJECT_PATH,
                    capture_output=True,
                    text=True,
                    check=True,
                    env={
                        **os.environ,
                        'GIT_SSH_COMMAND': 'ssh -i /home/nexus/.ssh/id_nexus -o IdentitiesOnly=yes -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'
                    }
                )
                print(f"Git pull output: {result.stdout}")

                print("Installing dependencies in virtual environment...")
                pip_result = subprocess.run(
                    [VENV_PIP, 'install', '-r', 'requirements.txt'],
                    cwd=PROJECT_PATH,
                    capture_output=True,
                    text=True
                )
                print(f"pip install stdout: {pip_result.stdout}")
                print(f"pip install stderr: {pip_result.stderr}")
                print(f"pip install returncode: {pip_result.returncode}")

                # Verify uvicorn is available in venv
                print("Verifying uvicorn installation in venv...")
                verify_result = subprocess.run(
                    [VENV_PYTHON, '-c', 'import uvicorn; print("uvicorn available")'],
                    cwd=PROJECT_PATH,
                    capture_output=True,
                    text=True
                )
                print(f"Uvicorn verification returncode: {verify_result.returncode}")
                print(f"Uvicorn stdout: {verify_result.stdout}")
                if verify_result.stderr:
                    print(f"Uvicorn stderr: {verify_result.stderr}")

                print("Restarting application via systemd...")
                restart_application()

                return jsonify({
                    'status': 'success',
                    'output': result.stdout,
                    'branch': branch,
                    'uvicorn_available': verify_result.returncode == 0
                })
        except Exception as e:
            print(f"Error processing webhook: {e}")
            import traceback
            print(traceback.format_exc())
            return jsonify({'status': 'error', 'message': str(e)}), 500

    return jsonify({'status': 'ignored'})

def verify_signature(payload_body, signature_header):
    print(f"=== SIGNATURE VERIFICATION DEBUG ===")
    print(f"Signature header: '{signature_header}'")
    print(f"WEBHOOK_SECRET exists: {WEBHOOK_SECRET is not None}")
    if WEBHOOK_SECRET:
        print(f"WEBHOOK_SECRET length: {len(WEBHOOK_SECRET)}")
        print(f"WEBHOOK_SECRET starts with: {WEBHOOK_SECRET[:10]}...")
    
    if not signature_header or not WEBHOOK_SECRET:
        print(f"FAIL: Missing signature or secret")
        return False

    if not signature_header.startswith('sha256='):
        print(f"FAIL: Invalid signature format")
        return False

    received_signature = signature_header[7:]
    
    # Calculate expected signature
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        msg=payload_body,
        digestmod=hashlib.sha256
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
        ['sudo', 'systemctl', 'restart', 'nexus.service'],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✅ Service restarted successfully")
        print(f"Service output: {result.stdout}")
    else:
        print(f"❌ Error restarting service: {result.stderr}")
        raise Exception(f"Failed to restart service: {result.stderr}")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'webhook listener running'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
