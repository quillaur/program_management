from flask import Flask, render_template, request, Response, url_for
import os
from collections import OrderedDict
import sys

# My specific imports
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(dir_path, "core"))
from programs_analysis import Programmer

app = Flask(__name__)


def generate_program(program_file, program_file_2, welcome_file, input_date):
    """
    Generate program for sono from filename

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


# Declare your table
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


@app.route('/submit', methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if request.form["submit_button"] == "Upload_2":
            name = request.form['name']
            date = request.form['date']
            part = request.form['part']
            msg = "I inserted: date: {} / name: {}".format(date, name)
            pgr = Programmer()
            pgr.insert_DB(date, name, part)
            return msg

        elif request.form["submit_button"] == "Upload":
            input_date = request.form['month']
            program_file = request.files["program_file"]
            program_file_2 = request.files["program_file_2"]
            welcome_file = request.files["welcome_program_file"]
            sono_program_dict = generate_program(program_file, program_file_2, welcome_file, input_date)

            # Formatting sono program for HTML
            items = format_dict_to_table(sono_program_dict, "sono")
            col_names = [key for key in items[0].keys()]
            contents = [[v for k, v in item.items()] for item in items]

        # Formatting welcome program for HTML
        # print("welcome dict: {}".format(welcome_program_dict))
        # items = format_dict_to_table(welcome_program_dict, "welcome")
        # welcome_col_names = [key for key in items[0].keys()]
        # welcome_contents = [[v for k,v in item.items()] for item in items]

        elif request.form["submit_button"] == "Generate new program":

            return render_template("upload.html")

        dir_path = os.path.dirname(os.path.realpath(__file__))
        absolute_file = os.path.join(dir_path, "resources", "results_content.txt")

        with open(absolute_file, "w") as my_txt:
            my_txt.write(str(col_names))
            my_txt.write("\n")
            my_txt.write(str(contents))

        return render_template("table.html", month=input_date, keys=col_names, values_list=contents)

    dropdown_months_list = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre",
                            "Octobre", "Novembre", "Décembre"]
    return render_template("upload.html", dropdown_months_list=dropdown_months_list)


if __name__ == '__main__':
    app.run(debug=True)

# Connect via : http://localhost:5000/submit
