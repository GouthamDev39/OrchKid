from paramiko import SSHClient, AutoAddPolicy, RSAKey
from pathlib import Path
from logger import logger  # ✅ use shared logger

#KEY_PATH = Path.home() / ".ssh" / "redhood_key"

def run_ssh_command(hostname: str, username: str, command: str,key_path: str, timeout: int = 30):
    #KEY_PATH = "/home/batman/.ssh/redhood_key"
    KEY_PATH = key_path
    logger.info(f"Connecting to {hostname} as {username}")
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
            
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            out = stdout.read().decode().strip()
            err = stderr.read().decode().strip()
            
            # if out:
            #     logger.info(f"Command output: {out}")
            # if err:
            #     logger.error(f"Command error: {err}")
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                logger.error(f"Command failed with exit status {exit_status}: !{err}!")
                #print(out, err, exit_status)
                return out, err
            logger.info(f"Command executed successfully: {command}")
            return out, err
        
    except Exception as e:
        logger.error(f"SSH connection failed: {e}", exc_info=True)
        return {"out": "", "err": str(e)}

# def file_transfer(ssh_client, local_path: str, remote_path: str):
#     logger.info(f"Transferring file from {local_path} to {remote_path}")
#     sftp = ssh_client.open_sftp()
#     try:
#         sftp.put(local_path, remote_path)
#         logger.info(f"File transferred successfully to {remote_path}")
#     except Exception as e:
#         logger.error(f"File transfer failed: {e}", exc_info=True)
#         raise e
#     finally:
#         sftp.close()