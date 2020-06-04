# -*- coding:utf-8 -*-
from PythonMiddleware.notify import Notify
from PythonMiddleware.graphene import Graphene
from PythonMiddleware.storage import configStorage
from PythonMiddleware.instance import set_shared_graphene_instance

import time
import json
import string
import hashlib
import random
import datetime
from logger import logger
from threading import Thread, Lock
from weather_api import query_live_weather
from config import register, sdk_config

gph = Graphene(node=sdk_config["node_address"], blocking=True)
set_shared_graphene_instance(gph)
count = 0

def random_uppercases(n):
    return ''.join([random.choice(string.ascii_uppercase) for i in range(n)])

def random_lowercases(n):
    return ''.join([random.choice(string.ascii_lowercase) for i in range(n)])

def get_block_num_from_id(block_id):
    return int(block_id[0:8], 16)

def create_file(filename, content, owner):
    try:
        response = gph.create_file(filename=filename, content=content, account=owner)
        logger.debug(response)
    except Exception as e:
        logger.error('file:{}, content {}, account: {}, error: {}'.format(
            filename, content, owner, repr(e)))
        return None, False
    return response, True

def init_wallet():
    try:
        if not gph.wallet.created():
            gph.newWallet(sdk_config["wallet_password"])
        logger.info("wallet create status: {}".format(gph.wallet.created()))

        if gph.wallet.locked():
            gph.wallet.unlock(sdk_config["wallet_password"])
        logger.info("wallet lock status: {}".format(gph.wallet.locked()))

        if gph.wallet.getPrivateKeyForPublicKey(register["public_key"]) is None:
            logger.info("import private key into wallet. public key: {}".format(
                register["public_key"]))
            gph.wallet.addPrivateKey(register["private_key"])

        logger.info("account id: {}, public key: {}".format(
            gph.wallet.getAccountFromPublicKey(register["public_key"]),
            register["public_key"]))

        configStorage["default_prefix"] = gph.rpc.chain_params["prefix"]
        configStorage["default_account"] = register["name"]
    except Exception as e:
        logger.error("init sdk wallet exception. {}".format(repr(e)))

def get_city_weather():
    city = 110100 # beijing
    return query_live_weather(city)

def weather_data_into_chain():
    weather_data, status = get_city_weather()
    if not status:
        return
    reporttime = weather_data["reporttime"]
    file_time = reporttime.replace("-", "")
    file_time = file_time.replace(" ", "")
    file_time = file_time.replace(":", "")
    filename = "wbj-{}".format(file_time)
    filename = "{}-{}".format(random_lowercases(3), file_time) # for test
    content = str(weather_data)
    logger.info("filename: {}, content: {}".format(filename, content))
    res, status = create_file(filename, content, register["name"])
    if status:
        logger.info("tx_id: {}".format(res["trx_id"]))

def weather_data_function():
    global count
    while True:
        count += 1
        logger.info(">>> weather update count: {}".format(count))
        weather_data_into_chain()
        # time.sleep(15*60*1) # 15分钟更新一次
        time.sleep(10)

def init():
    init_wallet()

def listen_event():
    def on_block_callback(recv_block_id):
        block_num = get_block_num_from_id(recv_block_id)
        logger.info("listen recv block id: {}".format(recv_block_id))
        block = gph.rpc.get_block_by_id(recv_block_id)
        pre_block_num = get_block_num_from_id(block["previous"])
        logger.info(">>> get_block_by_id {}\n{}\nblock_num:{} --> {}\n".format(recv_block_id, block, pre_block_num, block_num))

        if block_num == pre_block_num+1:
            try:
                # block = gph.rpc.get_block(block_num)
                witness_obj = gph.rpc.get_object(block['witness'])
                witness_account_obj = gph.rpc.get_object(witness_obj['witness_account'])
            except Exception as e:
                logger.error('get_object exception. block {}, error {}'.format(block_num, repr(e)))
            block_time = block['timestamp']
            transactions = block["transactions"]
            witness_sign = block['witness_signature']
            trx_total = 0
            ops_total = 0
            transactions_id = []
            if transactions:
                trx_total = len(transactions)
                for trx in transactions:
                    transactions_id.append(trx[0])
                    ops_total += len(trx[1]["operations"])
            block_data = {
                "block_num": block_num,
                "time": block_time,
                "witness_id": witness_obj["id"],
                "witness_account_id": witness_account_obj['id'],
                "witness_account_name":witness_account_obj["name"],
                "witness_sign": witness_sign,
                "transactions_total": trx_total,
                "transactions_id": transactions_id,
                "operations_total": ops_total
            }
            print("block_data: {}".format(block_data))

    def on_object_callback(object):
        logger.info("recv object: {}".format(object))
        try:
            if object["file_owner"] != register["id"]:
                return
        except Exception as e:
            logger.error('exception {}'.format(repr(e)))

    notify = Notify(
        # objects = ["1.18.x", "2.1.0", "1.11.x"],
        objects = ["1.18.x"],
        on_object = on_object_callback,
        # on_block = on_block_callback,
        graphene_instance = gph 
    )
    notify.listen() # 启动监听服务

if __name__ == '__main__':
    init()
    thread_listen = Thread(target=listen_event)
    thread_listen.start()

    thread_weather_data = Thread(target=weather_data_function)
    thread_weather_data.start()


