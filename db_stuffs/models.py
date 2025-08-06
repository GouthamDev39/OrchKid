from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint, Text, CheckConstraint
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP, DateTime

from .database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    
    command = Column(String, nullable=False)
    command_description = Column(String, nullable=True)
    hostname = Column(String, nullable=False)   
    username = Column(String, nullable=False)   
    
    server_id = Column(Integer, ForeignKey('servers.id'), nullable=False)  # Optional job script ID if linked to a script
    job_id = Column(Integer, ForeignKey('scripts.id'), nullable=True)  # Optional job script ID if linked to a script
    command_status = Column(String, default='pending')  # e.g. pending, running, completed, failed
    key_path = Column(String, nullable=False)

    runner = Column(String, ForeignKey('users.runner'), nullable=False)  # Foreign key to Use
    run_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    #updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))

    def __repr__(self):
        return f"<Job id={self.id} command='{self.command}'>"


class JobOutput(Base):
    __tablename__ = "job_outputs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)  


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    runner = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # Store hashed passwords
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    #is_active = Column(Boolean, default=True)  # To manage user status
    is_superuser = Column(Boolean, default=False)  # For admin privileges
    #role = Column(String, default='runner')  # User role (e.g. runner, admin, owner)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))


class Scripts(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    description = Column(String, nullable=True)
    file_name = Column(String, nullable=False)  # Unique file name for the script
    file_path = Column(String, nullable=False)  # Path to the script file
    hostname = Column(String, nullable=False)  # Hostname where the script is uploaded
    username = Column(String, nullable=False)  # Username for the remote host
    upload_status = Column(String, nullable=False)  # Upload status (e.g. pending, completed, failed)
    
    #approved = Column(Boolean, default=False)   
    server_id = Column(Integer, ForeignKey('servers.id'), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))
    runner = Column(String, ForeignKey('users.runner'), nullable=False)  # Foreign key to User
    tags = Column(String, nullable=True)  # Optional tags for the script

    __table_args__ = (UniqueConstraint('file_name', 'hostname', 'username', name='unique_script_per_host'),)  # Ensure unique script per host


class ScheduleJob(Base):
    __tablename__ = "schedule_jobs"

    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(Integer, ForeignKey('scripts.id'), nullable=False)

    cron_expression = Column(String, nullable=True)  # Cron expression for scheduling
    one_time_run = Column(DateTime(timezone=True), nullable=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)  # One-time run timestamp (naive)
    timezone = Column(String, nullable=True)  # Timezone name like 'Asia/Kolkata'
    is_active = Column(Boolean, default=True)  # To manage active/inactive status

    last_run_at = Column(DateTime(timezone=False), nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))
    
    __table_args__ = (UniqueConstraint('script_id', name='unique_schedule_job_per_script'),)  # Ensure unique schedule job per script
    __table_args__ = (
        CheckConstraint(
            "(cron_expression IS NOT NULL OR one_time_run IS NOT NULL)",
            name="at_least_one_schedule_set"
        ),
    )

class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer,primary_key=True,index=True)

    hostname =  Column(String, nullable=False)
    username = Column(String, nullable=False)
    port = Column(Integer, default=22,nullable=True)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    key_path = Column(String, nullable=False)
    #key_id
    added_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    tags = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'), onupdate=text('now()'))       

    __table_args__ = (UniqueConstraint('hostname', 'username', name='unique_server_per_host'),)  # Ensure unique server per host


#Upadtes to be added
# class ScriptTarget(Base):
#     __tablename__ = 'script_targets'

#     id = Column(Integer, primary_key=True, index=True)
#     script_id = Column(Integer, ForeignKey('scripts.id'), nullable=False)
#     server_id = Column(Integer, ForeignKey('servers.id'), nullable=False)

# class JobTarget(Base):
#     __tablename__ = 'job_targets'

#     id = Column(Integer, primary_key=True, index=True)
#     job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
#     server_id = Column(Integer, ForeignKey('servers.id'), nullable=False)
