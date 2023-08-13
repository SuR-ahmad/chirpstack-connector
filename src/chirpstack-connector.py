#import required 3rd party modules
import sys
import json                         # storing and exchanging data via JSON file
from datetime import datetime       # for current timestamp
import time                         # for sleep function
import logging                      # python logging module 
import random

#import functions and modules used in the app
from globals import logger
from globals import APP_NAME,CPSTACK_SERVER,CPSTACK_PORT,CPSTACK_API_KEY,MQTT_SERVER,MQTT_PORT,MQTT_USER,MQTT_PASSWORD,MQTT_METADATA_TOPIC,MQTT_DATA_READ_TOPIC,MQTT_DATA_WRITE_TOPIC,MQTT_STATUS_TOPIC
from globals import DEVICES, APPLICATIONS

from mqtt_client import MqttClient
from chirpstack_client import ChirpstackClient, LoraDevice

############################################################################################################
# chirpstack-connector:
# uses the Paho MQTT client to create a connection the ie-databus. 
# Polls the chirpstack server at regular intervals to get details for available applications and devices
############################################################################################################
# Function to check is the there is any difference between the existing instance of a device and the data polled from
# the chirpstack server
def device_updated(existing,new):
    chirpstack_client = ChirpstackClient.getInstance()
    new_updatedAt = datetime.strptime(new["updatedAt"],'%Y-%m-%dT%H:%M:%S.%fZ')
    new_device_profile = chirpstack_client.get_device_profile(new["deviceProfileId"])
    if new_updatedAt != existing.updatedAt or new_device_profile["deviceProfile"]["tags"] != existing.tags:
        return True
    else: 
        return False

#Function to poll all devices available in the chirpstack server and update the
#connection status for the application depending on if the devices were successfully polled
def update_devices(app_list):
    status_connections = []
    connection_status = {}
    device_list_changed = False
    devices_list = DEVICES
    chirpstack_client = ChirpstackClient.getInstance()
    for app in app_list:
        app_device_list = chirpstack_client.get_devices(app["id"])
        # logger.debug(f'{app["name"]} - Application Device List{app_device_list}')
        connection_status = {"name": app["name"], "status": "good"}
        if app_device_list is not None:
            for dev_number,device in enumerate(app_device_list):
                # find the devices in the locally stored list of devices where devEui is equal to the polled device eui
                result = [dev for dev in devices_list if dev.eui == device["devEui"]]

                # if the result is an empty list existing device does not exist else get the first record
                if not result: existing_dev =None 
                else: existing_dev = result[0]

                if existing_dev is None:
                    # If device doesn't exist (None) create it
                    logger.debug(f'Adding a new devive to {app["name"]} : {device}')
                    new_device = LoraDevice(device,dev_number,app)
                    new_device.update_meta()
                    devices_list.append(new_device)
                    logger.info(f'New Device: device Name: {new_device.name} device Eui: {new_device.eui} updated: {new_device.updatedAt}')
                    device_list_changed = True

                elif device_updated(existing_dev,device):
                    logger.debug(f'{device["name"]} found but it has been updated since last checked - updating the device record')
                    # If device exists but the updatedAt or the tags in device profile have changed update the device
                    existing_dev.eui = device["devEui"]
                    existing_dev.name = device["name"]
                    existing_dev.profile_name = device["deviceProfileName"]
                    existing_dev.profile_id = device["deviceProfileId"]
                    existing_dev.battery_level = device["deviceStatus"]["batteryLevel"]
                    existing_dev.createdAt = datetime.strptime(device["createdAt"],'%Y-%m-%dT%H:%M:%S.%fZ')
                    existing_dev.updatedAt = datetime.strptime(device["updatedAt"],'%Y-%m-%dT%H:%M:%S.%fZ')
                    existing_dev.last_seen = datetime.strptime(device["lastSeenAt"],'%Y-%m-%dT%H:%M:%S.%fZ')
                    existing_dev.app_name = app["name"]
                    existing_dev.app_id = app["id"]
                    existing_dev.meta_data_json = {
                            "name":existing_dev.name,
                            "topic":MQTT_DATA_READ_TOPIC + '/' + existing_dev.app_name + '/' + existing_dev.name,
                            "pubTopic":MQTT_DATA_WRITE_TOPIC + '/' + existing_dev.app_name + '/' + existing_dev.name,
                            "publishType":"bulk",
                            "dataPointDefinitions":[]
                        }
                    existing_dev.update_meta()
                    device_list_changed = True
                    logger.info(f'Device Updated: Name: {existing_dev.name} Eui: {existing_dev.eui} updated {existing_dev.updatedAt}')
        elif app_device_list is None:
            connection_status = {"name": app["name"], "status": "good"}
    status_connections.append(connection_status)
    return device_list_changed, devices_list,status_connections
              
def update_meta_json(app_list,device_list,old_meta):
    meta_json = old_meta
    meta_json["seq"] = meta_json["seq"] + 1
    meta_json["connections"] = []
    #generate 9 digit random number
    meta_json["hashVersion"] = random.randint(100000000, 999999999)
    for app in app_list:
        connection_meta = {
            "name":app["name"],
            "type":"loraWan",
            "dataPoints": []
        }
        for device in device_list:
            if device.app_id == app["id"]:
                connection_meta["dataPoints"].append(device.meta_data_json)
        meta_json["connections"].append(connection_meta)
    return meta_json

