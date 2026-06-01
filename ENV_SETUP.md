# NextAura Vault — Environment Setup

## What Was Wired

| Component | Status |
|---|---|
| **Django + allauth** | 5 OAuth providers configured |
| **GitHub login** | Priority #1, primary CTA |
| **Apple login** | Priority #2, biometric badge |
| **Google login** | Priority #3, Gmail badge |
| **Outlook/Microsoft** | Priority #4, enterprise badge |
| **Yahoo login** | Priority #5, legacy badge |
| **Supabase** | Custom provider code ready |
| **Magic link email** | Form ready, needs SMTP config |
| **Employee auto-promotion** | `@nextaura.fit` → `is_staff=True` |
| **Internal dashboard** | `/internal/` — staff only |
| **Public dashboard** | `/dashboard/` — any logged-in user |
| **Scan quota API** | `/api/v1/quota/` — 50 free, then paid |
| **Figma fields** | `figma_url` on ScanRun model |
| **Stripe fields** | `stripe_customer_id`, `stripe_subscription_id` on UserProfile |

## What You Need To Do (5 Minutes)

### Step 1: Create OAuth Apps

| Provider | Where | Callback URL |
|---|---|---|
| **GitHub** | https://github.com/settings/developers | `https://app4.nextaura.fit/accounts/github/login/callback/` |
| **Apple** | https://developer.apple.com | Same pattern |
| **Google** | https://console.cloud.google.com/apis/credentials | Same pattern |
| **Microsoft** | https://portal.azure.com > App registrations | Same pattern |
| **Yahoo** | https://developer.yahoo.com/apps | Same pattern |

### Step 2: Fill `.env`

```bash
cp .env.example .env
# Edit .env with your real credentials
```

### Step 3: Test Locally

```bash
$env:DJANGO_SECRET_KEY="dev-key"
$env:GITHUB_CLIENT_ID="your-id"
$env:GITHUB_CLIENT_SECRET="your-secret"
python manage.py runserver
```

Then visit: `http://localhost:8000/accounts/login/`

### Step 4: Deploy to IBM Code Engine

```bash
# Docker build + push (already scripted in Dockerfile)
docker build -t us.icr.io/nextaura/sdv1-django:latest .
ibmcloud cr login
docker push us.icr.io/nextaura/sdv1-django:latest

# Deploy to Code Engine
ibmcloud ce application create --name nextaura-vault \
  --image us.icr.io/nextaura/sdv1-django:latest \
  --env-from-configmap env-config
```

## Architecture

```
Cloudflare (SSL) → Envoy (rate limit) → IBM Code Engine (Django)
                           ↓
                    Background Workers (scan execution)
```

## Employee vs Public

| Path | User | Access |
|---|---|---|
| `/` | Anyone | Landing page |
| `/accounts/login/` | Anyone | OAuth chooser |
| `/dashboard/` | Logged-in | Scan history, quota, trigger scan |
| `/internal/` | Staff only | Operations dashboard |
| `/api/v1/scan/` | Paid users | Trigger scan after quota check |
| `/admin/` | Superuser | Django admin |

## Next Steps

1. **You create OAuth apps** (5 min each)
2. **You test login** on localhost
3. **I wire Stripe checkout** (`$50/scan` after 50 free)
4. **I wire Figma report generation**
5. **I deploy Envoy on IBM Code Engine**
6. **We go live**

Ready when you are. Create one OAuth app (GitHub is easiest) and paste the client ID/secret here.
