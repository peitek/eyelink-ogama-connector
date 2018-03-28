from os.path import join

import re
import math

trial = 0

# TODO remove participant codes
# TODO remove required response log file
# TODO remove required physio log file
# TODO generalize code better (e.g., conditions)
# TODO clean up code
# TODO comment/document functions


def main():
    #compute_single_participant("ea65")
    #compute_single_participant("jw13")
    #compute_single_participant("ks01")
    #compute_single_participant("mk55")
    #compute_single_participant("on85")
    #compute_single_participant("qw51")
    #compute_single_participant("qv57")
    #compute_single_participant("ia67")
    #compute_single_participant("qe90")
    #compute_single_participant("bo23")
    #compute_single_participant("qh83")


    # excluded due to data quality for now
    # compute_single_participant("bo49")
    #compute_single_participant("bd96")
    #compute_single_participant("jl58")
    #compute_single_participant("ew72")
    #compute_single_participant("ur84")
    #compute_single_participant("jw66")
    #compute_single_participant("gq73")
    #compute_single_participant("gf73")
    #compute_single_participant("xt73")
    #compute_single_participant("wb70")
    pass


def compute_single_participant(participant_id):
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
            if (i % 100000) == 0:
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


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def parse_eyetracking_data(participant_name):
    print("\nParse eyetracking data...")

    eyetracking_input_file_path = join("input", participant_name + ".asc")

    # read in eyelink file line for line
    all_lines = []

    global trial

    print("Reading file...")
    with open(eyetracking_input_file_path) as input_file:
        frames_size_code_counter = 0
        trial_image = ""
        trial_category = ""
        sequence = 0
        d2_task_number = 1
        dec_time_number = 1
        rest_number = 1
        timestamp = 1
        subject = participant_name
        snippet = ""

        gaze_positions_recognized = 0
        gaze_positions_not_recognized = 0

        for i, line in enumerate(input_file):
            if (i % 100000) == 0:
                print("-> Read row of eyetracking: ", i)

            csv_line_object = {
                "Line": i,
                "SubjectName": subject,
                "Snippet": snippet,
                "TrialNumber": trial,
                "TrialSequence": sequence,
                "TrialImage": trial_image,
                "TrialCategory": trial_category,
                "Time": None,
                "TimestampMs": timestamp,
                "GazePosX": None,
                "GazePosY": None,
                "HeartRate": None,
                "Breathing": None,
                "Response": None,
            }

            if line[0].isdigit():
                numbers = re.split(r'\t+', line.rstrip('\t'))
                csv_line_object["Time"] = numbers[0].lstrip()

                gaze_x = numbers[1].lstrip()

                if (is_number(gaze_x)):
                    gaze_positions_recognized += 1
                else:
                    gaze_positions_not_recognized += 1

                csv_line_object["GazePosX"] = gaze_x
                csv_line_object["GazePosY"] = numbers[2].lstrip()

                #if (i % 500) == 0:
                all_lines.append(csv_line_object)
                frames_size_code_counter += 1
                timestamp += 1

            elif line[0].isalpha():
                if "Rest Condition" in line:
                    snippet = "Rest" + str(rest_number)
                    trial_image = "rest_" + str(rest_number) + ".png"
                    rest_number += 1
                    print("--> found rest condition after frames ", frames_size_code_counter)
                    trial_category = "Rest"
                    frames_size_code_counter = 0
                    sequence += 1
                    trial += 1
                elif "Last Response" in line:
                    print("--> switching to decision time after frames: ", frames_size_code_counter)
                    snippet = "DecTime" + str(dec_time_number)
                    trial_image = "dec_time_" + str(dec_time_number) + ".png"
                    trial_category = "DecTime"
                    frames_size_code_counter = 0
                    sequence += 1
                    trial += 1
                    dec_time_number += 1
                elif "D2 Task" in line:
                    print("--> switching to d2 after frames: ", frames_size_code_counter)
                    snippet = "D2_" + str(d2_task_number)
                    trial_image = "attention_task_" + str(d2_task_number) + ".png"
                    trial_category = "D2"
                    frames_size_code_counter = 0
                    sequence += 1
                    trial += 1
                    d2_task_number += 1
                elif "!V IMGLOAD FILL" in line:
                    startpos = line.rfind("\\")
                    snippet = line[startpos+1:].replace('\r', '').replace('\n', '')
                    trial_image = snippet

                    print("--> found snippet " + snippet + " after frames ", frames_size_code_counter)

                    if "TD_B" in snippet:
                        trial_category = "Compr_TD_B"
                    elif "TD_N" in snippet:
                        trial_category = "Compr_TD_N"
                    elif "TD_U" in snippet:
                        trial_category = "Compr_TD_U"
                    elif "SY" in snippet:
                        trial_category = "Syntax"
                    else:
                        trial_category = "Compr_BU"

                    frames_size_code_counter = 0
                    sequence += 1
                    trial += 1
                elif "TRIALID TRIAL" in line:
                    startpos = line.find("TRIALID TRIAL")
                    #carry_over["TrialNumber"] = line[startpos+14:].replace('\r', '').replace('\n', '')
                elif "Subject" in line:
                    startpos = line.find("Subject")
                    subject = line[startpos+8:].replace('\r', '').replace('\n', '')

        print("-> Frames with gaze positions recognized: " + str(gaze_positions_recognized))
        print("-> Frames with gaze positions not recognized: " + str(gaze_positions_not_recognized))
        print("-> Percentage of recognized frames: " + str((gaze_positions_recognized/(gaze_positions_recognized+gaze_positions_not_recognized))*100))

    print("-> reading file: done!")

    return all_lines


