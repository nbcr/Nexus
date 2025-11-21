import requests
from app.core.config import settings

def send_registration_email(to_email: str, username: str):
    api_key = getattr(settings, "BREVO_API_KEY", None)
    if not api_key:
        raise ValueError("Brevo API key not set in .env or config")

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    data = {
        "sender": {"name": "Nexus App", "email": "your_verified_sender@domain.com"},
        "to": [{"email": to_email, "name": username}],
        "subject": "Welcome to Nexus!",
        "htmlContent": f"""
            <html>
                <body>
                    <h2>Welcome, {username}!</h2>
                    <p>Thank you for registering at Nexus.</p>
                </body>
            </html>
        """
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()
