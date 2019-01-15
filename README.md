# program_management
Manage programs for the different meetings of my assembly of Jehovah's witnesses.

# Include resources dir with test files

sudo apt install git
git clone https://github.com/quillaur/program_management.git
sudo apt install virtualenv
virtualenv program_management/ -p /usr/bin/python3
cd program_management/
source ./bin/activate
pip3 install -r requirements.txt
mkdir resources
python3 flask_visualisation.py
http://localhost:5000/submit

# TODO
- Improve README.md
- Add test files and mode
- Change date format in output table
- Output results correctly in csv format
- Send updated csv files from windows
- Add rule about the WT reader (Hermann)
- Add a counting system which will allow to better choose brother to use