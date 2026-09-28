import pandas as pd
import Feature_pipelines
import Feature_helpers
import pymongo
import os
from dotenv import load_dotenv
# import pyarrow

load_dotenv()

mongo_uri = os.getenv("mongo_uri")
# mongo_uri_local = os.getenv("mongo_uri_local")

try:
    client = pymongo.MongoClient(mongo_uri)
except NameError:
    print("mongo_uri not available, trying mongo_uri_local")
    client=pymongo.MongoClient(mongo_uri_local)

db = client["klapp-prod"]

pipeline_list = Feature_pipelines.pipeline_list
no_id_list = Feature_pipelines.no_id_list

def main():
    pipeline_dfs = []
    no_id = db[no_id_list[0][1]].aggregate(no_id_list[0][0])
    no_id_df = pd.DataFrame(no_id)

    ### create df from pipes, collections and db
    # pipeline_list
    for pipe, collection in pipeline_list:
        df = Feature_helpers.df_creator(db, collection, pipe)
        pipeline_dfs.append(df)

    # invoice_list
    invoice_dfs = list(db["invoices"].aggregate(Feature_pipelines.price_data_pipe))
    df_toechter = pd.DataFrame(invoice_dfs[0]["toechter_zu_mutter"])
    df_mutter = pd.DataFrame(invoice_dfs[0]["mutter_zu_toechter"])

    ### concat df's of invoice
    df_concat = pd.concat([df_toechter, df_mutter], ignore_index=True)

    ### convert ObjectId into str for df_invoice
    df_concat["_id"] = df_concat["_id"].astype(str)

    ### merge newly created df into one
    merged = Feature_helpers.merge_alle(pipeline_dfs, on="_id", how="outer")
    merged["_id"] = merged["_id"].astype(str)
    # merged = merged.drop(columns="_id")

    # merged_invoice = Feature_helpers.merge_alle(invoice_dfs, "_id", how="outer")    
    ### extract non digit columns
    digit_cols = merged.columns.difference(Feature_helpers.exception_cols)

    ### convert digit columns to int
    merged[digit_cols] = merged[digit_cols].fillna(0)
    merged[digit_cols] = merged[digit_cols].astype(int)

    ### convert non standardized datetimes to datetime
    merged["invoicing_start_date"] = pd.to_datetime(merged["invoicing_start_date"], errors="coerce", utc=True)
    merged["invoicing_cancellation_date"] = pd.to_datetime(merged["invoicing_cancellation_date"], errors="coerce", utc=True)
    
    ### generate snapshot + json
    merged.to_parquet("../data/snapshot.parquet", index=False)
    df_concat.to_json("../data/mother_daughter.json")
    no_id_df.to_parquet("../data/class_precentage.parquet")

if __name__ == "__main__":
    main()