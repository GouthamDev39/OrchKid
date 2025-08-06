from fastapi import FastAPI, HTTPException, APIRouter, Depends
from schemas import SSHCommandRequest, JobResponse
from sqlalchemy.orm import Session  
from db_stuffs.database import get_db
from db_stuffs.models import Job, JobOutput, Server  # Import Job model if needed for database operations
from db_stuffs.database import engine
from db_stuffs.models import Base
from ssh_utils import run_ssh_command
from logger import logger  # ✅ Import centralized logger
from oauth import get_current_user
from db_stuffs import models
from typing import List 



router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"]
)

ALLOWED_COMMANDS = ['uptime','hostname','df -h','free -m','whoami']  


@router.post("/run")
async def run_ssh_command_endpoint(req: SSHCommandRequest, db : Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    logger.info("Service opened by : " + current_user.runner)
    #logger.info("Authenticated user: " + )
    logger.info("Database session started")

    server_exits = db.query(Server).filter(Server.id == req.server_id).first()
    
    if not server_exits:
        logger.error(f"Server ID {req.server_id} not found")
        raise HTTPException(status_code=404, detail="Server ID not found")


    # if not job_info:
    #     logger.error(f"Job ID {req.server_id} not found")
    #     raise HTTPException(status_code=404, detail="Job ID not found")

    if current_user.is_superuser:
        logger.info("User is superuser, granting access to all commands.")

    
    else:
        logger.warning("User is not superuser, checking command permissions.")
        if req.command not in ALLOWED_COMMANDS:
            logger.error(f"The command {req.command} is in blacklist and cannot be executed.")
            err = "Blacklisted Command" 


            
            job = Job(
                command=req.command,
                hostname=server_exits.hostname,
                key_path=server_exits.key_path,
                username=server_exits.username,
                server_id = server_exits.id,
                command_description=req.command_description,
                runner=current_user.runner,
                command_status="Aborted"  # Set status to Aborted
            )
            db.add(job) 
            db.commit()
            job_output = JobOutput(
                job_id=job.id,
                stderr=err
            )
            db.add(job_output)  
            db.commit()
            logger.error(f"Job {job.id} output saved successfully")
            raise HTTPException(status_code=403, detail="Command not allowed")

    job = Job(
        command=req.command,
        hostname=server_exits.hostname,
        key_path=server_exits.key_path,
        username=server_exits.username,
        server_id=server_exits.id,
        command_description=req.command_description,
        runner=current_user.runner,  # Use the authenticated user's runner
        command_status="running"  # Set initial status to running
        # You can add more fields if needed, like hostname or command_description
    )

    logger.info(f"Received SSH command request: {server_exits.hostname} - {req.command}")
    
    db.add(job)
    db.commit()
    db.refresh(job)
    logger.info(f"Job created with ID: {job.id}")
    logger.info(f"Running command on {server_exits.hostname} as {server_exits.username}")


    try:
        out, err = run_ssh_command(server_exits.hostname, server_exits.username, req.command, server_exits.key_path)

          
        job_output = JobOutput(
            job_id=job.id,
            stdout=out,
            stderr=err
        )
        db.add(job_output)
        db.commit()
        db.refresh(job_output)  
        logger.info(f"Job output saved with ID: {job_output.id}")
        logger.info(f"Job {job.id} output saved successfully")          
        
        
        if err and not out:
            logger.warning(f"Command execution on {server_exits.hostname} returned an error: {err}")
            job.command_status = "failed"
            db.commit()
        else:
            logger.info(f"Command executed successfully on {server_exits.hostname}")
            job.command_status = "completed"
            db.commit()
            logger.info(f"Job {job.id} status updated to completed")
        return {"stdout": out, "stderr": err}
    
      
    except Exception as e:
        logger.error(f"SSH execution failed: {e}", exc_info=True)
        job.command_status = "failed"
        db.commit()
        logger.error(f"Job {job.id} status updated to failed")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        logger.info("Closing database session")
        db.close() 


@router.get("/v1/all", response_model=List[JobResponse])  
def get_all_jobs(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    logger.info("Fetching all jobs from the database")
    if not current_user.is_superuser:
        logger.warning("User is not superuser, returning empty job list")
        return []
    jobs = db.query(Job).all()
    logger.info(f"Retrieved {len(jobs)} jobs from the database")
    return [JobResponse(
        id=job.id,
        command=job.command,
        job_id=job.job_id,
        hostname=job.hostname,
        username=job.username,
        command_description=job.command_description,
        command_status=job.command_status,
        key_path=job.key_path,
        runner=job.runner,
        run_at=job.run_at
    ) for job in jobs]



@router.get("/v1/runner_jobs", response_model=List[JobResponse])
def get_user_jobs(db: Session = Depends(get_db), current_user: models.User = Depends  (get_current_user)):
    logger.info(f"Fetching jobs for user: {current_user.runner}")
    jobs = db.query(Job).filter(Job.runner == current_user.runner).all()
    if not jobs:
        logger.warning(f"No jobs found for user: {current_user.runner}")
        return []
        
    logger.info(f"Retrieved {len(jobs)} jobs for user: {current_user.runner}")
    return [JobResponse(
        id=job.id,
        command=job.command,
        hostname=job.hostname,
        username=job.username,
        command_description=job.command_description,
        command_status=job.command_status,
        runner=job.runner,
        run_at=job.run_at

    ) for job in jobs]


@router.get("/v1/{job_id}", response_model=JobResponse)
def get_job_by_id(job_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    logger.info(f"Fetching job with ID: {job_id}")
    if not current_user.is_superuser:
        logger.warning("User is not superuser, returning 403 Forbidden")
        raise HTTPException(status_code=403, detail="Access denied")
    
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.error(f"Job with ID {job_id} not found")
        raise HTTPException(status_code=404, detail="Job not found")
    
    logger.info(f"Job with ID {job_id} retrieved successfully")
    return JobResponse(
        id=job.id,
        command=job.command,
        hostname=job.hostname,
        username=job.username,
        command_description=job.command_description,
        command_status=job.command_status,
        runner=job.runner,
        run_at=job.run_at    
        )

    