import pandas as pd
import streamlit as st


def df_creator(db, collection: str ,pipe):
    '''Creates dataframes from pymongo queries and returns them.'''
    array = list(db[collection].aggregate(pipe))
    df = pd.DataFrame(array)
    return df

def merger(df_one, df_two, on, how):
    '''Allows to merge two dataframes into one.'''
    merged_df = pd.merge(df_one, df_two, on=on, how=how)
    return merged_df

def merge_alle(dataframes, on, how):
    '''Takes multiple dataframes and merges them, if name-col
    appears multiple times, it just keeps one'''
    result = dataframes[0]
    for df in dataframes[1:]:
        if "name" in df.columns:
            df = df.drop(columns="name")
        result = merger(result, df, on, how)
    return result


def timeframe_fields(pre_fix, conditions, is_money=False, add_anzahl_prefix=True, money_field="$amount"):
    '''Takes prefix and conditions, returns fields for pipeline.py'''
    fields = {}
    anzahl = "anzahl" if add_anzahl_prefix else ""
    if is_money:
        for suffix, condition in conditions.items():
            fieldname = f"{anzahl}_{pre_fix}_{suffix}"
            fields[fieldname] = {"$sum": {"$cond": [condition, money_field, 0]}}
    else:
        for suffix, condition in conditions.items():
            fieldname = f"{anzahl}_{pre_fix}_{suffix}"
            fields[fieldname] = {"$sum": {"$cond": [condition, 1, 0]}}
    return fields


def cond_cat(extra_field, extra_value, pipe_dict):
    '''Creates a dict from 'condition', and appends 'extra_filed' & 'extra_value' to the output name. \n 
    Also compares if they are eq to condition'''
    result = {}
    for suffix, condition in pipe_dict.items():
        result[suffix] =  {"$and": [condition, {"$eq": [f"${extra_field}", extra_value]}  ]}
    return result

def split_cols(col_name, suffix_labels):
    '''Takes in a col name and looks if it ends with the suffix, it then strips everything in front of the suffix and returns the feature and label.'''
    for suffix, label in suffix_labels.items():
        if col_name.endswith(suffix):
            feature = col_name[:-len(suffix)]
            return feature, label
    return col_name, None

def build_pipe_dict(field_name, vor_30_tagen, vor_90_tagen, letztes_schuljahr_start, letztes_schuljahr_ende):
    return {
        "30_tage": {"$gte": [f"${field_name}", vor_30_tagen]},
        "90_tage": {"$gte": [f"${field_name}", vor_90_tagen]},
        "letztes_schuljahr": {
            "$and": [
                {"$gte": [f"${field_name}", letztes_schuljahr_start]},
                {"$lte": [f"${field_name}", letztes_schuljahr_ende]}
            ]
        }
    }


def switch_school_mutter():
    gewaehlt = st.session_state["mutter_auswahl"]
    # st.write(f"DEBUG Callback: gewaehlt={gewaehlt}")
    if gewaehlt:
        st.session_state["selected_name"] = gewaehlt
    st.session_state["mutter_auswahl"] = ""

def switch_school_tab1():
    gewaehlt = st.session_state["Gesamtübersicht"]
    # st.write(f"DEBUG Callback: gewaehlt={gewaehlt}")
    if gewaehlt:
        st.session_state["selected_name"] = gewaehlt

def switch_school_uebersicht(df):
    auswahl = st.session_state["Gesamtübersicht_tabelle"]
    if auswahl["selection"]["rows"]:
        zeilen_index = auswahl["selection"]["rows"][0]
        selected_name = df.iloc[zeilen_index]["name"]
        st.session_state["selected_name"] = selected_name

def switch_school_dropdown():
    selection = st.session_state["Schule im Detail"]
    if selection:
        st.session_state["selected_name"] = selection
    st.session_state["Schule im Detail"] = ""

exception_cols = [
    "_id",
    "name", 
    "joker_tage_aktiviert", 
    "created_at", 
    "loeschstatus", 
    "kuendigungsstatus", 
    "status",
    "invoicing_start_date",
    "invoicing_cancellation_date",
    ]

