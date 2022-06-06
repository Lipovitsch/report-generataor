import os
import msvcrt
from datetime import datetime

import pandas as pd
from atlassian import Confluence


# Html code of requirements is replaced by ///div0///, ///div1/// and so on, depends on the number of requirements in the table
# Those are used in replace_signs_html_to_dataframe() and replace_signs_dataframe_to_html()
DF_SUCCESS_CHAR = "(/) Success" # DF stands for dataframe
DF_FAIL_CHAR = "(x) Fail"
DF_TABLE_CHAR = "///TABLE///"
DF_NEWLINE_CHAR = "///n///"
DF_STRONG_START_CHAR = "///ss///"
DF_STRONG_END_CHAR = "///es///"
DF_EM_START_CHAR = "///sem///"
DF_EM_END_CHAR = "///eem///"
DF_DIV_DISPLAY_START_CHAR = "///sdd///"
DF_DIV_DISPLAY_END_CHAR = "///edd///"
DF_REQUIREMENTS = []
HTML_REQUIREMENTS = """<div class="content-wrapper"><p><ac:structured-macro ac:name="requirement" ac:schema-version="1" ac:macro-id="53ae0f9b-4084-4e31-88c3-aba88e1eec3b"><ac:parameter ac:name="spaceKey">LWZ</ac:parameter><ac:parameter ac:name="freetext">Link</ac:parameter><ac:parameter ac:name="type">LINK</ac:parameter><ac:parameter ac:name="key">%s</ac:parameter></ac:structured-macro></p></div>"""
HTML_FAIL_CHAR = """
    <div class="content-wrapper">
    <p><ac:structured-macro ac:name="ry-test-result" ac:schema-version="1" ac:macro-id="9b70be61-3d37-4eed-98b2-ee4219283dac"><ac:parameter ac:name="status">(x) Fail</ac:parameter></ac:structured-macro></p></div>
    """
HTML_SUCCESS_CHAR = """
    <div class="content-wrapper">
    <p><ac:structured-macro ac:name="ry-test-result" ac:schema-version="1" ac:macro-id="7a735669-c8e8-4dad-99d6-3b9f37233d0a"><ac:parameter ac:name="status">(/) Success</ac:parameter></ac:structured-macro></p></div>
    """
DOCSTRING_HEADERS = ["[REQUIREMENTS]", "[TEST NAME]", "[TEST DESCRIPTION]", "[EXPECTED RESULT]", "[TEST SETUP]", "[COMMENTS]"]
TABLE_HEADER = {
    "Requirements": "Requirements",
    "Test Name": "Test Name",
    "Test Description": "Test Description",
    "Expected Result": "Expected Result",
    "Result": "Result",
    "Tester": "Tester",
    "Date": "Date",
    "Test Setup": "Test Setup",
    "Previous Results": "Previous Results",
    "Comments": "Comments"
}


def get_date():
    """Method returns date DD.MM.YYYY as a string
    """
    now = datetime.now()
    string_date = now.strftime("%d.%m.%Y")
    # string_time = now.strftime("%H:%M:%S")
    return string_date


def search_test_name_html(html_data_frame: pd.DataFrame, test_name_to_sign_result: str):
    """Search for hidden test name in dataframe generated from html table
    To know characters description see signs_to_replace() method
    """
    for i in range(len(html_data_frame)):
        test_name = html_data_frame.loc[i, TABLE_HEADER["Test Name"]]
        div_end = test_name.find(DF_DIV_DISPLAY_END_CHAR)
        if test_name[:div_end] == DF_DIV_DISPLAY_START_CHAR + test_name_to_sign_result:
            return i
    return -1


def search_test_name_csv(csv_data_frame: pd.DataFrame, test_name_search: str):
    """Search for the test name in the csv report file and return its row number
    """
    for i in range(len(csv_data_frame)):
        test_name = csv_data_frame.loc[i, "Name"]
        if test_name == test_name_search:
            return i


