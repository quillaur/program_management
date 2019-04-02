from flask import Flask, render_template, request, Response, url_for, redirect
import os
import sys
import mysql.connector
import pandas
from ast import literal_eval

# My specific imports
from python_scripts import utilities
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
            input_action = request.form["action"]
            action_date = request.form["action_date"]

            # Current directory
            current_dir = os.path.dirname(os.path.realpath(__file__))

            # Keep track of date in a tmp file
            filename = os.path.join(current_dir, "tmp_data/tmp_date.txt")
            with open(filename, "w") as my_file:
                my_file.write(str(action_date))

            # Keep track of action in a tmp file
            filename = os.path.join(current_dir, "tmp_data/tmp_action.txt")
            with open(filename, "w") as my_file:
                my_file.write(str(input_action))

            # Get tech dict from tmp_data and modify it
            filename = os.path.join(current_dir, "tmp_data/tmp_tech_dict.txt")
            with open(filename, "r") as my_file:
                handle = my_file.read()
                tech_dict = literal_eval(handle)

            return_df = pandas.DataFrame(tech_dict)

            # Select brothers only available at this date and able to do the wanted action
            brothers_list = utilities.generate_brother_list(date=action_date, action=input_action)

            # Get brothers busy that day
            date_indice = tech_dict["Date"].index(action_date)
            if input_action == "Part1" or input_action == "Part2":
                action_bros = tech_dict[input_action][date_indice].split(" / ")
            else:
                action_bros = [tech_dict[input_action][date_indice]]

            busy_bros = []
            for action in tech_dict:
                if action == "Part1" or action == "Part2":
                    busy_bros.extend(tech_dict[action][date_indice].split(" / "))
                else:
                    busy_bros.append(tech_dict[action][date_indice])

            reduced_brothers_list = [bro for bro in brothers_list if bro not in busy_bros]

            return render_template("table_1.html",
                                   dropdown_brothers_list=action_bros,
                                   dropdown_reduced_brothers_list=reduced_brothers_list,
                                   input_action=input_action,
                                   tables=[return_df.to_html(classes='data', header="true")],
                                   action_date=action_date)

        if "submit_brothers" in request.form:
            input_init_brother = request.form["init_brother"]
            input_new_brother = request.form["new_brother"]

            init_first_name, init_last_name = split_brother_name(brother_full_name=input_init_brother)
            new_first_name, new_last_name = split_brother_name(brother_full_name=input_new_brother)

            # Current directory
            current_dir = os.path.dirname(os.path.realpath(__file__))

            # Get the previously selected date
            filename = os.path.join(current_dir, "tmp_data/tmp_date.txt")
            with open(filename, "r") as my_file:
                action_date = my_file.read()

            # Get the previously selected action
            filename = os.path.join(current_dir, "tmp_data/tmp_action.txt")
            with open(filename, "r") as my_file:
                input_action = my_file.read()

            # Get tech dict from tmp_data and modify it
            current_dir = os.path.dirname(os.path.realpath(__file__))
            filename = os.path.join(current_dir, "tmp_data/tmp_tech_dict.txt")

            with open(filename, "r") as my_file:
                handle = my_file.read()
                tech_dict = literal_eval(handle)

            # tech dict works with lists so get the indice of list contained by the "Date" key:
            date_indice = tech_dict["Date"].index(action_date)
            tech_dict[input_action][date_indice] = tech_dict[input_action][date_indice].replace(init_first_name,
                                                                                                new_first_name).replace(
                init_last_name, new_last_name)

            with open(filename, "w") as my_file:
                my_file.write(str(tech_dict))

            return_df = pandas.DataFrame(tech_dict)

            actions_list = utilities.generate_action_list()

            return render_template("table.html",
                                   dropdown_brothers_list=[],
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
    micro_bros = [row[0] for row in cursor]

    tech_dict = utilities.build_sono_program_dict(brother_action_dict=brother_action_dict,
                                                  sono_bros=sono_bros,
                                                  micro_bros=micro_bros,
                                                  chinese_bros=chinese_bros,
                                                  action_dict=action_dict,
                                                  brother_id_dict=brother_id_dict)

    # Write file in tmp dir in order to re-use it in the next part of the script
    current_dir = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(current_dir, "tmp_data/tmp_tech_dict.txt")

    with open(filename, "w") as my_file:
        my_file.write(str(tech_dict))

    return_df = pandas.DataFrame(tech_dict)

    brothers_list = utilities.generate_brother_list(date=action_date)

    actions_list = utilities.generate_action_list()

    return render_template("table.html",
                           dropdown_brothers_list=brothers_list,
                           dropdown_actions_list=actions_list,
                           tables=[return_df.to_html(classes='data', header="true")],
                           action_date=action_date)


@app.route('/update/<action_date>', methods=["GET", "POST"])
def update_brother_action(action_date):
    brothers_list = utilities.generate_brother_list(date=action_date)

    actions_list = utilities.generate_action_list()

    return_df = utilities.select_brother_action_table(date=action_date)

    if request.method == "POST":
        if "submit_action" in request.form:
            input_brother = request.form["brother"]
            input_action = request.form["action"]

            utilities.insert_brother_action(brother=input_brother, action=input_action, date=action_date)

            brothers_list = utilities.generate_brother_list(date=action_date)

            return_df = utilities.select_brother_action_table(date=action_date)

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
# TO DO
# Insert sono program in mysql.
# Count brother actions.
# Create rule for chinese bros.
# Create a page with brother roles.
