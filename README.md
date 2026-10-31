# 🥊 INBOX STREET FIGHTER
> **"Your Inbox Is The Battlefield."**  
> An AI-powered email triage arcade game built for individual hackathons.

Turn overwhelming email management into a fast-paced retro 90s fighting game. Every unread email becomes a challenger monster with unique stats, threat ratings, and weaknesses. Fight through your queue with arcade moves and summon Gemini AI for genuine contextual email understanding and combat recommendations!

---

## 🤖 Gemini AI Integration Setup

The application features **Google Gemini 1.5 Flash** integration via the secure backend (`server.py` / `server.js`). The API key is stored safely in `.env` and is **never** exposed to client-side code.

### Step 1: Obtain a Free Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Sign in with your Google account.
3. Click **"Create API key"** and copy your key.

### Step 2: Configure Your Key
Open `.env` in the project root and add your key:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
PORT=8000
```

### Step 3: Launch the Game
```bash
./run.sh
```
Or:
```bash
python3 server.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser!

---

## 🛡️ Fallback Mode (Zero Setup Needed)
If no API key is provided, the game automatically switches to **Offline Heuristic Radar Mode**:
- Uses context-aware rule classification for college assignments, internships, contracts, shopping promos, and phishing fraud.
- Clearly displays the `🛡️ HEURISTIC RADAR` indicator in the AI popup.
- The game remains **100% playable** with full sound and animation even without internet or an API key!

---

## ⚡ The 5 Fighting Moves

| Move | Hotkey | Inbox Action | Gameplay Mechanic |
| :--- | :---: | :--- | :--- |
| **HEAVY PUNCH** | `[J]` | Defeat & Archive | 100 DMG, screen shake, fatal KO on spam/general emails. |
| **QUICK ATTACK** | `[K]` | Apply Category Label | Slashes enemy, applies `[PROMO]`, `[SOCIAL]`, or `[DEV]` tag. |
| **DEFEND** | `[L]` | Protect Important | Golden shield! Defending critical emails awards **+1,000 XP**! |
| **AI POWER** | `[Space]` | Gemini Tactical Radar | Real-time AI context analysis, threat score & auto-recommendation. |
| **SPECIAL ATTACK** | `[U]` | Hadoken Sweep | Batch-clean preview of multiple matching emails at once. |

---

## 🧪 Testing the AI Intelligence

Run the automated 10-email intelligence test suite:
```bash
python3 test_ai.py
```
Validates:
1. College Assignment Deadline $\rightarrow$ **Important** (Keep)
2. Internship Interview Invitation $\rightarrow$ **Important** (Keep)
3. Shopping Discount Newsletter $\rightarrow$ **Promotional** (Archive)
4. Social Media Notification $\rightarrow$ **Social** (Label)
5. Phishing & Fake Wire Alert $\rightarrow$ **Spam-like** (Archive)
6. Executed Apartment Lease $\rightarrow$ **Important** (Keep)
7. Food Delivery Coupon $\rightarrow$ **Promotional** (Archive)
8. GitHub CI Build Failure $\rightarrow$ **Social** (Label)
9. CEO Impersonation Gift Card Scam $\rightarrow$ **Spam-like** (Archive)
10. IRS Tax Refund Confirmation $\rightarrow$ **Important** (Keep)