def search_div_requirement(conf_page_body: str):
    """In html code of given Confluence page body search for string of characters 
    that starts with <div and ends with </div> statement and contains "requirement" 
    keyword and return a list of these strings
    """
    div_start = 0
    div_end = 0
    req_div_list = []
    for i in range(conf_page_body.count('<div')):
        div_start = conf_page_body.find('<div', div_start + 4)
        div_end = conf_page_body.find('</div>', div_end + 6)
        if "requirement" in conf_page_body[div_start:(div_end + 6)]:
            req_div_list.append(conf_page_body[div_start:(div_end + 6)])
    return req_div_list


def search_content_outside_table(conf_page_body: str):
    """In html code of given Confluence page body search for the table with at least 
    10 headers (because this is table with test cases), replace it with TEST_CASES_TABLE_CHAR
    and return html code with replaced table that later will be modified
    """
    table_start = 0
    for i in range(conf_page_body.count('<table')):
        table_start = conf_page_body.find('<table', table_start + 6)

    if table_start != -1:
        tr_start = conf_page_body.find('<tr', table_start)
        tr_end = conf_page_body.find('</tr>', table_start)
        td_count = conf_page_body.count('<th', tr_start, tr_end)
        if td_count < 10:
            return conf_page_body

        table_end = conf_page_body.find('</table>', table_start)
        content = conf_page_body.replace(conf_page_body[table_start:table_end + 8], DF_TABLE_CHAR)
        return content
    return conf_page_body


def replace_signs_html_to_dataframe(conf_page_body: str, req_div_list: list[str]):
    """Replace certain characters in the html code before converting to dataframe
    to avoid losing them
    """
    
    signs_to_replace = {
        '<br />': DF_NEWLINE_CHAR,
        '<strong>': DF_STRONG_START_CHAR,
        '</strong>': DF_STRONG_END_CHAR,
        '<em>': DF_EM_START_CHAR,
        '</em>': DF_EM_END_CHAR,
        '<div style="display: none;">': DF_DIV_DISPLAY_START_CHAR,
    }

    div_display_search_index = 0
    for i in range(conf_page_body.count('<div style="display: none;">')):
        div_display_start = conf_page_body.find('<div style="display: none;">', div_display_search_index)
        div_display_end_start = conf_page_body.find('</div>', div_display_start)
        div_display_search_index = div_display_start + len('<div style="display: none;">')
        conf_page_body = conf_page_body[:div_display_end_start] + DF_DIV_DISPLAY_END_CHAR + conf_page_body[div_display_end_start + 6:]

    if len(req_div_list) > 0:
        for i in range(len(req_div_list)):
            signs_to_replace[req_div_list[i]] = f"///div{i}///"

    for key in signs_to_replace.keys():
        conf_page_body = conf_page_body.replace(key, signs_to_replace[key])

    return conf_page_body


def replace_signs_dataframe_to_html(df_data: str, req_div_list: list[str]):
    """Replace back characters to html code after converting dataframe to html
    """
    signs_to_replace = {
        DF_FAIL_CHAR: HTML_FAIL_CHAR,
        DF_SUCCESS_CHAR: HTML_SUCCESS_CHAR,
        'NaN': '',
        DF_NEWLINE_CHAR: '<br />',
        DF_STRONG_START_CHAR: '<strong>',
        DF_STRONG_END_CHAR: '</strong>',
        DF_EM_START_CHAR: '<em>',
        DF_EM_END_CHAR: '</em>',
        DF_DIV_DISPLAY_START_CHAR: '<div style="display: none;">',
        DF_DIV_DISPLAY_END_CHAR: '</div>',
    }
    
    if DF_REQUIREMENTS != []:
        for req in DF_REQUIREMENTS:
            r = req[3:-3]
            r = r.replace(DF_NEWLINE_CHAR, "")
            df_data = df_data.replace(req, HTML_REQUIREMENTS % r)
    
    if len(req_div_list) > 0:
        for i in range(len(req_div_list)):
            signs_to_replace[f"///div{i}///"] = req_div_list[i]

    for key in signs_to_replace.keys():
        df_data = df_data.replace(key, signs_to_replace[key])

    return df_data


