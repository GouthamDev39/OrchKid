from fastapi import FastAPI, HTTPException, Request, Depends
#from schemas import SSHCommandRequest
from logger import logger # ✅ Import centralized logger
from db_stuffs.database import get_db
#from sqlalchemy.orm import Session  
#from fastapi import Depends
#from db_stuffs.models import Job, JobOutput  # Import Job model if needed for database operations
from contextlib import asynccontextmanager
from db_stuffs.database import engine
from db_stuffs.models import Base
from routers import jobs, users, scripts, servers
from scheduler import scheduler_loop
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates#front end
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi_tailwind import tailwind
from pathlib import Path
from schemas import ScheduleJobResponse
from db_stuffs.models import ScheduleJob, User, Job
from db_stuffs.database import get_db
from oauth import get_current_user
from sqlalchemy.orm import Session


# Create the database tables if they don't exist
Base.metadata.create_all(bind=engine)

static_files = StaticFiles(directory="static")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application lifespan")
    process = tailwind.compile(static_files.directory + "/css/styles.css")
    scheduler_task = asyncio.create_task(scheduler_loop())

    try:
        yield
    finally:
        logger.info("Stopping application lifespan")
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            logger.info("Scheduler task cancelled successfully")
    

app = FastAPI(lifespan = lifespan) 

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from the 'static' directory
app.mount("/static", static_files, name="static")

# Setup Jinja2 templates for rendering HTML files
templates = Jinja2Templates(directory="templates")



app.include_router(jobs.router)
app.include_router(users.router)
app.include_router(scripts.router)
app.include_router(servers.router)




@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})



@app.get("/register_ui",response_class=HTMLResponse)
def register_ui():
    return Path("templates/register.html").read_text()


@app.get('/login_ui', response_class=HTMLResponse)
def login_ui():
    return Path("templates/login.html").read_text()


@app.get("/home_ui", response_class=HTMLResponse)
def show_home_page(request: Request):
    return templates.TemplateResponse("scheduled.html", {"request": request})


@app.get("/servers_ui", response_class=HTMLResponse)
def show_servers_page(request: Request):
    return templates.TemplateResponse("servers.html", {"request": request})


@app.get("/scripts_ui", response_class=HTMLResponse)
def show_scripts_page(request: Request):
    return templates.TemplateResponse("scripts.html", {"request": request})

@app.get("/jobs_ui", response_class=HTMLResponse)
def job_page(request: Request):
    return templates.TemplateResponse("jobs.html", {"request": request})


@app.get("/add_server_ui", response_class=HTMLResponse)
def add_server_page(request: Request):
    return templates.TemplateResponse("partials/add_new_server.html", {"request": request})


@app.get("/add_script_ui", response_class=HTMLResponse)
def add_script_page(request: Request):
    return templates.TemplateResponse("partials/upload_scripts.html", {"request": request})


@app.get("/schedule_job_ui", response_class=HTMLResponse)
def schedule_job_page(request: Request):
    return templates.TemplateResponse("partials/schedule_job.html", {"request": request})


@app.get("/script/{id}", response_class=HTMLResponse)
def serve_script_detail_page(request: Request, id: int):
    return templates.TemplateResponse("partials/get_specific_script.html", {"request": request, "script_id": id})


@app.get("/server/{id}", response_class=HTMLResponse)
def server_details(request: Request, id : int):
    return templates.TemplateResponse("partials/get_specific_server.html", {"request": request, "server_id": id})


@app.get("/schedule/{id}", response_class=HTMLResponse)
def schedule_details(request: Request, id : int):
    return templates.TemplateResponse("partials/get_specific_job.html", {"request": request, "job_id": id})


@app.get('/history/{script_id}', response_class=HTMLResponse)
def history_page(request: Request, script_id: int):
    return templates.TemplateResponse("partials/history.html", {"request": request, "script_id": script_id})

@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    return {"status": "healthy"}


