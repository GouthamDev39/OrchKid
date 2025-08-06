from pydantic import BaseModel, model_validator, field_validator, Field, conint
from typing import Optional, Annotated
import datetime
import os

class SSHCommandRequest(BaseModel):
    server_id : int
    #status: str             # e.g. test
    #key_path: str
    command: str            # e.g. df -h
    command_description: Optional[str] = None  # Optional description of the command


class CreateUser(BaseModel):
    runner: str
    password: str
    is_superuser: bool 


class UserResponse(BaseModel):
    id: int
    runner: str
    is_superuser: bool
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    runner: str   


class JobResponse(BaseModel):
    id: int
    command: str
    hostname: str
    username: str
    job_id : int
    #key_path: str
    #server_id: int
    job_id: Optional[int] = None  # Optional job ID if linked to a script
    command_description: Optional[str] = None  # Optional description of the command
    command_status: str
    runner: str
    run_at: datetime.datetime
    class Config:
        from_attributes = True


class ScriptUploadRequest(BaseModel):
    name: str
    description: Optional[str] = None
    file_name: str
    file_path: str  # Path to the script file
    #hostname: str  # Hostname where the script is uploaded
    server_id: int
    #username: str  # Username for the remote host
    tags: Optional[str] = None  # Optional tags for the script

    @field_validator('file_name')
    def validate_script_extension(cls, v):
        if not v.endswith(('.sh')):
            raise ValueError("Only .sh files are allowed")
        return v

    @field_validator('file_path')
    def validate_script_path(cls, v):
        if not os.path.exists(v):
            raise ValueError("Script file does not exist")
        return v


class ScriptsResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    file_name: str
    file_path: str  # Path to the script file
    hostname: str  # Hostname where the script is uploaded
    username: str  # Username for the remote host
    created_at: datetime.datetime
    updated_at: datetime.datetime
    runner: str  # Runner who uploaded the script
    tags: Optional[str] = None  # Optional tags for the script

    class Config:
        from_attributes = True


