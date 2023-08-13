import logging
import json

#########################################################################
# define module constants                                               #
#########################################################################
CONFIG_FILE = "../cfg-data/config.json"
LOG_LEVEL = logging.DEBUG
LOG_FILE = "../logs/chirpstack-connector.log"

##########################################################################
#  define a python logger to be used in the app                          #
##########################################################################
logger = logging.getLogger('chirpstack-connector')
logger.setLevel(LOG_LEVEL)
# define handlers to write messages to the log file and the console
file_handler = logging.FileHandler(LOG_FILE) # type: ignore
console_handler = logging.StreamHandler()
# define and set the format for the log messages
formatter = logging.Formatter('%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# add the defined handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

##########################################################################
# define the global variables used in the app
#########################################################################
#constants
global APP_NAME     #Application name
APP_NAME = "chirpstack-connector"

#dynamically update globals
global DEVICES      #List of lorawan Devices - class defined in chirpstack_client.py - updated from the chirpstack server
DEVICES = []
global APPLICATIONS  #List of lorawan applications - class defined in chirpstack_client.py - updated from the chirpstack server
APPLICATIONS = []

#configurable globals
global CPSTACK_SERVER
global CPSTACK_PORT
global CPSTACK_TENANT_ID
global CPSTACK_API_KEY
global MQTT_SERVER
global MQTT_PORT
global MQTT_USER
global MQTT_PASSWORD
global MQTT_CLIENT_ID
global MQTT_METADATA_TOPIC
global MQTT_STATUS_TOPIC
global MQTT_DATA_WRITE_TOPIC
global MQTT_DATA_READ_TOPIC

##########################################################################
#   read the file called config.json in /cfg-data 
#   and use the configurations to initialise the global variables 
#   else set to default values
##########################################################################
logger.info(f"reading config parameters from {CONFIG_FILE}")

try:
    with open(CONFIG_FILE, 'r') as file:
        config_data = json.load(file)
    CPSTACK_SERVER=config_data["CPSTACK_SERVER"]
    CPSTACK_PORT = config_data["CPSTACK_PORT"]
    CPSTACK_TENANT_ID = config_data["CPSTACK_TENANT_ID"]
    CPSTACK_API_KEY = config_data["CPSTACK_API_KEY"]
    MQTT_SERVER = config_data["MQTT_SERVER"]
    MQTT_PORT = config_data["MQTT_PORT"]
    MQTT_USER = config_data["MQTT_USER"]
    MQTT_PASSWORD = config_data["MQTT_PASSWORD"]
    MQTT_CLIENT_ID = config_data["MQTT_CLIENT_ID"]
    MQTT_METADATA_TOPIC = config_data["MQTT_METADATA_TOPIC"]
    MQTT_STATUS_TOPIC = config_data["MQTT_STATUS_TOPIC"]
    MQTT_DATA_WRITE_TOPIC = config_data["MQTT_DATA_WRITE_TOPIC"]
    MQTT_DATA_READ_TOPIC = config_data["MQTT_DATA_READ_TOPIC"]
    logger.info("configuration data read - successful")
except Exception as e:
    logger.error(f"failed to read all the parameters from configuration file excpetion raised: {e}")
    logger.info("using default values:")
    CPSTACK_SERVER="chirpstack"
    CPSTACK_PORT = 8080
    CPSTACK_TENANT_ID = ""
    CPSTACK_API_KEY = ""
    MQTT_SERVER = "mosquitto"
    MQTT_PORT = 1883
    MQTT_USER = ""
    MQTT_PASSWORD = ""
    MQTT_CLIENT_ID = "chirpstack-connector",
    MQTT_METADATA_TOPIC = "ie/m/j/simatic/v1/chirpstack/dp"
    MQTT_STATUS_TOPIC = "ie/s/j/simatic/v1/chirpstack/status"
    MQTT_DATA_WRITE_TOPIC = "ie/d/j/simatic/v1/chirpstack/dp/r/application01/device01"
    MQTT_DATA_READ_TOPIC = "ie/d/j/simatic/v1/chirpstack/dp/w/application01/device01"

#######################################################################################
#       JSON Definations
#######################################################################################
# global METADATA_JSON
# METADATA_JSON = {}

# global STATUS_JSON
# STATUS_JSON = {
#     "seq":0,
#     "ts":"time_stamp",
#     "connector":{"status": "_status_"},
#     "connections":
#     [
#         {"name": "_connection_name_", "status": "_status_"}
#     ]
# }

# global meta_json_string
# meta_json_string = json.dumps(METADATA_JSON)
# global status_json_string
# status_json_string = json.dumps(STATUS_JSON)