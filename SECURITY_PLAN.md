# Security Plan — AI_Data_Literacy Project

## Threat Model

This is a personal blog analysis project. Data is public GitHub profile info.
Attack surface is small: one VPS, one local machine, one Google Drive account.

---

## 1. VPS (Hetzner) — Active Risks

### 1.1 SSH Access
- **Risk:** Brute force or credential theft gives full root access
- **Current state:** Root login via SSH key (id_ed25519), fail2ban installed
- **Required:**
  - Confirm `PasswordAuthentication no` in `/etc/ssh/sshd_config`
  - Confirm fail2ban is active: `systemctl status fail2ban`
  - Keep SSH key passphrase-protected locally

### 1.2 GitHub API Token
- **Risk:** Token in fetch_locations.py leaks — attacker burns your rate limit or impersonates you
- **Required:**
  - Token must live in `.env` file, never hardcoded in script
  - `.env` must be in `.gitignore` (already confirmed)
  - Token scope: read-only public_profile — no write permissions needed

### 1.3 Process Management
- **Risk:** Runaway duplicate processes corrupt data (already happened — fixed)
- **Required:**
  - Only one fetch_locations.py process at a time
  - Add PID lock file to script (write PID on start, check/remove on exit)

### 1.4 CSV Data Exposure
- **Risk:** CSV contains 197k GitHub usernames + scores — low sensitivity but should not be public
- **Current state:** Synced to Google Drive (private folder)
- **Required:**
  - Confirm Google Drive folder is not shared publicly
  - CSV excluded from git via .gitignore (already confirmed)

### 1.5 rclone OAuth Token
- **Risk:** ~/.config/rclone/rclone.conf contains a long-lived OAuth token
- **Required:**
  - File permissions: chmod 600 ~/.config/rclone/rclone.conf (set by rclone by default)
  - Never commit or copy this file anywhere

---

## 2. Local Machine (Windows) — Active Risks

### 2.1 PostgreSQL Access
- **Risk:** Default postgres superuser with weak/no password
- **Required:**
  - Set a strong password on the postgres superuser
  - Create a dedicated read/write user for this project (not superuser)
  - Bind PostgreSQL to 127.0.0.1 only (default on Windows installer)

### 2.2 Google Drive Credentials
- **Risk:** rclone or Google Drive desktop app token gives access to your entire Drive
- **Required:**
  - Only download the specific project folder, not full Drive sync
  - Use manual download or scoped rclone remote

### 2.3 geopy/Nominatim (future)
- **Risk:** Nominatim is free and keyless but has usage policies
- **Required:**
  - Set a proper user_agent string in geopy (required by Nominatim TOS)
  - Rate limit: max 1 request/second (build in sleep)
  - Cache geocode results in PostgreSQL — never geocode the same address twice

---

## 3. What Does NOT Need Securing

- The data itself is public (GitHub profiles are public)
- No user PII beyond what GitHub users chose to publish
- No payment info, no auth systems, no external-facing web app
- Kepler.gl and DBeaver are local-only tools

---

## 4. Security Checklist (run before Step 3)

```
[ ] VPS: PasswordAuthentication no in sshd_config
[ ] VPS: fail2ban active
[ ] VPS: GitHub token in .env, not hardcoded in fetch_locations.py
[ ] VPS: .env in .gitignore
[ ] VPS: rclone.conf permissions are 600
[ ] VPS: Google Drive folder not publicly shared
[ ] Local: PostgreSQL bound to 127.0.0.1
[ ] Local: Strong postgres superuser password set
[ ] Local: Project DB user is not superuser
[ ] Local: geopy uses proper user_agent + 1 req/sec rate limit
[ ] Local: geopy results cached — no repeat geocoding
```
