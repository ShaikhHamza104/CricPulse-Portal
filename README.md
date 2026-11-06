# 🏏 CricPulse-Portal — Developer Platform & Analytics Showcase

> **The production-grade Django developer portal and control plane for the [CricPulse-Engine](https://cricpulse-engine.onrender.com) analytical API. Featuring real user authentication, cryptographic API key issuance, an enterprise admin console, and an interactive cricket analytics hub.**
>
> ⚙️ **Backend Analytical Engine:** [https://cricpulse-engine.onrender.com](https://cricpulse-engine.onrender.com) | 📚 **Engine Swagger Docs:** [https://cricpulse-engine.onrender.com/docs](https://cricpulse-engine.onrender.com/docs)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2+-092e20.svg?logo=django&logoColor=white)](https://djangoproject.com)
[![Tests](https://img.shields.io/badge/Tests-15%20Passed-brightgreen.svg?logo=pytest&logoColor=white)](tests/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-CDN-38bdf8.svg?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![Package Manager](https://img.shields.io/badge/uv-Fast%20Packaging-DE5FE9.svg)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🌟 System Architecture: Decoupled 2-Tier Design

CricPulse implements the industry-standard **Separation of Concerns (Control Plane vs. Data Plane)** to maximize performance and prevent memory exhaustion under 512MB RAM cloud tiers:

```
                          [ BROWSER / DEVELOPER ]
                                     │
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │            SERVICE 1: CRICPULSE-PORTAL (Django)        │
        │                  "The Control Plane"                   │
        │  ├── Real User Auth (Signup, Login, Sessions, CSRF)    │
        │  ├── Cryptographic API Key Management (cric_live_...)  │
        │  ├── Django Admin Operations Console (/admin)          │
        │  ├── Interactive API Playground & Docs                 │
        │  └── Responsive Tailwind UI (Light Theme)              │
        └────────────────────────────┬───────────────────────────┘
                                     │
                                     │ (Validates Keys & Fetches Data)
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │            SERVICE 2: CRICPULSE-ENGINE (FastAPI)       │
        │                    "The Data Plane"                    │
        │  ├── DuckDB Columnar OLAP Analytics Engine             │
        │  ├── 1,243 Matches & 295,732 Ball Deliveries           │
        │  ├── Sub-30ms Aggregations (Parquet Medallion)         │
        │  └── Sliding-Window Memory-Safe Rate Limiter           │
        └────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Portal Features

### 1. 🔐 Real User Authentication & Security
* **Production Auth:** Complete registration, login, logout, and profile flows built on `django.contrib.auth`.
* **Cryptographic Password Hashing:** PBKDF2/SHA-256 algorithm with strict length and similarity validators.
* **Session Security:** HTTP-only cookies, CSRF protection on every form submission, and clickjacking protection (`X-Frame-Options: SAMEORIGIN`).
* **Route Protection:** `@login_required` decorators guarding developer dashboards and key endpoints.

### 2. 🔑 Cryptographic API Key Management
* **Instant Provisioning:** An initial 24-byte hex token (`cric_live_...`) is generated automatically via Django signals when a developer signs up.
* **Masked Security:** Keys are displayed safely in tables as `cric_live_••••••••••••3a7b` with one-click **Reveal** and **Copy to Clipboard**.
* **Lifecycle Management:** Developers can generate multiple scoped keys (e.g., *Production*, *Staging*, *Mobile App*) and permanently revoke keys with immediate invalidation.

### 3. ⚡ Operations Admin Console (`/admin`)
* **Role-Based Access:** Protected by Django superuser privileges.
* **Key Oversight:** Color-coded badges for active vs. revoked keys and subscription tiers (*Free*, *Pro*, *Enterprise*).
* **Bulk Admin Actions:** One-click administrative revocation and re-activation of developer keys with automated audit messaging.

### 4. 🏏 Interactive Cricket Showcase Hub
* **Rivalry Arena:** Select any two IPL franchises (e.g., `CSK` vs. `MI` or `RCB` vs. `KKR`) to see historical win percentages, head-to-head records, and clash counts.
* **Cap Leaderboards:** Season selector (2008–2024) rendering Orange Cap (top run-scorers) and Purple Cap (top wicket-takers) with domain rule compliance.
* **Player Career Scout:** Real-time search for cricketers (Kohli, Bumrah, Dhoni) with career batting strike rates and bowling economies.

### 5. 🛠️ Live Developer Playground
* Built-in interactive API runner: select any endpoint, execute requests live, view latency badges, and inspect formatted JSON payloads directly in the browser.

---

## 🧪 Automated Testing Suite (15 / 15 Passed)

The repository features comprehensive automated tests running on `pytest` and `pytest-django`:

```bash
# Run all tests using uv
uv run pytest
```

Test coverage includes:
- **`tests/test_auth.py`** — Registration, automatic key provisioning signal, duplicate email rejection, login/logout sessions, profile updates.
- **`tests/test_api_keys.py`** — Key token generation, masking rules, creating secondary keys, revocation flows, unauthenticated redirects.
- **`tests/test_views.py`** — Landing page rendering, documentation tables, showcase tabs (Rivalry, Caps, Player Scout), live query proxy.
- **`tests/test_admin.py`** — Admin site registration, preview helpers, bulk revocation/activation actions.

---

## 🛠️ Quickstart (Local Development)

### 1. Prerequisites
Install `uv` (recommended) or standard Python 3.11+:
```bash
# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex
```

### 2. Clone & Sync Dependencies
```bash
git clone https://github.com/ShaikhHamza104/CricPulse-Portal.git
cd CricPulse-Portal

# Install all dependencies into virtual environment
uv sync
```

### 3. Apply Database Migrations
```bash
uv run python manage.py migrate
```

### 4. Create Your Admin Superuser
```bash
uv run python manage.py createsuperuser
# Enter your desired username, email, and password
```

### 5. Run the Local Server
```bash
uv run python manage.py runserver
```
Visit:
* 🌐 **Web Portal:** `http://127.0.0.1:8000/`
* 🔑 **Developer Dashboard:** `http://127.0.0.1:8000/dashboard/`
* ⚡ **Django Admin Console:** `http://127.0.0.1:8000/admin/`

---

## ☁️ Deploying to Render

A turnkey `render.yaml` blueprint is included:

1. Push this repository to GitHub.
2. In the Render Dashboard, click **New + ➔ Blueprint**.
3. Select your `CricPulse-Portal` repository.
4. Render automatically configures:
   * Build command: `uv sync && uv run python manage.py collectstatic --noinput && uv run python manage.py migrate`
   * Start command: `uv run gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4`
   * Production static file compression with **WhiteNoise**.

---

## 👨‍💻 Author & Credits

**Mohd Hamza Shaikh**
* GitHub: [@ShaikhHamza104](https://github.com/ShaikhHamza104)
* Project Ecosystem: **CricPulse-Engine (FastAPI + DuckDB)** &amp; **CricPulse-Portal (Django)**
* Cricket Data: Sourced under ODbL license from [Cricsheet](https://cricsheet.org/).
