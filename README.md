# program_management
Manage programs for the different meetings of my assembly of Jehovah's witnesses.

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

## Program execution
```shell
python3 flask_visualisation.py
```

Go to http://localhost:5000/submit
Insert the requested files and click the "upload" button.
The result table should appear on your webpage.

# TO DO
- Fix count of brothers to include sono brothers in passing mikes.