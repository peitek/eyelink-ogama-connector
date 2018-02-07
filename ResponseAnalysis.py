import copy
from os.path import join

import re
import math


def main():
    participant_id = "jl58"

    print("Start script for participant ", participant_id)

    all_stimuli = parse_response_data(participant_id)
    [top_down_beacon, top_down_no_beacon, top_down_untrained, bottom_up, syntax, d2] = analyze_data(all_stimuli)

    write_csv_file_comprehension([top_down_beacon, top_down_no_beacon, top_down_untrained, bottom_up, syntax], participant_id)
    write_csv_file_d2(d2, participant_id)


def parse_response_data(participant_id):
    print("\nParse response data...")

    response_input_file_path = join("input", participant_id + "_response.log")

    all_stimuli = []

    with open(response_input_file_path) as input_file:
        start = False
        late_response = False
        initial_timestampMs = 0
        current_stimulus = None

        for i, line in enumerate(input_file):
            if (i % 100) == 0:
                print("-> Read row of response log: ", i)

            elements = line.split("\t")

            if not start and i == 9:
                initial_timestampMs = int(elements[4])
                start = True

            if start and elements[2] == "Picture":
                if elements[3] == "LastResponseCondition":
                    late_response = True
                    continue

                late_response = False

                if current_stimulus is not None:
                    all_stimuli.append(current_stimulus)

                current_stimulus = {
                    "name": elements[3],
                    "timestamp": math.floor((int(elements[4]) - initial_timestampMs) / 10),
                    "responses": [],
                    "late_responses": []
                }

            if start and elements[2] == "Response":
                timestampMs = math.floor((int(elements[4]) - initial_timestampMs) / 10)

                try:
                    if late_response:
                        current_stimulus["late_responses"].append({
                            "timestamp": timestampMs,
                            "response": elements[3],
                            "stimulus": current_stimulus["name"],
                            "response_time": timestampMs - current_stimulus["timestamp"]
                        })
                    else:
                        current_stimulus["responses"].append({
                            "timestamp": timestampMs,
                            "response": elements[3],
                            "stimulus": current_stimulus["name"],
                            "response_time": timestampMs - current_stimulus["timestamp"]
                        })
                except:
                    print("Exception: this shouldn't happen...")
                    break

    return all_stimuli


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def analyze_data(all_stimuli):
    print("#############")
    print("Summarizing and analyzing data now...")

    d2 = {
        "count": 0,
        "responded": 0,
        "overall_clicks": 0,

        "correct": 0,
        "incorrect": 0,

        "runs": []
    }
    top_down_beacon = {
        "count": 0,
        "responded": 0,
        "not_responded": 0,

        "correct": 0,
        "incorrect": 0,

        "late_responses": 0,
        "multi_clicks": 0,
        "overall_clicks": 0,
        "response_times": [],
        "click_times": [],
    }
    top_down_no_beacon = copy.deepcopy(top_down_beacon)
    top_down_untrained = copy.deepcopy(top_down_beacon)
    bottom_up = copy.deepcopy(top_down_beacon)
    syntax = copy.deepcopy(top_down_beacon)

    for i, line in enumerate(all_stimuli):
        if "TD_B" in line["name"]:
            analyze_comprehension_stimulus(line, top_down_beacon)
        elif "TD_N" in line["name"]:
            analyze_comprehension_stimulus(line, top_down_no_beacon)
        elif "TD_U" in line["name"]:
            analyze_comprehension_stimulus(line, top_down_untrained)
        elif "BinaryToDecimal" in line["name"] or "Factorial" in line["name"] or "CountVowels" in line["name"] or "Maximum" in line["name"] or "IntertwineTwoWords" in line["name"]:
            analyze_comprehension_stimulus(line, bottom_up)

        elif "SY" in line["name"]:
            analyze_comprehension_stimulus(line, syntax)

        elif "D2" in line["name"]:
            analyze_d2_stimulus(line, d2)

        elif "RestCondition" in line["name"]:
            continue

        else:
            print('unknown stimulus (' + line["name"] + ') ' + str(i))

    finalize_comprehension_summary([top_down_beacon, top_down_no_beacon, top_down_untrained, bottom_up, syntax])

    return [top_down_beacon, top_down_no_beacon, top_down_untrained, bottom_up, syntax, d2]


def finalize_comprehension_summary(all_stimuli):
    for stimuli in all_stimuli:
        stimuli["not_responded"] = 5 - stimuli["responded"]


