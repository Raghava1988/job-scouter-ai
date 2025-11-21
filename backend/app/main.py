from typing import List, Optional, Union
from datetime import datetime

from fastapi import FastAPI, Body
from pydantic import BaseModel

from fastapi import UploadFile, File, HTTPException
import io
import re
from .scorer import extract_text_from_pdf, calculate_match_score

from .db import get_conn

app = FastAPI(title="Job Scraper API")


# -------------------- Clients --------------------

class Client(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    is_active: bool


class ClientCreate(BaseModel):
    name: str
    email: Optional[str] = None


# -------------------- Search Profiles --------------------

class SearchProfile(BaseModel):
    id: int
    client_id: int
    name: str
    platforms: List[str]
    keywords: List[str]
    locations: List[str]
    is_active: bool


class SearchProfileCreate(BaseModel):
    name: str
    platforms: List[str]
    keywords: List[str]
    locations: List[str]


# -------------------- Job Ingest --------------------

class JobIngest(BaseModel):
    client_id: int
    profile_id: int
    source: str
    external_id: Optional[str] = None
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    job_link: str
    raw_description: Optional[str] = None
    match_score: Optional[int] = None


# -------------------- Jobs Out --------------------

class JobOut(BaseModel):
    id: int
    client_id: int
    profile_id: int
    source: str
    external_id: Optional[str] = None
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    job_link: str
    scraped_at: datetime


class PendingJob(BaseModel):
    id: int
    client_id: int
    profile_id: int
    source: str
    external_id: Optional[str] = None
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    job_link: str
    raw_description: Optional[str] = None
    match_score: Optional[int] = None  # from scraper / later LLM

    # PHASE 2 – queue fields
    queue_score: int                   # our computed ranking score (0+)
    is_senior: bool
    is_recruiter: bool
    matched_keywords: List[str] = []   # which profile keywords hit



# -------------------- Job Application Results --------------------

class JobApplicationResult(BaseModel):
    job_id: int
    client_id: int
    provider: str       # 'dice', 'indeed', 'linkedin', etc.
    status: str         # 'PENDING', 'APPLIED', 'FAILED', 'SKIPPED'
    application_url: Optional[str] = None
    error_message: Optional[str] = None
    applied_at: Optional[datetime] = None


# ============================================================
#  CLIENT ENDPOINTS
# ============================================================

@app.get("/clients", response_model=List[Client])
def list_clients():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, email, is_active FROM clients ORDER BY id;"
        )
        return cur.fetchall()


@app.post("/clients", response_model=Client)
def create_client(payload: ClientCreate):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO clients (name, email)
            VALUES (%s, %s)
            RETURNING id, name, email, is_active;
            """,
            (payload.name, payload.email),
        )
        return cur.fetchone()


# ============================================================
#  SEARCH PROFILE ENDPOINTS
# ============================================================

@app.get("/clients/{client_id}/profiles", response_model=List[SearchProfile])
def list_profiles(client_id: int):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, client_id, name, platforms, keywords, locations, is_active
            FROM client_search_profiles
            WHERE client_id = %s
            ORDER BY id;
            """,
            (client_id,),
        )
        return cur.fetchall()


@app.post("/clients/{client_id}/profiles", response_model=SearchProfile)
def create_profile(client_id: int, payload: SearchProfileCreate):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO client_search_profiles
                (client_id, name, platforms, keywords, locations)
            VALUES
                (%s, %s, %s, %s, %s)
            RETURNING id, client_id, name, platforms, keywords, locations, is_active;
            """,
            (
                client_id,
                payload.name,
                payload.platforms,
                payload.keywords,
                payload.locations,
            ),
        )
        return cur.fetchone()


# ============================================================
#  INTERNAL: PROFILES TO RUN (for n8n)
# ============================================================

@app.get("/internal/search-profiles-to-run", response_model=List[SearchProfile])
def get_profiles_to_run():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, client_id, name, platforms, keywords, locations, is_active
            FROM client_search_profiles
            WHERE is_active = TRUE
            ORDER BY id;
            """
        )
        return cur.fetchall()


# ============================================================
#  INTERNAL: JOB INGESTION (1 or many)
# ============================================================

@app.post("/internal/jobs/ingest")
def ingest_jobs(
    jobs: Union[JobIngest, List[JobIngest]] = Body(...),
):
    """
    Ingest one or many jobs.

    - If the body is a single object: { ... }  -> wrap in a list.
    - If the body is a list: [ {...}, {...} ] -> use directly.
    """
    if isinstance(jobs, JobIngest):
        jobs_list: List[JobIngest] = [jobs]
    else:
        jobs_list = jobs

    if not jobs_list:
        return {"total_processed": 0}

    job_values = [
        (
            job.client_id,
            job.profile_id,
            job.source,
            job.external_id,
            job.title,
            job.company,
            job.location,
            job.job_link,
            job.raw_description,
            job.match_score,
        )
        for job in jobs_list
    ]

    sql_query = """
    INSERT INTO jobs (
        client_id, profile_id, source, external_id,
        title, company, location, job_link,
        raw_description, match_score
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (client_id, source, job_link)
    DO UPDATE SET
        profile_id = EXCLUDED.profile_id,
        external_id = EXCLUDED.external_id,
        title = EXCLUDED.title,
        company = EXCLUDED.company,
        location = EXCLUDED.location,
        raw_description = EXCLUDED.raw_description,
        match_score = EXCLUDED.match_score;
    """

    with get_conn() as conn, conn.cursor() as cur:
        cur.executemany(sql_query, job_values)
        total_processed = cur.rowcount

    return {"total_processed": total_processed}


