import os
import json
import logging
import requests
from time import sleep

import pandas as pd

from iconsdk.exception import JSONRPCException
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.icon_service import IconService
from iconsdk.wallet.wallet import KeyWallet
from iconsdk.builder.transaction_builder import CallTransactionBuilder
from iconsdk.signed_transaction import SignedTransaction
from typing import List
from threading import Timer
from functools import wraps
from time import sleep
from logging import Logger


class RepeatedTimer(object):
    def __init__(self, interval, func, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.result = None
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.result = self.func(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

    def get(self):
        return self.result


def retry(exception_to_check: Exception or tuple, tries: int =10, delay: int =1, back_off: int=2, logger: Logger=None):
    """
    Retry calling the decorated function using an exponential backoff.
    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry
    :param exception_to_check: The exception to check. May be a tuple of exceptions to check
    :param tries: Number of times to try (not retry) before giving up
    :param delay: Initial delay between retries in seconds
    :param back_off: Back_off multiplier e.g. Value of 2 will double the delay each retry
    :param logger: Logger to use. If None, print
    """
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except exception_to_check as e:
                    msg = "Retrying in %d seconds..." % mdelay
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    sleep(mdelay)
                    mtries -= 1
                    mdelay *= back_off
            return f(*args, **kwargs)
        return f_retry  # true decorator
    return deco_retry

score_address = "cx36169736b39f59bf19e8950f6c8fa4bfa18b710a"
MIN_SNAP_ID = 2
MAX_SNAP_ID = 39

icon_url = "https://bicon.net.solidwallet.io"
icon_nid = 3
# wallet_key = bytes(os.environ["wallet_key"], "utf8")

logging.basicConfig(filename="./logs.log", level=logging.INFO, format="%(asctime)s-%(name)s-%(levelname)s-%(message)s")
with open("../contracts-private/keystores/balanced_test.pwd", "r") as f:
    key_data = f.read()
wallet = KeyWallet.load("../contracts-private/keystores/balanced_test.json", key_data)
icon_service = IconService(HTTPProvider(icon_url, 3))


def extract_data_from_api() -> None:
    """
    Extracts data from API and stores the data based on snapshot id

    Each snapshot id data is stored into a single directory identified by the id.
    Individual data is store into individual_*.tsv partitioned to store 50 records.
    Information related to total info of a day is store in total.json.

    If no data is returned from API, no action is taken for that snapshot id.
    If the data has already been downloaded, the data will not be re-downloaded.
    :return: None
    """
    for snap_id in range(MIN_SNAP_ID, MAX_SNAP_ID + 1):
        logging.info(f"Fetching {snap_id}")
        if os.path.exists(f"./data/{snap_id}"):
            logging.error(f"{snap_id} already exists.Ignoring..")
            continue
        response = requests.get(
            f"https://balanced.geometry.io/api/v1/balanced-token/stakers_snapshot?snapshot_id={snap_id}")
        response = response.json()
        if response is None:
            logging.info(f"Null in ID [{snap_id}]")
            continue

        os.makedirs(f"./data/{snap_id}")

        df = pd.DataFrame(response["accounts"]).T
        for file_idx, idx in enumerate(range(0, len(df), 50)):
            df.iloc[idx: min(idx + 50, len(df))].to_csv(f"./data/{snap_id}/individual_{file_idx}.tsv", sep="\t", index=False)
        del response["accounts"]
        with open(f"./data/{snap_id}/total.json", "w") as file:
            json.dump(response, file)


@retry(JSONRPCException, tries=10, delay=1, back_off=2)
def get_tx_result(_tx_hash):
    tx_result = icon_service.get_transaction_result(_tx_hash)
    return tx_result

def call_individual_score(data: List[dict]) -> None:
    """
    Send individual data to score
    :param data:
    :return:
    """
    tx = CallTransactionBuilder(
        from_=wallet.get_address(),
        to=score_address,
        step_limit=10000000,
        nid=icon_nid,
        method="loadBalnStakeSnapshot",
        params={"_data": data}
    ).build()
    signed_tx = SignedTransaction(tx, wallet)
    tx_hash = icon_service.send_transaction(signed_tx)
    logging.info(f"Tx hash:- {tx_hash}")
    sleep(4)
    tx_result = get_tx_result(tx_hash)
    if tx_result["status"] == 0:
        raise
    logging.info(f"Transaction {tx_hash} is sucesful")


def call_total_score(data: List[dict]) -> None:
    """
    Send aggregated data of a day to score
    :param data:
    :return:
    """
    tx = CallTransactionBuilder(
        from_=wallet.get_address(),
        to=score_address,
        step_limit=1000000,
        nid=icon_nid,
        method="loadTotalStakeSnapshot",
        params={"_data": data}
    ).build()
    signed_tx = SignedTransaction(tx, wallet)
    tx_hash = icon_service.send_transaction(signed_tx)
    sleep(4)
    tx_result = get_tx_result(tx_hash)
    logging.info(f"Tx hash:- {tx_hash}")
    if tx_result["status"] == 0:
        raise
    logging.info(f"Transaction {tx_hash} is sucesful")


def send_to_score() -> None:
    """
    Sends downloaded data to score

    Loops over all the downloaded data
    Individual data is sent to Score on daily basis
    All the successful days are stored
    Total daily aggregated data is sent to score after every individual data is sent or individual data sending fails.
    In case of failure of individual data, only days of fully successful individual data transfer is sent.
    Once data is successfully transferred, the data is deleted from local storage.
    :return: None
    """
    dir_names = os.listdir("./data/")
    dir_names = [int(i) for i in dir_names]
    dir_names = sorted(dir_names)
    successful_dir = []
    individual_file = None
    try:
        for dir_name in dir_names:
            for individual_file in os.listdir(f"./data/{dir_name}"):
                # logging.info("")
                if individual_file.endswith("done"):
                    continue
                if individual_file == "total.json":
                    continue
                csv_file_path = f"./data/{dir_name}/{individual_file}"
                logging.info(f"Loading {csv_file_path}")
                df = pd.read_csv(csv_file_path, sep="\t")
                df["day"] = dir_name
                df = df.rename(columns={"stake_amount": "amount"})
                df["amount"] = df["amount"].apply(int, base=16)
                logging.info(f"Loading {csv_file_path}")
                data = df.to_dict("records")
                # print(data)
                if len(data) == 0:
                    raise
                call_individual_score(data)
                logging.info(f"Loading {csv_file_path}")
                # os.remove(csv_file_path)
                os.rename(csv_file_path, csv_file_path + "-done")
            successful_dir.append(dir_name)
    except BaseException as e:
        logging.error(f"Error sending individual file: {individual_file}, Exception: {e}")
    logging.info(f"Successful days: {len(successful_dir)}")
    split_dirs = [successful_dir[i:i + 50] for i in range(0, len(successful_dir) + 1, 50)]
    for split_dir in split_dirs:
        logging.info(f"Score call [total]: {split_dir}")
        data = [json.load(open(f"./data/{_dir}/total.json")) for _dir in split_dir]
        data = [{"amount": j["total_staked_amount"], "day": j["snapshot_id"]} for j in data]
        call_total_score(data)
        for _dir in split_dir:
            os.remove(f"./data/{_dir}/total.json")
            logging.info(f"./data/{_dir}/total.json")


if __name__ == "__main__":
    # extract_data_from_api()
    send_to_score()
