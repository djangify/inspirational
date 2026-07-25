# Inspirational Guidance

[![Built with Django](https://img.shields.io/badge/Built%20With-Django%205.2-092E20?style=for-the-badge&logo=django)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS%204-38B2AC?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![HTMX](https://img.shields.io/badge/Frontend-HTMX-3366CC?style=for-the-badge)](https://htmx.org/)
[![PWA](https://img.shields.io/badge/PWA-Installable-5A0FC8?style=for-the-badge)](#progressive-web-app-pwa)
[![License: Custom](https://img.shields.io/badge/License-Custom-important?style=for-the-badge)](#license)

---

Welcome to the GitHub repository for [Inspirational Guidance](https://www.inspirationalguidance.com) — a calm, capable platform that helps women **stop putting their life on hold** and get back to the small, everyday moments that make life feel like theirs.

This Django-powered site brings together a digital shop, AI Mentor guides, journaling prompts, a goal tracker, the ALIVE List builder, a blog, and printable resources — all supporting intentional living for women navigating change, burnout, reinvention, and rediscovery.

> **Core message:** Start with *An ALIVE List* — and begin choosing the things that make ordinary days feel alive.

---

## What This Project Is

Inspirational Guidance is a personal growth platform built to move women from *passive thinkers* to *active choosers* — solving "The Perpetual Tomorrow," where you know what you want but keep pushing it to the bottom of the list.

Take a look at the getting started guide for new members.

[![Getting Started](https://img.shields.io/badge/-Getting_Started_Guide-blue?style=for-the-badge)](https://github.com/djangify/inspirational/blob/main/getting-started-inspirational-guidance.pdf)

---

## Core Features

- ✅ **An ALIVE List** builder — save and revisit the things that make ordinary days feel alive
- ✅ **AI Mentor guides** — purchasable, knowledge-grounded chatbots powered by Anthropic Claude
- ✅ Guided journaling prompts with categories, tags, and writing styles
- ✅ Writing goal tracker with sessions and progress tracking
- ✅ Experiment Weeks, milestone reflections, and goal tools
- ✅ Digital shop with Stripe checkout, coupons, and order bumps
- ✅ Product reviews, wishlists, and secure digital downloads
- ✅ Blog / News with categories, tags, and author profiles (EEAT-ready schema)
- ✅ Member dashboard with resources, order history, and profile management
- ✅ Multi-theme support with per-request theme switching
- ✅ Installable Progressive Web App (PWA) with offline fallback
- ✅ MailerLite email integration and welcome automation

---

## Project Layout

```
inspirational/
├── accounts/        # User profiles, auth, email verification, member resources, support
├── core/            # Homepage, site-wide pages, settings, robots.txt, error handlers
├── shop/            # Products, categories, orders, reviews, coupons, order bumps, Stripe
├── bots/            # AI Mentor guides — bot products, knowledge, access, conversations
├── prompt/          # Journaling prompts, categories, writing styles + writing goal tracker
├── tools/           # An ALIVE List, Experiment Weeks, goals, milestone reflections
├── news/            # Blog posts, categories, tags
├── templates/       # HTML templates (Tailwind + HTMX), including themes/ and pwa/
├── static/          # Source CSS/JS/images
├── staticfiles/     # Collected static assets (WhiteNoise)
├── media/           # User/admin uploads (products, news, resources, secure downloads)
├── inspirational/   # Project settings, URLs, theme loader/middleware, sitemaps, storage
└── manage.py
```

---

## Tech Stack

| Tech | Purpose |
|------|---------|
| **Django 5.2** | Backend framework powering the platform |
| **SQLite** | Default database (`db.sqlite3`) for users, prompts, goals, orders, bots |
| **Django REST Framework** | API for dynamic frontend features |
| **django-filter** | Filtering for prompts and listings |
| **Tailwind CSS 4** | Frontend styling for a clean, minimalist UI |
| **HTMX** | Dynamic frontend interactions without a heavy JS framework |
| **Stripe** | Checkout and payment processing |
| **Anthropic Claude** | Powers the AI Mentor guide chatbots |
| **TinyMCE** | Rich-text editing in the admin |
| **ReportLab / pypdf** | PDF generation and processing |
| **Adminita** | Enhanced Django admin dashboard |
| **WhiteNoise** | Static file serving in production |
| **MailerLite** | Email list management and welcome automation |
| **Self-hosted VPS** | Ubuntu-based deployment (Gunicorn + Nginx) |

Supporting libraries: `django-environ` (environment management), `django-tinymce`, `django-storages`, `django-widget-tweaks`, `django-cors-headers`, `Pillow`, `beautifulsoup4`, `cryptography`.

---

## Features Overview

### An ALIVE List
The signature feature. Members build and save their ALIVE List — the small, everyday moments worth choosing — directly from their dashboard.

### AI Mentor Guides
Purchasable chatbots (the `bots` app) backed by a shop product. Each bot has its own name, welcome message, system prompt, knowledge base, message limit, and time-bound access. Bundles grant higher message limits and longer access. Conversations are stored per member, with PDF download support.

### Digital Shop
A full storefront with categories, product images, reviews, guest checkout, Stripe payments, coupons, order bumps, download logging, and configurable shop/site settings. Members can build wishlists and access secure downloads.

### Journaling Prompts & Writing Tracker
Guided prompts organised by category, tag, and writing style, plus a writing goal tracker that records writing sessions and progress.

### Goal & Reflection Tools
Experiment Weeks, experiment goals, and milestone reflections help members set intentional goals built for emotional resilience — not just performance.

### Blog / News
Articles with categories, tags, and author profiles, structured with EEAT markers and schema following the May 2026 core update.

### Member Dashboard
A central hub to access purchased and free resources, save prompts, manage wishlists, track goals, review order history, and update profile settings.

### Theming
A custom template loader and middleware (`theme_loader.py` / `theme_middleware.py`) resolve an active theme per request, checking `templates/themes/<theme>/` before falling back to the global templates. Theme selection is thread-safe.

### Progressive Web App (PWA)
The site is installable, serving a web manifest and service worker from the site root with an offline fallback page (`templates/pwa/`).

---

## Getting Started (Local Development)

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install frontend dependencies and build CSS
npm install
npm run build                   # or: npm run dev  (watch mode)

# 4. Configure environment variables
#    Create a .env file (Stripe keys, Anthropic key, MailerLite, secret key, etc.)

# 5. Apply migrations and create an admin user
python manage.py migrate
python manage.py createsuperuser

# 6. Run the development server
python manage.py runserver
```

Tailwind build scripts are defined in `package.json`:
`npm run build` (minified) and `npm run dev` (watch).

---

## Deployment

Deployed to a self-hosted VPS running Ubuntu, using:

- **Gunicorn** as the application server
- **Nginx** as the reverse proxy
- **WhiteNoise** for compressed, manifest-based static file serving
- **Certbot / Let's Encrypt** for SSL certificates

---

## Contributor Notes

This project was created and is actively maintained by **Diane Corriette**, a full-stack developer focused on building calm, purposeful tools for personal growth.

Maintained by [Diane Corriette](https://github.com/todiane).

---

## License

This project is **closed-source for commercial use**.

---

## Acknowledgements

- Built with Django
- Styling inspired by the minimalism and clarity of Tailwind CSS
- AI Mentor guides powered by Anthropic Claude
- Hosted on a self-hosted VPS for full control and security

---

[https://www.inspirationalguidance.com](https://www.inspirationalguidance.com)
