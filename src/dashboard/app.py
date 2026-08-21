import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from pathlib import Path
from datetime import  datetime


#### TODO: FIX SPLITTING OF INVOICE FOR MOTHER DAUGHTER SCHOOLS

###### Set path for src import
projekt_root = Path(__file__).resolve().parents[2]
sys.path.append(str(projekt_root))

from src.lib import helpers

LOGO = "logo/klapp_logo.png"

###### Read in parquet 
df = pd.read_parquet("../../data/snapshot.parquet")
df_invoice = pd.read_json("../../data/mother_daughter.json")


##### convert datetimes to only display date to remove redundancy
df["created_at"] = df["created_at"].dt.date
df["kuendigungsstatus"] = df["kuendigungsstatus"].dt.date
df["loeschstatus"] = df["loeschstatus"].dt.date
df["invoicing_start_date"] = df["invoicing_start_date"].dt.date
df["invoicing_cancellation_date"] = df["invoicing_cancellation_date"].dt.date
df = df.dropna(axis=0, how="all")

mask = (
    df["name"].isna() & 
    (df["status"] == "Deaktiviert") #&
    # ((df[relevant_cols] == 0).all(axis=1))
)

df = df[~mask]

###### Title page
st.title("Feature-Usage Analyse")

st.logo(LOGO, size="large")

###### Initialize tabs

tab1, tab2, tab3 = st.tabs(["Gesamtübersicht", "Feature-Analyse", "Schule im Detail"], key="active_tab")

###### column handling

historie_col = df.columns[df.columns.str.contains("_historie")]
removed_cols = ["anzahl_aktive_schüler", "anzahl_aktive_lehrer", "anzahl_aktive_eltern"]
spalten_reihenfolge = [
    "name", 
    "created_at", 
    "status",
    "invoicing_start_date",
    "invoicing_cancellation_date", 
    "kuendigungsstatus", 
    "loeschstatus", 
    "joker_tage_aktiviert"] + list(removed_cols) + list(historie_col) 

non_relevant_cols = ["name", "joker_tage_aktiviert", "loeschstatus", "kuendigungsstatus", "status", "created_at"]
relevant_cols = df.columns.difference(non_relevant_cols)

    ###### selectbox mapping timeframes

timeframes = {
    "Letzte 30 Tage": "_30_tage",
    "Letzte 90 Tage": "_90_tage",
    "Letztes Schuljahr": "_letztes_schuljahr",
    "Gesamter Zeitraum": "_historie"
}


with tab1:
# ##### Creat searchbar for school name and plot overview table
    # Set table layout = wide
    st.set_page_config(layout="wide")

    #### set up cols for overview widgets
    col1, col2, col3, col4 = st.columns(4)
    #### col for total active schools
    with col1:
        df_no_deleted = df.drop(columns="loeschstatus")
        st.metric("Total aktive Schulen:", df_no_deleted[df_no_deleted["status"] == "Aktiv"]["name"].count())

    #### col for total active teachers
    with col2:
        st.metric("Total aktive Lehrpersonen", df_no_deleted[df_no_deleted["status"] == "Aktiv"]["anzahl_aktive_lehrer"].sum())

    #### col for total active students
    with col3:
        st.metric("Total aktive Schüler", df_no_deleted[df_no_deleted["status"] == "Aktiv"]["anzahl_aktive_schüler"].sum())

    #### col for total active parents
    with col4:
        st.metric("Total aktive Eltern", df_no_deleted[df_no_deleted["status"] == "Aktiv"]["anzahl_aktive_eltern"].sum())

    #### set session_state for click to tab 3 redirect
    
    merged_col = pd.Index.union(historie_col, non_relevant_cols)
    overview_col = merged_col.union(removed_cols)

    txt_input = st.text_input(label="Suchfeld",  key="Gesamtübersicht")
    filtered = df[df["name"].str.contains(txt_input, case=False)]
    df_cols = filtered[spalten_reihenfolge]
    
    # st.multiselect()
    
    #### logic to set session_state to selected name in overview, if not selected return none so it resets
    event = st.dataframe(
        df_cols, 
        on_select=lambda: helpers.switch_school_uebersicht(df_cols), 
        selection_mode="single-row", 
        hide_index=True, 
        key="Gesamtübersicht_tabelle",
        )

with tab2:

    ###### selectbox init
    selectbox = st.selectbox("Zeitraum:", 
                             ["Letzte 30 Tage", 
                              "Letzte 90 Tage", 
                              "Letztes Schuljahr", "Gesamter Zeitraum"
                              ], key="Feature Analyse")


    searched_suffix = timeframes[selectbox]
    suitable_cols = df.columns[df.columns.str.contains(searched_suffix)]
    searchbox_cols = df[suitable_cols]

    ###### Remove non int cols + Get total sum for overview 
    rest_cols = searchbox_cols.columns.difference(helpers.exception_cols)
    sum_digit_cols = searchbox_cols[rest_cols].sum().to_frame()

    ##### Reset index to avoid double index col for summmed feature chart, remove non important cols

    keep_cols = sum_digit_cols.columns.difference(removed_cols)
    filtered_df = sum_digit_cols[keep_cols]
    
    bar_df_filtered = filtered_df.reset_index()
    bar_df_filtered = bar_df_filtered.rename(
        columns={"index": "feature", 0: "anzahl"}).sort_values("anzahl", ascending=False)

    fig = px.bar(bar_df_filtered, x="feature", y="anzahl", log_y=True, text_auto="0,.0f")
    st.plotly_chart(fig)
    # st.write(bar_df_filtered)

