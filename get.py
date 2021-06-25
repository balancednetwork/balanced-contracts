import os
import json
import logging
import requests

import pandas as pd
from time import sleep
from typing import List
from logging import Logger
from functools import wraps
from threading import Timer

from iconsdk.exception import JSONRPCException
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.wallet.wallet import KeyWallet
from iconsdk.builder.transaction_builder import CallTransactionBuilder
from iconsdk.signed_transaction import SignedTransaction

score_address = "cxf61cd5a45dc9f91c15aa65831a30a90d59a09619"
MIN_SNAP_ID = 2
MAX_SNAP_ID = 60
BULK_LIMIT = 100

icon_url = "https://ctz.solidwallet.io"
icon_nid = 1
# wallet_key = bytes(os.environ["wallet_key"], "utf8")


logging.basicConfig(filename="./logs.log", level=logging.INFO, format="%(asctime)s-%(name)s-%(levelname)s-%(message)s")
with open("keystores/balanced_test.pwd", "r") as f:
    key_data = f.read()
wallet = KeyWallet.load("keystores/balanced_test.json", key_data)
icon_service = IconService(HTTPProvider(icon_url, 3))


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


def retry(exception_to_check: Exception or tuple, tries: int = 10, delay: int = 1, back_off: int = 2,
          logger: Logger = None):
    """
    Retry calling the decorated function using an exponential backoff.
    https://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: https://wiki.python.org/moin/PythonDecoratorLibrary#Retry
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
                except exception_to_check:
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


def extract_data_from_api() -> None:
    """
    Extracts data from API and stores the data based on snapshot id

    Each snapshot id data is stored into a single directory identified by the id.
    Individual data is store into individual_*.tsv partitioned to store BULK LIMIT records.
    Information related to total info of a day is store in total.json.

    If no data is returned from API, no action is taken for that snapshot id.
    If the data has already been downloaded, the data will not be re-downloaded.
    :return: None
    """

    df_fix = pd.read_csv("./data_fix.tsv", sep="\t", dtype={"day": int}).set_index("day")
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

        _fix_record = df_fix[df_fix.index == snap_id]
        fix_flag = len(_fix_record)
        if fix_flag:
            df = pd.concat([df, _fix_record])
            for _, row in _fix_record.iterrows():
                logging.info(f"Added {row['address']} to day {snap_id}")

        for file_idx, idx in enumerate(range(0, len(df), BULK_LIMIT)):
            df.iloc[idx: min(idx + BULK_LIMIT, len(df))].to_csv(
                f"./data/{snap_id}/individual_{file_idx}.tsv", sep="\t", index=False)
        del response["accounts"]
        with open(f"./data/{snap_id}/total.json", "w") as file:
            if fix_flag:
                fix_amount = sum([int(i, 16) for i in _fix_record["stake_amount"]])
                _initial = response["total_staked_amount"]
                _after = hex(fix_amount + int(_initial, 16))
                response["total_staked_amount"] = _after
                response["total_stakers"] += len(_fix_record)
                logging.info(f"Added {fix_amount} ({len(_fix_record)} records.) Initial:{_initial} After:{_after}")
            json.dump(response, file)


@retry(JSONRPCException)
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
    logging.info(f"Transaction {tx_hash} is successful")


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
    logging.info(f"Transaction {tx_hash} is successful")


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
                if len(data) == 0:
                    raise
                call_individual_score(data)
                logging.info(f"Loading {csv_file_path}")
                os.rename(csv_file_path, csv_file_path + "-done")
            successful_dir.append(dir_name)
    except BaseException as e:
        logging.error(f"Error sending individual file: {individual_file}, Exception: {e}")
    logging.info(f"Successful days: {len(successful_dir)}")
    split_dirs = [successful_dir[i:i + BULK_LIMIT] for i in range(0, len(successful_dir) + 1, BULK_LIMIT)]
    for split_dir in split_dirs:
        logging.info(f"Score call [total]: {split_dir}")
        data = [json.load(open(f"./data/{_dir}/total.json")) for _dir in split_dir
                if os.path.exists(f"./data/{_dir}/total.json")]
        data = [{"amount": j["total_staked_amount"], "day": j["snapshot_id"]} for j in data]
        call_total_score(data)
        for _dir in split_dir:
            if os.path.exists(f"././data/{_dir}/total.json"):
                os.rename(f"./data/{_dir}/total.json", f"./data/{_dir}/total.json" + "-done")
            logging.info(f"./data/{_dir}/total.json")


if __name__ == "__main__":
    # extract_data_from_api()
    send_to_score()
