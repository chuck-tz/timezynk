from flask import request
from datetime import datetime
import json
import requests
import random
from machine_learning_recommendation.recommendation import (
    machine_learning_models,
)
import logging


def get_arg_or_default(arg_name, arg_type, default):
    return (
        request.args.get(arg_name, type=arg_type)
        if request.args.get(arg_name, type=arg_type)
        else default
    )


def get_error_return(err_message):
    err_message_dict = {"message": err_message}
    return (
        json.dumps(err_message_dict),
        400,
        {"ContentType": "application/json"},
    )


def machine_learning_query(ml_on, qssec, query_shifts, num_candidates):
    """
    Read start, end, created of every queried shift
    then if ml_on is 1, query the ml recommend and append the list,
    if ml_on is 0, append an empty list,
    then return the list of lists.
    """
    recommend_list = []
    fmt = "%Y-%m-%dT%H:%M:%S.%f"
    sec = list(
        map(
            lambda x: (
                datetime.strptime(x[0], fmt),
                datetime.strptime(x[1], fmt),
                x[2],
            ),
            qssec,
        )
    )

    for index, _id in enumerate(query_shifts):
        if ml_on:
            feed_back = machine_learning_models.recommend(
                "5f3e1fc8d048e76cbdb4e600",  # _id
                sec[index][0],
                sec[index][1],
                sec[index][2],
                num_candidates,
            )
            recommend_list.append(feed_back)
        else:
            recommend_list.append([])

    return recommend_list


def lists_union(l1, l2, l3, l4):
    return list(
        map(
            lambda x1, x2, x3, x4: x1.union(x2, x3, x4),
            l1,
            l2,
            l3,
            l4,
        )
    )


def get_user_ids(backend_url, headers):
    logger = logging.getLogger(__name__)
    response = requests.request("GET", backend_url + "/users", headers=headers)
    if response.ok:
        users = json.loads(response.text)
        return [user["id"] for user in users]
    else:
        logger.warning(
            f"Fetch user-ids from backend not successful. Check if tzbackend is on."
        )
        return []


def lists_difference(l1, l2):
    """
    Used specifically to eliminate unfeasible users from full user list,
    for each shift in query.
    """
    ret = []
    for i in range(len(l1)):
        s1 = set(l1[i])
        s2 = set(l2[i])
        ret.append(list(s1 - s2))
    return ret


def list_shuffle(list_of_lists):
    """
    There is a river, called a river of ??
    """
    for _list in list_of_lists:
        random.shuffle(_list)


def concoct(ml_list, random_list, num_candidates):
    """
    Pick out num_cadidates numbers of users for each shift under query,
    ml_list gets a higher priority than random_list
    """
    ret = []
    for i in range(len(ml_list)):
        ml_list_i = ml_list[i]
        random_list_i = random_list[i]
        if len(ml_list_i) >= num_candidates:
            ret.append(ml_list_i[:num_candidates])
        else:
            ml_set_i = set(ml_list_i)
            random_set_i = set(random_list_i)
            diff_set_i = random_set_i - ml_set_i
            diff_list_i = list(diff_set_i)
            ret.append(ml_list_i + diff_list_i[: num_candidates - len(ml_list_i)])
    return ret


def object_and_200(_object):
    return (
        json.dumps(_object),
        200,
        {"ContentType": "application/json"},
    )
