import asyncio
from datetime import datetime
from croniter import croniter
import pytz
from datetime import timedelta
from db_stuffs.models import ScheduleJob, Scripts, Job
from db_stuffs.database import SessionLocal
from tasks import run_script
from logger import logger


CHECK_INTERVAL = 30  # seconds


async def scheduler_loop():
    while True:
        now = datetime.now()
        # logger.info("Running scheduler check")
        with SessionLocal() as db:
            schedules = db.query(ScheduleJob).filter_by(is_active=True).all()

            for sched in schedules:
                job = db.query(Scripts).filter_by(id=sched.script_id).first()
                if not job:
                    continue
                
                # Check if it's a one-time run
                if sched.one_time_run and not sched.last_run_at:
                    if sched.one_time_run and now >= sched.one_time_run.replace(tzinfo=None):
                        run_script.delay(script_id=job.job_id, job_id=job.id)
                        sched.last_run_at = now
                        db.commit()
                        logger.info(f"Committed run at {now}")


                # Or if it's a recurring job
                elif sched.cron_expression:
                    try:
                        # Use timezone or default to UTC
                        tz = pytz.timezone(sched.timezone) if sched.timezone else pytz.UTC
                        now_tz = datetime.now(tz)
                        #logger.info(f"Now_tz = {now_tz}")

                        #last_run = sched.last_run_at or now_tz - timedelta(seconds=CHECK_INTERVAL)
                        last_run = sched.last_run_at.astimezone(tz) if sched.last_run_at else now_tz - timedelta(seconds=CHECK_INTERVAL)
                        #logger.info(f"Last_run = {last_run}")
                        
                        # Ensure last_run is also timezone-aware
                        if last_run.tzinfo is None:
                            last_run = tz.localize(last_run)

                        next_run = croniter(sched.cron_expression, last_run).get_next(datetime)
                        #logger.info(f"Next_tz = {next_run}")

                        if last_run < next_run <= now_tz:
                            run_script.delay(script_id=job.id, job_id=job.id)
                            sched.last_run_at = now_tz.astimezone(pytz.UTC)
                            #logger.info(f"This time = {sched.last_run_at}")
                            #logger.info(f"Now_tz = {now_tz}")
                            db.commit()
                            logger.info(f"Scheduled job triggered at {now_tz} for script ID {job.id}")


                        # logger.info(f"datetime.now() = {datetime.now()}")  # naive
                        # logger.info(f"datetime.now(tz) = {datetime.now(tz)}")  # aware
                        # logger.info(f"tz.localize(datetime.now()) = {tz.localize(datetime.now())}") 

                    except Exception as e:
                        logger.error(f"Error scheduling job: {e}", exc_info=True)

        await asyncio.sleep(CHECK_INTERVAL)
