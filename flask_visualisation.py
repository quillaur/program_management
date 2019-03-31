from flask import Flask, render_template, request, Response, url_for, redirect
import os
import sys
import mysql.connector
import pandas
from collections import defaultdict
from random import shuffle
from ast import literal_eval

# My specific imports
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(dir_path, "core"))

app = Flask(__name__)


@app.route('/main_page', methods=["GET", "POST"])
def main_page():
    if request.method == "POST":
        if request.form["submit_button"] == "Submit":
            action_date = request.form["action_date"]

            return redirect(url_for("update_brother_action", action_date=action_date))

        elif request.form["submit_button"] == "Generate":
            action_date = request.form["month"]

            return redirect(url_for("generate_sono_program", action_date=action_date))

    dropdown_months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
                            "October", "November", "December"]
    return render_template("main_page.html", dropdown_months_list=dropdown_months_list)


@app.route('/generate-sono-program/<action_date>', methods=["GET", "POST"])
def generate_sono_program(action_date):
    if request.method == "POST":
        if "submit_action" in request.form:
            input_init_brother = request.form["init_brother"]
            input_action = request.form["action"]
            input_new_brother = request.form["new_brother"]
            action_date = request.form["action_date"]

            init_first_name, init_last_name = split_brother_name(brother_full_name=input_init_brother)
            new_first_name, new_last_name = split_brother_name(brother_full_name=input_new_brother)

            # Get tech dict from tmp_data and mofidy it
            current_dir = os.path.dirname(os.path.realpath(__file__))
            filename = os.path.join(current_dir, "tmp_data/tmp_tech_dict.txt")

            with open(filename, "r") as my_file:
                handle = my_file.read()
                tech_dict = literal_eval(handle)

            # tech dict works with lists so get the indice of list contained by the "Date" key:
            date_indice = tech_dict["Date"].index(action_date)
            tech_dict[input_action][date_indice] = tech_dict[input_action][date_indice].replace(init_first_name,
                                                                                                new_first_name).replace(init_last_name, new_last_name)

            with open(filename, "w") as my_file:
                my_file.write(str(tech_dict))

            return_df = pandas.DataFrame(tech_dict)

            brothers_list = generate_brother_list(date=action_date)

            actions_list = generate_action_list()

            return render_template("table.html",
                                   dropdown_brothers_list=brothers_list,
                                   dropdown_actions_list=actions_list,
                                   tables=[return_df.to_html(classes='data', header="true")],
                                   action_date=action_date)

    input_month = action_date.lower()
    month_str_to_int = {
        "january": "01",
        "february": "02",
        "march": "03",
        "april": "04",
        "may": "05",
        "june": "06",
        "july": "07",
        "august": "08",
        "september": "09",
        "october": "10",
        "november": "11",
        "december": "12"
    }

    wanted_date = "2019-{}".format(month_str_to_int[input_month])

    query = "SELECT * FROM BrotherAction WHERE ActionDate like '{}%';".format(wanted_date)
    connection = mysql.connector.connect(host="localhost", database="program_management", user="root",
                                         password="DPh8@v4%")
    cursor = connection.cursor()
    cursor.execute(query)

    brother_action_dict = {}
    for row in cursor:
        # {date : {brother_ ID: [action_ID, ...]}}
        if row[2] not in brother_action_dict:
            brother_action_dict[row[2]] = {}

        if row[1] not in brother_action_dict[row[2]]:
            brother_action_dict[row[2]][row[1]] = [row[3]]

        brother_action_dict[row[2]][row[1]].append(row[3])

    # Get all actions ID from database
    query = "SELECT * FROM Action;"
    cursor.execute(query)

    action_dict = {}
    for row in cursor:
        action_dict[row[1]] = row[0]
        action_dict[row[0]] = row[1]

    # Get all Brothers ID
    query = "SELECT IdBrother, BrotherFirstName, BrotherLastName FROM Brother;"
    cursor.execute(query)

    brother_id_dict = {
        row[0]: "{} {}".format(row[1], row[2])
        for row in cursor
    }

    # Get sono bros
    query = "SELECT IdBrother FROM Brother WHERE Sono = '1';"
    cursor.execute(query)

    sono_bros = [row[0] for row in cursor]

    # Get Chinese Bros
    query = "SELECT IdBrother FROM Brother WHERE Chinese = '1';"
    cursor.execute(query)

    chinese_bros = [row[0] for row in cursor]

    # Get micro bros
    query = "SELECT IdBrother FROM Brother WHERE Micro = '1';"
    cursor.execute(query)

    # Remove chinese bros from official sono schedule until better a rule is found.
    micro_bros = [row[0] for row in cursor if row[0] not in chinese_bros]

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

    # Write file in tmp dir in order to re-use it in the next part of the script
    current_dir = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(current_dir, "tmp_data/tmp_tech_dict.txt")

    with open(filename, "w") as my_file:
        my_file.write(str(tech_dict))

    return_df = pandas.DataFrame(tech_dict)

    brothers_list = generate_brother_list(date=action_date)

    actions_list = generate_action_list()

    return render_template("table.html",
                           dropdown_brothers_list=brothers_list,
                           dropdown_actions_list=actions_list,
                           tables=[return_df.to_html(classes='data', header="true")],
                           action_date=action_date)


