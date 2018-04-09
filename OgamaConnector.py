from os.path import join

import re
import math

# config variables, you may need to change these
INPUT_PATH = "input"
OUTPUT_PATH = "output"

RESPONSE_CODE_CORRECT = '3'
RESPONSE_CODE_INCORRECT = '4'

MOUSE_POSITION_NO_RESPONSE = "0;0"
MOUSE_POSITION_CORRECT_RESPONSE = "20;1000"
MOUSE_POSITION_INCORRECT_RESPONSE = "1200;1000"


# TODO clean up code
# TODO comment/document functions
# TODO add tests


def main():
    parse_eyelink_of_single_participant("example_participant_01")
    pass


def parse_eyelink_of_single_participant(participant_id, write_header=True, parse_physio=False, parse_response=False):
    print("Start script for participant: ", participant_id)

    all_eyetracking_frames = parse_eyetracking_data(participant_id)

    if parse_physio:
        all_eyetracking_frames = parse_physio_data(participant_id, all_eyetracking_frames)

    if parse_response:
        all_eyetracking_frames = parse_response_data(participant_id, all_eyetracking_frames)

    write_output_to_csv_file(participant_id, all_eyetracking_frames, write_header, parse_physio, parse_response)


def parse_eyetracking_data(participant_id):
    print("\nParsing EyeLink eye-tracking data for ", participant_id)

    eyetracking_input_file_path = join(INPUT_PATH, participant_id + '.asc')

    # read in EyeLink file line for line
    all_eyetracking_frames = []
    trial = 0

    print("Starting to read file at: ", eyetracking_input_file_path)
    with open(eyetracking_input_file_path) as input_file:
        # important data for each frame
        frame_size_code_counter = 0
        frame_timestamp = 1
        sequence = 0
        subject = participant_id
        snippet = ""
        trial_image = ""
        trial_category = ""

        # specific to our study (TODO move this to a config JSON?)
        config_task_category = [{
            'log_line': "Rest Condition",
            'snippet_name': "Rest",
            'trial_image': "rest_",
            'trial_category': "Rest",
            'counter': 1,
        },
        {
            'log_line': "Last Response",
            'snippet_name': "DecTime",
            'trial_image': "dec_time_",
            'trial_category': "DecTime",
            'counter': 1,
        },
        {
            'log_line': "D2 Task",
            'snippet_name': "D2_",
            'trial_image': "attention_task_",
            'trial_category': "D2",
            'counter': 1,
        }]

        # specific to our study (TODO move this to a config JSON?)
        config_snippet_condition = [{
            'log_line': "TD_B",
            'condition': "Compr_TD_B"
        },
        {
            'log_line': "TD_N",
            'condition': "Compr_TD_N"
        },
        {
            'log_line': "TD_U",
            'condition': "Compr_TD_U"
        },
        {
            'log_line': "SY",
            'condition': "Syntax"
        }]

        config_snippet_condition_fallback = {
            'log_line': "BU",
            'condition': "Compr_BU"
        }

        # statistics
        eyetracking_frames_successful = 0
        eyetracking_frames_failed = 0

        for i, line in enumerate(input_file):
            # print progress every X lines to console
            if (i % 100000) == 0:
                print("-> Read row of eye-tracking file: ", i)

            single_eyetracking_frame = {
                "Line": i,
                "SubjectName": subject,
                "Snippet": snippet,
                "TrialNumber": trial,
                "TrialSequence": sequence,
                "TrialImage": trial_image,
                "TrialCategory": trial_category,
                "Time": None,
                "TimestampMs": frame_timestamp,
                "GazePosX": None,
                "GazePosY": None,
                "PupilDilation": None,
                "HeartRate": None,
                "Breathing": None,
                "Response": None,
            }

            # if the first character of the line is a digit, we assume it's an actual eye-tracking frame
            if line[0].isdigit():
                timestamp, gaze_x, gaze_y, pupil_dilation, *rest = re.split(r'\t+', line.rstrip('\t'))

                if is_number(gaze_x.lstrip()):
                    eyetracking_frames_successful += 1
                else:
                    eyetracking_frames_failed += 1

                single_eyetracking_frame["Time"] = timestamp.lstrip()
                single_eyetracking_frame["GazePosX"] = gaze_x.lstrip()
                single_eyetracking_frame["GazePosY"] = gaze_y.lstrip()
                single_eyetracking_frame["PupilDilation"] = pupil_dilation.lstrip()

                all_eyetracking_frames.append(single_eyetracking_frame)
                frame_size_code_counter += 1
                frame_timestamp += 1

            # if the first character is a letter, it's a logging statement or an event
            elif line[0].isalpha():
                matching_category = next((item for item in config_task_category if item['log_line'] in line), None)

                if matching_category:
                    print("--> found " + matching_category['trial_category'] + " after frames " + str(frame_size_code_counter))

                    snippet = matching_category['snippet_name'] + str(config_task_category[0]['counter'])
                    trial_image = matching_category['trial_image'] + str(config_task_category[0]['counter']) + ".png"
                    trial_category = matching_category['trial_category']

                    matching_category['counter'] += 1
                    frame_size_code_counter = 0
                    sequence += 1
                    trial += 1

                elif "!V IMGLOAD FILL" in line:
                    startpos = line.rfind("\\")
                    snippet = line[startpos + 1:].replace('\r', '').replace('\n', '')

                    print("--> found snippet " + snippet + " after frames ", frame_size_code_counter)

                    matching_condition = next((item for item in config_snippet_condition if item['log_line'] in line), config_snippet_condition_fallback)
                    if matching_condition:
                        trial_category = matching_condition['condition']

                    trial_image = snippet
                    frame_size_code_counter = 0
                    sequence += 1
                    trial += 1

                elif "TRIALID TRIAL" in line:
                    # currently ignoring the trial information from EyeLink
                    pass

        print("-> Frames with eye tracking successful: " + str(eyetracking_frames_successful))
        print("-> Frames with eye tracking failed: " + str(eyetracking_frames_failed))
        print("-> Percentage of successful frames: " + str((eyetracking_frames_successful / (eyetracking_frames_successful + eyetracking_frames_failed)) * 100))

    print("-> reading file: done!")

    return all_eyetracking_frames


