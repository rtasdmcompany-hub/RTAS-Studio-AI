# RTAS Studio AI — Aap ko kya download karna hai

Ye list step-by-step hai. Pehle **zaroori**, phir **jab video AI connect karein**.

---

## 1. Zaroori (abhi install karein)

| Software | Kyun | Download |
|----------|------|----------|
| **Node.js 20 LTS** | Web app + tools | https://nodejs.org |
| **Git** | Code version control | https://git-scm.com/download/win |
| **VS Code** ya **Cursor** | Code editor (aap Cursor use kar rahe hain) | Already installed |
| **Android Studio** | Android app build | https://developer.android.com/studio |
| **Xcode** (Mac only) | iOS App Store | Mac App Store |

Install ke baad terminal mein check:

```powershell
node -v    # v20.x
npm -v
git --version
```

---

## 2. Python backend (FastAPI)

| Software | Kyun | Download |
|----------|------|----------|
| **Python 3.11+** | API server | https://www.python.org/downloads/ |

```powershell
cd apps\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Set `NEXT_PUBLIC_FASTAPI_URL=http://localhost:8000` in `apps/web/.env.local`.

## 3. Project dependencies (project folder mein)

```powershell
cd "H:\PERSONAL\RTAS Digital Marketing Company\RTAS Softwear\RTAS Studio AI"
npm install
```

---

## 3. AI video engines (API accounts — algorithms copy nahi, licensed APIs)

Hum competitors jaisa **quality stack** use karte hain — un ka secret code copy nahi hota, un ki **official APIs** integrate hoti hain:

| Provider | Best for | Sign up |
|----------|----------|---------|
| **Runway** | Professional ads, camera control | https://runwayml.com |
| **Kling** | Long clips, motion, character ID | https://klingai.com |
| **Replicate** | Multiple models one API | https://replicate.com |
| **Fal.ai** | Fast image/video | https://fal.ai |

`.env.local` mein keys daalenge (template: `apps/web/.env.example`).

**Real face quality:** Kling Character ID + Runway reference image workflow (docs/ARCHITECTURE.md).

---

## 4. Payments

| Service | Region | Link |
|---------|--------|------|
| **Stripe** | International cards | https://dashboard.stripe.com |
| **JazzCash Merchant** | Pakistan | https://www.jazzcash.com.pk/business |
| **EasyPaisa Merchant** | Pakistan | https://easypaisa.com.pk/business |
| **Payoneer / Wise** | PK bank receive (optional) | Business accounts |

Stripe Product: **$89/month** recurring, metadata: `credits=500`.

---

## 5. Database & auth (production)

| Service | Use |
|---------|-----|
| **Supabase** ya **Firebase** | User profiles, videos metadata, credits |
| **Cloudflare R2** ya **AWS S3** | Video file storage |

Local development: SQLite/JSON mock included in web app.

---

## 6. Mobile store accounts

| Store | Fee | Link |
|-------|-----|------|
| **Google Play Console** | One-time ~$25 | https://play.google.com/console |
| **Apple Developer** | $99/year | https://developer.apple.com |

Mobile app build:

```powershell
cd apps/mobile
npm install
npx expo start
```

---

## 7. Optional (team badhne par)

- **Docker Desktop** — same environment sab machines par  
- **FFmpeg** — server-side video merge/watermark (https://ffmpeg.org)  
- **Postman** — API testing  

---

## Order of work (recommended)

1. Node + Git install → `npm install` → `npm run dev`  
2. Logo `apps/web/public/logo.png`  
3. Stripe test mode + subscription product  
4. Runway/Kling API keys → real generation  
5. Supabase production DB  
6. Expo → Android APK → Play Store  
7. Mac + Xcode → iOS  

Koi step atak jaye to developer ko `docs/ARCHITECTURE.md` dikha dein.