def write_csv_file(all_lines, participant_name):
    print("\n====================\n")
    print("Final step: Write everything to a csv file...")

    # write objects to file as giant csv
    output_file_path = join("output", participant_name + ".csv")
    with open(output_file_path, 'w') as output_file:
        file_write = output_file.write
        
        if True or all_lines[0]["SubjectName"] == "ea65":
            file_write("SubjectName")
            file_write(';')
            file_write("Time")
            file_write(';')
            file_write("TrialID")
            file_write(';')
            file_write("TrialSequence")
            file_write(';')
            file_write("TrialImage")
            file_write(';')
            file_write("TrialCategory")
            file_write(';')
            file_write("GazePosX")
            file_write(';')
            file_write("GazePosY")
            file_write(';')
            #file_write("HeartRate")
            #file_write(';')
            #file_write("Breathing")
            #file_write(';')
            file_write("ResponseX")
            file_write(';')
            file_write("ResponseY\n")

        response_temp = None
        
        for i, line in enumerate(all_lines):
            if (i % 100000) == 0:
                print("-> row ", i)

            #file_write("\n{Line};{TimestampMs};{Time};{Subject};{Snippet};{TrialImage};{TrialNumber};{GazePosX};{GazePosY};".format(**line))
            file_write("{SubjectName};{Time};{TrialSequence};{TrialSequence};{TrialImage};{TrialCategory};{GazePosX};{GazePosY};".format(**line))

            #file_write("" if line["HeartRate"] is None else str(line["HeartRate"]))
            #file_write(';')
            #file_write("" if line["Breathing"] is None else str(line["Breathing"]))
            #file_write(';')

            # drag responses for 200ms, then move mouse out of the area
            if line["Response"] is not None:
                if line["Response"] == '3':
                    response_temp = True
                elif line["Response"] == '4':
                    response_temp = False
                else:
                    response_temp = None

            if response_temp is None:
                file_write("0;0")
            elif response_temp:
                file_write("20;1000")
            else:
                file_write("1200;1000")

            file_write("\n")

    print("-> saving file: done!")


main()
