import os
import re
import gzip
import json
from datetime import datetime, time, timedelta

"""
Basic classes to store log information
"""


class TimeInterval:
    def __init__(self, initial: datetime = None, final: datetime = None):
        self.interval = (initial, final)


class Log:
    def __init__(self, file_path: str = None, kind: str = None, time_interval: TimeInterval = None, events: [] = None):
        self.file = file_path if file_path else str()
        self.kind = kind if kind else str()
        self.t_interval = time_interval.interval if time_interval else None
        self.events = events if events else {}

    def print_name(self):
        print(self.file, "\n" + " " * 10, self.kind, ", ", self.t_interval)
        return

    def read_events(self, fields: [] = "all", filter_events = lambda x: False, *args):
        # skip summary logs
        if re.match(r".*-summary", self.kind):
            return
        else:
            with gzip.open(self.file, "r") as f:
                events = []
                event_type = self.kind
                for event in f:
                    content = json.loads(event)
                    if filter_events(content,*args):
                        #print("Im filtering ", *args)
                        continue
                    fields = content.keys() if fields == "all" else fields
                    events.append({key: content[key] for key in list(set(content.keys()) & set(fields))})
                self.events=events
                return


"""
# Helpers
# Functions for information in log's names
"""

# TODO: use smarter regex
def read_log_names(path,month,day):
    files = os.listdir(path)
    # extract type of log, starting time and stopping time
    logs = []
    for file_name in files:
        split_name = re.split(r"\.", file_name)
        split_name = [split_name[0], re.split(r"-", split_name[1])]
        log = Log(os.path.join(path, file_name), split_name[0], read_time_interval(split_name,month,day))

        logs.append(log)
    return sorted(logs, key=lambda x: x.t_interval[0])

def read_time_interval(split_log,month,day,year="2022"):
    time_int = TimeInterval(
        datetime(
            int(year), int(month), int(day),
            int(split_log[1][0][0:2]),
            int(split_log[1][0][5:7]),
            int(split_log[1][0][10:12])
        ),
        datetime(
            int(year), int(month), int(day),
            int(split_log[1][1][0:2]),
            int(split_log[1][1][5:7]),
            int(split_log[1][1][10:12])
        )
    )
    # time_int.append(time_int[1]-time_int[0])
    return time_int


# Functions for information inside the logs


def accumulate_events(log, time_interval=20):
    with gzip.open(os.path.join(PATH, log[0]), "r") as f:
        events = []
        event_type = log[1]
        for event in f:
            content = json.loads(event)
            event_datetime = datetime.fromtimestamp(int(content["ts"]))
            events.append([event_type, event_datetime])
        return events


def count_events(log):
    # skip summary logs
    if re.match(r".*-summary", log[0]):
        return None
    else:
        with gzip.open(os.path.join(PATH, log[0]), "r") as f:
            contents = list(f.readlines())
            num_lines = len(contents)
            middle_time = log[2][0] + timedelta(0, 120)
            return num_lines, middle_time


"""def count_events(log):
    #skip summary logs
    if re.match(r".*-summary",log[0]):
        return None
    else:
        with gzip.open(os.path.join(PATH,log[0]),"r") as f:
            contents=list(f.readlines())
            num_lines=len(contents)
            ts_first_line= json.loads(contents[0].strip().decode())["ts"]
            ts_last_line= json.loads(contents[-1].strip().decode())["ts"]
            middle_time=datetime.fromtimestamp(round(ts_first_line+(ts_last_line-ts_first_line)/2))
            return num_lines, middle_time            """
