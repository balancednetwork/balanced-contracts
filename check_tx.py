import os
import json
import logging
import pandas as pd
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.builder.call_builder import CallBuilder

START_DAY = 61
END_DAY = 61
ICON_NID = 1
ICON_NETWORK_URL = "https://ctz.solidwallet.io"

icon_service = IconService(HTTPProvider(ICON_NETWORK_URL, 3))
logging.basicConfig(filename="./check_logs.log", level=logging.INFO,
                    format="%(asctime)s-%(name)s-%(levelname)s-%(message)s")


class TestSync:

    @staticmethod
    def verify_individual_tx(row, day):
        tx = CallBuilder(to="cxf61cd5a45dc9f91c15aa65831a30a90d59a09619",
                         method="stakedBalanceOfAt",
                         params={"_account": row["address"], "_day": int(day)}).build()
        tx_result = icon_service.call(tx)
        if row["stake_amount"] != tx_result:
            logging.critical({"_account": row["address"], "_day": int(day)})
            raise Exception({"_account": row["address"], "_day": int(day)})

    @staticmethod
    def verify_total_tx(data):
        tx = CallBuilder(to="cxf61cd5a45dc9f91c15aa65831a30a90d59a09619",
                         method="totalStakedBalanceOfAt",
                         params={"_day": int(data["snapshot_id"])}).build()
        tx_result = icon_service.call(tx)
        if data["total_staked_amount"] != tx_result:
            logging.critical({"_day": int(data["snapshot_id"])})
            raise Exception({"_day": int(data["snapshot_id"])})

    def start(self):
        base_dir = "./data"
        all_days = [int(i) for i in os.listdir(base_dir)]
        sorted(all_days)
        for _dir in all_days:
            if not (START_DAY <= _dir <= END_DAY):
                continue
            _dir = str(_dir)

            # VERIFY SINGLE TX IN A LOOP
            for individual_file in os.listdir(os.path.join(base_dir, _dir)):
                if not (individual_file.startswith("individual_") and individual_file.endswith(".tsv-done")):
                    continue
                file_path = os.path.join(base_dir, _dir, individual_file)
                logging.info(f"Verifying {file_path}")
                df = pd.read_csv(file_path, sep="\t")
                for idx, row in df.iterrows():
                    self.verify_individual_tx(row, _dir)

            # VERIFY TOTAL TX FOR THE DAY
            file_path = os.path.join(base_dir, _dir, "total.json-done")
            logging.info(f"Verifying {file_path}")
            with open(file_path) as file:
                data = json.load(file)
                self.verify_total_tx(data)

            logging.info(f"All data verified for day:{_dir}.")
        logging.info("All data verified.")


if __name__ == "__main__":
    TestSync().start()
