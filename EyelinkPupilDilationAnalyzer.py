from os.path import join
import math
import numpy
import _pickle as pickle


# TODO remove participant codes
# TODO remove required response log file
# TODO remove required physio log file
# TODO generalize code better (e.g., conditions)
# TODO clean up code
# TODO comment/document functions


def main():
    #participants = ["bo23", "ea65", "ia67", "ks01", "mk55", "on85", "qe90", "qw51", "qv57", "zp65"]
    participants = ["bo23", "ea65", "ia67", "ks01", "mk55", "qe90", "qw51", "zp65"]
    #participants = ["ks01"]

    analyze_pupil_dilation_for_all_participants(participants)


def analyze_pupil_dilation_for_all_participants(participants, use_fixation_length=False):
    average_dilation_per_condition = []
    average_dilation_over_time = []

    for participant in participants:
        pupil_dilation_per_condition = {}
        pupil_dilation_over_time = {}
        pupil_dilation_per_participant = [[0, 0, 0] for i in range(len(participants))]

        [pupil_dilation_over_time, pupil_dilation_per_condition, pupil_dilation_per_participant] = analyze_each_frame(participants, participant, pupil_dilation_over_time, pupil_dilation_per_condition, pupil_dilation_per_participant)

        print("\n#### ANALYSIS FOR PARTICIPANT")
        for timestamp in sorted(pupil_dilation_over_time):
            data = pupil_dilation_over_time[timestamp]

            average_dilation_over_time.append({
                "participant": participant,
                "timestamp": timestamp,
                "average_dilation": math.floor(numpy.mean(data))
            })

        for condition in sorted(pupil_dilation_per_condition):
            for timestamp in sorted(pupil_dilation_per_condition[condition]):
                data = pupil_dilation_per_condition[condition][timestamp]

                average_dilation_per_condition.append({
                    "participant": participant,
                    "condition": condition,
                    "timestamp": timestamp,
                    "average_dilation": math.floor(numpy.mean(data))
                })

    print("\n#### WRITE RESULTS TO CSV")

    write_dilation_over_time(average_dilation_over_time)
    write_dilation_per_condition(average_dilation_per_condition)

    print("-> saving file: done!")


def write_dilation_over_time(average_dilation_over_time):
    # write objects to file as giant csv
    output_file_path = join("output", "pupil_dilation_time_sec.csv")
    with open(output_file_path, 'w') as output_file:
        file_write = output_file.write
        file_write("time;pupil_dilation;subject\n")

        for line in average_dilation_over_time:
            file_write(str(line["timestamp"]) + ";" + str(line["average_dilation"]) + ";" + line["participant"] + "\n")


def write_dilation_per_condition(average_dilation_per_condition):
    # write objects to file as giant csv
    output_file_path = join("output", "pupil_dilation_condition.csv")
    with open(output_file_path, 'w') as output_file:
        file_write = output_file.write
        file_write("condition;time;pupil_dilation;subject\n")

        for line in average_dilation_per_condition:
            file_write(line["condition"] + ";" + str(line["timestamp"]) + ";" + str(line["average_dilation"]) + ";" + line["participant"] + "\n")


def analyze_each_frame(participants, participant_id, pupil_dilation_over_time, pupil_dilation_per_condition, pupil_dilation_per_participant):
    with open(join("input", "fixations", participant_id + "_pupil_data_raw.pkl"), 'rb') as input:
        eyetracking_data = pickle.load(input)

        print("\n## " + participant_id)
        participant_pos = participants.index(participant_id)
        trial_category = None

        for et_frame in eyetracking_data:
            #print("-> found frame for " + str(et_frame["snippet"]) + " after " + str(et_frame["frames"]) + " frames, pupil dilation: " + et_frame["pupil_dilation"])

            if trial_category != et_frame["trial_category"]:
                #print("switched to " + et_frame["trial_category"] + " after " + str(et_frame["timestamp"]))
                trial_category = et_frame["trial_category"]

            # per condition
            grouped_frame = math.floor(et_frame["frames"]/10)
            if trial_category not in pupil_dilation_per_condition:
                pupil_dilation_per_condition[trial_category] = {}

            if grouped_frame not in pupil_dilation_per_condition[trial_category]:
                pupil_dilation_per_condition[trial_category][grouped_frame] = []

            pupil_dilation_per_condition[trial_category][grouped_frame].append(math.floor(float(et_frame["pupil_dilation"])))

            # over time
            grouped_time = math.floor(et_frame["timestamp"]/100)
            if grouped_time not in pupil_dilation_over_time:
                pupil_dilation_over_time[grouped_time] = []

            pupil_dilation_over_time[grouped_time].append(math.floor(float(et_frame["pupil_dilation"])))

    return [pupil_dilation_over_time, pupil_dilation_per_condition, pupil_dilation_per_participant]


main()
