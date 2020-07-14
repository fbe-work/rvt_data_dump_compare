import argparse
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def dict_compare(current, previous, mode="added"):
    set_current  = set( current.keys())
    set_previous = set(previous.keys())
    intersect   = set_current.intersection(set_previous)
    if mode == "added":
        return {o:f"{current[o]}" for o in set_current - intersect}
    elif mode == "removed":
        return {o:"<REMOVED>" for o in set_previous - intersect}
    elif mode == "changed":
        return {o:f"{previous[o]}->{current[o]}" for o in intersect if previous[o] != current[o]}
    elif mode == "unchanged":
        return {o:f"{current[o]}" for o in intersect if previous[o] == current[o]}
    else:
        return {}


def print_dict_changes(current, previous):
    compare_modes = {"added", "removed","changed"}
    change_collector = []
    change_result = {}
    guid = current['GUID']
    rvt_id = current['rvt_id']
    for mode in compare_modes:
        compare_result = dict_compare(current, previous, mode=mode)
        if compare_result:
            print(f"{mode.rjust(7)} elem {rvt_id.rjust(10)}: {compare_result}")
            change_collector.append(compare_result)

    if change_collector:
        for change in change_collector:
            # print(change)
            change_result.update(change)
            # print("change_result: ", change_result)

    added_param_curr = current_elems[guid].get(list_param)
    added_param_prev = previous_elems[guid].get(list_param)
    extra_param_curr = added_param_curr if added_param_curr else ""
    extra_param_prev = added_param_prev if added_param_prev else ""
    if extra_param_curr == extra_param_prev:
        extra_param_val = f";{extra_param_curr}"
    else:
        extra_param_val = f";{extra_param_prev}->{extra_param_curr}"

    if "location" in change_result:
        results["moved"].append([guid, rvt_id, "moved", str(change_result) + extra_param_val])
        results_raw["moved"].append([guid, rvt_id, "moved", change_result])
        reduced_header.update(change_result)
    else:
        results["changed"].append([guid, rvt_id, "changed", str(change_result) + extra_param_val])
        results_raw["changed"].append([guid, rvt_id, "changed", change_result])
        reduced_header.update(change_result)


parser = argparse.ArgumentParser(description='compare two csv element data dumps')
parser.add_argument('current_csv',  type=str, help='csv path to current elems')
parser.add_argument('previous_csv', type=str, help='csv path to previous elems to compare against')
parser.add_argument('--param', type=str, nargs='?', const=True, default=None)
args = parser.parse_args()

current_csv   = Path(args.current_csv)
previous_csv  = Path(args.previous_csv)
list_param    = args.param

today = datetime.now().strftime("%Y%m%d")

if not current_csv.exists() or not previous_csv.exists():
    print("please provide with functional paths")
    exit()

current_root          = current_csv.parent
result_csv            = current_root / f"{today}_comparison_result.csv"
result_table_view_csv = current_root / f"{today}_comparison_result_table_view.csv"

previous_elems = {}
current_elems  = {}
results        = defaultdict(list)
results_raw    = defaultdict(list)
reduced_header = set()

with open(current_csv) as txt_file:
    for line in txt_file.readlines():
        if line.startswith("rvt_id"):
            keys = line.strip().replace('"', '').split(";")
            current_header = keys
        else:
            vals = line.strip().replace('"', '').split(";")
            guid = vals[1]
            elem_dict = {k: v for k, v in zip(keys, vals) if v}
            current_elems[guid] = elem_dict

with open(previous_csv) as txt_file:
    for line in txt_file.readlines():
        if line.startswith("rvt_id"):
            keys = line.strip().replace('"', '').split(";")
        else:
            vals = line.strip().replace('"', '').split(";")
            guid = vals[1]
            elem_dict = {k:v for k, v in zip(keys, vals) if v}
            previous_elems[guid] = elem_dict

new_elem_ids = []
for guid in current_elems:
    if guid not in previous_elems:
        rvt_id = current_elems[guid]["rvt_id"]
        added_param = current_elems[guid].get(list_param)
        extra_param = ";" + added_param if added_param else ""
        new_elem_ids.append(rvt_id)
        results["new"].append([guid, rvt_id, "new", extra_param or ""])
        results_raw["new"].append([guid, rvt_id, "new"])


deleted_elem_ids = []
for guid in previous_elems:
    if guid not in current_elems:
        rvt_id = previous_elems[guid]["rvt_id"]
        added_param = previous_elems[guid].get(list_param)
        extra_param = ";" + added_param if added_param else ""
        deleted_elem_ids.append(rvt_id)
        results["deleted"].append([guid, rvt_id, "deleted", extra_param or ""])
        results_raw["deleted"].append([guid, rvt_id, "new"])

print(f"{today} - comparing revit elem data dumps:\ncurrent:  {current_csv}\nprevious: {previous_csv}")

print(f"elems in current:  {len(current_elems):>4}")
print(f"elems in previous: {len(previous_elems):>4}")

print(23*"=")
print("    new elems:")
for elem_id in new_elem_ids:
    print(f"    new elem {elem_id.rjust(10)}")

print(23*"=")
print("deleted elems:")
for elem_id in deleted_elem_ids:
    print(f"deleted elem {elem_id.rjust(10)}")

changed_data = []
print(23*"=")
print("changed elems:")
for guid in current_elems:
    curr_elem = current_elems[guid]
    prev_elem = previous_elems.get(guid)
    if not previous_elems.get(guid):
        continue
    if curr_elem != prev_elem:
        print_dict_changes(curr_elem, prev_elem)

print(23*"=")
for mode, elems in results.items():
    print(mode.rjust(7), len(elems))

print(f"writing: {result_csv}")
with open(result_csv, "w") as res_csv:
    header = f"guid;rvt_id;change_type;changed_parameters"
    if list_param:
        header = "{};{}".format(header, list_param)
    res_csv.write(header + "\n")
    for mode in results:
        for elem_data in results[mode]:
            data = ";".join(elem_data)
            res_csv.write(data + "\n")

print(f"writing: {result_table_view_csv}")
with open(result_table_view_csv, "w") as res_csv:
    header_prefix = f"guid;rvt_id;change_type;"
    header = header_prefix + ";".join(sorted(reduced_header))
    if list_param:
        header = "{};{}".format(header, list_param)
    res_csv.write(header + "\n")
    for mode in results:
        for elem_data in results[mode]:
            elem_data = [elem for elem in elem_data if elem]
            has_str_dict_data = elem_data[-1][0] == "{"
            # print(35*"-")
            # print(mode, elem_data)
            if has_str_dict_data:
                line_data = elem_data[:-1]
                if type(eval(elem_data[-1].rsplit(";")[0])) == dict:
                    str_to_dict = eval(elem_data[-1].rsplit(";")[0])
                    line_vals = [str_to_dict.get(key) or ""  for key in sorted(reduced_header)]
                    if list_param:
                        added_param = elem_data[-1].rsplit(";")[1]
                        # line_vals.append(added_param)
                        # print(added_param)
            else:
                line_data = elem_data
                if list_param:
                    if elem_data[-1] == mode:
                        line_data = elem_data
                    else:
                        line_data = elem_data[:-1]
                line_vals = ["" for key in sorted(reduced_header)]
                if list_param:
                    if elem_data[-1] == mode:
                        added_param = ""
                    else:
                        added_param = elem_data[-1].rsplit(";")[-1]
                    # print(added_param)

            line_data.extend(line_vals)
            if list_param:
                line_data.append(added_param)
            # print(len(line_data), line_data)
            line_data = ";".join(line_data)
            res_csv.write(line_data + "\n")