def main():
    logger.info(f'Starting {APP_NAME}')
    logger.info(f"CPSTACK_SERVER : {CPSTACK_SERVER}")
    logger.info(f"CPSTACK_PORT : {CPSTACK_PORT}")
    logger.info(f"CPSTACK_API_KEY:{CPSTACK_API_KEY}")
    logger.info(f"MQTT_SERVER:{MQTT_SERVER}")
    logger.info(f"MQTT_PORT:{MQTT_PORT}")
    logger.info(f"MQTT_USER :{MQTT_USER}")
    logger.info(f"MQTT_PASSWORD:{MQTT_PASSWORD}")
    logger.info(f"MQTT_METADATA_TOPIC :{MQTT_METADATA_TOPIC}")
    logger.info(f"MQTT_STATUS_TOPIC : {MQTT_STATUS_TOPIC}")
    logger.info(f"MQTT_DATA_WRITE_TOPIC : {MQTT_DATA_WRITE_TOPIC}")
    logger.info(f"MQTT_DATA_READ_TOPIC : {MQTT_DATA_READ_TOPIC}")

    #Initialise the global variables
    METADATA_JSON = {
        "seq":0,
        "hashVersion":123456789,
        "applicationName":APP_NAME,
        "statustopic":MQTT_STATUS_TOPIC,
        "connections":[]
    }

    STATUS_JSON = {
        "seq":0,
        "ts":"time_stamp",
        "connector":{"status": ""},
        "connections":[]
    }

    APPLICATIONS = []
    DEVICES = []

    meta_data_needs_update = False


    #Create a singleton for the mqttclient - so that it can used globally
    mqttclient = MqttClient.getInstance()
    mqttclient.add_subscription("application/#",1)
    #mqttclient.add_subscription("gateway/#",1)
    mqttclient.start_client()
    logger.info('Waiting for server CONNACK..')
    t=0
    tout=5
    while not mqttclient.connected_flag and t<tout:
        time.sleep(1)
        t=t+1
    if not mqttclient.connected_flag: logger.error('Timeout while waiting to connect..')

    #Create a singelton for chiirpstack client - so that it can used globally
    chirpstack_client = ChirpstackClient.getInstance()

    try:
        while True:
            
            # Check to see if the connection to broker is healthy is not try to reconnect
            if not mqttclient.connected_flag:
                logger.error('mqtt client not connected trying to reconnect...')
                mqttclient.start_client()
                logger.info('Waiting for server CONNACK..')
                t=0
                tout=5

                # wait to get connected to the mqtt broker
                while not mqttclient.connected_flag and t<tout:
                    time.sleep(1)
                    t=t+1
                if not mqttclient.connected_flag: 
                    logger.error('Timeout while waiting to connect - retrying to connect')

            #If broker connection is healthy initiate comms to Chirpstack to get data - no point carrying on if no connection to the broker
            if mqttclient.connected_flag:

                #Get applications available in the chirpstack server and check if anythings changed
                app_list = chirpstack_client.get_apps()
                if app_list == {} : logger.info(f'no application defined for the specified tenant')

                # set device list to none to keep from polling unnecessarily
                device_list = None
                device_list_updated = False

                if app_list is not None and app_list != {} and APPLICATIONS != app_list:

                    # if the polled applist is defferent from the local applist meta data needs updating
                    meta_data_needs_update = True

                    # save the polled applist local for subsequent checks
                    APPLICATIONS = app_list
                    logger.info(f'Application list update from chirpstack server - complete')
                    
                    # if we got an applist even if it is empty the status for the connector is good
                    STATUS_JSON["connector"] = {"status": "good"}
                
                # If we failed to get the applist the connector is not working
                elif app_list is None:
                    device_list = None
                    STATUS_JSON["connector"] = {"status": "bad"}

                # no need to poll devices if there are no  applications configured
                if app_list == {}:
                    STATUS_JSON["connections"] = [{}]
                    status_connections = [{}]
                else:
                    # Get devices from the chirpstack server create new if doesn't exist and update if required.
                    # Update the connection status for each depending on if we can successfully get the devices
                    device_list_updated,device_list,status_connections = update_devices(app_list)
                    STATUS_JSON["connections"] = status_connections

                # if there are devices in the device list and anyone of them has been updated we need to update the meta data
                if device_list is not None and device_list_updated:
                    meta_data_needs_update = True
                    DEVICES = device_list
                    logger.info(f'device list update from chirpstack server - complete')
                
                # If the applications or device have changed since the last check update and publish the metadeta
                if meta_data_needs_update:
                    #Get the updated Meta Data
                    meta_new = update_meta_json(APPLICATIONS,DEVICES,METADATA_JSON)
                    METADATA_JSON = meta_new
                    logger.info(f'Publishing updated Meta Data on {MQTT_METADATA_TOPIC}')
                    mqttclient.mqtt_client.publish(topic=MQTT_METADATA_TOPIC,payload=json.dumps(METADATA_JSON))
                    meta_data_needs_update = False

                # publish the connector status
                now = datetime.now()
                STATUS_JSON["ts"] = now.strftime("%Y-%m-%d %H:%M:%S")
                logger.debug(f'Connector Status: {STATUS_JSON}')
                logger.info(f'Publishing updated Status on {MQTT_STATUS_TOPIC}')
                mqttclient.mqtt_client.publish(topic=MQTT_STATUS_TOPIC,payload=json.dumps(STATUS_JSON))
                mqttclient.mqtt_client.publish(topic=MQTT_METADATA_TOPIC,payload=json.dumps(METADATA_JSON))
                time.sleep(10)

    except KeyboardInterrupt:
        logger.info(f'Keyboard interrupt - closing application {APP_NAME}')

    finally:
        mqttclient.stop_client()
        t=0
        tout=10
        while mqttclient.connected_flag and t<tout:
            time.sleep(1)
            t=t=1
        logger.error('timeout while waiting for a disconnect acknowledge forcing shutdown')
        mqttclient.mqtt_client.loop_stop()


# python specific only run this if the file was called from the main function
if __name__ == "__main__":
    main()