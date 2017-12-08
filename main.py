from os.path import join

import re
import math


def main():
    participant_id = "zp65"

    print("Start script for participant ", participant_id)

    all_lines = parse_eyetracking_data(participant_id)
    all_lines = parse_physio_data(all_lines, participant_id)
    all_lines = parse_response_data(all_lines, participant_id)
    write_csv_file(all_lines, participant_id)


def parse_physio_data(all_lines, participant_id):
    print("\nParse physio data...")

    physio_input_file_path = join("input", participant_id + "_physio.log")

    with open(physio_input_file_path) as input_file:
        start = False
        #todo correct the wrong resolution. currently we assume 500 hertz instead of the correct 496 hertz!
        #todo also minimize that heartrate/breathing only has a resolution of 100 hertz, currently it's added too often without an effect
        imestampMs = 0

        for i, line in enumerate(input_file):
            if (i % 10000) == 0:
                print("-> Read row of physio: ", i)

            if line.startswith("#"):
                continue

            elements = line.split(" ")

            if not start:
                mark = elements[12]

                if mark[0] == '1':
                    print("-> Found first frame of at line physio: ", i)
                    start = True

            if start:
                imestampMs += 2
                heartrate = elements[6]
                breathing = elements[7]

                try:
                    all_lines[imestampMs]["HeartRate"] = heartrate
                    all_lines[imestampMs]["Breathing"] = breathing
                except:
                    print("Exception: more physio data than eyetracking! This shouldn't happen...")
                    break

    return all_lines


def parse_response_data(all_lines, participant_id):
    print("\nParse response data...")

    response_input_file_path = join("input", participant_id + "_response.log")

    with open(response_input_file_path) as input_file:
        start = False
        initial_timestampMs = 0

        for i, line in enumerate(input_file):
            if (i % 100) == 0:
                print("-> Read row of response: ", i)

            elements = line.split("\t")

            if not start and i == 9:
                initial_timestampMs = int(elements[4])
                start = True

            if start and elements[2] == "Response":
                timestampMs = math.floor((int(elements[4]) - initial_timestampMs) / 10)

                try:
                    all_lines[timestampMs]["Response"] = elements[3]
                except:
                    print("Exception: more response data than eyetracking! This shouldn't happen...")
                    break

    return all_lines


def parse_eyetracking_data(participant_name):
    print("\nParse eyetracking data...")

    eyetracking_input_file_path = join("input", participant_name + ".asc")

    # read in eyelink file line for line
    all_lines = []

    print("Reading file...")
    with open(eyetracking_input_file_path) as input_file:
        frames_size_code_counter = 0
        trial_image = ""
        trial_number = 0
        d2_task_number = 1
        dec_time_number = 1
        rest_number = 1
        timestamp = 1
        subject = participant_name
        snippet = ""

        for i, line in enumerate(input_file):
            if (i % 25000) == 0:
                print("-> Read row of eyetracking: ", i)

            csv_line_object = {
                "Line": i,
                "Subject": subject,
                "Snippet": snippet,
                "TrialImage": trial_image,
                "TrialNumber": trial_number,
                "Time": None,
                "TimestampMs": timestamp,
                "GazePosX": None,
                "GazePosY": None,
                "HeartRate": None,
                "Breathing": None,
                "Response": None,
            }

            # if the current one is code
            if not snippet.startswith("D2") and not snippet.startswith("Rest") and not snippet.startswith("DecTime"):
                if frames_size_code_counter >= 30000:
                    print("--> switching to decision time after frames: ", frames_size_code_counter)
                    snippet = "DecTime" + str(dec_time_number)
                    trial_image = "dec_time_" + str(dec_time_number) + ".png"
                    frames_size_code_counter = 0
                    trial_number += 1
                    dec_time_number += 1
            elif not snippet.startswith("D2") and not snippet.startswith("Rest"):
                if frames_size_code_counter >= 2000:
                    print("--> switching to d2 after frames: ", frames_size_code_counter)
                    snippet = "D2_" + str(d2_task_number)
                    trial_image = "attention_task_" + str(d2_task_number) + ".png"
                    frames_size_code_counter = 0
                    trial_number += 1
                    d2_task_number += 1
            elif not snippet.startswith("D2") and frames_size_code_counter >= 15000:
                print("--> switching to rest after frames: ", frames_size_code_counter)
                snippet = "Rest" + str(rest_number)
                trial_image = "rest_" + str(rest_number) + ".png"
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
                timestamp += 1

            elif line[0].isalpha():
                if "!V IMGLOAD FILL" in line:
                    startpos = line.rfind("\\")
                    snippet = line[startpos+1:].replace('\r', '').replace('\n', '')
                    trial_image = snippet

                    print("--> found snippet " + snippet + " after frames ", frames_size_code_counter)
                    frames_size_code_counter = 0
                    trial_number += 1
                elif "TRIALID TRIAL" in line:
                    startpos = line.find("TRIALID TRIAL")
                    #carry_over["TrialNumber"] = line[startpos+14:].replace('\r', '').replace('\n', '')
                elif "Subject" in line:
                    startpos = line.find("Subject")
                    subject = line[startpos+8:].replace('\r', '').replace('\n', '')

    print("-> reading file: done!")

    return all_lines


def write_csv_file(all_lines, participant_name):
    print("\n====================\n")
    print("Final step: Write everything to a csv file...")

    # write objects to file as giant csv
    output_file_path = join("output", participant_name + ".csv")
    with open(output_file_path, 'w') as output_file:
        output_file.write("Line")
        output_file.write(';')
        output_file.write("TimestampMs")
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
        output_file.write(';')
        output_file.write("HeartRate")
        output_file.write(';')
        output_file.write("Breathing")
        output_file.write(';')
        output_file.write("Response")

        for i, line in enumerate(all_lines):
            if (i % 25000) == 0:
                print("-> row ", i)

            output_file.write('\n')
            output_file.write(str(line["Line"]))
            output_file.write(';')
            output_file.write(str(line["TimestampMs"]))
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
            output_file.write(';')
            output_file.write("" if line["HeartRate"] is None else str(line["HeartRate"]))
            output_file.write(';')
            output_file.write("" if line["Breathing"] is None else str(line["Breathing"]))
            output_file.write(';')
            output_file.write("" if line["Response"] is None else str(line["Response"]))
    print("-> saving file: done!")


main()
