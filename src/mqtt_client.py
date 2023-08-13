import time
import json
from datetime import datetime
import paho.mqtt.client as mqtt     # mqtt client for interacting with the databus

from globals import logger
from globals import APP_NAME,MQTT_SERVER,MQTT_PORT,MQTT_USER,MQTT_PASSWORD,MQTT_CLIENT_ID
# from globals import MQTT_METADATA_TOPIC,MQTT_STATUS_TOPIC,MQTT_DATA_WRITE_TOPIC,MQTT_DATA_READ_TOPIC
from globals import DEVICES

global PUBLISH_SEQ
PUBLISH_SEQ = 0

###################################################################################
#       MQTT CALLBACK FUNCTIONS
###################################################################################
def on_connect(client, userdata, flags, rc):
    mqttclient = MqttClient.getInstance()   #get the mqttclient as a singleton pattern is enforced only one instance is available
    if rc == 0:
        logger.info(f'mqtt client connected to {MQTT_SERVER}')
        mqttclient.connected_flag = True
        client.publish("chirpstack-connector/event","chirpstack-connector app connected")
        mqttclient.update_subscriptions()
    elif rc == 1:
        logger.error(f'mqtt client failed to connect to {MQTT_SERVER} - incorrect protocol version')
        mqttclient.connected_flag = False
    elif rc == 2:
        logger.error(f'mqtt client failed to connect to {MQTT_SERVER} - invalid client identifier')
        mqttclient.connected_flag = False
    elif rc == 3:
        logger.error(f'mqtt client failed to connect to {MQTT_SERVER} - server unavailable')
        mqttclient.connected_flag = False
    elif rc == 4:
        logger.error(f'mqtt client failed to connect to {MQTT_SERVER} - bad username/password')
        mqttclient.connected_flag = False
    elif rc == 5:
        logger.error(f'mqtt client failed to connect to {MQTT_SERVER} - not authorized')
        mqttclient.connected_flag = False
    else:
        logger.error(f'mqtt client failed to connect to {MQTT_SERVER} - Error Code: {rc}')
        mqttclient.connected_flag = False

def on_disconnect(client, userdata, rc):
    mqttclient = MqttClient.getInstance()
    if rc == 0 :
        mqttclient.connected_flag = False
        logger.info(f'mqtt client disconnected from {MQTT_SERVER}')
    elif rc == 1:
        mqttclient.connected_flag = False
        logger.error(f'mqtt client diconnected from server error code: {rc} - incorrect protocol version')
    elif rc == 2:
        mqttclient.connected_flag = False
        logger.error(f'mqtt client diconnected from server error code: {rc} - invalid client identifier')
    elif rc == 3:
        mqttclient.connected_flag = False
        logger.error(f'mqtt client diconnected from server error code: {rc} - server unavailable')
    elif rc == 4:
        mqttclient.connected_flag = False
        logger.error(f'mqtt client diconnected from server error code: {rc} - bad username/password')
    elif rc == 5:
        mqttclient.connected_flag = False
        logger.error(f'mqtt client diconnected from server error code: {rc} - not authorized')
    elif rc == 7:
        mqttclient.connected_flag = False
        logger.error(f'mqtt client diconnected from server error code: {rc}')
    else:
        mqttclient.connected_flag = False
        logger.error(f'mqtt client diconnected from server error code: {rc}')

def on_subscribe(client, userdata, mid, granted_qos):
    mqttclient = MqttClient.getInstance()
    topic = mqttclient.get_topic(mid)
    if topic is not None:
        topic["status"] = 'subscribed'
        logger.info(f'subscribed to: {topic["topic"][0]} mid : {mid} with QoS : {granted_qos[0]}')
    pass

def on_unsubscribe(client, userdata, mid):
    mqttclient = MqttClient.getInstance()
    topic = mqttclient.get_topic(mid)
    if topic is not None:
        topic["status"] = 'unsubscribed'
        logger.info(f'{APP_NAME} unsubscribed from: {mid}')
    pass

def on_message(client,userdata,msg):
    incoming_msgType = type(msg.payload)
    incomingTopic = msg.topic

    # Split the incoming topic and create a dictionary to determine message routing
    topic_elements = incomingTopic.split('/')
    topic_json = {
        'gateway':'',
        'application' : '',
        'device' : '',
        'event' : ''
    }
    for idx,elm in enumerate(topic_elements):
        if elm == 'gateway':
            topic_json["gateway"] = topic_elements[idx+1]
        if elm == 'application':
            topic_json["application"] = topic_elements[idx+1]
        if elm == 'device':
            topic_json["device"] = topic_elements[idx+1]
        if elm == 'event':
            topic_json["event"] = topic_elements[idx+1]

    
    #convert the incoming message to a dict object depending on type
    if incoming_msgType==bytes: #message of type json string
        try:
            json_payload = json.loads(msg.payload.decode('utf-8'))
        except:
            logger.warning(f'unable to decode the incoming message bytes - check that the message format is a json string ')
            logger.debug(f'received payload {msg.payload}')
            json_payload = {}
    elif incoming_msgType==dict:
        json_payload = msg.payload
    else:
        json_payload = {}

    logger.info(f'message received on {incomingTopic}')
    # logger.debug(f'message: {json_payload}')

    # Message is from the gateway
    if topic_json["gateway"] != '':
        pass

    #message for a device:
    if topic_json["device"] != '':
        if topic_json["event"] == 'up':
            msg_time = json_payload['time']
            device_info = json_payload['deviceInfo']
            device_name = device_info['deviceName']
            device_Eui = device_info['devEui']
            msg_object = json_payload['object']
            logger.info(f'message received for device {device_name}-{device_Eui} event type: {topic_json["event"]} msg: {msg_object}')
            userdata["publish_seq"] = userdata["publish_seq"]+1
            publish_message = {
                "seq": userdata["publish_seq"],
                "vals" : []
            }
            now = datetime.now()
            ts = now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            for device in DEVICES:
                # find the device based on the dev_Eui
                if device.eui == device_Eui:
                    # get the publish topic (/r/app/device) for the device
                    publish_topic = device.meta_data_json["topic"]
                    logger.info(f'publishing data to {publish_topic}')

                    for key,value in msg_object.items():
                        for datapoint in device.meta_data_json["dataPointDefinitions"]:
                            # find the datapoint defination for the incoming tag
                            if datapoint["name"] == key:
                                val = {
                                    "id" : datapoint["id"],
                                    "qc" : 3,
                                    "ts" : str(ts),
                                    "val" : value
                                }
                                publish_message["vals"].append(val)
                    client.publish(topic=publish_topic,payload=json.dumps(publish_message))

