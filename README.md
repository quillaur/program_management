# program_management
Manage programs for the different meetings of my assembly of Jehovah's witnesses.

## Project deployment
Install git if you do not already have it.
'sudo apt install git'

Clone the project repository.
'git clone https://github.com/quillaur/program_management.git '

## Virtualenv creation
Install virtualenv if you do not already have it. 
'sudo apt install virtualenv'

Create the virutalenv directly inside
'virtualenv program_management/ -p /usr/bin/python3'
'cd program_management/ | source ./bin/activate'

Install the project python module requirements
'pip3 install -r requirements.txt'

## Program execution
'python3 flask_visualisation.py'

Go to http://localhost:5000/submit
Insert the requested files and click the "upload" button.
The result table should appear on your webpage.

# TODO
- Add test files and mode
- Change date format in output table
- Output results correctly in csv format
- Send updated csv files from windows
- Add rule about the WT reader (Hermann)
- Add a counting system which will allow to better choose brother to use