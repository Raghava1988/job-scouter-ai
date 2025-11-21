# job-scouter-ai

AI-assisted **job scouting and scoring** platform for multiple clients.  
It pulls jobs from boards like Dice (and others later), stores them in Postgres, scores them against a client’s resume, and prepares a clean review queue.

> 🧠 Goal: act like a “mini job search agency” — you upload resumes, define search profiles, let the system scout jobs, and you just review & apply.

---

## ✨ Features (Phase 2)

- **Multi-client support**
  - Each client has their own resume and search profiles (keywords, locations, platforms).
- **Job ingestion pipeline**
  - n8n workflows + Apify/custom scrapers (currently Dice) push normalized jobs into Postgres via the backend.
- **Resume-based scoring**
  - Backend `scorer.py` compares each job description with the client’s resume and assigns a `match_score`.
- **Application queue**
  - Backend exposes `/internal` endpoints to:
    - list **pending** jobs for a client/profile
    - store application results (APPLIED / SKIPPED / FAILED)
- **Dockerized local setup**
  - One `docker-compose.yml` to spin up backend API, Postgres DB, and n8n workflow engine.

> 🔜 Coming later: simple frontend to review jobs in a table, upload resume, and mark jobs as applied/skipped.

---

## 🏗 Architecture

**Core components:**

- **Backend** – FastAPI  
  - Multi-tenant aware (clients + search profiles)
  - REST endpoints for:
    - ingesting jobs
    - scoring jobs
    - fetching pending jobs (queue)
    - saving application results
- **Database** – Postgres  
  - Tables for `clients`, `client_search_profiles`, `jobs`, `job_applications`, etc.
- **Orchestration** – n8n  
  - Scheduled or on-demand workflows
  - Calls scrapers (e.g., Dice via Apify)
  - Posts jobs to the backend
  - Triggers scoring endpoints

High-level flow:

1. n8n workflow runs for a given client/profile.
2. Scraper (e.g., Dice actor) returns raw job listings.
3. n8n normalizes them and calls `POST /internal/jobs/ingest`.
4. Backend stores jobs in Postgres.
5. Backend scoring endpoint compares resume vs job descriptions and updates `match_score`.
6. UI (later) or API consumer calls `/internal/jobs/pending` to get a **ranked queue** of jobs to review and apply manually.

---

## 📁 Repository Structure

```text
job-scouter-ai/
  backend/        # FastAPI app (API, models, scorer, internal endpoints)
  db/
    data/        # SQL init scripts / seed data for Postgres
  n8n/
    data/        # n8n workflows & configuration
  docs/          # Architecture notes, diagrams, planning docs
  docker-compose.yml
  README.md
