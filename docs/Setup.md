# Job Automation Agent – Setup Guide

This project is a **multi-client job automation platform** designed to:
- Scrape job boards (Dice, Indeed, LinkedIn…)
- Store jobs in a database
- Trigger AI-based auto-apply agents
- Track application status
- Scale to multiple clients
- Deploy easily to cloud environments

This file documents the full environment setup used for local development.

---

## 1. System Requirements

### Hardware
- Windows Laptop (primary development machine)
- Optional: macOS machine (temporary, helper only)

### Software
- Docker Desktop (Windows)
- Git
- DBeaver (Database GUI)
- Chrome / Edge browser
- Node & Python (added later for backend)

---

## 2. Project Structure
job-automation-agent/
    backend/ # FastAPI backend (created later)
    n8n/ # n8n workflow config & env
    db/ # Database volume
    docs/ # Documentation
    docker-compose.yml # Local & cloud-ready stack


---

## 3. Docker Setup

We use Docker Compose to manage:
- PostgreSQL
- n8n
- Backend API ( later )

### Start services:

```bash
docker-compose up -d


