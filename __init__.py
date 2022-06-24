"""
This __init__ file contains all functionality of creating report and exporting 
created report to Confluence.

To run this properly you need to add parameter -c or --config with name of configuration ini file
(example) python -m report_generation -c test_config

Program run:
1. Launching the tests by pytest with conditions specified in test_config.ini in [test] section
2. Generating csv report by allure to directory specified in test_config.ini in [file] section
3. Updating the Confluence page specified in test_config.ini in [page] section with the last generated report

Steps 1 and 2 can be omitted by typing -l or --load and only Confluence page update with last
generated report in directory specify in test_config.ini can be done
(example) python -m report_generation -c test_config -l

There is also an option to load tests description without loading results by typing -d or --description
(example) python -m report_generation -c test_config -d /works also with -l

To check what parameters are available type -h or --help.
"""

# ---------------------------------- TEST DOCSTRING TEMPLATE ----------------------------------
# 
# Every line must end with ";" that code can detect new line sign in docstring and do not to 
# confuse it with the new line sign in the csv file. Comma sign cannot be used since the test 
# docstring is saved in the csv file. To use parameters in docstring just put parameter in 
# braces - {parameter}. 
# 
# !!! To use this template, the allure library must be imported to the file with tests !!!
# 
# uncomment and use:
# 
# allure.dynamic.description(
#     f"""[REQUIREMENTS];
#         If header appears there must be requirement name, e.g. LWZ-090;
#         but this header is optional;
#         [TEST NAME];
#         There must be test name;
#         [TEST DESCRIPTION];
#         There must by test description;
#         [EXPECTED RESULT];
#         There must be expected result of the test;
#         [ACTUAL RESULT];
#         There must be actual result of the test;
#         [TEST SETUP];
#         There must be test setup;
#         [COMMENTS];
#         Comments are an option so header [COMMENTS] can be omitted;
#         """)
# 
# ---------------------------------------------------------------------------------------------

# ---------------------------------- CONFIG_NAME.INI TEMPLATE ---------------------------------
# 
# Template for ini file with configuration of test report directory, page and test conditions:
"""
[file]
    folder_name= ; name of the folder with test reports
    file_name= ; name that will be added to date and time
[page]
    url= ; general link to the Confluence (e.g. http://confluence.diehlako.local:8090/)
    page_id= ; id of the Confluence page
    page_title= ; title of the Confluence page
    page_space_key= ; space key of the Confluence page
[test]
    ; If there are no test conditions all tests will run
    ; (example) test_condition1= path\to\test.py
    ; (example) test_condition2= path\to\test.py::test_method
    ; (example) test_condition3= -m MARK
"""
# ---------------------------------------------------------------------------------------------


import os
import msvcrt
from configparser import ConfigParser
from argparse import ArgumentParser

from .CSVReport import CreateReport
from .ConfluenceDataloader import Dataloader


# In this parameter should be specified path to the directory with configuration files
CONFIG_DIR = "setup\\test_config"

# ArgumentParser for parsing parameters given in terminal
parser = ArgumentParser()
parser.add_argument(
    "-c", 
    "--config", 
    type=str, 
    help="Instead of CONFIG, enter the name of the ini file which contains the configuration of test report directory, page and test conditions"
    )
parser.add_argument(
    "-l", 
    "--load", 
    help="Skip creating report and load last created report to Confluence", 
    action="store_true"
    )
parser.add_argument(
    "-d", 
    "--description", 
    help="Load only description of tests and do not load results", 
    action="store_true"
    )
args = parser.parse_args()
CONFIG = os.path.join(CONFIG_DIR, args.config+".ini")
LOAD = args.load
DESCRIPTION_ONLY = args.description

# ConfigParser for parsing ini file with test configuration
test_config = ConfigParser()
test_config.read(CONFIG)
TEST_FOLDER_NAME = test_config['file']['folder_name']
TEST_FILE_NAME = test_config['file']['file_name']
URL = test_config['page']['url']
PAGE_ID = test_config['page']['page_id']
PAGE_TITLE = test_config['page']['page_title']
PAGE_SPACE_KEY = test_config['page']['page_space_key']
TEST_CONDITIONS = []
test_cond_items = test_config.items('test')
for name, condition in test_cond_items:
    TEST_CONDITIONS.append(condition)

# Generating the report
if not LOAD:
    results = CreateReport(
        folder_name=TEST_FOLDER_NAME,
        file_name=TEST_FILE_NAME,
        test_conditions=TEST_CONDITIONS
    )
    results.generate_report()

    print("\nDo you want to load generated report to Confluence? [y/n] ", end="")
    choice = msvcrt.getch().decode("utf-8")
    print()
else:
    choice = 'y'

# Loading report to the Confluence site
if choice == 'y':
    d = Dataloader(
        url=URL,
        page_id=PAGE_ID,
        page_title=PAGE_TITLE,
        page_space_key=PAGE_SPACE_KEY,
        csv_folder_name=TEST_FOLDER_NAME,
        csv_file_name=TEST_FILE_NAME,
        description_only=DESCRIPTION_ONLY
    )

    d.load_data_to_confluence()
    
