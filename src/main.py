import adafruit_bmp3xx
from adafruit_ltr329_ltr303 import LTR329
import board
import paho.mqtt.client as mqtt
from datetime import datetime
import time
import os
import logging
import sys
import socket
import json
import requests
import re

log = logging.getLogger()
log.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s:%(levelname)s: %(message)s", datefmt="%b %d %Y %H:%M:%S")
handler.setFormatter(formatter)
log.addHandler(handler)

mqtt_host = os.environ['MQTT_HOST']
mqtt_port = os.environ['MQTT_PORT']
mqtt_user = os.environ['MQTT_USER']
mqtt_password = os.environ['MQTT_PASSWORD']

hostname = socket.gethostname()

i2c = board.I2C()

bmp = adafruit_bmp3xx.BMP3XX_I2C(i2c)
ltr329 = LTR329(i2c)

bmp.pressure_oversampling = 8
bmp.temperature_oversampling = 2

state_topic = f"{hostname}/sensor"

airport = "KMSP"

## GET THE SURFACE LEVEL SEA PRESSURE TO SET THE BMP DEVICE
def get_slp_from_metar(airport_code):
    metar_data_url = f"https://aviationweather.gov/cgi-bin/data/metar.php?ids={airport_code.upper()}&hours=0&order=id%2C-obs&sep=true"
    response = requests.get(metar_data_url)
    logging.info(f"METAR URL Request: {response.status_code}")
    response.raise_for_status()

    metar_list = response.text.split()
    logging.info(f"METAR Active Time: {metar_list[1]}")

    for i in metar_list:
        if "SLP" in i:
            try:
                alt_string = re.split(r'(\d+)', i)[1]
            except IndexError:
                new_alt = "9999"
        else:
            new_alt = "9999"

    if int(alt_string[0]) >= 5:
        new_alt = f"9{alt_string}"
    else:
        new_alt = f"10{alt_string}"
    
    new_alt = int(new_alt)

    if new_alt != 9999:
        return float(new_alt)/10.
    else:
        return new_alt


## DEFINE THE HOME ASSISTANT DISCOVERY CONFIG OBJECTS ##
## START WITH PRESSURE/TEMP/ALT, THEN LIGHT, THEN MAG/ACCEL

