'''
Pipelines for data extraction for feature usage analysis.
'''

from src.lib import helpers
from datetime import datetime, timedelta

###########################################################################
HEUTE = datetime.now()
AKTUELLES_SCHULJAHR   = datetime(datetime.now().year, 7, 20)

VOR_30_TAGEN = HEUTE - timedelta(days=30)
VOR_30_TAGEN_PIPE = {"$gte": ["$created_at", VOR_30_TAGEN]}

VOR_90_TAGEN = HEUTE - timedelta(days=90)
VOR_90_TAGEN_PIPE = {"$gte": ["$created_at", VOR_90_TAGEN]}

schuljahresende_dieses_jahr = datetime(HEUTE.year, 7, 20)

if HEUTE > schuljahresende_dieses_jahr:
    LETZTES_SCHULJAHR_START = datetime(HEUTE.year -1 , 8, 1)
    LETZTES_SCHULJAHR_ENDE = datetime(HEUTE.year , 7, 20)
else:
    LETZTES_SCHULJAHR_START = datetime(HEUTE.year -2, 8, 1)
    LETZTES_SCHULJAHR_ENDE = datetime(HEUTE.year -1, 7, 20)

# LETZTES_SCHULJAHR_START = datetime(datetime.now().year - 1, 8, 1)
# LETZTES_SCHULJAHR_ENDE = datetime(datetime.now().year, 7, 20)
LETZTES_SCHULJAHR_PIPE = {"$and": [{"$gte": ["$created_at", LETZTES_SCHULJAHR_START]}, {"$lte": ["$created_at", LETZTES_SCHULJAHR_ENDE]}]}
###########################################################################
pipe_dict_created_at = helpers.build_pipe_dict("created_at", VOR_30_TAGEN, VOR_90_TAGEN, LETZTES_SCHULJAHR_START, LETZTES_SCHULJAHR_ENDE)
pipe_dict_date = helpers.build_pipe_dict("date", VOR_30_TAGEN, VOR_90_TAGEN, LETZTES_SCHULJAHR_START, LETZTES_SCHULJAHR_ENDE)

# chat_pipe_dict_created_at = {}

# for suffix, condition in pipe_dict_created_at.items():
#     chat_pipe_dict_created_at[suffix] = {"$and": [condition, {"$eq": ["$is_chat", True]}]}      ----> because we append new values to the pipe_dict_created_at
                                                                                        # it is no longer necessary
###########################################################################

teacher_student_pipe = [{
    "$lookup": {
        "from": "user",
        "localField": "teachers",
        "foreignField": "_id",
        "as": "school_teachers"
    }},
    {"$lookup": {
        "from": "student",
        "localField": "_id",
        "foreignField": "school",
        "as": "school_students"     ### muss anderen namen haben, da sonst dieses lookup das vorherige überschreibt
    }},
    {"$project": {
        "name" : 1,
        "anzahl_aktive_lehrer": {
        "$size": {
            "$filter": {
                "input": "$school_teachers",
                "as": "st",
                "cond": {"$ne": ["$$st.is_deleted", True]}
                }
            }
        },
        "anzahl_aktive_schüler": {
            "$size": {
                "$filter": {
                    "input": "$school_students",
                    "as": "s",
                    "cond": {"$eq": ["$$s.deleted_at", None]}
                }
            }
        },
        "anzahl_aktive_eltern": {
            "$size": {
                "$setUnion": {
                    "$reduce": {
                        "input": {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$school_students",
                                        "as": "s",
                                        "cond": {"$eq": ["$$s.deleted_at", None]}
                                    }
                                },
                                "as": "s",
                                "in": "$$s.parents"
                            }
                        },
                        "initialValue": [],
                        "in": {"$concatArrays": ["$$value", "$$this"]}
                    }
                }
            }
        },
        "created_at": 1,
        "_id": 1
    }},
    # {"$sort": {
    #     "anzahl_aktive_lehrer": -1}}
]

absence_pipe = [
    {"$match": {
        "event_type": {"$eq": "absence"},
        # "created_at": {"$gte": datetime(2026, 6, 1), "$lt": datetime(2026, 6, 30)}
    }},
    # {"$limit": 5},
    {"$group": {
        "_id": "$school",
        "anzahl_absenz_historie": {"$sum": 1},
        "anzahl_joker_tage_historie": {
            "$sum": {
                "$cond": [
                    {"$eq": ["$is_joker_day", True]},
                    1,
                    0
                ]
            }
        },
        **helpers.timeframe_fields("absenz", pipe_dict_created_at),
        **helpers.timeframe_fields("joker_tage",helpers.cond_cat("is_joker_day", True, pipe_dict_created_at))
    }},
    {"$lookup": {
        "from": "school",
        "localField": "_id",
        "foreignField": "_id",
        "as": "school_info"
    }},
    {"$unwind": "$school_info"},
    {"$project": {
        "joker_tage_aktiviert": {
            "$cond": [
                {"$eq": ["$school_info.joker_days_enabled", True]},
                "Aktiviert",
                "Nicht Aktiviert"
    ]
},
        # "$school_info.client_name": 1
        "name": "$school_info.name",
        "anzahl_absenz_30_tage": 1, 
        "anzahl_absenz_90_tage": 1,
        "anzahl_absenz_letztes_schuljahr": 1,
        "anzahl_absenz_historie": 1,
        "anzahl_joker_tage_30_tage": 1,
        "anzahl_joker_tage_90_tage": 1,
        "anzahl_joker_tage_letztes_schuljahr": 1,
        "anzahl_joker_tage_historie": 1,
        "_id": 1
    # }},
    # {"$sort": {
    #     "anzahl_absenz": -1
    }},
    # {"$sort": {
    #     "anzahl_joker_tage": 1,
    #     "joker_tage_aktiviert": 1}}
    
]