def parse_physio_data(participant_id, all_lines):
    print("\nParsing physio data for ", participant_id)
    print("This function is specific for our Philips physio logs. It will not work unless you use the exact same format.")

    physio_input_file_path = join(INPUT_PATH, participant_id + '_physio.log')

    with open(physio_input_file_path) as input_file:
        start = False
        # todo correct the wrong resolution. currently we assume 500 hertz instead of the correct 496 hertz!
        # todo also minimize that heart rate/respiration only has a resolution of 100 hertz, currently it's added too often without an effect
        timestamp_ms = 0

        for i, line in enumerate(input_file):
            if (i % 100000) == 0:
                print("-> Read row of physio: ", i)

            if line.startswith('#'):
                continue

            elements = line.split(' ')

            if not start:
                # TODO document this step better: why do we take the 12th character?
                mark = elements[12]

                if mark[0] == '1':
                    print("-> Found first frame of at line physio: ", i)
                    start = True

            if start:
                timestamp_ms += 2
                heart_rate = elements[6]
                respiration = elements[7]

                try:
                    all_lines[timestamp_ms]['HeartRate'] = heart_rate
                    all_lines[timestamp_ms]['Breathing'] = respiration
                except:
                    print("Exception: more physio data than eye tracking! This shouldn't happen...")
                    break

    return all_lines


def parse_response_data(participant_id, all_lines):
    print("\nParsing behavioral response data for ", participant_id)

    response_input_file_path = join(INPUT_PATH, participant_id + "_response.log")

    with open(response_input_file_path) as input_file:
        start = False
        initial_timestamp_ms = 0

        for i, line in enumerate(input_file):
            if (i % 100) == 0:
                print("-> Read row of response: ", i)

            elements = line.split("\t")

            if not start and i == 9:
                initial_timestamp_ms = int(elements[4])
                start = True

            if start and elements[2] == "Response":
                timestamp_ms = math.floor((int(elements[4]) - initial_timestamp_ms) / 10)

                try:
                    all_lines[timestamp_ms]["Response"] = elements[3]
                except:
                    print("Exception: more response data than eye tracking! This shouldn't happen...")
                    break

    return all_lines


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def write_output_to_csv_file(participant_name, all_lines, write_header=True, parse_physio=False, parse_response=False):
    print("\n====================\n")
    print("Final step: Write everything to a csv file for ", participant_name)

    # write objects to file in a giant csv
    output_file_path = join(OUTPUT_PATH, participant_name + ".csv")
    with open(output_file_path, 'w') as output_file:
        file_write = output_file.write

        if write_header:
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
            file_write("PupilDilation")
            file_write(';')

            if parse_physio:
                file_write("HeartRate")
                file_write(';')
                file_write("Breathing")
                file_write(';')

            if parse_response:
                file_write("ResponseX")
                file_write(';')
                file_write("ResponseY")

            file_write("\n")

        response_temp = None

        for i, line in enumerate(all_lines):
            if (i % 100000) == 0:
                print("-> row ", i)

            file_write("{SubjectName};{Time};{TrialSequence};{TrialSequence};{TrialImage};{TrialCategory};{GazePosX};{GazePosY};{PupilDilation};".format(**line))

            if parse_physio:
                file_write("" if line["HeartRate"] is None else str(line["HeartRate"]))
                file_write(';')
                file_write("" if line["Breathing"] is None else str(line["Breathing"]))
                file_write(';')

            if parse_response:
                # when a user responds, set the mouse position to an arbitrary X/Y coordinate
                # this way you can see it in Ogama in the data explorer
                if line["Response"] is not None:
                    if line["Response"] == RESPONSE_CODE_CORRECT:
                        response_temp = True
                    elif line["Response"] == RESPONSE_CODE_INCORRECT:
                        response_temp = False
                    else:
                        response_temp = None

                if response_temp is None:
                    file_write(MOUSE_POSITION_NO_RESPONSE)
                elif response_temp:
                    file_write(MOUSE_POSITION_CORRECT_RESPONSE)
                else:
                    file_write(MOUSE_POSITION_INCORRECT_RESPONSE)

            file_write("\n")

    print("-> saving file: done!")


main()