class ScriptDetails(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    file_name: str
    file_path: str  # Path to the script file
    hostname: str  # Hostname where the script is uploaded
    username: str  # Username for the remote host
    upload_status : str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    runner: str  # Runner who uploaded the script
    tags: Optional[str] = None  # Optional tags for the script

    class Config:
        from_attributes = True


class ScriptUpdateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    file_name: str
    file_path: str  # Path to the script file
    hostname: str  # Hostname where the script is uploaded
    username: str  # Username for the remote host
    server_id: int
    tags: Optional[str] = None  # Optional tags for the script

    @field_validator('file_name')
    def validate_script_extension(cls, v):
        if not v.endswith(('.sh', '.py')):
            raise ValueError("Only .sh or .py files are allowed")
        return v

class ScheduleJobRequest(BaseModel):
    script_id: int  # ID of the job to be scheduled
    cron_expression: Optional[str] = None  # Cron expression for scheduling
    one_time_run: Optional[datetime.datetime] = None  # Flag for one-time run
    timezone: Optional[str] = None # Timezone for the scheduled job
    is_active: bool = True  # To manage active/inactive status
    
    @model_validator(mode='after')
    def check_schedule_requirements(cls,values):
        cron = values.cron_expression
        one_time_run = values.one_time_run
        if not cron and not one_time_run:
            raise ValueError("At least one schedule requirement must be provided")
        return values
        

class ScheduleJobResponse(BaseModel):
    id: int
    script_id: int  # ID of the job to be scheduled
    cron_expression: Optional[str] = None  # Cron expression for scheduling
    one_time_run: Optional[datetime.datetime] = None  # Flag for one-time run
    timezone: Optional[str] = None  # Timezone for the scheduled job
    is_active: bool = True  # To manage active/inactive status
    last_run_at: Optional[datetime.datetime] = None  # Last run time of the scheduled job

    class Config:
        from_attributes = True


class ScheduleJobEdit(BaseModel):
    cron_expression: Optional[str] = None 
    one_time_run: Optional[datetime.datetime] = None
    is_active: bool = True 

    @model_validator(mode='after')
    def check_schedule_requirements(cls,values):
        cron = values.cron_expression
        one_time_run = values.one_time_run
        if not cron and not one_time_run:
            raise ValueError("At least one schedule requirement must be provided")
        return values

class ServerAddRequest(BaseModel):
    hostname: str
    username: str
    owner_id: Optional[int]
    key_path: str
    #key_id:
    port: Optional[int]
    tags: Optional[str]

class ServerAddResponse(BaseModel):
    id: int
    hostname: str
    username: str
    owner_id: Optional[int]

    #key_id:
    added_by: int
    port: Optional[conint(ge=1, le=65535)] = 22
    tags: Optional[str] 

    class Config:
        from_attributes = True

class SerevrEdit(BaseModel):
    owner_id: Optional[int] = None
    key_path: Optional[str] = None
    #key_id:
    port: Optional[int] = 22
    tags: Optional[str]


class ServerEditResponse(BaseModel):
    hostname: str
    username: str
    owner_id: Optional[int]
    #key_id:
    added_by: int
    port: Optional[int]
    tags: Optional[str]

    class Config:
        from_attributes = True


#v2 changes comings

# from pydantic import BaseModel
# from typing import Optional
# import datetime



# class SSHCommandRequest(BaseModel):
#     hostname: str           # e.g. 192.168.122.201
#     username: str
#     #status: str             # e.g. test
#     command: str            # e.g. df -h
#     command_description: Optional[str] = None  # Optional description of the command

# class CreateUser(BaseModel):
#     runner: str
#     password: str
#     is_superuser: bool 
#     role: str

# class UserResponse(BaseModel):
#     id: int
#     runner: str
#     is_superuser: bool
#     role: str
#     class Config:
#         from_attributes = True

# class Token(BaseModel):
#     access_token: str
#     token_type: str

# class TokenData(BaseModel):
#     runner: str   

# class JobResponse(BaseModel):
#     id: int
#     command: str
#     server_id: int
#     job_id: Optional[int] = None  # Optional job ID if linked to a script
#     command_description: Optional[str] = None  # Optional description of the command
#     command_status: str
#     runner: str
#     run_at: datetime.datetime
#     class Config:
#         from_attributes = True


# class ScriptUploadRequest(BaseModel):
#     name: str
#     description: Optional[str] = None
#     file_name: str
#     file_path: str  # Path to the script file
#     approved: bool
#     server_id: int # Server ID where the script is uploaded
#     tags: Optional[str] = None  # Optional tags for the script

# class ScriptsResponse(BaseModel):
#     id: int
#     name: str
#     description: Optional[str] = None
#     file_name: str
#     file_path: str  # Path to the script file
#     server_id: int  # Server ID where the script is uploaded
#     approved: bool
#     created_at: datetime.datetime
#     updated_at: datetime.datetime
#     runner: str  # Runner who uploaded the script
#     tags: Optional[str] = None  # Optional tags for the script

#     class Config:
#         from_attributes = True

# class ScriptUpdateRequest(BaseModel):
#     name: str
#     description: Optional[str] = None
#     file_name: str
#     file_path: str  # Path to the script file
#     server_id: int  # Hostname where the script is uploaded
#     tags: Optional[str] = None  # Optional tags for the script

# class ScheduleJobRequest(BaseModel):
#     script_id: int  # ID of the job to be scheduled
#     cron_expression: Optional[str] = None  # Cron expression for scheduling
#     one_time_run: Optional[datetime.datetime] = None  # Flag for one-time run
#     timezone: Optional[str] = None # Timezone for the scheduled job
#     is_active: bool = True  # To manage active/inactive status


# class ScheduleJobResponse(BaseModel):
#     id: int
#     script_id: int  # ID of the job to be scheduled
#     cron_expression: Optional[str] = None  # Cron expression for scheduling
#     one_time_run: Optional[datetime.datetime] = None  # Flag for one-time run
#     timezone: Optional[str] = None  # Timezone for the scheduled job
#     is_active: bool = True  # To manage active/inactive status
#     last_run_at: Optional[datetime.datetime] = None  # Last run time of the scheduled job

#     class Config:
#         from_attributes = True

# class ScheduleJobEdit(BaseModel):
#     cron_expression: Optional[str] = None 
#     one_time_run: Optional[datetime.datetime] = None
#     is_active: bool = True 

# class ServerAddRequest(BaseModel):
#     hostname: str
#     username: str
#     owner_id: Optional[int]
#     ssh_key_path: str
#     port: Optional[int]
#     tags: Optional[str]

# class ServerAddResponse(BaseModel):
#     hostname: str
#     username: str
#     owner_id: Optional[int]
    
#     added_by: int
#     port: Optional[int]
#     tags: str 

#     class Config:
#         from_attributes = True

# class SerevrEdit(BaseModel):
#     owner_id: Optional[int] = None
#     #key_id:
#     port: Optional[int] = 22
#     tags: Optional[str]


# class ServerEditResponse(BaseModel):
#     hostname: str
#     username: str
#     owner_id: Optional[int]
#     #key_id:
#     added_by: int
#     port: Optional[int]
#     tags: Optional[str]

#     class Config:
#         from_attributes = True