message_pipe = [
    {"$group": {
    "_id": "$school",
    "anzahl_notification_historie": {"$sum": 1},
    "davon_chat_nachricht_historie": {
    "$sum": {
        "$cond": [
            {"$eq": ["$is_chat", True]},
            1,
            0
        ]
    }
},
    **helpers.timeframe_fields("notification", pipe_dict_created_at),
    **helpers.timeframe_fields("davon_chat_nachricht", helpers.cond_cat("is_chat", True, pipe_dict_created_at), add_anzahl_prefix=False)
    }},
    {"$lookup": {
        "from": "school",
        "localField": "_id",
        "foreignField": "_id",
        "as": "school_notification"
    }},
    {"$unwind": "$school_notification"},
    {"$project": {
        "name": "$school_notification.name",
        "anzahl_notification_30_tage": 1,
        "anzahl_notification_90_tage": 1,
        "anzahl_notification_letztes_schuljahr": 1,
        "anzahl_notification_historie": 1,
        "davon_chat_nachricht_30_tage": 1,
        "davon_chat_nachricht_90_tage": 1,
        "davon_chat_nachricht_letztes_schuljahr": 1,
        "davon_chat_nachricht_historie": 1,
        "_id": 1
    }}

]

event_pipe_meet = [
    {"$match": {
        "event_type": {"$eq": "meet"}
    }},
    {"$group": {
        "_id": "$school",
        "anzahl_meetings_historie": {"$sum": 1},
        **helpers.timeframe_fields("meetings", pipe_dict_created_at)
    }},
    {"$lookup": {
        "from": "school",
        "localField": "_id",
        "foreignField": "_id",
        "as": "school_meet"
    }},
    {"$project": {
        "name": "$school_meet.name",
        "anzahl_meetings_30_tage": 1,
        "anzahl_meetings_90_tage": 1,
        "anzahl_meetings_letztes_schuljahr": 1,
        "anzahl_meetings_historie": 1,
        "_id": 1
    }}
]

event_pipe_event = [
    {"$match": {
        "event_type": {"$eq": "event"}
    }},
    {"$group": {
        "_id": "$school",
        "anzahl_events_historie": {"$sum": 1},
        **helpers.timeframe_fields("events", pipe_dict_created_at)
    }},
    {"$lookup": {
        "from": "school",
        "localField": "_id",
        "foreignField": "_id",
        "as": "school_event"
    }},
    {"$project": {
        "name": "$school_event.name",
        "anzahl_events_30_tage": 1,
        "anzahl_events_90_tage": 1,
        "anzahl_events_letztes_schuljahr": 1,
        "anzahl_events_historie": 1,
        "_id": 1
    }}
]

event_pipe_category = [{
    "$group": {
        "_id": "$school",
        "anzahl_event_event_historie": {
            "$sum": {
                "$cond": [{"$eq": ["$event_category", "event"]}, 1, 0]}
        },
        "anzahl_holiday_event_historie": {
            "$sum": {
                "$cond": [{"$eq": ["$event_category", "holiday"]}, 1,0]}
        },
        "anzahl_task_event_historie": {
            "$sum": {
                "$cond": [{"$eq": ["$event_category", "task"]}, 1, 0]}
        },
        "anzahl_test_event_historie": {
            "$sum": {
                "$cond": [{"$eq": ["$event_category", "test"]}, 1, 0]}
        },
        **helpers.timeframe_fields("event_event", helpers.cond_cat("event_category", "event", pipe_dict_created_at)),
        **helpers.timeframe_fields("holiday_event", helpers.cond_cat("event_category", "holiday", pipe_dict_created_at)),
        **helpers.timeframe_fields("task_event", helpers.cond_cat("event_category", "task", pipe_dict_created_at)),
        **helpers.timeframe_fields("test_event", helpers.cond_cat("event_category", "test", pipe_dict_created_at))
        }
    }
]