with tab3:
    
    options = [""] + list(df["name"].unique())
    selected_school = st.selectbox("Schule suchen", options, key="Schule im Detail", on_change=helpers.switch_school_dropdown)

    selected_name = st.session_state.get("selected_name")

    if selected_name is None:
        name = df[df["name"] == selected_school]
    else: 
        name = df[df["name"] == st.session_state.get("selected_name")]


    if name.empty:
        st.info("Bitte eine Schule auswählen!")
    else: 
        st.header(name.iloc[0]["name"])
        if name.iloc[0]["status"] == "Aktiv":
            st.success("Aktiv")
        else:
            st.error("Nicht Aktiv")
        # st.write(f"DEBUG: selected_name={st.session_state.get('selected_name')}, name ist leer={name.empty}")
        ##### Initialize columns for widgets
        col1, col2, col3, col4 ,col5 = st.columns(5)

        with col1:
            st.metric("Aktive Lehrer", name.iloc[0]["anzahl_aktive_lehrer"])

        with col2:
            st.metric("Aktive Schüler", name.iloc[0]["anzahl_aktive_schüler"])

        with col3:
            if pd.isna(name.iloc[0]["kuendigungsstatus"]):
                st.metric("Kündigungsstatus", "Nicht Gekündigt")
            else:
                datum = name.iloc[0]["kuendigungsstatus"]
                st.metric("Kündigungsdatum", datum.strftime("%d.%m.%Y"))

        with col4: 
            if pd.isna(name.iloc[0]["loeschstatus"]):
                pass
            else:
                delete_date = name.iloc[0]["loeschstatus"]
                st.metric("Löschdatum", delete_date.strftime("%d.%m.%Y"))


        with col5:
            #### define hit for the json where id's match
            hit = df_invoice[df_invoice["_id"] == name.iloc[0]["_id"]]

            formatted_currency = f"CHF {name.iloc[0]["anzahl_invoices_historie"]:,.2f}".replace(",", "'")
            st.metric("Rechnungsbetrag (Historie)", formatted_currency)

            if hit.empty:
                pass
            else:
                school = None
                if hit.iloc[0]["toechter_details"] is None:
                   school = st.selectbox("Tochterschule von:", ["", hit.iloc[0]["mother_school_name"]], key="mutter_auswahl", on_change=helpers.switch_school_mutter)
                else:   
                    if len(hit["toechter_details"].iloc[0]) == 1:
                        select = ["", hit.iloc[0]["toechter_details"][0]["name"]]
                        school = st.selectbox("Mutterschule von: ", select, key="mutter_auswahl", on_change=helpers.switch_school_mutter)
                    else:
                        select = [""]
                        for objekt in hit["toechter_details"].iloc[0]:
                            select.append(objekt["name"])
                        school = st.selectbox("Mutterschule von: ", select, key="mutter_auswahl", on_change=helpers.switch_school_mutter)

                if school:
                    st.session_state["selected_name"] = school
                    # st.session_state["mutter_auswahl"] = ""
                    # st.write(f"DEBUG: school={school}, selected_name vorher={st.session_state.get('selected_name')}")
                    st.rerun()
                    
        # st.write(type(hit.iloc[0]["toechter_details"][0]["name"]))
        # st.dataframe(df_invoice)
        #### column config for tab2 table to hide non relevant cols
        cols_to_keep = ["created_at", "joker_tage_aktiviert", "invoicing_start_date", "invoicing_cancellation_date"]
        cols_to_drop = name.columns.difference(cols_to_keep)

        #### dict to hide inrelevant cols

        hide_cols = {name: None for name in cols_to_drop}

        st.dataframe(name, hide_index=True, column_config=hide_cols)

        #### convert data from wide format to long format
        long_list_pattern = "_30_tage|_90_tage|_letztes_schuljahr|_historie"
        long_name = name.columns[name.columns.str.contains(long_list_pattern)]
        long_form = pd.melt(name, value_vars=long_name, var_name="column", value_name="Wert")

        #### create suffix mapping for plotting
        suffix_labels = {value: key for key, value in timeframes.items()}

        long_form[["Feature","Zeitraum"]] = long_form["column"].apply(lambda x: pd.Series(helpers.split_cols(x, suffix_labels=suffix_labels)))


        #### sort column order
        right_order = list(suffix_labels.values())

        # st.write(long_form)
        agg_bar_chart = px.bar(long_form, 
                               x="Feature", 
                               y = "Wert", 
                               color="Zeitraum", 
                               barmode="group", 
                               category_orders={"Zeitraum": right_order},
                               text_auto=True)
        
        agg_bar_chart.update_traces(textposition="outside", textfont_size=16, textangle=0)
        st.write(agg_bar_chart)

        st.write(df_invoice)
        # st.write(long_form)