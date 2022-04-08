import base64
import sys
from datetime import datetime
from subprocess import PIPE, Popen

from workflow.workflow import ICON_CLOCK
from workflow.workflow3 import Workflow3

DEFAULT_CAL = "Work"
FOREVER = 0xffffffff

template = '''
tell application "Calendar"
	tell calendar "{cal_name}"
		make new event at end with properties {{summary:"{event_name}", start date:(current date) - ({h} * hours) - ({m} * minutes), end date:((current date))}}
	end tell
end tell
'''

def get_time_diff(start):
        diff = datetime.now() - start
        hours = diff.seconds // (60 * 60)
        minutes = (diff.seconds // 60) % 60
        return hours, minutes


def on_start(wf: Workflow3):
    start = wf.cached_data("start", max_age=FOREVER)
    if start == None:
        if len(wf.args) == 1 or wf.args[1] == "":
            task = wf.cached_data("info") if wf.cached_data("info") else ""
        else:
            task = wf.args[1]
        wf.add_item(
            title="You don't have task to do now",
            subtitle=f"ENTER to add task {task}",
            valid=True,
            arg=f"{task}")
    else:
        info = wf.cached_data("info", max_age=FOREVER)
        cal_name, event_name = info.split(":")
        hours, minutes = get_time_diff(start)
        wf.logger.debug(f"{cal_name}, {event_name}, {hours}, {minutes}")
        item = wf.add_item(
            title=f"You are working on {event_name}",
            subtitle=f"Last {hours} hour(s) and {minutes} minute(s). Do you want to pause it? (CMD to stop)",
            icon=ICON_CLOCK,
            valid=True,
            arg=f"{info}"
        )
        item.add_modifier(
            key="cmd",
            subtitle="Did you finish your working?"
        )
        item.add_modifier(
            key="ctrl",
            subtitle="Are you sure to delete your work?"
        )
    wf.send_feedback()


def on_end(wf: Workflow3, pause=False):
    start = wf.cached_data("start", max_age=FOREVER)
    if start == None:
        start = datetime.now()
        wf.cache_data("start", data=start)
        event = wf.args[1].split(":")
        wf.logger.debug(event)
        event_name = event[1] if len(event) > 1 else event[0]
        cal_name = event[0] if len(event) > 1 else DEFAULT_CAL
        wf.cache_data("info", data=f'{cal_name}:{event_name}')
        print(f"Add task {event_name} on {cal_name}")
    else:
        info = wf.cached_data("info", max_age=FOREVER)
        cal_name, event_name = info.split(":")
        hours, minutes = get_time_diff(start)
        script = template.format(cal_name=cal_name, event_name=event_name, h=hours, m=minutes)
        p = Popen(['osascript', '-'], stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        _, stderr = p.communicate(script)
        wf.logger.debug(stderr)
        clear_data(pause)
        leader = "Puased" if pause else "Stoped"
        print(f"{leader} current task")


def clear_data(pause=False):
    wf.cache_data("start", None)
    if not pause:
        wf.cache_data("info", None)


def main(wf: Workflow3):
    option = wf.args[0]
    wf.logger.debug(wf.args)
    if option == "start":
        on_start(wf)
    if option == "end":
        on_end(wf)
    if option == "pause":
        on_end(wf, pause=True)
    if option == "delete":
        clear_data()
        print("Cleared previous calendar info")


if __name__ == "__main__":
    wf = Workflow3()
    sys.exit(wf.run(main))
