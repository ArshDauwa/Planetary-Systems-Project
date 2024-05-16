# !/usr/bin/env python3
from flask import Flask, jsonify, request, Response
import requests
import redis
import logging
import json
from jobs import add_job, get_job_by_id, jdb, rd, rdb
import os

# Initialize Flask app and redis client
app = Flask(__name__)

# Configure logging
log_level = os.environ.get('LOG_LEVEL', 'WARNING')
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

# Debugging information
logging.debug(f"Logging level set to: {log_level}")
logging.debug(f"Connecting to Redis at address: {os.environ.get('REDIS_HOST')}")
logging.debug(f"Connecting to Redis at port: {os.environ.get('REDIS_PORT')}")
logging.debug(f"Testing Redis connection...")

try:
    logging.debug("Redis connection successful!" if rd.ping() else "Redis connection failed!")
except:
    logging.error("Error connecting to Redis!")

# Constants
URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select+pl_name,hostname,sy_snum,sy_pnum,discoverymethod,disc_year,disc_facility,pl_orbper,pl_orbsmax,pl_rade,pl_bmasse,pl_orbeccen,st_spectype,st_teff,st_rad,st_mass,st_met,st_logg,rastr,decstr,sy_dist,sy_vmag,sy_kmag,sy_gaiamag+from+pscomppars&format=json"

def fetch_exoplanet_data() -> list:
    """
    Fetch exoplanet data from the specified URL.

    Returns:
        list: A list of dictionaries representing the exoplanet data. Each dictionary
              contains information about an exoplanet system.
    """
    try:
        response = requests.get(URL)
        response.raise_for_status()
        data = response.json()
        logging.debug(f"Received JSON data: {type(data)}")
        logging.debug(f"Number of exoplanets: {len(data)}")
        logging.debug(f"First exoplanet data: {data[0]}")
        return data
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching exoplanet data: {e}")
        raise
    except (IndexError, TypeError) as e:
        logging.error(f"Error accessing data in the JSON response: {e}")
        raise

