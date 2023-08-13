# Functions that retrun error codes

## Connection Return Codes

0: Connection successful
1: Connection refused – incorrect protocol version
2: Connection refused – invalid client identifier
3: Connection refused – server unavailable
4: Connection refused – bad username or password
5: Connection refused – not authorised
6-255: Currently unused.

## subscribe() error codes

MQTT_ERR_AGAIN = -1
MQTT_ERR_SUCESS = 0
MQTT_ERR_NOMEN = 1
MQTT_ERR_PROTOCOL = 2
MQTT_ERR_INVAL = 3
MQTT_ERR_NO_CONN = 4
MQTT_ERR_CONN_REFUSED = 5
MQTT_ERR_NOT_FOUND = 6
MQTT_ERR_CONN_LOST = 7
MQTT_ERR_TLS = 8
MQTT_ERR_PAYLOAD_SIZE = 9
MQTT_ERR_NOT_SUPPORTED = 10
MQTT_ERR_AUTH = 11
MQTT_ERR_ACL_DENIED = 12
MQTT_ERR_UNKNOWN = 13
MQTT_ERR_ERRNO = 14
MQTT_ERR_QUEUE_SIZE = 15
