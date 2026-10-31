/**
 * INBOX STREET FIGHTER — Node.js Backend Server
 * Provides the official /api/analyze-email endpoint using Google Gemini API.
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

// 1. Load .env file
function loadEnv() {
  const envPath = path.join(__dirname, '.env');
  const env = {};
  if (fs.existsSync(envPath)) {
    const lines = fs.readFileSync(envPath, 'utf8').split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
        const [key, ...vals] = trimmed.split('=');
        env[key.trim()] = vals.join('=').trim().replace(/^['"]|['"]$/g, '');
      }
    }
  }
  return env;
}

const envVars = loadEnv();
const GEMINI_API_KEY = process.env.GEMINI_API_KEY || envVars.GEMINI_API_KEY || '';
const PORT = process.env.PORT || envVars.PORT || 8000;

// 2. Fallback Heuristic Classifier
function fallbackClassify(email) {
  const text = `${email.subject || ''} ${email.sender || ''} ${email.senderEmail || ''} ${email.fullBody || email.snippet || ''}`.toLowerCase();

  // Spam signals
  if (['wire transfer', 'seed phrase', 'apple gift card', 'bitcoin', 'btc', 'claim 2.', 'unauthorized login', 'verify full ssn', '.xyz', '.ru'].some(s => text.includes(s))) {
    return {
      category: "Spam-like",
      priority: "High",
      summary: "High-risk suspicious communication exhibiting credential theft or financial fraud.",
      recommendedAction: "Archive",
      reason: "Unsolicited message requesting sensitive actions or urgent payments.",
      confidenceScore: 94,
      requiresReply: false,
      suggestedReply: "Reported as Phishing and deleted.",
      source: "fallback"
    };
  }

  // Important signals
  if (['official offer', 'job offer', 'salary', 'contract', 'docusign', 'lease', 'tax refund', 'irs', 'assignment due', 'deadline', 'boarding pass', 'series a', 'term sheet', 'internship', 'interview'].some(s => text.includes(s))) {
    const requiresReply = ['offer', 'sign', 'confirm', 'review', 'interview', 'schedule'].some(k => text.includes(k));
    return {
      category: "Important",
      priority: "High",
      summary: "Critical time-sensitive message containing official agreements, travel, or academic obligations.",
      recommendedAction: "Keep",
      reason: "High-impact document requiring player attention and preservation.",
      confidenceScore: 96,
      requiresReply,
      suggestedReply: "Thank you! I have reviewed this and will follow up shortly.",
      source: "fallback"
    };
  }

  // Promotional signals
  if (['off everything', 'discount', 'coupon', 'sale', 'promo', 'doordash', 'free shipping', 'black friday', 'cyber monday'].some(s => text.includes(s))) {
    return {
      category: "Promotional",
      priority: "Low",
      summary: "Commercial newsletter offering retail discounts or promotional incentives.",
      recommendedAction: "Archive",
      reason: "Non-urgent commercial marketing. Safe to archive or label as Promo.",
      confidenceScore: 91,
      requiresReply: false,
      suggestedReply: "Saved for future reference.",
      source: "fallback"
    };
  }

  // Social signals
  if (['linkedin', 'profile', 'github', 'build #', 'mentioned you', 'slack', 'calendar'].some(s => text.includes(s))) {
    return {
      category: "Social",
      priority: text.includes('build') || text.includes('calendar') ? "Medium" : "Low",
      summary: "Social platform update, developer notification, or team workspace digest.",
      recommendedAction: "Label",
      reason: "Informational notification from a connected service.",
      confidenceScore: 88,
      requiresReply: false,
      suggestedReply: "Notification acknowledged.",
      source: "fallback"
    };
  }

  return {
    category: "General",
    priority: "Medium",
    summary: "Standard business or personal correspondence.",
    recommendedAction: "Review",
    reason: "Context requires manual review to verify action items.",
    confidenceScore: 75,
    requiresReply: true,
    suggestedReply: "Thanks for reaching out! Reviewing your message now.",
    source: "fallback"
  };
}

// 3. Gemini REST Call
async function callGemini(email, apiKey) {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`;
  const prompt = `
You are the Tactical AI Battle Assistant in the arcade game "INBOX STREET FIGHTER".
Evaluate this email context and return the optimal fighting action:

Subject: ${email.subject || ''}
Sender: ${email.sender || ''} <${email.senderEmail || ''}>
Date: ${email.date || ''}
Snippet: ${email.snippet || ''}
Body: ${email.fullBody || ''}

GUIDELINES:
- College assignments, internship interviews, job offers, contracts, flight tickets = "Important" (Priority: "High", recommendedAction: "Keep").
- Shopping discounts, coupons, sales promos = "Promotional" (Priority: "Low", recommendedAction: "Archive" or "Label").
- Social media notifications, GitHub builds, Slack digests = "Social" (Priority: "Low" or "Medium", recommendedAction: "Label").
- Phishing lures, gift cards, bank wires, seed phrase scams = "Spam-like" (Priority: "High", recommendedAction: "Archive" (Heavy Punch)).
- General memos, updates = "General" (Priority: "Medium", recommendedAction: "Review").

Return ONLY valid JSON:
{
  "category": "Important" | "Promotional" | "Social" | "Spam-like" | "General",
  "priority": "High" | "Medium" | "Low",
  "summary": "1-2 sentence briefing",
  "recommendedAction": "Keep" | "Archive" | "Label" | "Review",
  "reason": "Rationale based on context",
  "confidenceScore": 95,
  "requiresReply": true | false,
  "suggestedReply": "1-sentence reply draft",
  "source": "gemini"
}
`;

  const payload = {
    contents: [{ parts: [{ text: prompt }] }],
    generationConfig: {
      temperature: 0.2,
      maxOutputTokens: 400,
      responseMimeType: "application/json"
    }
  };

  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    throw new Error(`Gemini API returned status ${res.status}`);
  }

  const json = await res.json();
  let text = json.candidates[0].content.parts[0].text.trim();
  text = text.replace(/^```json\s*/, '').replace(/\s*```$/, '');
  const parsed = JSON.parse(text);
  parsed.source = 'gemini';
  return parsed;
}

// 4. HTTP Server
const server = http.createServer(async (req, res) => {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    return res.end();
  }

  if (req.method === 'POST' && req.url === '/api/analyze-email') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', async () => {
      let emailData = {};
      try { emailData = JSON.parse(body); } catch (e) {}

      const apiKey = process.env.GEMINI_API_KEY || loadEnv().GEMINI_API_KEY || '';
      let result = null;

      if (apiKey && apiKey.trim().length > 5) {
        try {
          result = await callGemini(emailData, apiKey.trim());
        } catch (e) {
          console.warn('⚠️ Gemini error:', e.message, 'Using fallback classifier.');
          result = fallbackClassify(emailData);
          result.fallbackReason = e.message;
        }
      } else {
        result = fallbackClassify(emailData);
        result.note = 'Running in Offline Heuristic Mode. Add GEMINI_API_KEY in .env for live Gemini 1.5 Flash.';
      }

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(result));
    });
    return;
  }

  // Static file serving
  let filePath = path.join(__dirname, req.url === '/' ? 'index.html' : req.url);
  fs.readFile(filePath, (err, content) => {
    if (err) {
      res.writeHead(404);
      res.end('Not found');
    } else {
      const ext = path.extname(filePath);
      const mime = ext === '.html' ? 'text/html' : ext === '.js' ? 'text/javascript' : ext === '.css' ? 'text/css' : 'text/plain';
      res.writeHead(200, { 'Content-Type': mime });
      res.end(content);
    }
  });
});

server.listen(PORT, () => {
  console.log(`==========================================================`);
  console.log(`🥊 INBOX STREET FIGHTER — NODE.JS SERVER`);
  console.log(`📡 Serving at http://localhost:${PORT}`);
  console.log(`🤖 Gemini API Status: ${GEMINI_API_KEY ? 'CONFIGURED (Live)' : 'FALLBACK HEURISTIC (Add GEMINI_API_KEY in .env)'}`);
  console.log(`==========================================================`);
});
