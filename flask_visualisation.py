from flask import Flask, render_template, request, Response, url_for
from flask_weasyprint import HTML, render_pdf
import os
from collections import OrderedDict
import sys
from ast import literal_eval
# My specific imports
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(dir_path, "core"))
from programs_analysis import Programmer

app = Flask(__name__)

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

def generate_program(program_file, program_file_2, brothers_file, sono_file, welcome_file):
	"""
	Generate program for sono from filename

	:param program_file: class object containing the content of the PDF file
	:type program_file: <class 'werkzeug.datastructures.FileStorage'>

	:param program_file_2: class object containing the content of the PDF file
	:type program_file: <class 'werkzeug.datastructures.FileStorage'>

	:param brothers_file: class object containing the names of all brothers able to pass microphones in CSV format
	:type brothers_file: <class 'werkzeug.datastructures.FileStorage'>

	:param sono_file: class object containing the names of all brothers that are part of the sono team
	:type sono_file: <class 'werkzeug.datastructures.FileStorage'>

	:param welcome_file: class object containing the names of all brothers that are part of the welcome team
	:type welcome_file: <class 'werkzeug.datastructures.FileStorage'>

	:return: dictionary containing the program
	:rtype: dict
	"""
	dir_path = os.path.dirname(os.path.realpath(__file__))
	
	absolute_program_file = os.path.join(dir_path, program_file.filename)
	absolute_program_file_2 = os.path.join(dir_path, program_file_2.filename)
	absolute_brothers_file = os.path.join(dir_path, "ressources", brothers_file.filename)
	absolute_sono_file = os.path.join(dir_path, "ressources", sono_file.filename)
	absolute_welcome_file = os.path.join(dir_path, "ressources", welcome_file.filename)
	
	program_file.save(absolute_program_file)
	program_file_2.save(absolute_program_file_2)
	brothers_file.save(absolute_brothers_file)
	sono_file.save(absolute_sono_file)
	welcome_file.save(absolute_welcome_file)
	
	programmer = Programmer(absolute_program_file, absolute_program_file_2, absolute_brothers_file, absolute_sono_file, absolute_welcome_file)
	sono_program_dict = programmer.run()

	return sono_program_dict

@app.route('/submit', methods=["GET", "POST"])
def upload():
	
	if request.method == "POST":

		if request.form["submit_button"] == "Upload": 
			program_file = request.files["program_file"]
			program_file_2 = request.files["program_file_2"]
			brothers_file = request.files["micro_bro_file"]
			sono_file = request.files["sono_bro_file"]
			welcome_file = request.files["welcome_bro_file"]
			response = generate_program(program_file, program_file_2, brothers_file, sono_file, welcome_file)
			sono_program_dict, welcome_program_dict = response[0], response[1]

			# Formatting sono program for HTML
			items = format_dict_to_table(sono_program_dict, "sono")
			col_names = [key for key in items[0].keys()]
			contents = [[v for k,v in item.items()] for item in items]

			# Formatting welcome program for HTML
			print("wlecome dict: {}".format(welcome_program_dict))
			items = format_dict_to_table(welcome_program_dict, "welcome")
			welcome_col_names = [key for key in items[0].keys()]
			welcome_contents = [[v for k,v in item.items()] for item in items]

		elif request.form["submit_button"] == "Generate new program":

			return render_template("upload.html")

		dir_path = os.path.dirname(os.path.realpath(__file__))
		absolute_file = os.path.join(dir_path, "ressources", "results_content.txt")

		with open(absolute_file, "w") as my_txt:
			my_txt.write(str(col_names))
			my_txt.write("\n")
			my_txt.write(str(contents))
			my_txt.write("\n")
			my_txt.write(str(welcome_col_names))
			my_txt.write("\n")
			my_txt.write(str(welcome_contents))
		
		return render_template("table.html", keys=col_names, values_list=contents, welcome_keys=welcome_col_names, welcome_values_list=welcome_contents)
	
	return render_template("upload.html")

@app.route('/save_pdf/<mode>', methods=["GET", "POST"])
def save_pdf(mode):
	"""
	Save program to PDF

	:param mode: which program am I saving?
	:type mode: str

	:return: None
	"""
	dir_path = os.path.dirname(os.path.realpath(__file__))
	absolute_file = os.path.join(dir_path, "ressources", "results_content.txt")

	if os.path.exists(absolute_file):
		with open(absolute_file, "r") as my_txt:
			handle = my_txt.read()
			results = handle.split("\n")
			col_names = literal_eval(results[0])
			contents = literal_eval(results[1])
			welcome_col_names = literal_eval(results[2])
			welcome_contents = literal_eval(results[3])

	# Make a PDF straight from HTML in a string.
	if mode == "sono":
		html = render_template('table_to_pdf.html', keys=col_names, values_list=contents)
	elif mode == "welcome":
		html = render_template('table_to_pdf.html', keys=welcome_col_names, values_list=welcome_contents)
	
	return render_pdf(HTML(string=html))


if __name__ == '__main__':
	app.run(debug = True)

	# Connect via : http://localhost:5000/submit