def get_pass():
    """Control echo in the terminal to safely enter the password
    """
    print("Password: ", end="", flush=True)
    password = ''
    while True:
        x = msvcrt.getch().decode("utf-8")
        if x == '\r' or x == '\n':
            break
        if x == "\x08":
            password = password[0:-1]
            continue
        password += x
    print()
    return password


class Dataloader:
    """To load data from last created csv report to Confluence use load_data_to_confluence() method
    """
    def __init__(self, url: str, page_id: str, page_title: str, page_space_key: str, csv_folder_name: str, csv_file_name: str, description_only: bool = False):
        self.url = url
        self.page_id = page_id
        self.page_title = page_title
        self.page_space_key = page_space_key
        self.csv_dir = os.path.join("Test_data", csv_folder_name)
        self.csv_file_name = csv_file_name
        self.description_only = description_only
        self.__tester_name = ''
        
        listing = os.listdir(path=self.csv_dir)
        csv_files = [item for item in listing if item.endswith(self.csv_file_name + '.csv')]
        try:
            self.csv_df = pd.read_csv(os.path.join(self.csv_dir, csv_files[-1]))
        except IndexError:
            raise RuntimeError("CSV File does not exist")
        
        print(f"\nUPLOADING THE FILE:\n{self.csv_dir}\{csv_files[-1]}")
        print(f"ON THE PAGE TITLED:\n{self.page_title}")
        print("\nCONFLUENCE CREDENTIALS")
        self.__login = input("User name: ")
        password = get_pass()

        self.__confluence = Confluence(
            url=self.url,
            username=self.__login,
            password=password,
        )

    def __get_tester_name(self):
        """Get tester name and surname"""
        self.__tester_name = self.__confluence.get_user_details_by_username(self.__login, expand=None)['displayName']
    
    def __create_table_header(self, content: str):
        """Creates table header on given Confluence page
        """
        table = """<table border="1" class="dataframe">
        <thead>
        <tr style="text-align: right;">
        """
        for key in TABLE_HEADER.keys():
            table = table + "<th>" + TABLE_HEADER[key] + "</th>\n"
        
        table = table + "</tr></thead>\n<tbody></tbody>\n</table>"
        
        self.__confluence.update_page(
            page_id=self.page_id,
            title=self.page_title,
            body=content + table
        )
        
        return content + DF_TABLE_CHAR

    def __update_table_data(self, html_data_frame: pd.DataFrame, csv_data_frame: pd.DataFrame):
        """Method updates html dataframe with results from csv dataframe and creates temporary 
        file with converted dataframe to html code
        """
        
        csv_status_to_html = {
            "passed": DF_SUCCESS_CHAR,
            "failed": DF_FAIL_CHAR
        }
        last_result_change = {
            DF_SUCCESS_CHAR: "Success",
            DF_FAIL_CHAR: "Fail"
        }
        
        self.__get_tester_name()

        csv_name_list = [test_name for test_name in csv_data_frame.Name]
        # csv_name_list.sort()

        for i in range(len(csv_name_list)): 
            csv_row = search_test_name_csv(csv_data_frame, csv_name_list[i])

            csv_status = csv_data_frame.loc[csv_row, "Status"]
            # If status is not "passed" or "failed" then skip updating table
            if csv_status not in csv_status_to_html.keys():
                continue
            
            # Reading elements from the test docstring
            
            csv_desc = csv_data_frame.loc[csv_row, "Description"]
            req_start = csv_desc.find(DOCSTRING_HEADERS[0])
            name_start = csv_desc.find(DOCSTRING_HEADERS[1])
            name_end = csv_desc.find(DOCSTRING_HEADERS[2])
            desc_end = csv_desc.find(DOCSTRING_HEADERS[3])
            exp_end = csv_desc.find(DOCSTRING_HEADERS[4])
            setup_end = csv_desc.find(DOCSTRING_HEADERS[5])
            
            
            newline_char_len = len(DF_NEWLINE_CHAR)
            req_header_len = len(DOCSTRING_HEADERS[0]) + newline_char_len
            test_name_header_len = len(DOCSTRING_HEADERS[1]) + newline_char_len
            test_desc_header_len = len(DOCSTRING_HEADERS[2]) + newline_char_len
            exp_result_header_len = len(DOCSTRING_HEADERS[3]) + newline_char_len
            test_setup_header_len = len(DOCSTRING_HEADERS[4]) + newline_char_len
            comments_header_len = len(DOCSTRING_HEADERS[5]) + newline_char_len
            

            if name_start == -1 or name_end == -1 or desc_end == -1 or exp_end == -1:
                raise ValueError("One or more of the mandatory headers could not be found in the test docstring")
            
            if req_start != -1:
                if not (req_start < name_start and name_start < name_end and name_end < desc_end and desc_end < exp_end):
                    raise ValueError("Wrong order of the headers in the test docstring")
            else:
                if not (name_start < name_end and name_end < desc_end and desc_end < exp_end):
                    raise ValueError("Wrong order of the headers in the test docstring")
            
            if req_start != -1:
                csv_req = csv_desc[req_start + req_header_len:name_start]
                if csv_req == '':
                    raise ValueError('"Requirements" cell cannot be empty')
            
            csv_test_name = csv_desc[name_start + test_name_header_len:name_end]
            if csv_test_name == '':
                raise ValueError('"Test Name" cell cannot be empty')

            csv_test_description = csv_desc[name_end + test_desc_header_len:desc_end]
            if csv_test_description == '':
                raise ValueError('"Test Description" cell cannot be empty')

            csv_expected_result = csv_desc[desc_end + exp_result_header_len:exp_end]
            if csv_expected_result == '':
                raise ValueError('"Expected Result" cell cannot be empty')

            if setup_end == -1:
                csv_test_setup = csv_desc[exp_end + test_setup_header_len:-newline_char_len]
            else:
                if not exp_end < setup_end:
                    raise ValueError("Wrong order of the headers in the test docstring")
                csv_test_setup = csv_desc[exp_end + test_setup_header_len:setup_end]
            if csv_test_setup == '':
                raise ValueError('"Test Setup" cell cannot be empty')

            if setup_end != -1:
                csv_comments = csv_desc[setup_end + comments_header_len:]

            test_name_row = search_test_name_html(html_data_frame, csv_name_list[i])

            if test_name_row != -1 and not self.description_only:
                last_result = html_data_frame.loc[test_name_row, TABLE_HEADER["Result"]]
                last_test_setup = html_data_frame.loc[test_name_row, TABLE_HEADER["Test Setup"]]
                if last_test_setup[-newline_char_len:] == DF_NEWLINE_CHAR:
                    last_test_setup = last_test_setup[:-newline_char_len]

                if html_data_frame.loc[test_name_row, TABLE_HEADER["Previous Results"]] == DF_NEWLINE_CHAR:
                    html_data_frame.loc[test_name_row, TABLE_HEADER["Previous Results"]] = \
                        last_result_change[last_result] + DF_NEWLINE_CHAR + last_test_setup
                else:
                    html_data_frame.loc[test_name_row, TABLE_HEADER["Previous Results"]] = \
                        last_result_change[last_result] + DF_NEWLINE_CHAR + last_test_setup \
                        + 2*DF_NEWLINE_CHAR + html_data_frame.loc[test_name_row, TABLE_HEADER["Previous Results"]]
                # html_data_frame.loc[test_name_row, "Previous Results"] = newline_char

            if test_name_row == -1:
                test_name_row = len(html_data_frame)
                html_data_frame.loc[test_name_row, TABLE_HEADER["Test Name"]] = DF_DIV_DISPLAY_START_CHAR + csv_name_list[i] + DF_DIV_DISPLAY_END_CHAR + csv_test_name
                html_data_frame.loc[test_name_row, TABLE_HEADER["Previous Results"]] = DF_NEWLINE_CHAR
            else:
                div_index = html_data_frame.loc[test_name_row, TABLE_HEADER["Test Name"]].find(DF_DIV_DISPLAY_END_CHAR)
                store_html_test_name = html_data_frame.loc[test_name_row, TABLE_HEADER["Test Name"]][:div_index + len(DF_DIV_DISPLAY_END_CHAR)]
                html_data_frame.loc[test_name_row, TABLE_HEADER["Test Name"]] = store_html_test_name + csv_test_name

            html_data_frame.loc[test_name_row, TABLE_HEADER["Test Description"]] = csv_test_description
            html_data_frame.loc[test_name_row, TABLE_HEADER["Expected Result"]] = csv_expected_result
            if not self.description_only:
                html_data_frame.loc[test_name_row, TABLE_HEADER["Result"]] = csv_status_to_html[csv_status]
            html_data_frame.loc[test_name_row, TABLE_HEADER["Date"]] = get_date()
            html_data_frame.loc[test_name_row, TABLE_HEADER["Tester"]] = self.__tester_name
            html_data_frame.loc[test_name_row, TABLE_HEADER["Test Setup"]] = csv_test_setup
            if setup_end != -1:
                html_data_frame.loc[test_name_row, TABLE_HEADER["Comments"]] = csv_comments
            if req_start != -1:
                html_data_frame.loc[test_name_row, TABLE_HEADER["Requirements"]] = "///" + csv_req + "///"
                DF_REQUIREMENTS.append("///" + csv_req + "///")
            
        html_data_frame = html_data_frame.sort_values(by="Test Name")
        html_data_frame.to_html('temp_html.html', index=False)

    def __send_updated_data_to_confluence(self, cont_outside_table: str, div_req_list: list[str]):
        """Method reads data converted from dataframe from html file, merges this code with content 
        outside table saved earlier and updates given Confluence page with merged code
        """
        with open('temp_html.html', 'r') as f:
            data_html = f.read()
        os.remove('temp_html.html')

        data_html = replace_signs_dataframe_to_html(data_html, div_req_list)
        if DF_TABLE_CHAR in cont_outside_table:
            data_to_confluence = cont_outside_table.replace(DF_TABLE_CHAR, data_html)
        else:
            data_to_confluence = cont_outside_table + data_html

        self.__confluence.update_page(
            page_id=self.page_id,
            title=self.page_title,
            body=data_to_confluence
        )

    def get_page_body(self):
        """Method returns page body of given Confluence page
        """
        space_content = self.__confluence.get_space_content(
            space_key=self.page_space_key,
            expand="body.storage.content",
        )
        for i in range(len(space_content['page']['results'])):
            pages_id = space_content['page']['results'][i]['body']['storage']['content']['id']
            if pages_id == self.page_id:
                return space_content['page']['results'][i]['body']['storage']['value']
        raise RuntimeError("Page not found")

    def load_data_to_confluence(self):
        """This method do all the job to export data from last created csv report to the Confluence page
        """
        confluence_page_body = self.get_page_body()
        div_requirement_list = search_div_requirement(confluence_page_body)
        content_outside_table = search_content_outside_table(confluence_page_body)
        confluence_page_body = replace_signs_html_to_dataframe(confluence_page_body, div_requirement_list)

        try:
            dfs = pd.read_html(confluence_page_body)
            df = dfs[-1]
            if df.shape[1] < 10:
                content_outside_table = self.__create_table_header(content_outside_table)
                confluence_page_body = self.get_page_body()
                confluence_page_body = replace_signs_html_to_dataframe(confluence_page_body, div_requirement_list)
                dfs = pd.read_html(confluence_page_body)
        except ValueError:
            content_outside_table = self.__create_table_header(content_outside_table)
            confluence_page_body = self.get_page_body()
            confluence_page_body = replace_signs_html_to_dataframe(confluence_page_body, div_requirement_list)
            dfs = pd.read_html(confluence_page_body)

        df = dfs[-1]
        if df.shape[1] < 10:
            raise RuntimeError("Cannot find table header on Confluence site")
        df_html = pd.DataFrame(df)

        self.__update_table_data(df_html, self.csv_df)
        self.__send_updated_data_to_confluence(content_outside_table, div_requirement_list)
