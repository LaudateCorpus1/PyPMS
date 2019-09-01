"""
Read a PMS5003/PMS7003/PMSA003 sensor and push PM measurements to a MQTT server

Usage:
    pms.mqtt [options]

Options:
    -t, --topic <topic>     MQTT root/topic [default: homie/test]
    -h, --host <host>       MQTT host server [default: test.mosquitto.org]
    -p, --port <port>       MQTT host port [default: 1883]
    -u, --user <username>   MQTT username
    -P, --pass <password>   MQTT password

Other:
    -s, --serial <port>     serial port [default: /dev/ttyUSB0]
    -n, --interval <secs>   seconds to wait between updates [default: 60]
    --help                  display this help and exit

NOTE:
Environment variables take precedence over command line options
- PMS_MQTT_TOPIC    overrides -t, --topic
- PMS_MQTT_HOST     overrides -h, --host
- PMS_MQTT_PORT     overrides -p, --port
- PMS_MQTT_USER     overrides -u, --user
- PMS_MQTT_PASS     overrides -P, ---pass
- PMS_INTERVAL      overrides -n, --interval
- PMS_SERIAL        overrides -s, --serial

NOTE:
Only partial support for Homie v2.0.0 MQTT convention
https://homieiot.github.io/specification/spec-core-v2_0_0/
"""

import os
import time
from typing import Dict, Union, Any
import paho.mqtt.client as mqtt
from . import read, logger


def parse_args(args: Dict[str, str]) -> Dict[str, Any]:
    """Extract options from docopt output"""
    return dict(
        interval=int(os.environ.get("PMS_INTERVAL", args["--interval"])),
        serial=os.environ.get("PMS_SERIAL", args["--serial"]),
        host=os.environ.get("PMS_MQTT_HOST", args["--host"]),
        port=int(os.environ.get("PMS_MQTT_PORT", args["--port"])),
        username=os.environ.get("PMS_MQTT_USER", args["--user"]),
        password=os.environ.get("PMS_MQTT_PASS", args["--pass"]),
        topic=os.environ.get("PMS_MQTT_TOPIC", args["--topic"]),
    )


def setup(
    topic: str, host: str, port: int, username: str, password: str
) -> mqtt.Client:

    c = mqtt.Client(topic)
    if username:
        c.username_pw_set(username, password)
    c.on_connect = lambda client, userdata, flags, rc: client.publish(
        f"{topic}/$online", "true", 1, True
    )
    c.will_set(f"{topic}/$online", "false", 1, True)

    c.connect(host, port, 60)
    c.loop_start()
    return c


def pub(client: mqtt.Client, data: Dict[str, Union[int, str]]) -> None:
    for k, v in data.items():
        client.publish(k, v, 1, True)


def main(interval: int, serial: str, topic: str, **kwargs) -> None:
    client = setup(topic, **kwargs)

    for k, v in [("pm01", "PM1"), ("pm25", "PM2.5"), ("pm10", "PM10")]:
        pub(
            client,
            {
                f"{topic}/{k}/$type": v,
                f"{topic}/{k}/$properties": "sensor,unit,concentration",
                f"{topic}/{k}/sensor": "PMx003",
                f"{topic}/{k}/unit": "ug/m3",
            },
        )

    for pm in read(serial):
        pub(
            client,
            {
                f"{topic}/pm01/concentration": pm.pm01,
                f"{topic}/pm25/concentration": pm.pm25,
                f"{topic}/pm10/concentration": pm.pm10,
            },
        )

        delay = interval - (time.time() - pm.time)
        if delay > 0:
            time.sleep(delay)


if __name__ == "__main__":
    from docopt import docopt

    args = parse_args(docopt(__doc__))
    try:
        main(**args)
    except KeyboardInterrupt:
        print()
    except Exception as e:
        logger.exception(e)