@app.route('/data', methods=['POST'])
def load_data() -> tuple:
    """
    Load exoplanet data into Redis.

    Returns:
        tuple: A tuple containing the JSON response and HTTP status code.
    """
    try:
        exoplanet_data = fetch_exoplanet_data()
        for exoplanet in exoplanet_data:
            exoplanet_json = json.dumps(exoplanet)
            pl_name = exoplanet.get('pl_name')
            if pl_name:
                rd.set(pl_name, exoplanet_json)
            else:
                logging.warning(f"Skipping exoplanet without 'pl_name': {exoplanet}")
        logging.info("Data loaded into Redis")
        return jsonify({"status": "success", "message": "Data loaded into Redis"}), 200
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/data', methods=['GET'])
def get_data() -> tuple:
    """
    Retrieve exoplanet data from Redis.

    Returns:
        tuple: A tuple containing the JSON response and HTTP status code.
    """
    try:
        keys = rd.keys('*')
        data = []
        for key in keys:
            exoplanet_json = rd.get(key)
            exoplanet_data = json.loads(exoplanet_json)
            data.append(exoplanet_data)
        logging.info("Data retrieved from Redis")
        return jsonify(data), 200
    except Exception as e:
        logging.error(f"Error retrieving data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/data', methods=['DELETE'])
def delete_data() -> tuple:
    """
    Delete exoplanet data from Redis.

    Returns:
        tuple: A tuple containing the JSON response and HTTP status code.
    """
    try:
        rd.flushdb()
        logging.info("Data deleted from Redis")
        return jsonify({"status": "success", "message": "Data deleted from Redis"}), 200
    except Exception as e:
        logging.error(f"Error deleting data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/exoplanets', methods=['GET'])
def get_exoplanet_names() -> tuple:
    """
    Retrieve exoplanets based on query parameters.

    Query Parameters:
        min_radius (float): The minimum radius value in Earth radii.
        max_radius (float): The maximum radius value in Earth radii.
        method (str): The discovery method.
        start_year (int): The start year for discovery.
        end_year (int): The end year for discovery.

    Returns:
        tuple: A tuple containing the JSON response and HTTP status code.
    """
    try:
        min_radius = float(request.args.get('min_radius', 0))
        max_radius = float(request.args.get('max_radius', float('inf')))
        method = request.args.get('method')
        start_year = request.args.get('start_year')
        end_year = request.args.get('end_year')

        if start_year:
            start_year = int(start_year)
        if end_year:
            end_year = int(end_year)

        exoplanet_names = []
        for key in rd.keys():
            exoplanet_json = rd.get(key)
            if exoplanet_json:
                exoplanet = json.loads(exoplanet_json)
                radius = exoplanet.get('pl_rade')
                discovery_method = exoplanet.get('discoverymethod')
                discovery_year = exoplanet.get('disc_year')

                if radius is not None and min_radius <= radius <= max_radius:
                    if method is None or method == discovery_method:
                        if start_year is None or (start_year and discovery_year >= start_year):
                            if end_year is None or (end_year and discovery_year <= end_year):
                                exoplanet_names.append(exoplanet['pl_name'])

        logging.info(f"Retrieved {len(exoplanet_names)} exoplanets")
        return jsonify(exoplanet_names), 200
    except ValueError as e:
        logging.error(f"Invalid query parameter: {e}")
        return jsonify({"status": "error", "message": "Invalid query parameter"}), 400
    except Exception as e:
        logging.error(f"Error retrieving exoplanets: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/exoplanets/<pl_name>', methods=['GET'])
def get_exoplanet_data(pl_name: str) -> tuple:
    """
    Retrieve exoplanet data for a specific exoplanet host name from Redis.

    Args:
        pl_name (str): The name of the exoplanet.

    Returns:
        tuple: A tuple containing the JSON response and HTTP status code.
    """
    try:
        exoplanet_json = rd.get(pl_name)
        if exoplanet_json:
            exoplanet_data = json.loads(exoplanet_json)
            logging.info(f"Exoplanet data retrieved for {pl_name}")
            return jsonify(exoplanet_data), 200
        else:
            logging.warning(f"Exoplanet data not found for {pl_name}")
            return jsonify({"status": "error", "message": "Exoplanet not found"}), 404
    except Exception as e:
        logging.error(f"Error retrieving exoplanet data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/hosts', methods=['GET'])
def get_host_stars() -> tuple:
    """
    Retrieve all unique host stars from the exoplanet data.

    Returns:
        tuple: A tuple containing the JSON response and HTTP status code.
    """
    try:
        host_stars = set()
        for key in rd.keys():
            exoplanet_json = rd.get(key)
            if exoplanet_json:
                exoplanet = json.loads(exoplanet_json)
                hostname = exoplanet.get('hostname')
                if hostname:
                    host_stars.add(hostname)

        host_stars_list = list(host_stars)
        logging.info(f"Retrieved {len(host_stars_list)} unique host stars")
        return jsonify(host_stars_list), 200
    except Exception as e:
        logging.error(f"Error retrieving host stars: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/hosts/<hostname>', methods=['GET'])
def get_planets_by_hostname(hostname: str) -> tuple:
    """
    Retrieve all planets associated with a given host star.

    Args:
        hostname (str): The name of the host star.

    Returns:
        tuple: A tuple containing the JSON response and HTTP status code.
    """
    try:
        exoplanet_names = []
        for key in rd.keys():
            exoplanet_json = rd.get(key)
            if exoplanet_json:
                exoplanet = json.loads(exoplanet_json)
                if exoplanet.get('hostname') == hostname:
                    exoplanet_names.append(exoplanet['pl_name'])

        if exoplanet_names:
            host_data = {
                'hostname': hostname,
                'num_planets': len(exoplanet_names),
                'planets': exoplanet_names
            }
            logging.info(f"Retrieved {len(exoplanet_names)} planets for host star {hostname}")
            return jsonify(host_data), 200
        else:
            logging.warning(f"No planets found for host star {hostname}")
            return jsonify({"status": "error", "message": "No planets found for the specified host star"}), 404
    except Exception as e:
        logging.error(f"Error retrieving planets by hostname: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/facilities', methods=['GET'])
def get_facilities() -> tuple:
    """
    Retrieve all unique discovery facilities.

    Returns:
        tuple: A tuple containing the JSON response and HTTP status code.
    """
    try:
        facilities = set()
        for key in rd.keys():
            exoplanet_json = rd.get(key)
            if exoplanet_json:
                exoplanet = json.loads(exoplanet_json)
                facility = exoplanet.get('disc_facility')
                if facility:
                    facilities.add(facility)

        facilities_list = list(facilities)
        logging.info(f"Retrieved {len(facilities_list)} unique discovery facilities")
        return jsonify(facilities_list), 200
    except Exception as e:
        logging.error(f"Error retrieving discovery facilities: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/facilities/<facility_name>', methods=['GET'])
def get_planets_by_facility(facility_name: str) -> tuple:
    """
    Retrieve all planets discovered by a specific facility.

    Args:
        facility_name (str): The name of the discovery facility.

    Returns:
        tuple: A tuple containing the JSON response and HTTP status code.
    """
    try:
        exoplanet_names = []
        for key in rd.keys():
            exoplanet_json = rd.get(key)
            if exoplanet_json:
                exoplanet = json.loads(exoplanet_json)
                facility = exoplanet.get('disc_facility')
                if facility == facility_name:
                    exoplanet_names.append(exoplanet['pl_name'])

        logging.info(f"Retrieved {len(exoplanet_names)} exoplanets discovered by {facility_name}")
        return jsonify(exoplanet_names), 200
    except Exception as e:
        logging.error(f"Error retrieving exoplanets by facility: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/jobs', methods=['POST'])
def submit_route() -> tuple:
    """
    Submit a job to plot the histogram of planet size distribution.

    Returns:
        tuple: A tuple containing the JSON response and HTTP status code.
    """
    data = request.get_json()
    logging.debug(f"Received JSON data: {data}")
    bin_size = data.get('bin_size', 1.0)  # Default bin size is 1.0
    job_dict = add_job(bin_size)
    logging.debug(f"Job added: {job_dict}")
    return job_dict, 200

@app.route('/jobs', methods=['GET'])
def get_job_ids() -> tuple:
    """
    Retrieve job IDs from the job queue.

    Returns:
        tuple: A tuple containing the JSON response and HTTP status code.
    """
    job_ids = jdb.keys("*")
    job_ids = [job_id.decode('utf-8') for job_id in job_ids]
    logging.debug(f"Retrieved job IDs: {job_ids}")
    return jsonify(job_ids), 200

@app.route('/jobs/<jobid>', methods=['GET'])
def get_job(jobid: str) -> dict:
    """
    Retrieve a job by its ID.

    Args:
        jobid (str): The ID of the job.

    Returns:
        dict: The job dictionary.
    """
    return get_job_by_id(jobid)

@app.route('/results/<jobid>', methods=['GET'])
def get_result(jobid: str) -> tuple:
    """
    Retrieve the result of a job by its ID.

    Args:
        jobid (str): The ID of the job.

    Returns:
        tuple: A tuple containing the JSON response and HTTP status code.

    Example:
        curl -X GET -o histogram.png http://localhost:5000/results/<jobid>
    """
    try:
        job = get_job_by_id(jobid)
        if job:
            job_status = job['status']
            if job_status == 'complete':
                plot_data = rdb.get(jobid)
                if plot_data:
                    return Response(plot_data, mimetype='image/png'), 200
                else:
                    return jsonify({"status": "error", "message": "Plot data not found"}), 404
            elif job_status == 'failed':
                return jsonify({"status": "error", "message": "Job failed"}), 500
            else:
                return jsonify({"status": "pending", "message": "Job is still in progress"}), 202
        else:
            return jsonify({"status": "error", "message": "Job not found"}), 404
    except Exception as e:
        logging.error(f"Error retrieving result for job {jobid}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/help', methods=['GET'])
def show_routes() -> tuple:
    """
    Display information about all the routes in the Flask application.

    Returns:
        tuple: A tuple containing the JSON response and HTTP status code.
    """
    routes = {}
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            doc = app.view_functions[rule.endpoint].__doc__
            doc = ' '.join(doc.split()) if doc else ""
            routes[str(rule)] = {
                'methods': ','.join(rule.methods),
                'doc': doc,
            }
    return jsonify(routes), 200
    """
    Display information about all the routes in the Flask application.

    Returns:
        tuple: A tuple containing the JSON response and HTTP status code.
    """
    routes = {}
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            doc = app.view_functions[rule.endpoint].__doc__
            doc = ' '.join(doc.split()) if doc else ""
            routes[str(rule)] = {
                'methods': ','.join(rule.methods),
                'doc': doc,
            }
    return jsonify(routes), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