def analyze_d2_stimulus(line, stimulus_summary):
    stimulus_summary["count"] += 1
    stimulus_summary["overall_clicks"] += len(line["responses"])/2

    clicks = []

    if len(line["responses"]) > 0:
        stimulus_summary["responded"] += 1

        current_click = None
        current_time = None
        for i, response in enumerate(line["responses"]):
            if current_click is None:
                current_click = response["response"] == '3'
                current_time = response["response_time"]
            else:
                clicks.append({
                    "choice": current_click,
                    "response_time": response["response_time"] - current_time,
                })
                current_click = None

    stimulus_summary["runs"].append({
        "name": line["name"],
        "i": stimulus_summary["count"] - 1,
        "clicks": clicks
    })


def analyze_d2_click(resp, stimulus_summary):
    response = resp[len(resp) - 2]

    if response["response"] == '3':
        stimulus_summary["correct"] += 1
    else:
        stimulus_summary["incorrect"] += 1

    stimulus_summary["response_times"].append(response["response_time"])
    stimulus_summary["click_times"].append(resp[len(resp) - 1]["response_time"] - response["response_time"])


def analyze_comprehension_stimulus(line, stimulus_summary):
    stimulus_summary["count"] += 1
    stimulus_summary["overall_clicks"] += len(line["responses"])/2 + len(line["late_responses"])/2

    if len(line["responses"]) > 0:
        stimulus_summary["responded"] += 1
        analyze_last_click_comprehension(line["responses"], stimulus_summary)

    if len(line["responses"]) > 2:
        stimulus_summary["multi_clicks"] += 1

    if len(line["late_responses"]) > 0:
        stimulus_summary["responded"] += 1
        stimulus_summary["late_responses"] += 1
        analyze_last_click_comprehension(line["late_responses"], stimulus_summary)


def analyze_last_click_comprehension(resp, stimulus_summary):
    response = resp[len(resp) - 2]

    if response["response"] == '3':
        stimulus_summary["correct"] += 1
    else:
        stimulus_summary["incorrect"] += 1

    stimulus_summary["response_times"].append(response["response_time"])
    stimulus_summary["click_times"].append(resp[len(resp) - 1]["response_time"] - response["response_time"])


def write_csv_file_d2(d2, participant_name):
    print("\n====================\n")
    print("Write d2 result to a csv file for ...", participant_name)

    # write objects to file as giant csv
    output_file_path = join("output", participant_name + "_responses.csv")
    with open(output_file_path, 'w') as output_file:
        output_file.write("Participant")
        output_file.write(';')
        output_file.write("Condition")
        output_file.write(';')
        output_file.write("Run")
        output_file.write(';')
        output_file.write("Count")
        output_file.write(';')
        output_file.write("Responded")
        output_file.write(';')
        output_file.write("Overall clicks")
        output_file.write(';')
        output_file.write("Correct")
        output_file.write(';')
        output_file.write("Incorrect")
        output_file.write(';')
        output_file.write("ResponseTime1")
        output_file.write(';')
        output_file.write("ResponseTime2")
        output_file.write(';')
        output_file.write("ResponseTime3")
        output_file.write(';')
        output_file.write("ResponseTime4")
        output_file.write(';')
        output_file.write("ResponseTime5")
        output_file.write(';')
        output_file.write("ResponseTime6")
        output_file.write(';')
        output_file.write("ResponseTime7")
        output_file.write(';')
        output_file.write("ResponseTime8")
        output_file.write(';')
        output_file.write("ResponseTime9")
        output_file.write(';')
        output_file.write("ResponseTime10")
        output_file.write(';')
        output_file.write("ResponseTime11")
        output_file.write(';')
        output_file.write("ResponseTime12")
        output_file.write(';')
        output_file.write("ResponseTime13")
        output_file.write(';')
        output_file.write("ResponseTime14")
        output_file.write(';')
        output_file.write("ResponseTime15")
        output_file.write(';')
        output_file.write("ResponseTime16")
        output_file.write(';')
        output_file.write("ResponseTime17")
        output_file.write(';')
        output_file.write("ResponseTime18")
        output_file.write(';')
        output_file.write("ResponseTime19")
        output_file.write(';')
        output_file.write("ResponseTime20")
        output_file.write(';')
        output_file.write("ClickTime1")
        output_file.write(';')
        output_file.write("ClickTime2")
        output_file.write(';')
        output_file.write("ClickTime3")
        output_file.write(';')
        output_file.write("ClickTime4")
        output_file.write(';')
        output_file.write("ClickTime5")
        output_file.write(';')
        output_file.write("ClickTime6")
        output_file.write(';')
        output_file.write("ClickTime7")
        output_file.write(';')
        output_file.write("ClickTime8")
        output_file.write(';')
        output_file.write("ClickTime9")
        output_file.write(';')
        output_file.write("ClickTime10")
        output_file.write(';')
        output_file.write("ClickTime11")
        output_file.write(';')
        output_file.write("ClickTime12")
        output_file.write(';')
        output_file.write("ClickTime13")
        output_file.write(';')
        output_file.write("ClickTime14")
        output_file.write(';')
        output_file.write("ClickTime15")
        output_file.write(';')
        output_file.write("ClickTime16")
        output_file.write(';')
        output_file.write("ClickTime17")
        output_file.write(';')
        output_file.write("ClickTime18")
        output_file.write(';')
        output_file.write("ClickTime19")
        output_file.write(';')
        output_file.write("ClickTime20")


        write_line_for_condition(output_file, participant_name, top_down_beacon, "TD_B")
        write_line_for_condition(output_file, participant_name, top_down_no_beacon, "TD_N")
        write_line_for_condition(output_file, participant_name, top_down_untrained, "TD_U")
        write_line_for_condition(output_file, participant_name, bottom_up, "BU")
        write_line_for_condition(output_file, participant_name, syntax, "SY")
    print("-> saving file: done!")


