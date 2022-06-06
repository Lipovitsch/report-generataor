import os
import json
from datetime import datetime

import pytest
import pandas as pd


DF_NEWLINE_CHAR = "///n///" # DF stands for dataframe
CURRENT_PATH = os.getcwd() + "\\Test_data"


def delete_files_in_dir(dir_path: str):
    """Method to delete all files in directory specified by dir_path
    """
    if os.path.exists(dir_path):
        file_list = [f for f in os.listdir(dir_path)]
        for file in file_list:
            os.remove(dir_path + "\\" + file)


def get_number_of_tests():
        with open(CURRENT_PATH + "\\allure-report\\history\\history-trend.json") as f:
            data = json.load(f)
        return data[0]['data']['total']


def sort_csv(path: str):
    csv_df = pd.read_csv(path)
    csv_df = csv_df.sort_values(by=["Name"])
    csv_df.to_csv(path, index=False)


class CreateReport:
    """To generate report use generate_report(). This will generate report in directory specified by folder_name.
    Report will be named "DD-MM-YYYY HH-MM-SS file_name.csv"
    """

    def __init__(self, folder_name: str, file_name: str, test_conditions: list):
        self.folder_name = folder_name
        self.file_name = file_name
        self.test_conditions = test_conditions

    def __print_allure_report_file(self, path_to_csv: str):
        """This function prints out on a terminal report created in current run. Function can be skipped
        """
        # Number of spaces between columns "__|__" - two spaces on each side of "|"
        col_separate_spaces = 2

        # Import all data from file
        with open(path_to_csv, "r") as f:
            data_from_file = f.read()

        # Remove no needed characters from data and change new lines in description
        data_from_file_filtered = data_from_file.replace('"', '')
        # data_from_file_filtered = data_from_file_filtered.replace("-\n", "\\")
        # data_from_file_filtered = data_from_file_filtered.replace("    ", "")
        data_from_file_filtered = data_from_file_filtered.replace("\n", ",")

        # Check column length
        data_to_check_columns_number = data_from_file.split("\n")
        data_to_check_columns_number_1list = data_to_check_columns_number[0].split(",")
        columns_number = len(data_to_check_columns_number_1list)

        # Split data to 1D list
        data_1d = data_from_file_filtered.split(",")

        # Split data to 2D list
        data_2d = []
        row_list = []
        rows_number = len(data_1d)//columns_number
        for i in range(rows_number):
            for j in range(columns_number):
                row_list.append(data_1d[i * columns_number + j])
            data_2d.append(row_list[::])
            row_list.clear()

        # Count each column max length to print out data nicely
        temp_column_length = []
        column_length = []
        for j in range(len(data_2d[0])):
            for i in range(len(data_2d)):
                temp_column_length.append(len(data_2d[i][j]))
            column_length.append(max(temp_column_length))
            temp_column_length.clear()

        # Printing data on terminal
        print("\n\n")
        for i in range(len(data_2d)):
            for j in range(len(data_2d[0])):
                num_of_spaces = column_length[j] - len(data_2d[i][j])
                if j == 0:
                    print("|", end=" " * col_separate_spaces)
                print(data_2d[i][j] + " " * num_of_spaces + " " * col_separate_spaces + "|", end=" " * col_separate_spaces)
            print()

    def __check_csv_report(self, path_to_csv: str):
        test_no = get_number_of_tests()
        with open(path_to_csv, "r") as f:
            for i, l in enumerate(f):
                pass
            if i != test_no:
                raise RuntimeError("An error occurred during checking csv file, possible lack of semicolon in test docstring. Open generated csv file to check error")
    
    def __rewrite_generated_report(self, path_to_csv: str):
        """Copy files from allure-report to TEST_FOLDER_NAME and change name to DD-MM-YYYY HH-MM-SS TEST_FILE_NAME,
        also change newline characters in the test docstring to a character that represents the newline in html
        """
        with open(CURRENT_PATH + "\\allure-report\\data\\suites.csv", "r") as file_r:
            data_report = file_r.read()

        data_report = data_report.replace(";\n", DF_NEWLINE_CHAR)
        data_report = data_report.replace("    ", "")
        
        if not os.path.exists(CURRENT_PATH + "\\" + self.folder_name):
                os.mkdir(CURRENT_PATH + "\\" + self.folder_name)
                
        with open(path_to_csv, "w") as file_w:
            file_w.write(data_report)

    def generate_report(self):
        """Generates report to directory named folder_name. Generated file name is "DD-MM-YYYY HH-MM-SS file_name.csv"
        """
        if not os.path.exists(CURRENT_PATH):
            os.mkdir(CURRENT_PATH)

        # Delete JSON files from last run
        delete_files_in_dir(CURRENT_PATH + "\\allure_results")

        # Run tests and create results as JSON files in directory allure_results
        self.test_conditions.insert(0, "-s")
        self.test_conditions.insert(0, "--alluredir=" + CURRENT_PATH + "\\allure_results")
        pytest.main(self.test_conditions)

        # Generate report from JSON files which contains needed .csv file
        os.system("allure generate " + CURRENT_PATH + "\\allure_results" + " --clean -o " + CURRENT_PATH + "\\allure-report")

        # Get the current date and time needed to rename report file
        now = datetime.now()
        # Change date and time to string
        date_time = now.strftime("%Y-%m-%d %H-%M-%S")
        
        path_to_csv = CURRENT_PATH + "\\" + self.folder_name + "\\" + date_time + " " + self.file_name + ".csv"
        
        test_no = get_number_of_tests()
        if test_no > 0:
            # Rewrite report to TEST_FOLDER_NAME
            self.__rewrite_generated_report(path_to_csv)
            
            # Check if rewrited csv report is ok
            self.__check_csv_report(path_to_csv)
            
            # Sort data in generated report by test name
            sort_csv(path_to_csv)

            # Print generated report file in terminal
            # self.__print_allure_report_file(path_to_csv)
        