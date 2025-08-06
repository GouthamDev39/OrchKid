from fastapi import FastAPI, HTTPException, APIRouter, Depends
from schemas import  ServerAddRequest, ServerAddResponse, SerevrEdit, ServerEditResponse
from sqlalchemy.orm import Session  
from db_stuffs.database import get_db
from db_stuffs.models import   Server# Import Job model if needed for database operations
from db_stuffs.database import engine
from db_stuffs.models import Base, Server, User
from ssh_utils import run_ssh_command
from logger import logger  # ✅ Import centralized logger
from oauth import get_current_user
from db_stuffs import models
from typing import List 


router = APIRouter(
    prefix="/servers",
    tags=["Server"]
)


@router.post("/add", response_model=ServerAddResponse,status_code=201)
async def server_add(req: ServerAddRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    logger.info(f"Recived request to add new server {req.hostname} from runner {current_user.runner}")


    server = db.query(Server).filter(Server.hostname == req.hostname, Server.username == req.username).first()
    if server:
        logger.warning(f"Server {req.hostname} already exists for {req.username} .")
        raise HTTPException(status_code=400, detail="Server already exists")

    #owner = db.query(User).filter(User.runner == req.owner).first()
    new_server = Server(
        hostname=req.hostname, 
        username=req.username,
        port=req.port, 
        owner_id=req.owner_id,
        added_by=current_user.id,
        key_path=req.key_path,
        tags=req.tags,
    )
    db.add(new_server)
    db.commit()
    db.refresh(new_server)
    logger.info(f"Added {req.hostname} into the db list")

    logger.info(f"Server {req.hostname} added successfully")
    
    return ServerAddResponse.from_orm(new_server)


@router.get("/list", response_model=List[ServerAddResponse])
async def server_list(db: Session = Depends(get_db), current_user = Depends(get_current_user)): 
    logger.info(f"Recived request to list all servers from runner {current_user.runner}")

    if not current_user.is_superuser:
        logger.error("User is not authorized to list servers.")
        raise HTTPException(status_code=403, detail="Not authorized to list servers") 
    
    servers = db.query(Server).all()
    return [ServerAddResponse.from_orm(server) for server in servers]


@router.put("/edit/{server_id}", response_model=ServerEditResponse, status_code=201)
async def server_edit(server_id: int, req: SerevrEdit, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    logger.info(f"Recived request to edit server {server_id} from runner {current_user.runner}")

    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        logger.error(f"Server with ID: {server_id} not found")
        raise HTTPException(status_code=404, detail="Server not found")
    
    server.owner_id = req.owner_id
    server.port = req.port
    server.tags = req.tags
    db.commit()
    db.refresh(server)

    logger.info(f"Server with ID: {server_id} edited successfully")
    return ServerEditResponse.from_orm(server)


@router.delete("/delete/{server_id}", status_code=204)
async def server_delete(server_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    logger.info(f"Recived request to delete server {server_id} from runner {current_user.runner}")

    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        logger.error(f"Server with ID: {server_id} not found")
        raise HTTPException(status_code=404, detail="Server not found")
    
    db.delete(server)
    db.commit()
    logger.info(f"Server with ID: {server_id} deleted successfully")
    return  {"message": "Server deleted successfully", "server_id": server_id}


@router.get("/{server_id}", response_model=ServerAddResponse)
async def server_get(server_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    logger.info(f"Recived request to get server {server_id} from runner {current_user.runner}")

    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        logger.error(f"Server with ID: {server_id} not found")
        raise HTTPException(status_code=404, detail="Server not found")
    
    logger.info(f"Server with ID: {server_id} retrieved successfully")
    return ServerAddResponse.from_orm(server)
    

