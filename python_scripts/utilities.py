
import mysql.connector
from collections import defaultdict
import pandas
from random import shuffle


def split_brother_name(brother_full_name: str):
    """
    Split brother first and last name in 2 different string variables.

    :param brother_full_name: string containing brother first and last names.
    :type brother_full_name: str

    :return: first and last names in 2 separated variables.
    """
    brother_name_list = brother_full_name.split(" ")
    if len(brother_name_list) > 2:
        first_name = brother_name_list[0]
        last_name = " ".join(brother_name_list[1:])

    else:
        first_name = brother_name_list[0]
        last_name = brother_name_list[1]

    return first_name, last_name


def select_brother_action_table(date: str = ""):
    """
    Select brothers and actions for a given date or any date.

    :param date: string of the selected date.
    :type date: str

    :return: pandas dataframe containing a dict: {"Brother": [], "Action": [], "Date": []}
    """
    connection = get_mysql_connection()
    cursor = connection.cursor()
    query = "SELECT B.BrotherFirstName, B.BrotherLastName, A.ActionName, BA.ActionDate " \
            "FROM BrotherAction AS BA " \
            "INNER JOIN Brother AS B ON BA.IdBrother = B.IdBrother " \
            "INNER JOIN Action AS A ON BA.IdAction = A.IdAction"

    if date:
        query = query + " WHERE BA.ActionDate = '{}';".format(date)

    else:
        query = query + ";"

    cursor.execute(query)
    brother_action_dict = defaultdict(list)
    for row in cursor:
        brother_action_dict["Brother"].append("{} {}".format(row[0], row[1]))
        brother_action_dict["Action"].append(row[2])
        brother_action_dict["Date"].append(row[3])

    connection.close()
    return pandas.DataFrame(brother_action_dict)


def generate_brother_list(date: str, action: str = "") -> list:
    """
    Select a list of brothers according to given date and/or action.

    :param date: given date
    :type date: str
    :param action: given action
    :type action: str

    :return: list of brothers
    """
    connection = get_mysql_connection()
    cursor = connection.cursor()
    if action:
        action = "Micro" if action == "Part1" or action == "Part2" else action
        query = "SELECT BrotherFirstName, BrotherLastName FROM Brother " \
                "WHERE IdBrother NOT IN (SELECT IdBrother FROM BrotherAction WHERE ActionDate = '{}') " \
                "AND {} = '1';".format(date, action)
    else:
        query = "SELECT BrotherFirstName, BrotherLastName FROM Brother " \
                "WHERE IdBrother NOT IN (SELECT IdBrother FROM BrotherAction WHERE ActionDate = '{}');".format(date)
    cursor.execute(query)
    brothers_list = ["{} {}".format(row[0], row[1]) for row in cursor]
    connection.close()
    return brothers_list


def generate_action_list():
    """
    Generate a list of all possible actions.

    :return: list of actions
    """
    connection = get_mysql_connection()
    cursor = connection.cursor()
    query = "SELECT ActionName FROM Action;"
    cursor.execute(query)
    actions_list = [row[0] for row in cursor]
    connection.close()
    return actions_list


def insert_brother_action(brother: str, action: str, date: str):
    """
    Insert brother actions according to date in mysql database.

    :param brother: given brother first and last names
    :type brother: str
    :param action: brother's action
    :type action: str
    :param date: selected date
    :type date: str

    :return: None
    """
    first_name, last_name = split_brother_name(brother_full_name=brother)

    connection = get_mysql_connection()
    query = "SELECT (SELECT idBrother " \
            "FROM Brother " \
            "WHERE BrotherFirstName = '{}' AND BrotherLastName = '{}'), " \
            "idAction FROM Action WHERE ActionName = '{}';".format(first_name, last_name, action)

    cursor = connection.cursor()
    cursor.execute(query)

    for row in cursor:
        insert_dict = {
            "id_brother": row[0],
            "id_action": row[1],
            "action_date": date
        }

    query = "INSERT INTO BrotherAction (idBrother, ActionDate, idAction) " \
            "VALUES (%(id_brother)s, %(action_date)s, %(id_action)s);"
    cursor.execute(query, insert_dict)
    connection.commit()
    connection.close()