#########################################################################
# MQTT Client Class - Singleton Method Enforced                         #
#########################################################################
class MqttClient:
    __instance = None
    mqtt_client = mqtt.Client()
    connected_flag = False
    status = 'unknown'
    subscribed_topics=[]

    def __init__(self):
        raise RuntimeError('Sigelton pattern enforced call getInstance() instead')

    @classmethod
    def getInstance(cls):
        if cls.__instance is None:
            cls.__instance = cls.__new__(cls)
            cls.mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_ID,clean_session=True,protocol=4,transport="tcp") #MQTTv3.11 protocol = 4
            cls.mqtt_client.on_connect = on_connect
            cls.mqtt_client.on_disconnect = on_disconnect
            cls.mqtt_client.on_message = on_message
            cls.mqtt_client.on_subscribe = on_subscribe
            cls.mqtt_client.on_unsubscribe = on_unsubscribe
            cls.mqtt_client.user_data_set({'publish_seq':0})
            cls.mqtt_client.loop_start()
            cls.connected_flag = False
            cls.status = 'unknown'
            cls.subscribed_topics=[]
        return cls.__instance

    def start_client(self):
        logger.info(f'Attempting to connect to the broker: {MQTT_SERVER}...')
        try:
            self.mqtt_client.username_pw_set(username=MQTT_USER,password=MQTT_PASSWORD)
            self.mqtt_client.connect(MQTT_SERVER,MQTT_PORT,keepalive=60)
        except Exception as e:
            logger.error(f'failed to start the client exception raised: {e}')
            return False
        
    def stop_client(self):
        logger.info(f'Attempting to gracefully disconnect from broker: {MQTT_SERVER}')
        try:
            self.mqtt_client.disconnect()
            self.mqtt_client.loop_stop()
            return True
        
        except Exception as e:
            logger.error(f'failure while disconnecting exception raised: {e}')
            return False
    
    def add_subscription(self,topic,qos):
        str_topic = str(topic)
        int_qos = int(qos)
        if int_qos < 0 or qos > 3:
            logger.error(f'Error adding {str_topic} allowed values for qos: 0-3')
            return True
        topic = {
            'topic' : (topic,qos),
            'mid': 0,
            'status':'unknown'
        }
        try:
            self.subscribed_topics.append(topic)
            return True
        except:
            logger.error(f'failed to add topic {topic}')
            return False

        
    def update_subscriptions(self):
        for idx,topic in enumerate(self.subscribed_topics):
            result , mid = self.mqtt_client.subscribe(self.subscribed_topics[idx]["topic"])
            self.subscribed_topics[idx]["mid"] = mid
            if result == 0:
                logger.debug(f'subscription request sent: {self.subscribed_topics[idx]["topic"][0]} , messageid:{mid} with Qos: {self.subscribed_topics[idx]["topic"][1]}')
            elif result == 3:
                logger.debug(f'Failed to subscribe to: {self.subscribed_topics[idx]["topic"][0]} , Error: Invalid')
            elif result == 4:
                logger.debug(f'Failed to subscribe to: {self.subscribed_topics[idx]["topic"][0]} , Error: No Connection')
            elif result == 5:
                logger.debug(f'Failed to subscribe to: {self.subscribed_topics[idx]["topic"][0]} , Error: Connection Refused')
            elif result == 6:
                logger.debug(f'Failed to subscribe to: {self.subscribed_topics[idx]["topic"][0]} , Error: Not Found')
            elif result == 7:
                logger.debug(f'Failed to subscribe to: {self.subscribed_topics[idx]["topic"][0]} , Error: Connection Lost')
            elif result == 8:
                logger.debug(f'Failed to subscribe to: {self.subscribed_topics[idx]["topic"][0]} , Error: TLS Error')
            elif result == 9:
                logger.debug(f'Failed to subscribe to: {self.subscribed_topics[idx]["topic"][0]} , Error: Payload Size')
            elif result == 10:
                logger.debug(f'Failed to subscribe to: {self.subscribed_topics[idx]["topic"][0]} , Error: No Supported')
            elif result == 11:
                logger.debug(f'Failed to subscribe to: {self.subscribed_topics[idx]["topic"][0]} , Authetication Error')
            elif result == 12:
                logger.debug(f'Failed to subscribe to: {self.subscribed_topics[idx]["topic"][0]} , Access Control List Denied')
            else:
                logger.debug(f'Failed to subscribe to: {self.subscribed_topics[idx]["topic"][0]} , Error Code:{result} - lookup the error code in the MQTT Error codes list/Subscribe Errors')
            
    def get_topic(self,mid):
        for topic in self.subscribed_topics:
            if topic["mid"] == mid:
                return topic
        return None