from http.client import HTTPException
from paramiko import SSHClient, AutoAddPolicy, RSAKey
#from pathlib import Path
from logger import logger  # ✅ use shared logger
import os



def run_scp_command(hostname: str, username: str, source: str, destination: str, key_path: str, timeout: int = 30):
    logger.info(f"Connecting to {hostname} as {username}")
    KEY_PATH = key_path
    private_key = RSAKey.from_private_key_file(str(KEY_PATH))
    logger.info(f"Using private key from {KEY_PATH}")
    if not private_key:
        logger.error(f"Private key not found at {KEY_PATH}")
        raise FileNotFoundError(f"Private key not found at {KEY_PATH}")

    try:
        with SSHClient() as client:
            client.set_missing_host_key_policy(AutoAddPolicy())
            client.connect(hostname, username=username, pkey=private_key, timeout=timeout)
            logger.info(f"Connected to {hostname} successfully")
            
            sftp = client.open_sftp()
            try:
                sftp.stat(f"/home/{username}/bin/")
            except FileNotFoundError:
                sftp.mkdir(f"/home/{username}/bin/")
            
            if not os.path.exists(source):
                logger.error(f"Local script not found: {source}")
                raise HTTPException(status_code=400, detail="Local script not found")
            logger.info(f"Trasnsferring file from {source} to {destination}")
            sftp.put(source, destination)
            client.exec_command(f"chmod +x {destination}")
            sftp.close()
            logger.info(f"File transferred successfully from {source} to {destination}")
            
    except Exception as e:
        logger.error(f"SCP transfer failed: {e}", exc_info=True)
        raise e