from os.path import join

import _pickle as pickle
import re

# TODO remove participant codes
# TODO clean up code
# TODO comment/document functions

trial = 0


def main():
    participants = ["bo23", "ea65", "ia67", "jw13", "ks01", "mk55", "qe90", "qw51"]

    for participant in participants:
        find_fixations_for_single_participant(participant)


def find_fixations_for_single_participant(participant_name):
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

        rest_condition = 0
        fixation_count = 0

        # TODO extract all fixation lines to analyze them
        all_fixations = []

        for i, line in enumerate(input_file):
            if (i % 100000) == 0:
                print("-> Read row of eyetracking: ", i)

            if line[0].isdigit():
                frames_size_code_counter += 1
                timestamp += 1

            elif line[0].isalpha():
                if "EFIX L" in line:
                    fixation_info = re.split(r'\t+', line.rstrip('\t'))
                    print("----> found fixation after " + str(frames_size_code_counter) + " frames, for " + fixation_info[2] + " msec, at position x=" + fixation_info[3] + ", y=" + fixation_info[4])
                    all_fixations.append({
                        "trial_category": trial_category,
                        "snippet": snippet,
                        "timestamp": timestamp,
                        "rest_condition": rest_condition,
                        "frames": frames_size_code_counter,
                        "data": fixation_info
                    })
                    fixation_count += 1

                elif "Rest Condition" in line:
                    snippet = "Rest" + str(rest_number)
                    trial_image = "rest_" + str(rest_number) + ".png"
                    rest_number += 1
                    print("--> found rest condition " + str(rest_condition) + " after frames ", frames_size_code_counter)
                    trial_category = "Rest"
                    rest_condition += 1
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
        print("-> Amount of fixations: " + str(fixation_count))

    # write fixations to file
    with open(join("input", "fixations", participant_name + ".pkl"), 'wb') as output:
        pickle.dump(all_fixations, output)

    print("-> reading file: done!")

    return all_lines


main()
