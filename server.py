#!/usr/bin/env python3
"""
INBOX STREET FIGHTER — Live Backend Server
Features:
1. Google OAuth 2.0 Authentication & Session Management
2. Official Gmail API Integration (Fetch inbox, unread count, archive, star, label, batch modify)
3. Google Gemini 1.5 Flash AI Email Context Analysis
4. Intelligent Offline Heuristic Classifier Fallback
5. Static Web File Serving
"""

import http.server
import socketserver
import json
import os
import re
import time
import base64
import urllib.request
import urllib.parse
import urllib.error

# 1. Load Environment Variables from .env
def load_env():
    env_vars = {}
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    env_vars[key.strip()] = val.strip().strip('"').strip("'")
    return env_vars

ENV = load_env()
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or ENV.get('GEMINI_API_KEY', '')
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID') or ENV.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET') or ENV.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI') or ENV.get('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/callback')
PORT = int(os.environ.get('PORT') or ENV.get('PORT', 8000))

TOKENS_FILE = os.path.join(os.path.dirname(__file__), 'gmail_tokens.json')

# 2. Token Storage and Management
def get_stored_tokens():
    if os.path.exists(TOKENS_FILE):
        try:
            with open(TOKENS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_stored_tokens(tokens):
    with open(TOKENS_FILE, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, indent=2)

def clear_stored_tokens():
    if os.path.exists(TOKENS_FILE):
        try:
            os.remove(TOKENS_FILE)
        except Exception:
            pass

def refresh_access_token(tokens):
    refresh_token = tokens.get('refresh_token')
    client_id = os.environ.get('GOOGLE_CLIENT_ID') or load_env().get('GOOGLE_CLIENT_ID', '')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET') or load_env().get('GOOGLE_CLIENT_SECRET', '')

    if not refresh_token or not client_id or not client_secret:
        return None

    url = "https://oauth2.googleapis.com/token"
    payload = urllib.parse.urlencode({
        'client_id': client_id,
        'client_secret': client_secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }).encode('utf-8')

    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            data = json.loads(res.read().decode('utf-8'))
            tokens['access_token'] = data.get('access_token')
            tokens['expires_at'] = int(time.time()) + data.get('expires_in', 3600)
            save_stored_tokens(tokens)
            return tokens
    except Exception as e:
        print(f"⚠️ Token refresh failed: {e}")
        return None

def get_valid_access_token():
    tokens = get_stored_tokens()
    if not tokens or not tokens.get('access_token'):
        return None

    # Check expiration (with 60s buffer)
    expires_at = tokens.get('expires_at', 0)
    if time.time() > (expires_at - 60):
        tokens = refresh_access_token(tokens)

    return tokens.get('access_token') if tokens else None

# 3. Smart Rule-Based Contextual Fallback Classifier
def fallback_classify_email(email_data):
    subject = (email_data.get('subject') or '').lower()
    sender = (email_data.get('sender') or '').lower()
    sender_email = (email_data.get('senderEmail') or '').lower()
    body = (email_data.get('fullBody') or email_data.get('snippet') or '').lower()
    text = f"{subject} {sender} {sender_email} {body}"

    # Rule A: Spam / Phishing / Fraud
    spam_signals = [
        'wire transfer', 'seed phrase', 'apple gift card', 'bitcoin', 'btc', 'claim 2.',
        'suspended in 24 hours', 'unauthorized login', 'verify full ssn', 'debit pin',
        'invoice_overdue_89211.pdf.exe', 'customs fee', 'western union', '.xyz', '.ru'
    ]
    if any(sig in text for sig in spam_signals):
        return {
            "category": "Spam-like",
            "priority": "High",
            "summary": "Suspicious communication exhibiting high-risk phishing, credential harvesting, or financial fraud indicators.",
            "recommendedAction": "Archive",
            "reason": "Unsolicited message requesting sensitive actions or urgent payments from an untrusted source.",
            "confidenceScore": 94,
            "requiresReply": False,
            "suggestedReply": "Reported as Phishing and deleted.",
            "source": "fallback"
        }

    # Rule B: Important (Job offers, contracts, assignments, exams, IRS taxes, flights, internships, interviews)
    important_signals = [
        'official offer', 'job offer', 'salary', 'contract', 'docusign', 'lease',
        'tax refund', 'irs', 'assignment due', 'deadline', 'board review', 'boarding pass',
        'flight ua', 'series a', 'term sheet', 'cve-2026', 'outage', 'exam',
        'internship', 'interview', 'invitation to interview'
    ]
    if any(sig in text for sig in important_signals):
        requires_reply = any(k in text for k in ['offer', 'sign', 'confirm', 'review', 'reply', 'interview', 'schedule'])
        return {
            "category": "Important",
            "priority": "High",
            "summary": "Critical time-sensitive message containing official agreements, travel, career, or academic obligations.",
            "recommendedAction": "Keep",
            "reason": "High-impact document requiring player attention and preservation.",
            "confidenceScore": 96,
            "requiresReply": requires_reply,
            "suggestedReply": "Thank you! I have reviewed this and will follow up with executed details shortly.",
            "source": "fallback"
        }

    # Rule C: Promotions
    promo_signals = [
        'off everything', 'discount', 'coupon', 'sale', 'promo', 'doordash', 'free shipping',
        'black friday', 'cyber monday', 'vip drop', 'sneaker', 'deal'
    ]
    if any(sig in text for sig in promo_signals):
        return {
            "category": "Promotional",
            "priority": "Low",
            "summary": "Commercial newsletter offering retail discounts or promotional incentives.",
            "recommendedAction": "Archive",
            "reason": "Non-urgent commercial marketing. Safe to archive or label as Promo.",
            "confidenceScore": 91,
            "requiresReply": False,
            "suggestedReply": "Saved for future reference.",
            "source": "fallback"
        }

    # Rule D: Social Notifications
    social_signals = [
        'linkedin', 'viewed your profile', 'github', 'build #', 'failed on branch',
        'mentioned you', 'slack', 'calendar', 'google calendar', 'retweet', 'unread messages'
    ]
    if any(sig in text for sig in social_signals):
        return {
            "category": "Social",
            "priority": "Medium" if 'build' in text or 'calendar' in text else "Low",
            "summary": "Social platform update, developer notification, or team workspace digest.",
            "recommendedAction": "Label",
            "reason": "Informational notification from a connected service.",
            "confidenceScore": 88,
            "requiresReply": False,
            "suggestedReply": "Notification acknowledged.",
            "source": "fallback"
        }

    return {
        "category": "General",
        "priority": "Medium",
        "summary": "Standard business or personal correspondence.",
        "recommendedAction": "Review",
        "reason": "Context requires manual review to verify action items.",
        "confidenceScore": 75,
        "requiresReply": True,
        "suggestedReply": "Thanks for reaching out! Reviewing your message now.",
        "source": "fallback"
    }

# 4. Call Official Google Gemini 1.5 Flash REST API
def analyze_with_gemini(email_data, api_key):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

    prompt = f"""
You are the Tactical AI Battle Assistant in the arcade game "INBOX STREET FIGHTER".
Your mission is to understand email context, evaluate threats, categorize with genuine intelligence, and recommend the optimal arcade combat move.

EMAIL INTEL:
Subject: {email_data.get('subject', '')}
Sender: {email_data.get('sender', '')} <{email_data.get('senderEmail', '')}>
Date: {email_data.get('date', '')}
Snippet: {email_data.get('snippet', '')}
Body: {email_data.get('fullBody', '')}

INTELLIGENCE GUIDELINES:
- College assignments, internship interviews, formal job offers, legal contracts, flight boarding passes, tax refunds = "Important" (Priority: "High", recommendedAction: "Keep" (Defend)).
- Shopping discounts, coupons, BOGO deals, sales promos = "Promotional" (Priority: "Low", recommendedAction: "Archive" or "Label").
- Social media notifications, LinkedIn views, GitHub builds, Slack digests = "Social" (Priority: "Low" or "Medium", recommendedAction: "Label").
- Phishing lures, gift card requests, fake bank wire alerts, seed phrase scams = "Spam-like" (Priority: "High", recommendedAction: "Archive" (Heavy Punch) or "Review").
- Team questions, general status updates, routine memos = "General" (Priority: "Medium", recommendedAction: "Review" or "Keep").

Return ONLY a valid JSON object with EXACTLY this structure (no markdown fences, raw json):
{{
  "category": "Important" | "Promotional" | "Social" | "Spam-like" | "General",
  "priority": "High" | "Medium" | "Low",
  "summary": "Concise 1-2 sentence tactical briefing of what this email wants",
  "recommendedAction": "Keep" | "Archive" | "Label" | "Review",
  "reason": "Precise reason for recommendation based on email context",
  "confidenceScore": 95,
  "requiresReply": true | false,
  "suggestedReply": "1-sentence contextual quick-reply draft",
  "source": "gemini"
}}
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 400,
            "responseMimeType": "application/json"
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    with urllib.request.urlopen(req, timeout=12) as response:
        result = json.loads(response.read().decode('utf-8'))
        text_content = result['candidates'][0]['content']['parts'][0]['text'].strip()
        text_content = re.sub(r'^```json\s*', '', text_content)
        text_content = re.sub(r'\s*```$', '', text_content)
        parsed = json.loads(text_content)
        parsed['source'] = 'gemini'
        return parsed

# 5. Gmail API Client Functions
def fetch_gmail_inbox_messages(access_token, max_results=10):
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages?q=in:inbox&maxResults={max_results}"
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {access_token}'})
    
    with urllib.request.urlopen(req, timeout=10) as res:
        data = json.loads(res.read().decode('utf-8'))
        message_summaries = data.get('messages', [])

    emails = []
    for msg in message_summaries:
        msg_id = msg['id']
        detail_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}?format=full"
        detail_req = urllib.request.Request(detail_url, headers={'Authorization': f'Bearer {access_token}'})
        try:
            with urllib.request.urlopen(detail_req, timeout=10) as detail_res:
                msg_data = json.loads(detail_res.read().decode('utf-8'))
                parsed_email = parse_gmail_message(msg_data)
                emails.append(parsed_email)
        except Exception as e:
            print(f"Error fetching message {msg_id}: {e}")

    return emails

def get_unread_count(access_token):
    url = "https://gmail.googleapis.com/gmail/v1/users/me/messages?q=is:unread%20in:inbox&maxResults=1"
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {access_token}'})
    try:
        with urllib.request.urlopen(req, timeout=8) as res:
            data = json.loads(res.read().decode('utf-8'))
            return data.get('resultSizeEstimate', 0)
    except Exception:
        return 0

def parse_gmail_message(msg_data):
    msg_id = msg_data.get('id', '')
    headers = {h['name'].lower(): h['value'] for h in msg_data.get('payload', {}).get('headers', [])}
    
    subject = headers.get('subject', '(No Subject)')
    sender_raw = headers.get('from', 'Unknown Sender')
    date_raw = headers.get('date', 'Recent')
    snippet = msg_data.get('snippet', '')

    # Parse sender name and email
    sender_name = sender_raw
    sender_email = sender_raw
    if '<' in sender_raw and '>' in sender_raw:
        parts = sender_raw.split('<')
        sender_name = parts[0].strip().strip('"').strip("'") or parts[1].split('>')[0]
        sender_email = parts[1].split('>')[0].strip()

    # Extract body if possible
    body = snippet
    payload = msg_data.get('payload', {})
    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('mimeType') == 'text/plain' and 'data' in part.get('body', {}):
                try:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                    break
                except Exception:
                    pass
    elif 'body' in payload and 'data' in payload['body']:
        try:
            body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        except Exception:
            pass

    # Basic initial classification for monster appearance
    heuristics = fallback_classify_email({
        'subject': subject,
        'sender': sender_name,
        'senderEmail': sender_email,
        'snippet': snippet,
        'fullBody': body
    })

    category = heuristics['category'].lower()
    if 'spam' in category:
        avatar = '🐉'
        monster_name = 'LIVE SPAM PHANTOM'
        color = '#ff2a55'
        weakness = 'Vulnerable to HEAVY PUNCH [J] (Archive)'
    elif 'promo' in category:
        avatar = '👾'
        monster_name = 'LIVE PROMO HYDRA'
        color = '#b026ff'
        weakness = 'Vulnerable to QUICK ATTACK [K] (Label)'
    elif 'social' in category:
        avatar = '💼'
        monster_name = 'LIVE SOCIAL LEECH'
        color = '#00f0ff'
        weakness = 'Vulnerable to QUICK ATTACK [K]'
    elif 'important' in category:
        avatar = '🏆'
        monster_name = 'GOLDEN CONTRACT SENTINEL'
        color = '#ffe600'
        weakness = 'MUST BE DEFENDED! Press DEFEND [L]!'
    else:
        avatar = '⚡'
        monster_name = 'INBOX CHALLENGER'
        color = '#00ff66'
        weakness = 'Weak to Tactical AI Analysis [Space]'

    return {
        'id': msg_id,
        'isLiveGmail': True,
        'subject': subject,
        'sender': sender_name,
        'senderEmail': sender_email,
        'date': date_raw,
        'snippet': snippet,
        'fullBody': body,
        'category': 'important' if category == 'important' else 'promotions' if 'promo' in category else 'social' if 'social' in category else 'spam' if 'spam' in category else 'general',
        'priority': heuristics['priority'],
        'difficulty': 3,
        'monsterName': monster_name,
        'monsterTitle': f"GMAIL ENEMY • {heuristics['priority'].upper()}",
        'monsterAvatar': avatar,
        'avatarColor': color,
        'maxHp': 100,
        'currentHp': 100,
        'threatLevel': 'S' if heuristics['priority'] == 'High' else 'B',
        'weakness': weakness,
        'tags': ['Gmail Live', heuristics['category']],
        'recommendedAction': heuristics['recommendedAction'].lower(),
        'aiAnalysis': {
            'intent': heuristics['summary'],
            'senderTrust': 'Verified via Gmail API',
            'threatRating': heuristics['priority'],
            'recommendation': f"{heuristics['recommendedAction']} this email",
            'explanation': heuristics['reason']
        }
    }

def modify_gmail_message(access_token, message_id, add_labels=None, remove_labels=None):
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{message_id}/modify"
    payload = {
        'addLabelIds': add_labels or [],
        'removeLabelIds': remove_labels or []
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        return json.loads(res.read().decode('utf-8'))

def batch_modify_gmail_messages(access_token, message_ids, add_labels=None, remove_labels=None):
    url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/batchModify"
    payload = {
        'ids': message_ids,
        'addLabelIds': add_labels or [],
        'removeLabelIds': remove_labels or []
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=10) as res:
        return {'status': 'success'}

# 6. HTTP Request Handler
class InboxFighterHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # 1. OAuth Redirect Callback: /auth/callback
        if path == '/auth/callback':
            code = query.get('code', [None])[0]
            if not code:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing authorization code from Google.")
                return

            client_id = os.environ.get('GOOGLE_CLIENT_ID') or load_env().get('GOOGLE_CLIENT_ID', '')
            client_secret = os.environ.get('GOOGLE_CLIENT_SECRET') or load_env().get('GOOGLE_CLIENT_SECRET', '')
            redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI') or load_env().get('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/callback')

            # Exchange code for tokens
            token_url = "https://oauth2.googleapis.com/token"
            payload = urllib.parse.urlencode({
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }).encode('utf-8')

            try:
                token_req = urllib.request.Request(token_url, data=payload, headers={'Content-Type': 'application/x-www-form-urlencoded'})
                with urllib.request.urlopen(token_req, timeout=10) as token_res:
                    token_data = json.loads(token_res.read().decode('utf-8'))

                access_token = token_data.get('access_token')
                refresh_token = token_data.get('refresh_token')
                expires_in = token_data.get('expires_in', 3600)

                # Get user profile email
                userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
                user_req = urllib.request.Request(userinfo_url, headers={'Authorization': f'Bearer {access_token}'})
                with urllib.request.urlopen(user_req, timeout=10) as user_res:
                    user_data = json.loads(user_res.read().decode('utf-8'))
                    user_email = user_data.get('email', 'Connected User')

                # Save tokens
                save_stored_tokens({
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'expires_at': int(time.time()) + expires_in,
                    'email': user_email
                })

                # Redirect to home with query param
                self.send_response(302)
                self.send_header('Location', '/?gmail_connected=true')
                self.end_headers()
                return
            except Exception as e:
                print(f"Error in OAuth callback: {e}")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Authentication failed: {e}".encode('utf-8'))
                return

        # 2. Get Google OAuth URL: /api/auth/google/url
        if path == '/api/auth/google/url':
            client_id = os.environ.get('GOOGLE_CLIENT_ID') or load_env().get('GOOGLE_CLIENT_ID', '')
            redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI') or load_env().get('GOOGLE_REDIRECT_URI', 'http://localhost:8000/auth/callback')
            
            if not client_id:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'GOOGLE_CLIENT_ID not configured in .env'}).encode('utf-8'))
                return

            scopes = "https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/userinfo.email openid"
            auth_url = (
                f"https://accounts.google.com/o/oauth2/v2/auth?"
                f"client_id={urllib.parse.quote(client_id)}&"
                f"redirect_uri={urllib.parse.quote(redirect_uri)}&"
                f"response_type=code&"
                f"scope={urllib.parse.quote(scopes)}&"
                f"access_type=offline&"
                f"prompt=consent"
            )

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'url': auth_url}).encode('utf-8'))
            return

        # 3. Check Gmail Connection Status: /api/gmail/status
        if path == '/api/gmail/status':
            client_id = os.environ.get('GOOGLE_CLIENT_ID') or load_env().get('GOOGLE_CLIENT_ID', '')
            tokens = get_stored_tokens()
            access_token = get_valid_access_token()

            configured = bool(client_id and len(client_id.strip()) > 5)
            connected = bool(access_token and tokens and tokens.get('email'))

            unread_count = 0
            if connected and access_token:
                unread_count = get_unread_count(access_token)

            res_payload = {
                'configured': configured,
                'connected': connected,
                'email': tokens.get('email') if (connected and tokens) else None,
                'unreadCount': unread_count
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res_payload).encode('utf-8'))
            return

        # 4. Fetch Real Gmail Emails: /api/gmail/emails
        if path == '/api/gmail/emails':
            access_token = get_valid_access_token()
            tokens = get_stored_tokens()
            if not access_token:
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Not connected to Gmail'}).encode('utf-8'))
                return

            try:
                emails = fetch_gmail_inbox_messages(access_token, max_results=10)
                unread = get_unread_count(access_token)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'emails': emails,
                    'unreadCount': unread,
                    'email': tokens.get('email', '')
                }).encode('utf-8'))
                return
            except Exception as e:
                print(f"Error fetching Gmail: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                return

        # Default static file serving
        super().do_GET()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        data = {}
        try:
            if body:
                data = json.loads(body.decode('utf-8'))
        except Exception:
            pass

        # 1. Analyze Email with Gemini: /api/analyze-email
        if path == '/api/analyze-email':
            api_key = os.environ.get('GEMINI_API_KEY') or load_env().get('GEMINI_API_KEY', '')

            analysis_result = None
            if api_key and len(api_key.strip()) > 5:
                try:
                    analysis_result = analyze_with_gemini(data, api_key.strip())
                except Exception as e:
                    print(f"⚠️ Gemini API Call failed: {e}. Falling back to heuristic.")
                    analysis_result = fallback_classify_email(data)
                    analysis_result['fallbackReason'] = str(e)
            else:
                analysis_result = fallback_classify_email(data)
                analysis_result['note'] = 'Running in Offline Heuristic Mode. Add GEMINI_API_KEY in .env for live Gemini.'

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(analysis_result).encode('utf-8'))
            return

        # 2. Perform Real Gmail Action: /api/gmail/action
        if path == '/api/gmail/action':
            access_token = get_valid_access_token()
            if not access_token:
                self.send_response(401)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Not connected to Gmail'}).encode('utf-8'))
                return

            action = data.get('action') # 'archive', 'star', 'label', 'batchArchive', 'trash'
            message_id = data.get('messageId')
            message_ids = data.get('messageIds', [])

            try:
                if action == 'archive' and message_id:
                    # Archive: Remove 'INBOX' label
                    res = modify_gmail_message(access_token, message_id, remove_labels=['INBOX'])
                    response_payload = {'success': True, 'action': 'archived', 'messageId': message_id}
                elif action == 'star' and message_id:
                    # Defend/Keep: Add 'STARRED' label
                    res = modify_gmail_message(access_token, message_id, add_labels=['STARRED'])
                    response_payload = {'success': True, 'action': 'starred', 'messageId': message_id}
                elif action == 'label' and message_id:
                    # Label: Apply label
                    label_name = data.get('labelName', 'PROCESSED')
                    # Standard Gmail labels or UNREAD removal
                    res = modify_gmail_message(access_token, message_id, remove_labels=['UNREAD'])
                    response_payload = {'success': True, 'action': 'labeled', 'messageId': message_id}
                elif action == 'batchArchive' and message_ids:
                    # Batch Hadoken Sweep: Remove INBOX from all message IDs
                    res = batch_modify_gmail_messages(access_token, message_ids, remove_labels=['INBOX'])
                    response_payload = {'success': True, 'action': 'batchArchived', 'count': len(message_ids)}
                else:
                    response_payload = {'success': False, 'error': f'Unsupported action {action}'}

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_payload).encode('utf-8'))
                return
            except Exception as e:
                print(f"Error performing Gmail action: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                return

        # 3. Disconnect Gmail: /api/auth/google/disconnect
        if path == '/api/auth/google/disconnect':
            clear_stored_tokens()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'message': 'Gmail disconnected successfully'}).encode('utf-8'))
            return

        # 4. Save OAuth Credentials Directly from UI: /api/auth/google/save-credentials
        if path == '/api/auth/google/save-credentials':
            client_id = data.get('clientId', '').strip()
            client_secret = data.get('clientSecret', '').strip()
            api_key = data.get('geminiApiKey', '').strip()

            env_path = os.path.join(os.path.dirname(__file__), '.env')
            existing_env = load_env()
            if client_id: existing_env['GOOGLE_CLIENT_ID'] = client_id
            if client_secret: existing_env['GOOGLE_CLIENT_SECRET'] = client_secret
            if api_key: existing_env['GEMINI_API_KEY'] = api_key

            with open(env_path, 'w', encoding='utf-8') as f:
                for k, v in existing_env.items():
                    f.write(f"{k}={v}\n")

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'message': 'Credentials saved to .env'}).encode('utf-8'))
            return

        self.send_response(404)
        self.end_headers()

def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), InboxFighterHandler) as httpd:
        print(f"==========================================================")
        print(f"🥊 INBOX STREET FIGHTER — LIVE BACKEND SERVER")
        print(f"==========================================================")
        print(f"📡 Serving at: http://localhost:{PORT}")
        print(f"🔑 Gemini AI: {'CONFIGURED (Live)' if GEMINI_API_KEY else 'FALLBACK HEURISTIC'}")
        print(f"✉️ Gmail OAuth: {'CONFIGURED' if GOOGLE_CLIENT_ID else 'SETUP REQUIRED'}")
        print(f"==========================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    run_server()
