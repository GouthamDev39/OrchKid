from celery_worker import celery_app
from ssh_utils import run_ssh_command
from scp_utils import run_scp_command
from db_stuffs.database import get_db
from db_stuffs.models import Scripts, Job, JobOutput, Server
from logger import logger
import os


@celery_app.task(name="tasks.run_script")
def run_script(script_id: int, job_id: int):
    logger.info(f"Running script task for script ID: {script_id} and job ID: {job_id}")

    logger.info("Acquiring database session for running script task")
    db_gen = get_db()
    logger.info("Database session acquired")
    db = next(db_gen)
    try:
        script_exitst = db.query(Scripts).join(Server, Scripts.server_id == Server.id).filter(Scripts.id == script_id).first()
        if not script_exitst:
            raise ValueError(f"Script with ID {script_id} not found")

        job = db.query(Server).join(Job, Server.id == Job.server_id).filter(Job.id == job_id).first()
        job_info = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job with ID {job_id} not found")

        command = f"bash /home/{job.username}/bin/{script_exitst.file_name}"
        out, err = run_ssh_command(job.hostname, job.username, command, job.key_path)


        # Save job output
        job_output = JobOutput(job_id=job.id, stdout=out, stderr=err)
        db.add(job_output)

        # Update job status
        job_info.command_status = 'completed' if not err else 'failed'
        db.commit()

        return {
            "job_id": job.id,
            "output": out,
            "error": err
        }
    
    except Exception as e:
        logger.error(f"Error running script: {e}", exc_info=True)
        if job:
            job_info.command_status = 'failed'
            db.commit()
        raise e

    finally:

        if out == "out" and err == "err":
            logger.error(f"No output or error returned for job ID {job.id}. This might indicate an issue with the command execution.")
            job_info.command_status = 'failed'
            db.commit()
        
        #logger.info("Committing database changes after running script task")
        db_gen.close()
        logger.info("Database session closed after running script task")


@celery_app.task(name="tasks.upload_script")
def upload_script(source: str, destination: str,key_path : str ,hostname: str, username: str):
    logger.info(f"Uploading script from {source} to {destination} on {hostname} as {username}")
    db_gen = get_db()
    db = next(db_gen)
    script = db.query(Scripts).filter(Scripts.file_path == source).first()
    if not script:
        raise ValueError(f"Script with file path {source} not found")
    logger.info("Database session acquired for script upload")
    if not os.path.exists(source):
        logger.error(f"Source script not found: {source}")
        raise FileNotFoundError(f"Source script not found: {source}")
    
    try:
        run_scp_command(hostname, username, source, destination, key_path)
        logger.info(f"Script uploaded successfully from {source} to {destination}")
        script.upload_status = "Completed"
        db.commit()
    except Exception as e:
        logger.error(f"Failed to upload script: {e}", exc_info=True)
        script.upload_status = "Failed"
        db.commit()
        raise e
    

    return {
        "status": "success",
        "message": f"Script uploaded from {source} to {destination} on {hostname}"
    }