def register_devices_using_discovery(mqtt_client):
    """Create config objects for HA Discovery."""

    ha_discovery_root = "homeassistant/sensor"

    temp_unique_id = f"{hostname}_temp"
    pressure_unique_id = f"{hostname}_pressure"
    altitude_unique_id = f"{hostname}_altitude"
    report_time_unique_id = f"{hostname}_report_time"
    vis_ir_unique_id = f"{hostname}_vis_ir"
    ir_unique_id = f"{hostname}_ir"
    visible_unique_id = f"{hostname}_visible"
    slp_unique_id = f"{hostname}_surface_level_pressure"


    temp_discovery_topic = f"{ha_discovery_root}/{temp_unique_id}/config"
    pressure_discovery_topic = f"{ha_discovery_root}/{pressure_unique_id}/config"
    alt_discovery_topic = f"{ha_discovery_root}/{altitude_unique_id}/config"
    report_time_discovery_topic = f"{ha_discovery_root}/{report_time_unique_id}/config"
    vis_ir_discovery_topic = f"{ha_discovery_root}/{vis_ir_unique_id}/config"
    ir_discovery_topic = f"{ha_discovery_root}/{ir_unique_id}/config"
    visible_discovery_topic = f"{ha_discovery_root}/{visible_unique_id}/config"
    slp_discovery_topic = f"{ha_discovery_root}/{slp_unique_id}/config"

    device_dict = {
        "identifiers": f"{hostname}_Raspi_Cam_and_Env_Sensors",
        "manufacturer": "RPI Foundation + Adafruit + hahnx117",
        "name": f"Raspberry Pi4 2GB Cam and Env Sensors: {hostname}",
    }

    temp_config_object = {
        "name": "Temperature",
        "unique_id": temp_unique_id,
        "state_topic": state_topic,
        "device_class": "temperature",
        "unit_of_measurement": "°C",
        "value_template": "{{ value_json.payload.temperature | float | round(1) }}",
        "device": device_dict,
    }

    pressure_config_object = {
        "name": "Pressure",
        "unique_id": pressure_unique_id,
        "state_topic": state_topic,
        "device_class": "atmospheric_pressure",
        "unit_of_measurement": "hPa",
        "value_template": "{{ value_json.payload.pressure | float | round(2) }}",
        "device": device_dict,
    }

    altitude_config_object = {
        "name": "Altitude",
        "unique_id": altitude_unique_id,
        "state_topic": state_topic,
        "device_class": "distance",
        "unit_of_measurement": "m",
        "value_template": "{{ value_json.payload.altitude | int }}",
        "device": device_dict,
    }

    report_time_config_object = {
        "name": "Timestamp",
        "unique_id": report_time_unique_id,
        "state_topic": state_topic,
        "device_class": "timestamp",
        "value_template": "{{ value_json.payload.report_time }}",
        "device": device_dict,
    }

    vis_ir_config_object = {
        "name": "Visible + IR Light",
        "unique_id": vis_ir_unique_id,
        "state_topic": state_topic,
        "device_class": "illuminance",
        "unit_of_measurement": "lx",
        "value_template": "{{ value_json.payload.visible_plus_ir }}",
        "device": device_dict,
    }

    ir_config_object = {
        "name": "IR Light",
        "unique_id": ir_unique_id,
        "state_topic": state_topic,
        "device_class": "illuminance",
        "unit_of_measurement": "lx",
        "value_template": "{{ value_json.payload.infrared }}",
        "device": device_dict,
    }

    visible_config_object = {
        "name": "Visible Light",
        "unique_id": visible_unique_id,
        "state_topic": state_topic,
        "device_class": "illuminance",
        "unit_of_measurement": "lx",
        "value_template": "{{ value_json.payload.visible_light }}",
        "device": device_dict,
    }

    surface_level_pressure_config_object = {
        "name": "Surface Level Pressure",
        "unique_id": slp_unique_id,
        "state_topic": state_topic,
        "device_class": "atmospheric_pressure",
        "unit_of_measurement": "hPa",
        "value_template": "{{ value_json.payload.slp | float | round(1) }}",
        "device": device_dict,
    }


    logging.info("Discovery config objects:")
    logging.info(json.dumps(temp_config_object))
    logging.info(json.dumps(pressure_config_object))
    logging.info(json.dumps(altitude_config_object))
    logging.info(json.dumps(report_time_config_object))
    logging.info(json.dumps(vis_ir_config_object))
    logging.info(json.dumps(ir_config_object))
    logging.info(json.dumps(visible_config_object))
    logging.info(json.dumps(surface_level_pressure_config_object))

    try:
        mqtt_client.publish(temp_discovery_topic, json.dumps(temp_config_object), qos=1, retain=True)
        mqtt_client.publish(pressure_discovery_topic, json.dumps(pressure_config_object), qos=1, retain=True)
        mqtt_client.publish(alt_discovery_topic, json.dumps(altitude_config_object), qos=1, retain=True)
        mqtt_client.publish(report_time_discovery_topic, json.dumps(report_time_config_object), qos=1, retain=True)
        mqtt_client.publish(vis_ir_discovery_topic, json.dumps(vis_ir_config_object), qos=1, retain=True)
        mqtt_client.publish(ir_discovery_topic, json.dumps(ir_config_object), qos=1, retain=True)
        mqtt_client.publish(visible_discovery_topic, json.dumps(visible_config_object), qos=1, retain=True)
        mqtt_client.publish(slp_discovery_topic, json.dumps(surface_level_pressure_config_object), qos=1, retain=True)
    except Exception as e:
        logging.error(e)

client = mqtt.Client()
client.username_pw_set(mqtt_user, mqtt_password)
client.connect(mqtt_host, int(mqtt_port))
client.loop_start()

if __name__ == "__main__":
    while True:
        register_devices_using_discovery(client)

        sea_level_pressure = get_slp_from_metar(airport)
        
        if sea_level_pressure != "9999":
            bmp.sea_level_pressure = sea_level_pressure

        data_dict = {
            "topic": state_topic,
            "payload": {
                "temperature": bmp.temperature,
                "pressure": bmp.pressure,
                "slp": bmp.sea_level_pressure,
                "altitude": bmp.altitude,
                "visible_plus_ir": ltr329.visible_plus_ir_light,
                "infrared": ltr329.ir_light,
                "visible_light": (ltr329.visible_plus_ir_light - ltr329.ir_light),
                "report_time": datetime.now().astimezone().isoformat(),
            },
            "status": "online",
        }

        sensor_payload = json.dumps(data_dict)
        logging.info("sensor_payload:")
        logging.info(sensor_payload)

        client.publish(state_topic, sensor_payload, qos=1, retain=True)

        data_dict = None
        time.sleep(30)


