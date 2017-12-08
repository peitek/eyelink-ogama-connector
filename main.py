from PIL import Image, ImageDraw, ImageFont

import random
import os
from os.path import join

import re


def main():
    print("Starting script...")

    # read in eyelink file line for line
    input_file_path = "C:/Users/npeitek/Documents/GitHub/EyeLinkOgamaConnector/input/eyetracking_zp65_2017_12_06.asc"

    all_lines = []

    # create appropriate object with all information (subject, ...)

    carry_over = {
        "Subject": "",
        "Snippet": "",
        "TrialImage": "",
        "TrialNumber": ""
    }

    print("Reading file...")
    # check whether line is header, MSG or eyetracking file
    with open(input_file_path) as input_file:
        frames_size_code_counter = 0
        trial_number = 0
        d2_task_number = 1
        dec_time_number = 1
        rest_number = 1

        for i, line in enumerate(input_file):
            if (i % 5000) == 0:
                print("-> row ", i)

            csv_line_object = {
                "Id": i,
                "Subject": "zp65", #carry_over["Subject"],
                "Snippet": carry_over["Snippet"],
                "TrialImage": carry_over["TrialImage"],
                "TrialNumber": trial_number,
                "Time": None,
                "GazePosX": None,
                "GazePosY": None,
            }

            # if the current one is code
            # todo detect specific d2 image
            if not carry_over["Snippet"].startswith("D2") and not carry_over["Snippet"].startswith("Rest") and not carry_over["Snippet"].startswith("DecTime"):
                if frames_size_code_counter >= 30000:
                    print("--> switching to decision time after frames: ", frames_size_code_counter)
                    carry_over["Snippet"] = "DecTime" + str(dec_time_number)
                    carry_over["TrialImage"] = "dec_time_" + str(dec_time_number) + ".png"
                    frames_size_code_counter = 0
                    trial_number += 1
                    dec_time_number += 1
            elif not carry_over["Snippet"].startswith("D2") and not carry_over["Snippet"].startswith("Rest"):
                if frames_size_code_counter >= 2000:
                    print("--> switching to d2 after frames: ", frames_size_code_counter)
                    carry_over["Snippet"] = "D2_" + str(d2_task_number)
                    carry_over["TrialImage"] = "attention_task_" + str(d2_task_number) + ".png"
                    frames_size_code_counter = 0
                    trial_number += 1
                    d2_task_number += 1
            elif carry_over["Snippet"].startswith("D2") and frames_size_code_counter >= 15000:
                print("--> switching to rest after frames: ", frames_size_code_counter)
                carry_over["Snippet"] = "Rest" + str(rest_number)
                carry_over["TrialImage"] = "rest_" + str(rest_number) + ".png"
                frames_size_code_counter = 0
                trial_number += 1
                rest_number += 1

            if line[0].isdigit():
                numbers = re.split(r'\t+', line.rstrip('\t'))
                csv_line_object["Time"] = numbers[0].lstrip()
                csv_line_object["GazePosX"] = numbers[1].lstrip()
                csv_line_object["GazePosY"] = numbers[2].lstrip()

                #if (i % 500) == 0:
                all_lines.append(csv_line_object)
                frames_size_code_counter += 1

            elif line[0].isalpha():
                if "!V IMGLOAD FILL" in line:
                    startpos = line.rfind("\\")
                    snippet = line[startpos+1:].replace('\r', '').replace('\n', '')
                    carry_over["TrialImage"] = snippet
                    carry_over["Snippet"] = snippet
                    print("--> found snippet " + snippet + " after frames ", frames_size_code_counter)
                    frames_size_code_counter = 0
                    trial_number += 1
                elif "TRIALID TRIAL" in line:
                    startpos = line.find("TRIALID TRIAL")
                    #carry_over["TrialNumber"] = line[startpos+14:].replace('\r', '').replace('\n', '')
                elif "Subject" in line:
                    startpos = line.find("Subject")
                    carry_over["Subject"] = line[startpos+8:].replace('\r', '').replace('\n', '')

    print("-> reading file: done!")

    print("Save objects to file...")
    # write objects to file as giant csv
    output_file_path = "C:/Users/npeitek/Documents/GitHub/EyeLinkOgamaConnector/output/eyetracking_zp65_2017_12_06.csv"
    with open(output_file_path, 'w') as output_file:
        output_file.write("Id")
        output_file.write(';')
        output_file.write("Time")
        output_file.write(';')
        output_file.write("Subject")
        output_file.write(';')
        output_file.write("Snippet")
        output_file.write(';')
        output_file.write("TrialImage")
        output_file.write(';')
        output_file.write("TrialNumber")
        output_file.write(';')
        output_file.write("GazePosX")
        output_file.write(';')
        output_file.write("GazePosY")

        for i, line in enumerate(all_lines):
            if (i % 5000) == 0:
                print("-> row ", i)

            output_file.write('\n')
            output_file.write(str(line["Id"]))
            output_file.write(';')
            output_file.write(str(line["Time"]))
            output_file.write(';')
            output_file.write(str(line["Subject"]))
            output_file.write(';')
            output_file.write(str(line["Snippet"]))
            output_file.write(';')
            output_file.write(str(line["TrialImage"]))
            output_file.write(';')
            output_file.write(str(line["TrialNumber"]))
            output_file.write(';')
            output_file.write(str(line["GazePosX"]))
            output_file.write(';')
            output_file.write(str(line["GazePosY"]))

    print("-> saving file: done!")


main()