def get_mysql_connection():
    """
    Connect to mysql.

    :return: mysql connection
    """
    return mysql.connector.connect(host="localhost",
                                   database="program_management",
                                   user="root",
                                   password="DPh8@v4%")


def build_sono_program_dict(brother_action_dict: dict,
                            sono_bros: list,
                            chinese_bros: list,
                            action_dict: dict,
                            micro_bros: list,
                            brother_id_dict: dict):
    """
    Build automatically a program for the sono team with the given parameters.

    :param brother_action_dict: {date : {brother_ ID: [action_ID, ...]}}
    :type brother_action_dict: dict
    :param sono_bros: list of brothers doing sono
    :type sono_bros: list
    :param chinese_bros: list of brothers in the chinese group
    :type chinese_bros: list
    :param action_dict: dict to convert action name to ID and vice-versa
    :type action_dict: dict
    :param micro_bros: list of brothers passing microphones
    :type micro_bros: list
    :param brother_id_dict: dict converting ID to brother name
    :type brother_id_dict: dict

    :return: dictionary containing sono program and formated to easily be transformed as panda dataframe.
    """
    sono_dict = {}
    stage_dict = {}
    micro_dict = {}
    tech_dict = {
        "Date": [],
        "Part1": [],
        "Part2": [],
        "Stage": [],
        "Sono": []
    }

    ordered_date = sorted(list(brother_action_dict))
    for date in ordered_date:
        # Available bros at this date = no participation at all that day:
        available_sono_bros = [bro for bro in sono_bros
                               if bro not in brother_action_dict[date]
                               or bro not in chinese_bros]

        # Remove the last brother who did sono
        if ordered_date.index(date) != 0:
            previous_date_index = ordered_date.index(date) - 1
            previous_date = ordered_date[previous_date_index]

            if sono_dict[previous_date] in available_sono_bros:
                last_sono_bro_index = available_sono_bros.index(sono_dict[previous_date])
                del available_sono_bros[last_sono_bro_index]

        if available_sono_bros:
            shuffle(available_sono_bros)
            sono_dict[date] = available_sono_bros[0]
            del available_sono_bros[0]

            if available_sono_bros:
                # Remove the last brother who did stage
                if ordered_date.index(date) != 0:
                    previous_date_index = ordered_date.index(date) - 1
                    if stage_dict[ordered_date[previous_date_index]] in available_sono_bros:
                        last_stage_bro_index = available_sono_bros.index(
                            stage_dict[ordered_date[previous_date_index]])
                        del available_sono_bros[last_stage_bro_index]

                stage_dict[date] = available_sono_bros[0]

            else:
                shuffle(sono_bros)
                # Remove the bro doing sono
                del sono_bros[sono_bros.index(sono_dict[date])]
                stage_dict[date] = sono_bros[0]
        else:
            shuffle(sono_bros)
            sono_dict[date] = sono_bros[0]
            shuffle(sono_bros)
            stage_dict[date] = sono_bros[0] if sono_bros[0] != sono_dict[date] else sono_bros[1]

        brother_action_dict[date][sono_dict[date]] = action_dict["Sono"]
        brother_action_dict[date][stage_dict[date]] = action_dict["Stage"]

        # Micro bros
        available_micro_bros = [bro for bro in micro_bros if bro not in brother_action_dict[date]]

        shuffle(available_micro_bros)
        micro_dict[date] = {
            "Part1": [brother_id_dict[available_micro_bros[0]], brother_id_dict[available_micro_bros[1]]],
            "Part2": [brother_id_dict[available_micro_bros[2]], brother_id_dict[available_micro_bros[3]]]
        }

        tech_dict["Date"].append(str(date))
        tech_dict["Part1"].append("{} / {}".format(micro_dict[date]["Part1"][0], micro_dict[date]["Part1"][1]))
        tech_dict["Part2"].append("{} / {}".format(micro_dict[date]["Part2"][0], micro_dict[date]["Part2"][1]))
        tech_dict["Stage"].append(brother_id_dict[stage_dict[date]])
        tech_dict["Sono"].append(brother_id_dict[sono_dict[date]])

    return tech_dict