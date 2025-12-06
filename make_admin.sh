#!/bin/bash
sudo -u postgres psql -d nexus <<EOF
UPDATE users SET is_admin = true WHERE username = 'yot' OR email LIKE '%yot%';
SELECT username, is_admin FROM users WHERE is_admin = true;
EOF