def write_csv_file_comprehension(reports, participant_name):
    print("\n====================\n")
    print("Write comprehension result to a csv file for ...", participant_name)

    # write objects to file as giant csv
    output_file_path = join("output", participant_name + "_responses.csv")
    with open(output_file_path, 'w') as output_file:
        output_file.write("Participant")
        output_file.write(';')
        output_file.write("Condition")
        output_file.write(';')
        output_file.write("Count")
        output_file.write(';')
        output_file.write("Responded")
        output_file.write(';')
        output_file.write("Not Responded")
        output_file.write(';')
        output_file.write("Correct")
        output_file.write(';')
        output_file.write("Incorrect")
        output_file.write(';')
        output_file.write("Late Responded")
        output_file.write(';')
        output_file.write("MultiClicks")
        output_file.write(';')
        output_file.write("OverallClicks")
        output_file.write(';')
        output_file.write("ResponseTime1")
        output_file.write(';')
        output_file.write("ResponseTime2")
        output_file.write(';')
        output_file.write("ResponseTime3")
        output_file.write(';')
        output_file.write("ResponseTime4")
        output_file.write(';')
        output_file.write("ResponseTime5")
        output_file.write(';')
        output_file.write("ClickTime1")
        output_file.write(';')
        output_file.write("ClickTime2")
        output_file.write(';')
        output_file.write("ClickTime3")
        output_file.write(';')
        output_file.write("ClickTime4")
        output_file.write(';')
        output_file.write("ClickTime5")

        [top_down_beacon, top_down_no_beacon, top_down_untrained, bottom_up, syntax] = reports

        write_line_for_condition(output_file, participant_name, top_down_beacon, "TD_B")
        write_line_for_condition(output_file, participant_name, top_down_no_beacon, "TD_N")
        write_line_for_condition(output_file, participant_name, top_down_untrained, "TD_U")
        write_line_for_condition(output_file, participant_name, bottom_up, "BU")
        write_line_for_condition(output_file, participant_name, syntax, "SY")
    print("-> saving file: done!")


def write_line_for_condition(output_file, participant_name, summary, name):
    output_file.write('\n')
    output_file.write(participant_name)
    output_file.write(';')
    output_file.write(name)
    output_file.write(';')
    output_file.write(str(summary["count"]))
    output_file.write(';')
    output_file.write(str(summary["responded"]))
    output_file.write(';')
    output_file.write(str(summary["not_responded"]))
    output_file.write(';')
    output_file.write(str(summary["correct"]))
    output_file.write(';')
    output_file.write(str(summary["incorrect"]))
    output_file.write(';')
    output_file.write(str(summary["late_responses"]))
    output_file.write(';')
    output_file.write(str(summary["multi_clicks"]))
    output_file.write(';')
    output_file.write(str(summary["overall_clicks"]))
    output_file.write(';')
    output_file.write("" if len(summary["response_times"]) == 0 else str(summary["response_times"][0]))
    output_file.write(';')
    output_file.write("" if len(summary["response_times"]) < 2 else str(summary["response_times"][1]))
    output_file.write(';')
    output_file.write("" if len(summary["response_times"]) < 3 else str(summary["response_times"][2]))
    output_file.write(';')
    output_file.write("" if len(summary["response_times"]) < 4 else str(summary["response_times"][3]))
    output_file.write(';')
    output_file.write("" if len(summary["response_times"]) < 5 else str(summary["response_times"][4]))
    output_file.write(';')
    output_file.write("" if len(summary["click_times"]) == 0 else str(summary["click_times"][0]))
    output_file.write(';')
    output_file.write("" if len(summary["click_times"]) < 2 else str(summary["click_times"][1]))
    output_file.write(';')
    output_file.write("" if len(summary["click_times"]) < 3 else str(summary["click_times"][2]))
    output_file.write(';')
    output_file.write("" if len(summary["click_times"]) < 4 else str(summary["click_times"][3]))
    output_file.write(';')
    output_file.write("" if len(summary["click_times"]) < 5 else str(summary["click_times"][4]))


main()
