from fastapi import FastAPI, HTTPException, APIRouter, Depends
from schemas import ScriptDetails,ScriptUploadRequest, JobResponse, ScriptsResponse, ScriptUpdateRequest, ScheduleJobRequest, ScheduleJobResponse, ScheduleJobEdit
from sqlalchemy.orm import Session  
from db_stuffs.database import get_db
from db_stuffs.models import Job, JobOutput, Scripts, User, ScheduleJob, Server    # Import Job model if needed for database operations
from db_stuffs.database import engine
from db_stuffs.models import Base
from ssh_utils import run_ssh_command
from logger import logger  # ✅ Import centralized logger
from oauth import get_current_user
from typing import List 
from tasks import run_script, upload_script  # Import the Celery task for running scripts
from scp_utils import run_scp_command
#from celery import current_app


router = APIRouter(
    prefix="/scripts",
    tags=["Scripts"]
)   

#suucefully_refractored
@router.post("/upload", status_code=201)
async def upload_script_endpoint(
    req: ScriptUploadRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    #logger.info(f"Received script upload request: {req.file_name} on {req.hostname} by {current_user.runner}")
    logger.info("Authenticated user: " + current_user.runner)

    # Check if script already exists for same filename and hostname
   

    server_exits = db.query(Server).filter(Server.id == req.server_id).first()

    if not server_exits:
        logger.error(f"Server ID {req.server_id} not found")
        raise HTTPException(status_code=404, detail="Server ID not found")

    script = db.query(Scripts).filter(
        Scripts.file_name == req.file_name,
        Scripts.hostname == server_exits.hostname
    ).first()

    logger.info(f"Request recived to upload {req.file_name} to server {server_exits.hostname} by {current_user.runner}")
    # Upload the file (always, since it might be new or an update)
    try:
        task = upload_script.delay(
            source=req.file_path,
            destination=f"/home/{server_exits.username}/bin/{req.file_name}",
            hostname=server_exits.hostname,
            username=server_exits.username,
            key_path=server_exits.key_path
        )
        logger.info(f"Upload task enqueued for script {req.file_name} to {server_exits.hostname} with task ID: {task.id}")
    except Exception as e:
        logger.error(f"Failed to upload script {req.file_name} to {server_exits.hostname}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload script: {str(e)}")

    if script:
        logger.warning(f"Script {req.file_name} already exists on {server_exits.hostname} — will overwrite it.")

        script.name = req.name
        script.description = req.description
        script.server_id = req.server_id
        script.hostname = server_exits.hostname
        script.upload_status = "On Queue"
        script.file_path = req.file_path
        script.username = server_exits.username
        script.runner = current_user.runner
        script.tags = req.tags

        db.commit()
        db.refresh(script)

        logger.info(f"Script {script.name} updated successfully with ID: {script.id}")

        return {
            "message": "Script updated successfully",
            "script_id": script.id,
            "upload_status": "On Queue",
            "remote_path": f"/home/{server_exits.username}/bin/{req.file_name}",
            "host": server_exits.hostname
        }

    
    new_script = Scripts(
        name=req.name,
        description=req.description,
        file_name=req.file_name,
        server_id=req.server_id,
        upload_status="On Queue",
        file_path=req.file_path,
        hostname=server_exits.hostname,
        username=server_exits.username,
        runner=current_user.runner,
        tags=req.tags
    )

    db.add(new_script)
    db.commit()
    db.refresh(new_script)

    logger.info(f"Script {new_script.name} is in queue for upload with ID: {new_script.id}")

    return {
        "message": "Script uploaded successfully",
        "upload_status": "On Queue",
        "script_id": new_script.id,
        "remote_path": f"/home/{server_exits.username}/bin/{req.file_name}",
        "host": server_exits.hostname
    }


@router.get("/all", response_model=List[ScriptDetails], status_code=200)
async def list_scripts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logger.info(f"Listing scripts for user: {current_user.runner}")
    
    if not current_user.is_superuser:
        logger.error("User is not authorized to list scripts.")
        raise HTTPException(status_code=403, detail="Not authorized to list scripts")
    
    scripts = db.query(Scripts).all()

    return [ScriptDetails(
        id=script.id,
        name=script.name,
        description=script.description,
        upload_status=script.upload_status,
        file_name=script.file_name,
        file_path=script.file_path,
        hostname=script.hostname,
        username=script.username,
        created_at=script.created_at,
        updated_at=script.updated_at,
        runner=script.runner,
        tags=script.tags
    ) for script in scripts]


@router.get("/runner_scripts", response_model=List[ScriptsResponse], status_code=200)
async def list_user_scripts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logger.info(f"Listing scripts for user: {current_user.runner}") 
    scripts = db.query(Scripts).filter(Scripts.runner == current_user.runner).all()
    if not scripts:
        logger.warning(f"No scripts found for user: {current_user.runner}")
        return []   
    logger.info(f"Retrieved {len(scripts)} scripts for user: {current_user.runner}")
    return [ScriptsResponse(
        id=script.id,
        name=script.name,
        description=script.description,
        file_name=script.file_name,
        file_path=script.file_path,
        hostname=script.hostname,
        username=script.username,
        created_at=script.created_at,
        updated_at=script.updated_at,
        runner=script.runner,
        tags=script.tags
    ) for script in scripts]


@router.delete("/{script_id}", status_code=204)
async def delete_script(script_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logger.info(f"Deleting script with ID: {script_id} for user: {current_user.runner}")
    if not current_user.is_superuser:
        logger.error("User is not authorized to delete scripts.")
        raise HTTPException(status_code=403, detail="Not authorized to delete scripts") 
    script = db.query(Scripts).filter(Scripts.id == script_id).first()
    if not script:
        logger.error(f"Script with ID {script_id} not found")
        raise HTTPException(status_code=404, detail="Script not found") 
    db.delete(script)
    db.commit()
    logger.info(f"Script with ID {script_id} deleted successfully")
    return {"message": "Script deleted successfully", "script_id": script_id}   


@router.get("/{script_id}", response_model=ScriptsResponse, status_code=200)
async def get_script(script_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logger.info(f"Fetching script with ID: {script_id} for user: {current_user.runner}")
       
    script = db.query(Scripts).filter(Scripts.id == script_id).first()
    if not script:
        logger.error(f"Script with ID {script_id} not found")
        raise HTTPException(status_code=404, detail="Script not found")
    
    return ScriptsResponse(
        id=script.id,
        name=script.name,
        description=script.description,
        file_name=script.file_name,
        file_path=script.file_path,
        hostname=script.hostname,
        username=script.username,
        created_at=script.created_at,
        updated_at=script.updated_at,
        runner=script.runner,
        tags=script.tags
    )

#redone successfully
@router.post("/execute/{script_id}", response_model=JobResponse, status_code=201)
async def execute_script(
    script_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Queuing execution for script ID: {script_id} by user: {current_user.runner}")
        
    script = db.query(Scripts).filter(Scripts.id == script_id).join(Server, Scripts.server_id == Server.id).first()
    server_info = db.query(Server).filter(Server.id == script.server_id).first()

    if not script:
        logger.error(f"Script with ID {script_id} not found")
        raise HTTPException(status_code=404, detail="Script not found")
    if not server_info:
        logger.error(f"Server with ID {script.server_id} not found")
        raise HTTPException(status_code=404, detail="Server not found")

    # Create job entry in DB with "queued" status
    job = Job(
        command=f"bash /home/{server_info.username}/bin/{script.file_name}",
        hostname=server_info.hostname,
        server_id=script.server_id,
        key_path=server_info.key_path,
        job_id=script.id,
        username=server_info.username,
        command_description=script.description,
        command_status="queued",
        runner=current_user.runner
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Trigger Celery task (non-blocking)
    task = run_script.delay(script.id, job.id)

    logger.info(f"Job {job.id} queued via Celery with task ID: {task.id}")
    
    return JobResponse(
        id=job.id,
        command=job.command,
        hostname=server_info.hostname,
        job_id=job.job_id,
        username=server_info.username,
        command_description=script.description,
        command_status="queued", 
        runner=current_user.runner,
        run_at=job.run_at
    )


#if you want to upload script and run it in a go!
@router.post("/super_run", response_model=JobResponse, status_code=201)
async def upload_and_run_script(
    req: ScriptUploadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Received request to upload and run script: {req.file_name} on {req.hostname} by {current_user.runner}")

    if not current_user.is_superuser:
        logger.error("User is not authorized to use super_run.")
        raise HTTPException(status_code=403, detail="Not authorized to use super_run.")

    # Upload the script first
    upload_response = await upload_script_endpoint(req, db, current_user)
    
    # Now execute the uploaded script
    job = Job(
        command=f"bash /home/{req.username}/bin/{req.file_name}",
        hostname=req.hostname,
        job_id=upload_response['script_id'],
        username=req.username,
        command_description=req.description,
        command_status="running",
        runner=current_user.runner
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    logger.info(f"Job created with ID: {job.id} for uploaded script ID: {upload_response['script_id']}")
    
    out, err = run_ssh_command(req.hostname, req.username, f"bash /home/{req.username}/bin/{req.file_name}")

    if err:
        logger.error(f"Error executing uploaded script {upload_response['script_id']}: {err}")
        job.command_status = "failed"
        db.commit() 
        job_output = JobOutput(
            job_id=job.id,
            stderr=err
        )
        db.add(job_output)
        db.commit()
        db.refresh(job_output)  
        logger.info(f"Job output saved with ID: {job_output.id} for job ID: {job.id}")
        
        return JobResponse(
            id=job.id,
            command=job.command,
            hostname=req.hostname,
            job_id=upload_response['script_id'],
            username=req.username,
            command_description=req.description,
            command_status="failed",
            runner=current_user.runner,
            run_at=job.run_at
        )

    else:
        logger.info(f"Uploaded script executed successfully")
        job.command_status = "completed"    
        db.commit()
        
    
    job_output = JobOutput(
        job_id=job.id,
        stdout=out,
        stderr=err
    )
    
    db.add(job_output)
    db.commit()
    db.refresh(job_output)
    

    logger.info(f"Job output saved with ID: {job_output.id} for job ID: {job.id}")
    logger.info(f"Job {job.id} output saved successfully")
    
    return JobResponse(
        id=job.id,
        command=job.command,
        hostname=req.hostname,
        job_id=upload_response['script_id'],
        username=req.username,
        command_description=req.description,
        command_status="completed",
        runner=current_user.runner,
        run_at=job.run_at
    )

##TODO: Update script
@router.put("/update/{script_id}", response_model=ScriptsResponse, status_code=200)
async def update_script(
    script_id: int,
    req: ScriptUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Received request to update script ID: {script_id} by user: {current_user.runner}")

    script = db.query(Scripts).filter(Scripts.id == script_id, Scripts.hostname == req.hostname).first()
    if not script:
        logger.error(f"Script with ID: {script_id} not found or not owned by user: {current_user.runner}")
        raise HTTPException(status_code=404, detail="Script not found")

    run_scp_command(
        hostname=req.hostname,
        username=req.username,
        local_path=req.file_path,  # Assuming file_path is the local path to the script
        remote_path=f"/home/{req.username}/bin/{req.file_name}"  # Adjust the remote path as needed
    )
    logger.info(f"Script {req.file_name} updated successfully on {req.hostname} by {current_user.runner}")

    # Update script details
    script.name = req.name
    script.description = req.description
    script.file_name = req.file_name
    script.file_path = req.file_path
    script.hostname = req.hostname
    script.username = req.username
    script.runner = current_user.runner
    script.tags = req.tags

    db.commit()
    db.refresh(script)

    logger.info(f"Script with ID: {script.id} updated successfully")
    return ScriptsResponse.from_orm(script)


@router.get("/history/{script_id}", response_model=List[JobResponse], status_code=200)
async def get_script_history(
    script_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Received request to get history for script ID: {script_id} by user: {current_user.runner}")

    jobs = db.query(Job).filter(Job.job_id == script_id).all()
    if not jobs:
        logger.warning(f"No job history found for script ID: {script_id}")
        return []

    logger.info(f"Job history retrieved successfully for script ID: {script_id} with {len(jobs)} entries by user: {current_user.runner}")
    return [JobResponse.from_orm(job) for job in jobs]


@router.get("/v1/runner_history", response_model=List[JobResponse])
async def get_runner_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Received request to get runner history by user: {current_user.runner}")

    jobs = db.query(Job).filter(Job.runner == current_user.runner).all()
    if not jobs:
        logger.warning(f"No job history found for user: {current_user.runner}")
        return []

    logger.info(f"Job history retrieved successfully for user: {current_user.runner} with {len(jobs)} entries")
    return [JobResponse.from_orm(job) for job in jobs]



@router.post("/schedule", response_model=ScheduleJobResponse, status_code=201)
async def schedule_job(
    req: ScheduleJobRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    logger.info(f"Received request to schedule job by user: {current_user.runner}")
    logger.info(f"SCheduling job for script {req.script_id}")
    if not current_user.is_superuser:
        logger.error("User is not authorized to schedule jobs.")
        raise HTTPException(status_code=403, detail="Not authorized to schedule jobs")

    script = db.query(Scripts).filter(Scripts.id == req.script_id).first()
    if not script:
        logger.error(f"Job with ID {req.script_id} not found")
        raise HTTPException(status_code=404, detail="Job not found")

    scheduled_job = ScheduleJob(
        script_id=script.id,
        cron_expression=req.cron_expression,
        one_time_run=req.one_time_run,
        timezone=req.timezone,
        is_active=req.is_active
    )

    db.add(scheduled_job)
    db.commit()
    db.refresh(scheduled_job)

    logger.info(f"Job scheduled successfully with ID: {scheduled_job.id}")

    return ScheduleJobResponse.from_orm(scheduled_job)


@router.get("/schedule/{scheduled_job_id}", response_model=ScheduleJobResponse, status_code=200)
async def get_shceduled_job(
    scheduled_job_id : int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    logger.info(f"Received request to get scheduled Job iD of: {scheduled_job_id} by user: {current_user.runner}")
    job = db.query(ScheduleJob).filter(ScheduleJob.id == scheduled_job_id).first()

    if not job:
        logger.error(f"There are no scheduled job with id {scheduled_job_id}")
        raise HTTPException(status_code=404, detail="Job not found")

    logger.info(f"Scheduled Job retrieved successfully for Schdued Job ID: {scheduled_job_id} by user: {current_user.runner}")
    
    return ScheduleJobResponse.from_orm(job)


@router.put ("/schedule/{scheduled_job_id}", response_model=ScheduleJobResponse, status_code=201)
async def get_shceduled_job(
    scheduled_job_id : int,
    req: ScheduleJobEdit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    logger.info(f"Received an edit request to get scheduled Job iD of: {scheduled_job_id} by user: {current_user.runner}")

    
    job = db.query(ScheduleJob).filter(ScheduleJob.id == scheduled_job_id).first()

    if not job:
        logger.error(f"There are no scheduled job with id {scheduled_job_id}")
        raise HTTPException(status_code=404, detail="Job not found")
    
    job.cron_expression = req.cron_expression
    job.one_time_run = req.one_time_run
    job.is_active = req.is_active
    db.commit()
    db.refresh(job)


    logger.info(f"Scheduled Job edited successfully for Schdued Job ID: {scheduled_job_id} by user: {current_user.runner}")
    
    return ScheduleJobResponse.from_orm(job)


@router.delete ("/schedule/{scheduled_job_id}", status_code=204)
async def get_shceduled_job(
    scheduled_job_id : int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    logger.info(f"Received a delete request to get scheduled Job iD of: {scheduled_job_id} by user: {current_user.runner}")


    if not current_user.is_superuser:
        logger.error("User is not authorized to delete scheduled jobs.")
        raise HTTPException(status_code=403, detail="Not authorized to schedule jobs")
    
    job = db.query(ScheduleJob).filter(ScheduleJob.id == scheduled_job_id).first()

    if not job:
        logger.error(f"There are no scheduled job with id {scheduled_job_id}")
        raise HTTPException(status_code=404, detail="Job not found")
    
    db.delete(job)
    db.commit()

    logger.info(f"Scheduled Job deleted successfully for Schdued Job ID: {scheduled_job_id} by user: {current_user.runner}")
    
    return {"message": "Script deleted successfully", "script_id": scheduled_job_id}   



@router.get("/v1/schedule/all", response_model=List[ScheduleJobResponse], status_code=200)
async def get_all_shceduled_job(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    logger.info(f"Received request to get all scheduled Job by user: {current_user.runner}")

    
    jobs = db.query(ScheduleJob).all()

    if not jobs:
        logger.error(f"There are no scheduled jobs")
        raise HTTPException(status_code=404, detail="No Job found")

    logger.info(f"All Scheduled Job retrieved successfull by user: {current_user.runner}")
    
    return [ScheduleJobResponse.from_orm(job) for job in jobs]

