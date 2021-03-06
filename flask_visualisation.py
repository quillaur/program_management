from flask import Flask, render_template, request, Response, url_for
import os
from collections import OrderedDict
import sys
import mysql.connector
import pandas
from collections import defaultdict
from random import shuffle

# My specific imports
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(dir_path, "core"))
from programs_analysis import Programmer

app = Flask(__name__)


def generate_program(program_file, program_file_2, welcome_file, input_date):
    """
    Use the class Programmer to generate program from input files. Saves the used files to the desired directory.

    :param program_file: class object containing the content of the PDF file
    :type program_file: <class 'werkzeug.datastructures.FileStorage'>

    :param program_file_2: class object containing the content of the CSV file
    :type program_file: <class 'werkzeug.datastructures.FileStorage'>

    :param welcome_file: class object containing the content of the CSV file
    :type welcome_file: <class 'werkzeug.datastructures.FileStorage'>

    :param input_date: month given as input by the user
    :type input_date: str

    :return: dictionary containing the program
    :rtype: dict
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))

    absolute_program_file = os.path.join(dir_path, "resources/already_tested_programs", program_file.filename)
    absolute_program_file_2 = os.path.join(dir_path, "resources/already_tested_programs", program_file_2.filename)
    absolute_program_file_3 = os.path.join(dir_path, "resources/already_tested_programs", welcome_file.filename)

    program_file.save(absolute_program_file)
    program_file_2.save(absolute_program_file_2)
    welcome_file.save(absolute_program_file_3)

    programmer = Programmer(absolute_program_file, absolute_program_file_2, absolute_program_file_3, input_date)
    sono_program_dict = programmer.run()

    return sono_program_dict


def format_dict_to_table(program_dict: dict, mode: str):
    """
    Format the program dictionary so as to be printed as HTML table

    :param program_dict: dictionary containing the program
    :type program_dict: dict

    :param mode: which dictionary type am I formatting?
    :type mode: str

    :return: list of html items
    :rtype: list
    """
    if mode == "sono":
        # Intermediate formating of sono dict to be able to print it as a table
        items = []
        for key in program_dict.keys():
            data_dict = OrderedDict()
            data_dict["Date"] = key
            data_dict["Sono"] = program_dict[key]["Sono"]
            data_dict["Part 1"] = "/".join([program_dict[key]["Part 1"][0], program_dict[key]["Part 1"][1]])
            data_dict["Part 2"] = "/".join([program_dict[key]["Part 2"][0], program_dict[key]["Part 2"][1]])
            data_dict["Scène"] = program_dict[key]["Scène"]
            items.append(data_dict)

    elif mode == "welcome":
        # Intermediate formating of welcome dict to be able to print it as a table
        items = []
        for key in program_dict.keys():
            data_dict = OrderedDict()
            data_dict["Date"] = key
            data_dict["Welcome center"] = program_dict[key]
            items.append(data_dict)

    return items


@app.route('/main_page', methods=["GET", "POST"])
def main_page():
    return render_template("main_page.html")


@app.route('/submit', methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        # if request.form["submit_button"] == "Upload_2":
        #     name = request.form['name']
        #     date = request.form['date']
        #     part = request.form['part']
        #     msg = "I inserted: date: {} / name: {}".format(date, name)
        #     pgr = Programmer()
        #     pgr.insert_DB(date, name, part)
        #     return msg
        #
        # elif request.form["submit_button"] == "Upload":
        #     input_date = request.form['month']
        #     program_file = request.files["program_file"]
        #     program_file_2 = request.files["program_file_2"]
        #     welcome_file = request.files["welcome_program_file"]
        #     sono_program_dict = generate_program(program_file, program_file_2, welcome_file, input_date)
        #
        #     # Formatting sono program for HTML
        #     items = format_dict_to_table(sono_program_dict, "sono")
        #     col_names = [key for key in items[0].keys()]
        #     contents = [[v for k, v in item.items()] for item in items]
        #
        # elif request.form["submit_button"] == "Generate new program":
        #
        #     return render_template("upload.html")
        #
        # dir_path = os.path.dirname(os.path.realpath(__file__))
        # absolute_file = os.path.join(dir_path, "resources/temporary", "results_content.txt")
        #
        # with open(absolute_file, "w") as my_txt:
        #     my_txt.write(str(col_names))
        #     my_txt.write("\n")
        #     my_txt.write(str(contents))
        if request.form["submit_button"] == "Upload":
            input_month = request.form['month'].lower()
            month_str_to_int = {"janvier": "01", "fevrier": "02", "mars": "03", "avril": "04", "mai": "05",
                                "juin": "06", "juillet": "07", "aout": "08", "septembre": "09", "octobre": "10",
                                "novembre": "11", "decembre": "12"}

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

                tech_dict["Date"].append(date)
                tech_dict["Part1"].append("{} / {}".format(micro_dict[date]["Part1"][0], micro_dict[date]["Part1"][1]))
                tech_dict["Part2"].append("{} / {}".format(micro_dict[date]["Part2"][0], micro_dict[date]["Part2"][1]))
                tech_dict["Stage"].append(brother_id_dict[stage_dict[date]])
                tech_dict["Sono"].append(brother_id_dict[sono_dict[date]])

            return_df = pandas.DataFrame(tech_dict)

            return render_template("table.html", tables=[return_df.to_html(classes='data', header="true")])

    dropdown_months_list = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre",
                            "Octobre", "Novembre", "Décembre"]
    return render_template("upload.html", dropdown_months_list=dropdown_months_list)


def select_brother_action_table(date: str = ""):
    connection = mysql.connector.connect(host="localhost", database="program_management", user="root",
                                         password="DPh8@v4%")
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


@app.route('/update', methods=["GET", "POST"])
def update_brother_action():
    connection = mysql.connector.connect(host="localhost", database="program_management", user="root",
                                         password="DPh8@v4%")
    cursor = connection.cursor()
    query = "SELECT BrotherFirstName, BrotherLastName FROM Brother;"
    cursor.execute(query)
    brothers_list = ["{} {}".format(row[0], row[1]) for row in cursor]

    query = "SELECT ActionName FROM Action;"
    cursor.execute(query)
    actions_list = [row[0] for row in cursor]

    return_df = select_brother_action_table()

    if request.method == "POST":
        if request.form["submit_button"] == "Update":
            input_brother = request.form["brother"]
            input_action = request.form["action"]
            action_date = request.form["action_date"]

            brother_name = input_brother.split(" ")
            if len(brother_name) > 2:
                first_name = brother_name[0]
                last_name = " ".join(brother_name[1:])

            else:
                first_name = brother_name[0]
                last_name = brother_name[1]

            query = "SELECT (SELECT idBrother " \
                    "FROM Brother " \
                    "WHERE BrotherFirstName = '{}' AND BrotherLastName = '{}'), " \
                    "idAction FROM Action WHERE ActionName = '{}';".format(first_name, last_name, input_action)

            cursor = connection.cursor()
            cursor.execute(query)

            for row in cursor:
                insert_dict = {
                    "id_brother": row[0],
                    "id_action": row[1],
                    "action_date": action_date
                }

            query = "INSERT INTO BrotherAction (idBrother, ActionDate, idAction) " \
                    "VALUES (%(id_brother)s, %(action_date)s, %(id_action)s);"
            cursor.execute(query, insert_dict)
            connection.commit()

            return_df = select_brother_action_table(date=action_date)

            return render_template("update.html", dropdown_brothers_list=brothers_list,
                                   dropdown_actions_list=actions_list,
                                   tables=[return_df.to_html(classes='data', header="true")])

    return render_template("update.html", dropdown_brothers_list=brothers_list,
                           dropdown_actions_list=actions_list,
                           tables=[return_df.to_html(classes='data', header="true")])


if __name__ == '__main__':
    app.run(debug=True)

# Connect via : http://localhost:5000/submit
