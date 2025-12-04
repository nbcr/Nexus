# Email Registration Configuration Guide

## Overview

Registration emails are now automatically sent to new users when they sign up. The system is configured with fallback support for multiple email providers.

## Current Configuration

✅ **Local Mail (Postfix)** - Installed and running  
✅ **Brevo API** - Configured (API key in .env)  
✅ **SMTP Settings** - Configured in .env

## Email Flow

1. User registers with username, email, and password
2. Account is created in database
3. Anonymous session data is migrated (if applicable)
4. **Welcome email is sent asynchronously**
5. Registration response returns immediately (email sending doesn't block)

## Email Provider Priority

The system tries to send emails in this order:

1. **Brevo API** - If `BREVO_API_KEY` is set in .env
2. **SMTP** - Falls back to configured SMTP server (currently localhost:25 with Postfix)

## Configuration Files

### .env Settings
```bash
# Email Configuration
SMTP_SERVER=localhost
SMTP_PORT=25
SMTP_USER=              # Leave empty for local mail
SMTP_PASSWORD=          # Leave empty for local mail
SENDER_EMAIL=nexus@comdat.ca
ADMIN_EMAIL=webmaster@comdat.ca
BREVO_API_KEY=...       # (already configured)
```

### app/core/config.py
Email settings are loaded from .env and include:
- `SMTP_SERVER` - Mail server hostname
- `SMTP_PORT` - Mail server port
- `SMTP_USER` - Username (optional)
- `SMTP_PASSWORD` - Password (optional)
- `SENDER_EMAIL` - From address for emails
- `ADMIN_EMAIL` - Admin notification recipient

## Features

### Welcome Email Includes
- Personalized greeting with user's username
- Professional HTML and plain text versions
- Link to Nexus application
- Footer with admin contact info
- Encouragement to customize news feed

### Error Handling
- Email failures don't block registration
- Errors are logged to `/home/nexus/nexus/logs/error.log`
- User registration completes even if email fails
- Admin can resend emails manually if needed

## Testing

### Manual Test
```bash
cd /home/nexus/nexus
source venv/bin/activate
python3 << 'EOF'
from app.services.email_service import email_service
result = email_service.send_registration_email("test@example.com", "testuser")
print(f"Result: {result}")
EOF
```

### Check Logs
```bash
# Application logs
tail -50 /home/nexus/nexus/logs/error.log

# Postfix logs
sudo tail -50 /var/log/mail.log

# System logs
journalctl -u postfix -n 50
```

## Troubleshooting

### Email not sending
1. Check Postfix status:
   ```bash
   sudo systemctl status postfix
   sudo systemctl start postfix
   ```

2. Test SMTP connection:
   ```bash
   telnet localhost 25
   # Should connect without error
   ```

3. Check mail logs:
   ```bash
   sudo tail -100 /var/log/mail.log
   ```

### Brevo vs SMTP
- If `BREVO_API_KEY` is set, Brevo is tried first
- If Brevo fails or key is missing, SMTP fallback is used
- To force SMTP only: remove `BREVO_API_KEY` from .env

### Test specific provider
```bash
# Test Brevo only
python3 -c "from app.services.email_service import EmailService; s = EmailService(); s._send_via_brevo('test@example.com', 'Test', '<h1>Test</h1>')"

# Test SMTP only
python3 -c "from app.services.email_service import EmailService; s = EmailService(); s._send_via_smtp('test@example.com', 'Test', '<h1>Test</h1>')"
```

## Configuration Options

### Use Brevo Only
```bash
# In .env, keep BREVO_API_KEY set and SMTP_SERVER=localhost
```

### Use Gmail
```bash
# In .env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SENDER_EMAIL=your-email@gmail.com

# Generate app password at: https://myaccount.google.com/apppasswords
```

### Use AWS SES
```bash
# In .env
SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=ses-smtp-user
SMTP_PASSWORD=ses-password
SENDER_EMAIL=noreply@yourdomain.com

# Verify sender email in AWS SES console first
```

## Monitoring

### Check if emails are sending
1. Register a test user
2. Check if email is received
3. Check logs: `tail -100 /home/nexus/nexus/logs/error.log`

### Email Volume
- One email per registration
- Sent asynchronously (non-blocking)
- No rate limiting currently implemented

## Future Enhancements

Possible additions:
- Password reset emails
- Email verification before account activation
- Notification emails for saved articles
- Digest emails for trending topics
- Email preferences per user

---

**Last Updated**: 2025-12-04  
**Status**: ✅ Production Ready  
**Email System**: Postfix + Brevo API + SMTP Fallback