# ============================================================
#  INTERNAL: GET PENDING JOBS FOR AUTO-APPLY
# ============================================================

@app.get("/internal/jobs/pending", response_model=List[PendingJob])
def get_pending_jobs(client_id: int, limit: int = 20):
    """
    Return jobs for a client that do NOT yet have a job_applications record.

    These are the jobs n8n should try to auto-apply for.
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                j.id,
                j.client_id,
                j.profile_id,
                j.source,
                j.external_id,
                j.title,
                j.company,
                j.location,
                j.job_link,
                j.raw_description,
                j.match_score
            FROM jobs j
            LEFT JOIN job_applications a
                ON a.job_id = j.id
               AND a.client_id = j.client_id
               AND a.status IN ('APPLIED', 'SKIPPED')
            WHERE j.client_id = %s
              AND a.id IS NULL
            ORDER BY j.scraped_at DESC
            LIMIT %s;
            """,
            (client_id, limit),
        )
        return cur.fetchall()


# ============================================================
#  INTERNAL: SAVE JOB APPLICATION RESULTS
# ============================================================

@app.post("/internal/jobs/applications/result")
def save_application_results(
    results: Union[JobApplicationResult, List[JobApplicationResult]] = Body(...),
):
    """
    Save one or many job application results coming back from n8n.

    Each result upserts into job_applications on (job_id, client_id).
    """
    if isinstance(results, JobApplicationResult):
        res_list: List[JobApplicationResult] = [results]
    else:
        res_list = results

    if not res_list:
        return {"total_processed": 0}

    values = []
    for r in res_list:
        applied_at = r.applied_at or datetime.utcnow()
        values.append(
            (
                r.job_id,
                r.client_id,
                r.provider,
                r.status,
                r.application_url,
                r.error_message,
                applied_at,
            )
        )

    sql = """
    INSERT INTO job_applications (
        job_id,
        client_id,
        provider,
        status,
        application_url,
        error_message,
        applied_at
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (job_id, client_id)
    DO UPDATE SET
        provider = EXCLUDED.provider,
        status = EXCLUDED.status,
        application_url = EXCLUDED.application_url,
        error_message = EXCLUDED.error_message,
        applied_at = EXCLUDED.applied_at;
    """

    with get_conn() as conn, conn.cursor() as cur:
        cur.executemany(sql, values)
        total_processed = cur.rowcount

    return {"total_processed": total_processed}


# ============================================================
#  LIST JOBS FOR A CLIENT (for debugging / UI)
# ============================================================

@app.get("/clients/{client_id}/jobs", response_model=List[JobOut])
def list_jobs_for_client(client_id: int, limit: int = 50):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, client_id, profile_id, source, external_id, title,
                   company, location, job_link, scraped_at
            FROM jobs
            WHERE client_id = %s
            ORDER BY scraped_at DESC
            LIMIT %s;
            """,
            (client_id, limit),
        )
        return cur.fetchall()
@app.post("/clients/{client_id}/resume")
async def upload_resume(client_id: int, file: UploadFile = File(...)):
    """
    Upload a PDF resume, extract text, and save it to the client record.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # 1. Read file
    file_content = await file.read()
    file_stream = io.BytesIO(file_content)
    
    # 2. Extract text
    text = extract_text_from_pdf(file_stream)
    
    if not text:
        raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
    # 3. Save to DB
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE clients SET resume_text = %s WHERE id = %s",
            (text, client_id)
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Client not found")
            
    return {"message": "Resume uploaded and text extracted successfully", "length": len(text)}


# ============================================================
#  SCORING ENDPOINT (Trigger this from n8n or UI)
# ============================================================

@app.post("/internal/jobs/score")
def score_unscored_jobs(client_id: int, limit: int = 50):
    """
    Finds jobs with no score, compares them to the client's resume, and updates the score.
    """
    scored_count = 0
    with get_conn() as conn, conn.cursor() as cur:
        # 1. Get Client Resume
        cur.execute("SELECT resume_text FROM clients WHERE id = %s", (client_id,))
        res = cur.fetchone()
        if not res or not res[0]:
            raise HTTPException(status_code=400, detail="Client has no resume uploaded")
        
        resume_text = res[0]
        
        # 2. Get Unscored Jobs
        cur.execute(
            """
            SELECT id, raw_description 
            FROM jobs 
            WHERE client_id = %s AND match_score IS NULL AND raw_description IS NOT NULL
            LIMIT %s
            """,
            (client_id, limit)
        )
        jobs_to_score = cur.fetchall()
        
        scored_count = 0
        
        # 3. Loop and Score
        for job_id, job_desc in jobs_to_score:
            score = calculate_match_score(resume_text, job_desc)
            
            # Update Job
            cur.execute(
                "UPDATE jobs SET match_score = %s WHERE id = %s",
                (score, job_id)
            )
            scored_count += 1
        conn.commit()
            
    return {"processed": scored_count}