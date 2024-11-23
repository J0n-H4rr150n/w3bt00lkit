# w3bt00lkit
Command-line web application security toolkit.  

## Install

1. Clone the repo
2. Create a python virtual environment
3. Install requirements
4. Create an `alias` to load the virtual environment and then the `main.py` script in the `src` folder
5. Make sure `PostgreSQL` is running locally
6. Run the toolkit with the `alias`
7. Create the database tables and insert initial data to the database.
    - `w3bt00lkit` > `database`
    - `w3bt00lkit (database)` > `setup`

### Style and Syntax  
`pylint ./src --output=pylint.txt ; cat pylint.txt`  

### Units Tests and Code Coverage  
`coverage run -m unittest discover -s src/tests/ && coverage report`  

### Generate Documentation  
From the `src` folder:  
`pdoc --html . --output-dir ../docs`  

Then go to `docs/src/index.html` to view the generated documentation.  

## Features

## General Features
1. Tab suggestion / completion  
2. Typing `clear` or `cls` followed by `enter` will clear the screen.
2. `back` menu option
3. `help` menu option
4. `exit` menu option

## Custom Features
1. Targets
    1. Add a new target and save it in the database.
    2. List all active targets from the database.
    3. Select a target to be used throughout the entire w3bt00lkit.
2. Manage the database
3. Checklists
    1. OWASP Web Security Testing Guide (WSTG)

## Integrations
1. Integration with man-in-the-middle proxy ([mitmproxy](https://github.com/mitmproxy/mitmproxy)).  

## Roadmap

1. Add the ability to add scopes (in/out) to a target.
2. Update the proxy code to store additional information in the database.
3. Integrate existing tools into the w3bt00lkit and store the results in the database.
4. TBD...
