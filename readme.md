# Introduction

Application connects the Chirpstack application server to the ie-databus available on the siematic edge device. The application reads the configurations from the application server (over and api connection) and dynamically creates the appropriate read and write topics for the configured devices.

## MQTT Topics

MQTT_DATA_READ_TOPIC:"ie/d/j/simatic/v1/chirpstack/dp/r/{{Lora Application Name}}/{{Lora Device Name}}"
MQTT_DATA_WRITE_TOPIC:"ie/d/j/simatic/v1/chirpstack/dp/w/{{Lora Application Name}}/{{Lora Device Name}}"

The chirpstack application server, postgresql database and a redis server are pre-packaged with the application. Postgresql database and redis server are required by the chirpstack application and network server for functioning. See the docker compose file and the configuration files for details of the available configurations and credentials.

## Application versions

    Chirpstack v4
    Python v3.10.6

## File structure

The application has the following folder structure:

    chirpstack-connector
        |-->cfg-data
        |-->docs
        |-->logs
        |-->src

## Source

The source software including all the modules are available in /src folder. The entry point for the application is /src/chirpstack-connector.py.

## Configurations

Available configurations for the application are defined in the **config.json** file located in /cfg-data folder.

## Globals

The global variables used in the application are defined and updated (based on the configration file) in /src/globals.py.

## MQTT Client

MqttClient Class optimized for the ie-databus and chirpstack-connector is defined in /src/mqtt_client.py file.

## Chirpstack Client

ChirpstackClient class for the chirpstack v4 is defined in /src/chipstack_client.py

## Usage

1. Create chirpstack server instance
2. Update the configuration file **config.json**
3. run the chirpstack-connector.py
