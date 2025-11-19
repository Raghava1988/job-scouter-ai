from typing import List, Optional
from pydantic import BaseModel
from fastapi import Body

# --- Clients ---

class Client(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    is_active: bool

class ClientCreate(BaseModel):
    name: str
    email: Optional[str] = None


# --- Search Profiles ---

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


# --- Jobs ingest model ---

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



@app.post("/internal/jobs/ingest")
def ingest_jobs(jobs: List[JobIngest] = Body(...)):
    if not jobs:
        return {"inserted": 0, "updated": 0}

    inserted = 0
    updated = 0

    with get_conn() as conn, conn.cursor() as cur:
        for job in jobs:
            cur.execute(
                """
                INSERT INTO jobs (
                    client_id, profile_id, source, external_id,
                    title, company, location, job_link,
                    raw_description, match_score
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (client_id, source, job_link)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    company = EXCLUDED.company,
                    location = EXCLUDED.location,
                    raw_description = EXCLUDED.raw_description,
                    match_score = EXCLUDED.match_score;
                """,
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
                ),
            )
            # Insert vs update detection is optional; we can just return total.
            inserted += 1  # or smarter rowcount logic if you want

    return {"inserted": inserted, "updated": updated}


class JobOut(BaseModel):
    id: int
    client_id: int
    profile_id: int
    source: str
    title: str
    company: str | None = None
    location: str | None = None
    job_link: str
    scraped_at: str

@app.get("/clients/{client_id}/jobs", response_model=List[JobOut])
def list_jobs_for_client(client_id: int, limit: int = 50):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, client_id, profile_id, source, title, company, location,
                   job_link, scraped_at
            FROM jobs
            WHERE client_id = %s
            ORDER BY scraped_at DESC
            LIMIT %s;
            """,
            (client_id, limit),
        )
        return cur.fetchall()


