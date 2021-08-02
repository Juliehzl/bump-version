import os
import subprocess
import xml.etree.ElementTree as ET
import re
import argparse
import sys
from pipes import quote


def get_failed_tests(test_path, azure_cli_folder="E:\Microsoft\AzureCLI\\azure-cli"):
    tree = ET.parse(test_path)
    root = tree.getroot()
    failed_tests = {}
    testsuite = root.find('testsuite')
    for elem in root:
        for subelem in elem:
            # Collect failed tests
            failures = subelem.findall('failure')
            if failures:
                message = failures[0].attrib['message']
                test_case = subelem.attrib['name']
                failed_tests[test_case] = {}
                failed_tests[test_case]['message'] = message

                recording_folder = os.path.join(os.path.dirname(subelem.attrib['file']), 'recordings')
                if 'src' not in recording_folder:
                    recording_folder = os.path.join(os.path.join('src', 'azure-cli'), recording_folder)
                recording_file = os.path.join(os.path.join(azure_cli_folder, recording_folder), test_case + '.yaml')
                if os.path.exists(recording_file):
                    failed_tests[test_case]['record'] = recording_file
                else:
                    failed_tests[test_case]['record'] = ''
    return failed_tests

def replace_api_version_for_failed_tests(test_path):
    failed_tests = get_failed_tests(test_path)
    for test in failed_tests:
        if failed_tests[test]['record']:
            git_checkout(failed_tests[test]['record'])
            replace_api_version(file_path=failed_tests[test]['record'], old_version='2021-02-01', new_version='2021-04-01', resource_type='Microsoft.Storage')
        else:
            print("No recording file for " + test)

def git_checkout(file_path):
    print("git checkout {} to upstream/dev.".format(file_path))
    out = subprocess.Popen(["git", "checkout", "upstream/dev", file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, err = out.communicate()
    print(stdout)
    return stdout

def git_commit(file_path, message):
    print("git commit {} with message '{}'.".format(file_path, message))
    out = subprocess.Popen(["git", "commit", "upstream/dev", file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, _ = out.communicate()

def replace_api_version(file_path, old_version, new_version, resource_type):
    OLD_VERSION = resource_type + '[^:]{0,100}api-version=' + old_version
    NEW_VERSION = new_version

    with open(file_path, 'r') as file_in:
        list_in = file_in.readlines()

    flag = True
    for i in range(0, len(list_in)):
        result = re.search(OLD_VERSION, list_in[i])
        if result:
            idx = result.span()[1]
            print("{}:\nReplacing{} to{} \n".format(file_path, list_in[i], list_in[i][:idx - 10] + NEW_VERSION + list_in[i][idx:]))
            list_in[i] = list_in[i][:idx - 10] + NEW_VERSION + list_in[i][idx:]
            flag = False
    if flag:
        return

    with open(file_path, 'w') as file_out:
        file_out.writelines(list_in)


def search_edit(folder):
    for filename in os.listdir(folder):
        fp = os.path.join(folder, filename)
        if os.path.isfile(fp) and str(fp).find('.yaml') > -1:
            print(f'find {str(fp)}')
            edit_file(str(fp))
        elif os.path.isdir(fp):
            search_edit(fp)


def search_edit_test(test, folder):
    for filename in os.listdir(folder):
        fp = os.path.join(folder, filename)
        if os.path.isfile(fp) and str(fp).find('.yaml') > -1 and filename.replace('.yaml', '') in test:
            print(f'find {str(fp)}')
            edit_file(str(fp))
        elif os.path.isdir(fp) and str(fp).find('hybrid_') == -1:
            search_edit_test(test, fp)

def store_failed_test_results(failed_test):
    result = "The following tests are failed:\n"
    for item in failed_test:
        result += '    - ' + item + '\n'
    with open("~/failures.txt", "w") as f:
        f.write(result) 
    print("Store test results to ~/failures.txt")
 


if __name__ == "__main__":
    replace_api_version_for_failed_tests(test_path='E:\\Microsoft\\AzureCLI\\azure-cli\\env\\.azdev\\env_config\\Microsoft\\AzureCLI\\azure-cli\\env\\test_results.xml')