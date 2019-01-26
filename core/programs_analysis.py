#!/usr/bin/env python
# Contact: aurelienquillet@gmail.com
# Date: 28/10/2018
# Purpose: Automatically generating programs for sono team and welcome center

import configparser
import os
import PyPDF2
import fitz
from unidecode import unidecode
from collections import OrderedDict
from random import sample
import csv
import mysql.connector
from datetime import datetime

class Programmer():

	def __init__(self, program_file: str, program_file_2: str, input_date: str):
		""" 
		Programmer init

		:param program_file: PDF file path loaded by the user
		:type program_file: str
		"""
		# get config
		config = configparser.ConfigParser()
		dir_path = os.path.dirname(os.path.realpath(__file__))
		dir_path = dir_path.replace("core", "")
		config_file_path = os.path.join(dir_path, "config.cfg")
		
		if os.path.isfile(config_file_path):
			config.read(config_file_path)
		else:
			print("Could not find config file !\n{}".format(config_file_path))

		# Connect to DB
		# self.mydb = mysql.connector.connect(database=config_parser["CONNECTION"]["DATABASE"], 
		# 	host= config_parser["CONNECTION"]["HOST"], 
		# 	user=config_parser["CONNECTION"]["USER"], 
		# 	passwd=config_parser["CONNECTION"]["PASSWORD"])

		# self.cur = self.mydb.cursor()

		if program_file is not None:
			# Input and output files
			self.input_file = os.path.abspath(program_file)
			self.input_file_2 = os.path.abspath(program_file_2)
			self.output_csv = os.path.join(dir_path, "sono_program.csv")

			# Class variables
			self.months_list = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", 
			"septembre", "octobre", "novembre", "décembre"]
			self.input_date = input_date
			
			self.brothers_list = []
			with open(config["FILES"]["MICRO_BROS"], "r") as my_csv:
				handle = csv.reader(my_csv)
				for row in handle:
					self.brothers_list.append(row[0])
			
			self.sono_list = []
			with open(config["FILES"]["SONO_BROS"], "r") as my_csv:
				handle = csv.reader(my_csv)
				for row in handle:
					self.sono_list.append(row[0])

			self.welcome_list = []
			with open(config["FILES"]["WELCOME_BROS"], "r") as my_csv:
				handle = csv.reader(my_csv)
				for row in handle:
					self.welcome_list.append(row[0])
			
			self.brother_actions_dict = OrderedDict()
			self.sono_program_dict = OrderedDict()
			self.welcome_program_dict = OrderedDict()
			self.month_str_to_int = {"janvier": "01", "fevrier": "02", "mars": "03", "avril": "04", "mai": "05", "juin": "06", "juillet": "07", "aout": "08", "septembre": "09", "octobre": "10", "novembre": "11", "decembre": "12"}

			self.weekend_dates = []
			self.weekends_bro = []
			self.busy_bro_list = []
			self.other_language_bro = []

			self.wt_conductor = "Delapille"

	def insert_DB(self, date, name, part):
		"""
		Insert date and names of meeting actors.

		:param date: date of the meeting
		:type date: date

		:param name: actor during this meeting
		:type name: str

		:param part: part of the meeting during which the actor acts
		:type part: str

		:return: None
		"""
		data_dict = {"DATE": date, "NAME": name, "PART": part}
		query = "INSERT INTO date_actors (date, name, part) VALUES (%(DATE)s, %(NAME)s, %(PART)s);"

		self.cur.execute(query, data_dict)
		self.mydb.commit()

	def extract_text_from_pdf_file(self, filename: str):
		"""
		Extract text content from PDF file

		:param filename: absolute file path
		:type filename: str

		:return: list of lines from the PDF extracted text
		:rtype: list
		"""
		pdfFileObject = open(filename, 'rb')
		pdfReader = PyPDF2.PdfFileReader(pdfFileObject, strict=False)
		count = pdfReader.numPages
		pdf_text = []
		
		for i in range(count):
			page = pdfReader.getPage(i)
			pdf_text.extend(page.extractText().split("\n"))

		# Remove undesired elements from the list
		clean_pdf_text = [line for line in pdf_text if len(line) > 1]

		return clean_pdf_text

	def get_brother_actions(self, clean_pdf_text: list):
		"""
		Put in a dictionary which brothers are busy for the part 1 of the meeting or for part 2.

		:param clean_pdf_text: list of lines from the PDF extracted text
		:type clean_pdf_text: list

		:return: list of lines from the extracted text
		:rtype: list
		"""
		###########################################################################
		######################## WEEK-END MEETINGS INFO ###########################
		###########################################################################
		with open(self.input_file_2, "r") as my_csv:
			handle = csv.reader(my_csv, delimiter=';')
			next(handle)

			for row in handle:
				self.weekend_dates.append(row[0])
				self.weekends_bro.append(row[1:])

		###########################################################################
		######################### WEEKLY MEETINGS INFO ############################
		###########################################################################
		# Init tags
		part_1 = False
		part_2 = False

		# Analyse text
		for line in clean_pdf_text:

			# Looking for a date
			if part_1 is False:
				
				# Add a space to month search to be more specific and remove accents and capitalize letters
				month = " " + unidecode(self.input_date.lower())

				if month in unidecode(line.lower()):
					print(month)
					print(str(datetime.today().year))
					date = " ".join([line.strip().split(" ")[0], self.month_str_to_int[month.strip()], str(datetime.today().year)])

					# We enter the first part of the meeting
					part_1 = True

					if date not in self.brother_actions_dict.keys():
						# Declare and insert keys individually to keep order in the dict							
						self.brother_actions_dict[date] = OrderedDict()
						self.brother_actions_dict[date]["Part_1"] = []
						self.brother_actions_dict[date]["Part_2"] = []

			# If we enter the "Vie Chrétienne" part, then set part tags accordingly
			elif "CHRÉTIENNE" in line:
				part_1 = False
				part_2 = True

			# If we are in the first or second part of the meeting, then look for brothers
			if part_1 or part_2:
				all_brothers = self.brothers_list + self.sono_list
				
				for brother in all_brothers:

					if part_1:

						if unidecode(brother.lower()) in unidecode(line.lower()):
							self.brother_actions_dict[date]["Part_1"].append(brother)

					elif part_2:

						if unidecode(brother.lower()) in unidecode(line.lower()):
							self.brother_actions_dict[date]["Part_2"].append(brother)

		print("####################################################################")
		print("######################## MAIN SCHEDULE INFO ########################")
		print("####################################################################")
		for key in self.brother_actions_dict.keys():
			print("\nDate: {}".format(key))

			for key_1 in self.brother_actions_dict[key].keys():
				self.brother_actions_dict[key][key_1] = list(set(self.brother_actions_dict[key][key_1]))
				print("{}: {}".format(key_1, self.brother_actions_dict[key][key_1]))

	def make_sono_program(self):
		"""
		Create a program for the sono team based on brother availability.

		:return: None
		"""
		# Order dates to do the sono program for
		date_list = [x for x in self.brother_actions_dict.keys()]
		ordered_dates = []
		for dates in zip(self.weekend_dates, date_list):
			ordered_dates.extend(dates)

		# Init program dict
		for date in ordered_dates:

			if date not in self.sono_program_dict.keys():
				self.sono_program_dict[date] = OrderedDict()
				self.sono_program_dict[date]["Sono"] = ""
				self.sono_program_dict[date]["Part 1"] = []
				self.sono_program_dict[date]["Part 2"] = []
				self.sono_program_dict[date]["Scène"] = ""
		
		for i, v in enumerate(ordered_dates):
			# Week-end brother management
			if v in self.weekend_dates:
				# Keep available brothers
				sono_list = [x for x in self.sono_list if x not in self.weekends_bro]
				brothers_part_1_list = [x for x in self.brothers_list if x not in self.weekends_bro and self.wt_conductor not in x and x not in self.other_language_bro]
				brothers_part_2_list = [x for x in self.brothers_list if x not in self.weekends_bro and self.wt_conductor not in x and x not in self.other_language_bro]
				potential_stage_brothers = [x for x in self.brothers_list if x not in self.weekends_bro]

			# Mid-week brother management
			else:
				# Keep available brothers
				sono_list = [x for x in self.sono_list if x not in self.brother_actions_dict[v]["Part_1"] and x not in self.brother_actions_dict[v]["Part_2"]]
				brothers_part_1_list = [x for x in self.brothers_list if x not in self.brother_actions_dict[v]["Part_1"]]
				brothers_part_2_list = [x for x in self.brothers_list if x not in self.brother_actions_dict[v]["Part_2"]]
				potential_stage_brothers = [x for x in self.brothers_list if x not in self.brother_actions_dict[v]["Part_1"] and x not in self.brother_actions_dict[v]["Part_2"]]

			# randomize list
			sono_list = sample(sono_list, len(sono_list))
			brothers_part_1_list = sample(brothers_part_1_list, len(brothers_part_1_list))
			brothers_part_2_list = sample(brothers_part_2_list, len(brothers_part_2_list))
			potential_stage_brothers = sample(potential_stage_brothers, len(potential_stage_brothers))

			# Looking for sono brother first
			if len(sono_list) > 0:
				# Put the first bro of the list unless he already did sono last time
				if i != 0: 
					
					if sono_list[0] not in self.sono_program_dict[ordered_dates[i-1]]["Sono"]:
						self.sono_program_dict[v]["Sono"] = sono_list[0]
						self.busy_bro_list.append(sono_list[0])
						del sono_list[0]
					
					else:
						self.sono_program_dict[v]["Sono"] = sono_list[1]
						self.busy_bro_list.append(sono_list[1])
						del sono_list[1]
				
				else:
					self.sono_program_dict[v]["Sono"] = sono_list[0]
					self.busy_bro_list.append(sono_list[0])
					del sono_list[0]

			else:
				print("WARNING: no brother found for sono for {}".format(v))

			# Looking for stage bro, first looking through sono team
			if len(sono_list) > 0:
				# Put the first bro of the list unless he already did stage last time
				if i != 0: 
					
					if sono_list[0] not in self.sono_program_dict[ordered_dates[i-1]]["Scène"]:
						self.sono_program_dict[v]["Scène"] = sono_list[0]
						self.busy_bro_list.append(sono_list[0])
						del sono_list[0]
					
					else:
						self.sono_program_dict[v]["Scène"] = sono_list[1]
						self.busy_bro_list.append(sono_list[1])
						del sono_list[1]
				
				else:
					self.sono_program_dict[v]["Scène"] = sono_list[0]
					self.busy_bro_list.append(sono_list[0])
					del sono_list[0]

			else:
				self.sono_program_dict[v]["Scène"] = potential_stage_brothers[0]
				self.busy_bro_list.append(potential_stage_brothers[0])
				del potential_stage_brothers[0]

			# Now microphones part 1
			if len(brothers_part_1_list) > 1:

				for brother in brothers_part_1_list[:2]:
					self.sono_program_dict[v]["Part 1"].append(brother)
					self.busy_bro_list.append(brother)
					# Remove bro from potential second part of the reunion
					if brother in brothers_part_2_list:
						brothers_part_2_list.remove(brother)

			# Now microphones part 2
			if len(brothers_part_2_list) > 1:

				for brother in brothers_part_2_list[:2]:
					self.sono_program_dict[v]["Part 2"].append(brother)
					self.busy_bro_list.append(brother)
		
		print("\n####################################################################")
		print("######################## Sono SCHEDULE INFO ########################")
		print("####################################################################")
		for date in self.sono_program_dict.keys():
			print("\nDate: {}".format(date))

			for key in self.sono_program_dict[date].keys():
				print("{} : {}".format(key, self.sono_program_dict[date][key]))

	def make_welcome_program(self):
		"""
		Create a program for the welcome team based on brother availability.

		:return: None
		"""
		# Order dates to do the sono program for
		date_list = [x for x in self.brother_actions_dict.keys()]
		ordered_dates = []
		for dates in zip(self.weekend_dates, date_list):
			ordered_dates.extend(dates)
		# Init program dict
		for date in ordered_dates:

			if date not in self.welcome_program_dict.keys():
				self.welcome_program_dict[date] = []

		for i, v in enumerate(ordered_dates):
			# Week-end brother management
			if v in self.weekend_dates:
				# Keep available brothers
				welcome_list = [x for x in self.welcome_list if x not in self.weekends_bro and x not in self.busy_bro_list]

			# Mid-week brother management
			else:
				# Keep available brothers
				welcome_list = [x for x in self.welcome_list if x not in self.brother_actions_dict[v]["Part_1"] and x not in self.brother_actions_dict[v]["Part_2"] and x not in self.busy_bro_list]

			if len(welcome_list) > 0:
				# Put the first bro of the list unless he already did the welcome role last time
				if i != 0: 

					if welcome_list[0] not in self.welcome_program_dict[ordered_dates[i-1]]:
						self.welcome_program_dict[v] = welcome_list[0]
						self.busy_bro_list.append(welcome_list[0])
						del welcome_list[0]
					
					else:
						self.welcome_program_dict[v] = welcome_list[1]
						self.busy_bro_list.append(welcome_list[1])
						del welcome_list[1]
				
				else:
					self.welcome_program_dict[v] = welcome_list[0]
					self.busy_bro_list.append(welcome_list[0])
					del welcome_list[0]

			else:
				print("WARNING: no brother found for welcome for {}".format(v))

	def print_to_csv(self):
		"""
		Print sono program to CSV file.

		:return: None
		"""
		with open(self.output_csv, "w") as csv_file:
			writer = csv.writer(csv_file, delimiter=';')
			header = ["Date", "Sono", "Micro part 1", "Micro part 2", "Scène"]
			writer.writerow(header)
			
			for date in self.sono_program_dict.keys():
				tmp_data = [date, self.sono_program_dict[date]["Sono"], 
				"/".join([self.sono_program_dict[date]["Part 1"][0], self.sono_program_dict[date]["Part 1"][1]]), 
				"/".join([self.sono_program_dict[date]["Part 2"][0], self.sono_program_dict[date]["Part 2"][1]]),
				self.sono_program_dict[date]["Scène"]]
				writer.writerow(tmp_data)

	def run(self):
		"""
		Order of execution of the Programmer class.

		:return: None
		"""
		clean_pdf_text = self.extract_text_from_pdf_file(self.input_file)
		self.get_brother_actions(clean_pdf_text)
		self.make_sono_program()
		self.make_welcome_program()
		self.print_to_csv()

		return [self.sono_program_dict, self.welcome_program_dict]


if __name__ == "__main__":
	programmer = Programmer()
	programmer.run()