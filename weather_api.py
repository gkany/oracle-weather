# -*- coding:utf-8 -*-
import requests 

from config import weather_api
from logger import logger

def query_live_weather(city):
    data = {'key': weather_api["key"], "city": city}
    try: 
        response = requests.post(weather_api["url"], data).json()
        weather_info = dict(response)
        weather = weather_info['lives'][0]
        return weather, True
    except Exception as e:
        logger.error("exception {}".format(repr(e)))
    return "", False
