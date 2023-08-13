import grpc
from google.protobuf.json_format import MessageToJson
from chirpstack_api import api
import json
from datetime import datetime

from globals import logger
from globals import CPSTACK_SERVER,CPSTACK_PORT,CPSTACK_API_KEY,CPSTACK_TENANT_ID
from globals import MQTT_DATA_WRITE_TOPIC,MQTT_METADATA_TOPIC,MQTT_DATA_READ_TOPIC,MQTT_STATUS_TOPIC

#########################################################################
# Classes required for the chirpstack client                            #
#########################################################################
class LoraDevice:
    eui = ''
    name = ''
    profile_name = ''
    profile_id = ''
    battery_level = ''
    createdAt = ''
    updatedAt = ''
    last_seen = ''
    app_name = ''
    app_id = ''
    number = 0
    tags={}
    meta_data_json = {
                "name":name,
                "topic":MQTT_DATA_READ_TOPIC + '/' + app_name + '/' + name,
                "pubTopic":MQTT_DATA_WRITE_TOPIC + '/' + app_name + '/' + name,
                "publishType":"bulk",
                "dataPointDefinitions":[]
            }

    def __init__(self,device,number,application):
        self.eui = device["devEui"]
        self.name = device["name"]
        self.profile_name = device["deviceProfileName"]
        self.profile_id = device["deviceProfileId"]
        # self.battery_level = device["deviceStatus"]["batteryLevel"]
        self.createdAt = datetime.strptime(device["createdAt"],'%Y-%m-%dT%H:%M:%S.%fZ')
        self.updatedAt = datetime.strptime(device["updatedAt"],'%Y-%m-%dT%H:%M:%S.%fZ')
        # self.last_seen = datetime.strptime(device["lastSeenAt"],'%Y-%m-%dT%H:%M:%S.%fZ')
        self.app_name = application["name"]
        self.app_id = application["id"]
        self.number = number
        self.tags = {}
        self.meta_data_json = {
                "name":self.name,
                "topic":MQTT_DATA_READ_TOPIC + '/' + self.app_name + '/' + self.name,
                "pubTopic":MQTT_DATA_WRITE_TOPIC + '/' + self.app_name + '/' + self.name,
                "publishType":"bulk",
                "dataPointDefinitions":[]
            }

    def update_meta(self):
        chirpstack_client = ChirpstackClient.getInstance()
        dev_profile = chirpstack_client.get_device_profile(self.profile_id)
        tags = dev_profile["deviceProfile"]["tags"]
        self.tags = tags
        #update the meta_data_json based on the device profile tags
        datapoint_definations = []
        id = self.number * 100
        for key,value in tags.items():
            data_point = {
                            "name":str(key),
                            "id":str(id),
                            "dataType":str(value)
                        }
            id = id + 1
            datapoint_definations.append(data_point)
        self.meta_data_json["dataPointDefinitions"] = datapoint_definations
        return True

#########################################################################
# Chirpstack Client Class - Singleton Method Enforced                   #
#########################################################################
class ChirpstackClient:
    _instance = None
    app_list = []
    device_list = []

    def __init__(self):
        raise RuntimeError('Sigelton pattern enforced call getInstance() instead')
    
    @classmethod
    def getInstance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
        return cls._instance


    #function to get all the applications configured in the chirpstack server using grpc and chirpstack v4
    def get_apps(self):
        address = str(CPSTACK_SERVER) + ':' + str(CPSTACK_PORT)
        api_token = CPSTACK_API_KEY
        auth_token = [("authorization", "Bearer %s" % api_token)]
        try:
            channel = grpc.insecure_channel(address)
            api_client = api.ApplicationServiceStub(channel)
            req  = api.ListApplicationsRequest(limit=100,offset=0,tenant_id=CPSTACK_TENANT_ID) # type: ignore
            response = api_client.List(req,metadata=auth_token)
            response_json = MessageToJson(response)
            response_dict = json.loads(response_json)
            if response_dict != {}:
                app_list = response_dict["result"]
            else:
                app_list = {}
            return app_list
        except Exception as e:
            logger.error(f"failed to get application list from chirpstack server - check server address, port, API Token and Tenant ID")
            logger.debug(f"Exception raised while trying to poll application list : {e}")
            return None

    def get_devices(self,app_id):
        address = str(CPSTACK_SERVER) + ':' + str(CPSTACK_PORT)
        api_token = CPSTACK_API_KEY
        auth_token = [("authorization", "Bearer %s" % api_token)]
        try:
            channel = grpc.insecure_channel(address)
            device_api_client = api.DeviceServiceStub(channel)
            auth_token = [("authorization", "Bearer %s" % api_token)]
            req = api.ListDevicesRequest(application_id=app_id,limit=100,offset=0) # type: ignore
            response = device_api_client.List(req, metadata=auth_token)
            response_json = MessageToJson(response)
            response_dict = json.loads(response_json)
            device_list = response_dict["result"]
            return device_list
        except Exception as e:
            logger.error(f"failed to get device list from chirpstack server - check server address, port, API Token and Tenant ID - exception raised: {e}")
            return None

    def get_device_profile(self,profile_id):
        #get device profile from the chirpstack server v4 using grpc
        address = str(CPSTACK_SERVER) + ':' + str(CPSTACK_PORT)
        api_token = CPSTACK_API_KEY
        auth_token = [("authorization", "Bearer %s" % api_token)]
        channel = grpc.insecure_channel(address)
        device_profile_client = api.DeviceProfileServiceStub(channel)
        get_device_profile_request = api.GetDeviceProfileRequest(id=profile_id) # type: ignore
        response = device_profile_client.Get(get_device_profile_request,metadata =auth_token)
        response_json = MessageToJson(response)
        response_dict = json.loads(response_json)
        return response_dict


    