file_pipe = [
    {"$group": {
        "_id": "$school",
        "anzahl_files_historie": {"$sum": 1},
        **helpers.timeframe_fields("files", pipe_dict_created_at)
    }},
    {"$lookup": {
        "from": "school",
        "localField": "_id",
        "foreignField": "_id",
        "as": "school_files"
    }},
    {"$project": {
        "name": "$school_files.name",
        "anzahl_files_30_tage": 1,
        "anzahl_files_90_tage": 1,
        "anzahl_files_letztes_schuljahr": 1,
        "anzahl_files_historie": 1,
        "_id": 1
    }}
]

question_pipe = [
    {"$group": {
        "_id": "$school",
        "anzahl_questions_historie": {"$sum": 1},
        **helpers.timeframe_fields("questions", pipe_dict_created_at)
    }},
    {"$lookup": {
        "from": "school",
        "localField": "_id",
        "foreignField": "_id",
        "as": "school_question"
    }},
    {"$project": {
        "name": "$school_question.name",
        "anzahl_questions_30_tage": 1,
        "anzahl_questions_90_tage": 1,
        "anzahl_questions_letztes_schuljahr": 1,
        "anzahl_questions_historie": 1,
        "_id": 1
    }}
]

status_pipe = [{
    "$project": {
        "loeschstatus": {
        "$cond":[{"$ne": ["$deleted_at", None]},
                "$deleted_at",
                None]
        },
        "kuendigungsstatus": {
            "$cond": [{"$ne": ["$invoicing_cancellation_date", None]},
                        "$invoicing_cancellation_date",
                        None]
        },
        "status": {
            "$cond": [{"$eq": ["$deactivated", True]},
                        "Deaktiviert",
                        "Aktiv"]
        },
        "_id": 1
    }
}
]

money_pipe = [{
    "$unwind": "$price_data"},
    {"$group": {
        "_id": "$price_data.school",
        "anzahl_invoices_historie": {"$sum": "$price_data.amount_invoiced"},
        **helpers.timeframe_fields("invoices", pipe_dict_date, is_money=True, money_field="$price_data.amount_invoiced")
    }},
    {"$lookup": {
        "from": "school",
        "localField": "_id",
        "foreignField": "_id",
        "as": "school_total"
    }},
    {"$unwind": "$school_total"},
    {"$project": {
        "_id": 1,
        "anzahl_invoices_historie": 1,
        "invoicing_start_date": "$school_total.invoicing_start_date",
        "invoicing_cancellation_date": "$school_total.invoicing_cancellation_date",
        "anzahl_invoices_30_tage": 1,
        "anzahl_invoices_90_tage": 1,
        "anzahl_invoices_letztes_schuljahr": 1,
        "anzahl_invoices_historie": 1,
    }
}]

price_data_pipe = [
    {"$unwind": "$price_data"},
    {"$match": {
        "$expr": {"$ne": ["$price_data.school", "$school_id"]}
    }},
    {"$lookup": {
        "from": "school",
        "foreignField": "_id",
        "localField": "price_data.school",
        "as": "toechter_name"
    }},
    {"$unwind": "$toechter_name"},

    {"$facet": {
        "toechter_zu_mutter": [
            {"$group": {
                "_id": "$price_data.school",
                "mutterschule_id": {"$first": "$school_id"}
            }},
            {"$lookup": {
                "from": "school",
                "localField": "mutterschule_id",
                "foreignField": "_id",
                "as": "mother_school"
            }},
            {"$unwind": "$mother_school"},
            {"$project": {
                "mother_school_name": "$mother_school.name"
            }}
        ],
        "mutter_zu_toechter": [
            {"$group": {
                "_id": "$price_data.school",
                "mutterschule_id": {"$first": "$school_id"},
                "daughter_name": {"$first": "$toechter_name"},
                "toechter_betrag": {"$sum": "$price_data.amount_invoiced"}
            }},
            {"$group": {
                "_id": "$mutterschule_id",
                "anzahl_toechter": {"$sum": 1},
                "toechter_details": {"$push": {"name": "$daughter_name.name", "betrag": "$toechter_betrag"}}
            }},
            {"$lookup": {
                "from": "school",
                "localField": "_id",
                "foreignField": "_id",
                "as": "mother_school"
            }},
            {"$unwind": "$mother_school"},
            {"$project": {
                "mother_school_name": "$mother_school.name",
                "anzahl_toechter": 1,
                "toechter_details": 1
            }}
        ]
    }}
]


#################################################
# Pipeline list

pipeline_list = [
    (teacher_student_pipe, "school"), 
    (absence_pipe, "event"), 
    (message_pipe, "notification"), 
    (event_pipe_meet, "event"),
    (event_pipe_event, "event"),
    (event_pipe_category, "event"),
    (file_pipe, "file"),
    (question_pipe, "question"),
    (status_pipe, "school"),
    (money_pipe, "invoices")
    ]

invoice_list = [
    (price_data_pipe, "invoices")
]