import json
import uuid
import redis
from hotqueue import HotQueue
import os
import logging

# Environment variables
redis_host= os.environ.get('REDIS_HOST')
redis_port= os.environ.get('REDIS_PORT')

# Configure logging
log_level = os.environ.get('LOG_LEVEL', 'WARNING')
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

rd = redis.Redis(host=redis_host, port=redis_port, db=0)
q = HotQueue("queue", host=redis_host, port=redis_port, db=1)
jdb = redis.Redis(host=redis_host, port=redis_port, db=2)
rdb = redis.Redis(host=redis_host, port=redis_port, db=3)

def _generate_jid() -> str:
    """
    Generate a pseudo-random identifier for a job.

    Returns:
        str: The generated job ID.
    """
    return str(uuid.uuid4())

def _instantiate_job(jid: str, status: str, bin_size: float) -> dict:
    """
    Create the job object description as a python dictionary.

    Args:
        jid (str): The job ID.
        status (str): The status of the job.
        start (int): The start value for the job.
        end (int): The end value for the job.

    Returns:
        dict: The job object description.
    """
    return {'id': jid,
            'status': status,
            'bin_size': bin_size}

def _save_job(jid: str, job_dict: dict) -> None:
    """
    Save a job object in the Redis database.
    
    Args:
        jid (str): The job ID.
        job_dict (dict): The job object description.
    """
    jdb.set(jid, json.dumps(job_dict))
    logging.info(f"Job {jid} saved to Redis database")
    return

def _queue_job(jid: str) -> None:
    """
    Add a job to the redis queue.
    
    Args:
        jid (str): The job ID.
    """
    q.put(jid)
    logging.info(f"Job {jid} added to the queue")
    return

def add_job(bin_size: float, status: str = "submitted") -> dict:
    """
    Add a job to the redis queue.
    
    Args:
        start (int): The start value for the job.
        end (int): The end value for the job.
        status (str): The status of the job (default: "submitted").

    Returns:
        dict: The job object description.
    """
    jid = _generate_jid()
    job_dict = _instantiate_job(jid, status, float(bin_size))
    _save_job(jid, job_dict)
    _queue_job(jid)
    logging.info(f"Job {jid} added with bin_size={bin_size}, status={status}")
    return job_dict

def get_job_by_id(jid: str) -> dict:
    """
    Return job dictionary given jid
    
    Args:
        jid (str): The job ID.

    Returns:
        dict: The job object description.
    """
    return json.loads(jdb.get(jid))

def update_job_status(jid: str, status: str) -> None:
    """
    Update the status of job with job id `jid` to status `status`.
    
    Args:
        jid (str): The job ID.
        status (str): The new status of the job.
    """
    job_dict = get_job_by_id(jid)
    if job_dict:
        job_dict['status'] = status
        _save_job(jid, job_dict)
        logging.info(f"Updated job {jid} status to {status}")
    else:
        logging.warning(f"Job {jid} not found in database")
        raise Exception()
