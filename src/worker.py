from jobs import get_job_by_id, update_job_status, q, rd, rdb
import json
import logging
import os
import matplotlib.pyplot as plt
import io
import numpy as np

# Configure logging
log_level = os.environ.get('LOG_LEVEL', 'WARNING')
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

@q.worker
def do_work(jobid: str) -> None:
    """
    Plot the histogram of planet size distribution based on parameters from a given job ID.

    Args:
        jobid (str): The ID of the job.
    """
    try:
        job = get_job_by_id(jobid)
        bin_size = job['bin_size']
        logging.info(f"Processing job {jobid}")
        update_job_status(jobid, "in progress")

        # Retrieve planet data from Redis
        planet_radii = []
        for key in rd.keys():
            planet_json = rd.get(key)
            planet = json.loads(planet_json)
            radius = planet.get('pl_rade')
            if radius:
                planet_radii.append(radius)

        # Create a new figure
        fig, ax = plt.subplots(figsize=(8, 6))

        # Plot the histogram
        bins = np.arange(0, max(planet_radii) + bin_size, bin_size)
        ax.hist(planet_radii, bins=bins, edgecolor='black')
        ax.set_xlabel('Planet Radius (Earth Radii)')
        ax.set_ylabel('Count')
        ax.set_title('Distribution of Planet Sizes')

        # Save the plot to a bytes buffer
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png')
        buffer.seek(0)

        # Store the plot data in the results database
        rdb.set(jobid, buffer.getvalue())

        # Close the figure to free up memory
        plt.close(fig)

        logging.info(f"Job {jobid} completed")
        update_job_status(jobid, "complete")

    except Exception as e:
        logging.error(f"Error processing job {jobid}: {e}")
        update_job_status(jobid, "failed")

do_work()
