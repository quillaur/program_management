# program_management
Manage programs for the different meetings of my assembly of Jehovah's witnesses.
The goal is to take the following programs to then build the sono team program according to brothers availibility:
- Week-end program (CSV)
- Mid-week program (PDF)
- Welcome program (CSV)

## Project deployment
Install git if you do not already have it.
```shell
sudo apt install git
```

Clone the project repository.
```shell
git clone https://github.com/quillaur/program_management.git
```

## Virtualenv creation
Install virtualenv if you do not already have it. 
```shell
sudo apt install virtualenv
```

Create the virutalenv using the main project directory (i.e the following command line) or another directory of your choice (not showed here).
```shell
virtualenv program_management/ -p /usr/bin/python3
```
```shell
cd program_management/ | source ./bin/activate
```

Install the project python module requirements
```shell
pip3 install -r requirements.txt
```

## Create your config
Open the "config.cfg.dist" file into your favorite text 
editor and change the "BROTHER_PATH" key so that path 
corresponds to where you deployed 
the "program_management" project.

Once done, save it as "config.cfg" in your 
"program_management" directory.

## Program execution
```shell
python3 flask_visualisation.py
```

Go to http://localhost:5000/submit
Insert the requested files and click the "upload" button.
The result table should appear on your webpage.
