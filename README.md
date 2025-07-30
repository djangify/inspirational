# ✨ Inspirational Guidance

[![Built with Django](https://img.shields.io/badge/Built%20With-Django-092E20?style=for-the-badge&logo=django)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Hosted on VPS](https://img.shields.io/badge/Hosting-VPS%20Self--Hosted-blue?style=for-the-badge)](https://www.hetzner.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: Custom](https://img.shields.io/badge/License-Custom-important?style=for-the-badge)](#)

---

Welcome to the GitHub repository for [Inspirational Guidance](https://www.inspirationalguidance.com) — a calm and capable platform designed to help women **live with purpose**.

This Django-powered site offers journal prompts, calming tools, goal tracker and printable resources — all supporting intentional living for women navigating change, burnout, reinvention, and rediscovery.

---

## 🧭 What This Project Is

Inspirational Guidance is a personal growth platform with a soul. It was created to support quiet, thoughtful women who want to return to a life that feels meaningful — one decision, one prompt, one purpose-led moment at a time.

### 🎯 Core Features

- ✅ Guided journal prompts
- ✅ Personalised goal tracker
- ✅ Wishlists and product access for members
- ✅ Printable journals and digital downloads
- ✅ Interactive calming tools
- ✅ Email signup and order history
- 🛒 Stripe-based checkout and dashboard delivery

---

## 🛠 Tech Stack

| Tech | Purpose |
|------|---------|
| **Django 5.2** | Main backend framework |
| **PostgreSQL** | Database (relational) |
| **Django REST Framework (DRF)** | API endpoints for dynamic content |
| **Tailwind CSS** | Utility-first front-end styling |
| **HTMX** | Interactive UX without full JS frameworks |
| **Stripe** | Secure checkout + webhook-based order updates |
| **Hetzner VPS** | Self-hosted, Ubuntu-based Linux server |

---

## 📦 Project Layout
```
inspirational/
├── accounts/ # User profiles, login, dashboard
├── prompts/ # Affirmations, journaling prompts & filters
├── shop/ # Digital product management & Stripe checkout
├── tracker/ # Goal tracking models & views
├── tools/ # Calming circle & bubble pop tools
├── templates/ # HTML templates with Tailwind
├── static/ # CSS, images, JS
├── config/ # Project settings and URLs
└── manage.py
```

---

## 🛠 Tech Stack

This project is built with:

| Tech | Purpose |
|------|---------|
| **Django 5.2** | Backend framework powering the platform |
| **PostgreSQL** | Database for storing users, prompts, goals, orders |
| **Django REST Framework (DRF)** | API for dynamic frontend features and prompt generation |
| **Tailwind CSS** | Frontend styling framework for clean, minimalist UI |
| **HTMX** | For dynamic front-end interactions without React |
| **Stripe** | Handles checkout and payment processing |
| **Self-hosted VPS (Hetzner)** | Ubuntu-based deployment environment |

Optional tools used in development:
- `django-allauth` for authentication and email verification
- `django-cleanup` for file management
- `python-decouple` for environment management

---

## 📦 Features Overview

### 🔐 Member Dashboard
- Access purchased/free resources
- Save journal prompts
- Add products to a wishlist
- Track goals & update progress
- Access calming tools and profile management

### 📘 Free Resource Library
Includes printable journals, checklists, quote cards, and audio-guided reflection tools. The library is regularly updated and is available to all signed-up members.

### 🎯 Goal Tracker
A self-directed tool to set and track intentional goals. Built for emotional resilience — not just performance.

### 🎧 Voice Tools (planned feature)
A future update will allow members to record and play back affirmations in their own voice.

---

🌐 Deployment
This project is deployed to a self-hosted VPS running Ubuntu, using:

Gunicorn as the application server

Nginx as the reverse proxy

PostgreSQL installed and managed via systemd

Certbot/Let’s Encrypt for SSL certificates


🙋‍♀️ Contributor Notes
This project was created and is actively maintained by Diane Corriette, a full-stack developer and writer focused on building calm, purposeful tools for personal growth. She has the help of AI Assistant Diana Morgan.

```

✨ License
This project is closed-source for commercial use. Code contributions are welcome but will be governed by internal license terms for derivative and AI-assisted work. Contact us for collaboration opportunities.
```
---

🤝 Acknowledgements
Built with ❤️ using Django

Styling inspired by the minimalism and clarity of Tailwind CSS

Hosted on Hetzner for full control and security

Developed in alignment with the philosophy of “coming home to yourself”