def split_brother_name(brother_full_name: str):
    brother_name_list = brother_full_name.split(" ")
    if len(brother_name_list) > 2:
        first_name = brother_name_list[0]
        last_name = " ".join(brother_name_list[1:])

    else:
        first_name = brother_name_list[0]
        last_name = brother_name_list[1]

    return first_name, last_name

def select_brother_action_table(date: str = ""):
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

    return pandas.DataFrame(brother_action_dict)


def generate_brother_list(date: str):
    connection = get_mysql_connection()
    cursor = connection.cursor()
    query = "SELECT BrotherFirstName, BrotherLastName FROM Brother " \
            "WHERE IdBrother NOT IN (SELECT IdBrother FROM BrotherAction WHERE ActionDate = '{}');".format(date)
    cursor.execute(query)
    brothers_list = ["{} {}".format(row[0], row[1]) for row in cursor]
    connection.close()
    return brothers_list


def generate_action_list():
    connection = get_mysql_connection()
    cursor = connection.cursor()
    query = "SELECT ActionName FROM Action;"
    cursor.execute(query)
    actions_list = [row[0] for row in cursor]
    connection.close()
    return actions_list


def insert_brother_action(brother: str, action: str, date: str):
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
    return mysql.connector.connect(host="localhost",
                                   database="program_management",
                                   user="root",
                                   password="DPh8@v4%")


@app.route('/update/<action_date>', methods=["GET", "POST"])
def update_brother_action(action_date):
    brothers_list = generate_brother_list(date=action_date)

    actions_list = generate_action_list()

    return_df = select_brother_action_table(date=action_date)

    if request.method == "POST":
        if "submit_action" in request.form:
            input_brother = request.form["brother"]
            input_action = request.form["action"]

            insert_brother_action(brother=input_brother, action=input_action, date=action_date)

            brothers_list = generate_brother_list(date=action_date)

            return_df = select_brother_action_table(date=action_date)

            return render_template("update.html", dropdown_brothers_list=brothers_list,
                                   dropdown_actions_list=actions_list,
                                   tables=[return_df.to_html(classes='data', header="true")],
                                   action_date=action_date)

        elif "submit_date" in request.form:
            action_date = request.form["action_date"]

            return redirect(url_for("update_brother_action", action_date=action_date))

    return render_template("update.html", dropdown_brothers_list=brothers_list,
                           dropdown_actions_list=actions_list,
                           tables=[return_df.to_html(classes='data', header="true")],
                           action_date=action_date)


if __name__ == '__main__':
    app.run(debug=True)

# Connect via : http://localhost:5000/main_page
