
Create file:  
`job-automation-agent/docs/DATABASE_SCHEMA.md`

```md
# Job Automation Agent – Database Schema

This document defines the **multi-client relational schema** for the Job Automation Agent.

The schema supports:
- Unlimited clients
- Separate job lists per client
- Tracking application actions
- Status automation via n8n flows
- Eventual cloud deployment (Cloud SQL)

---

# 1. `clients` Table

Stores all user profiles the platform manages.

```sql
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    target_title VARCHAR(150),
    keywords TEXT,         
    locations TEXT,        
    seniority VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW()
);

Purpose

Manage multiple user accounts

Control active/inactive profiles

Store targeting preferences

2. jobs Table

Stores job postings scraped per client.

CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    client_id INT REFERENCES clients(id) ON DELETE CASCADE,
    source VARCHAR(50) NOT NULL,
    title VARCHAR(200),
    company VARCHAR(200),
    location VARCHAR(200),
    job_link TEXT NOT NULL,
    raw_description TEXT,
    match_score INT,
    status VARCHAR(50) DEFAULT 'new',
    applied_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

Purpose

Capture all scraped jobs

Connect each job to a client

Support future auto-apply pipeline

Enable filtering, scoring, deduplication

3. job_applications Table

Tracks the application life cycle for each job.

CREATE TABLE IF NOT EXISTS job_applications (
    id SERIAL PRIMARY KEY,
    job_id INT REFERENCES jobs(id) ON DELETE CASCADE,
    client_id INT REFERENCES clients(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

Status examples:

pending

submitted

queued_for_apply

interview

rejected

offer

4. Indexes

Essential for scaling beyond 10+ clients.

CREATE INDEX IF NOT EXISTS idx_jobs_client_id ON jobs(client_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_match_score ON jobs(match_score);

5. Future Enhancements

Convert keywords/locations → JSONB

Add job “vector embeddings” for AI matching

Add audit logs

Add clients' resume versions
