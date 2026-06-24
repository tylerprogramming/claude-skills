#!/usr/bin/env python3
"""Generate .ics calendar file from a fitness plan markdown file.

Usage:
    python3 generate_calendar.py [plan_path] [output_path]

Defaults:
    plan_path:   ~/fitness/<current_month>-plan.md (e.g. march-plan.md)
    output_path: ~/fitness/<plan_name>.ics

Parses the plan title for year (e.g. "March 2026 Training Plan") and
week headers for month + date ranges (e.g. "## Week 1 (Mar 9-15)").
Works for any month/year — not hardcoded.
"""

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

from icalendar import Calendar, Event, Alarm

# Day abbreviation to weekday number (Monday=0)
DAY_MAP = {
    "Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6
}

# Month abbreviation to number
MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
}

# Full month name to number
MONTH_FULL_MAP = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
}


def parse_year_from_title(text):
    """Extract year from the plan title line, e.g. '# March 2026 Training Plan'."""
    match = re.search(r"^#\s+\w+\s+(\d{4})", text, re.MULTILINE)
    if match:
        return int(match.group(1))
    # Fallback: look for any 4-digit year
    match = re.search(r"20\d{2}", text)
    return int(match.group(0)) if match else datetime.now().year


def parse_month_from_header(header_text):
    """Extract month number from a week header like 'Mar 9-15' or 'Mar 31'."""
    for abbr, num in MONTH_MAP.items():
        if abbr in header_text:
            return num
    return None


def parse_focus_from_table(text):
    """Parse the weekly structure table to get day focus labels."""
    focus_map = {}
    table_pattern = re.compile(
        r"\|\s*\*\*(\w+)\*\*\s*\|\s*([^|]+?)\s*\|"
    )
    day_name_to_num = {
        "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
        "Friday": 4, "Saturday": 5, "Sunday": 6
    }
    for match in table_pattern.finditer(text):
        day_name = match.group(1)
        focus = match.group(2).strip()
        if day_name in day_name_to_num:
            focus_map[day_name_to_num[day_name]] = focus
    return focus_map


def parse_plan(plan_path):
    """Parse a plan markdown file and return (date, title, description) tuples."""
    text = Path(plan_path).read_text()
    year = parse_year_from_title(text)
    focus_map = parse_focus_from_table(text)
    events = []

    # Match week sections: "## Week 1 (Mar 9-15)" or "## Bonus (Mar 31)"
    week_pattern = re.compile(
        r"## (?:Week \d+|Bonus) \(([^)]+)\)\s*\n((?:- \*\*\w+\*\*:.*\n?)+)"
    )

    for match in week_pattern.finditer(text):
        date_range = match.group(1)
        workout_block = match.group(2)

        # Parse month and start day from range like "Mar 9-15" or "Mar 31"
        month = parse_month_from_header(date_range)
        if month is None:
            continue

        day_nums = re.findall(r"\d+", date_range)
        if not day_nums:
            continue
        start_day = int(day_nums[0])

        # Parse each day's workout in this week
        day_pattern = re.compile(r"- \*\*(\w+)\*\*: (.+)")
        for day_match in day_pattern.finditer(workout_block):
            day_abbr = day_match.group(1)
            details = day_match.group(2).strip()

            if day_abbr not in DAY_MAP:
                continue

            target_weekday = DAY_MAP[day_abbr]

            # Calculate the actual date
            # Find the Monday of the week containing start_day
            ref_date = datetime(year, month, start_day)
            ref_weekday = ref_date.weekday()
            week_monday = ref_date - timedelta(days=ref_weekday)
            event_date = week_monday + timedelta(days=target_weekday)

            # Use focus from table, or fall back to day abbreviation
            title = focus_map.get(target_weekday, f"{day_abbr} Workout")

            events.append((event_date, title, details))

    return events


def generate_ics(events, output_path, cal_name="Training Plan"):
    """Generate an .ics calendar file from parsed events."""
    cal = Calendar()
    cal.add("prodid", "-//Fitness Plan//claude-skills//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("x-wr-calname", cal_name)

    for event_date, title, description in events:
        event = Event()
        event.add("summary", f"🏋️ {title}")
        event.add("description", description)

        # Event at 5:00 AM
        start = event_date.replace(hour=5, minute=0, second=0)
        event.add("dtstart", start)
        event.add("dtend", start + timedelta(hours=1, minutes=30))

        # Night-before reminder at 8 PM (= 9 hours before 5 AM event)
        alarm = Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add("description", f"Tomorrow: {title} - {description}")
        alarm.add("trigger", timedelta(hours=-9))
        event.add_component(alarm)

        cal.add_component(event)

    Path(output_path).write_bytes(cal.to_ical())
    print(f"Generated {len(events)} events -> {output_path}")


def main():
    # Determine plan path
    if len(sys.argv) > 1:
        plan_path = Path(sys.argv[1])
    else:
        # Default: look for <month>-plan.md in ~/fitness/
        fitness_dir = Path.home() / "fitness"
        plans = sorted(fitness_dir.glob("*-plan.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        if plans:
            plan_path = plans[0]
            print(f"Using most recent plan: {plan_path.name}")
        else:
            print("Error: No plan files found in ~/fitness/")
            sys.exit(1)

    if not plan_path.exists():
        print(f"Error: Plan file not found at {plan_path}")
        sys.exit(1)

    # Determine output path
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    else:
        output_path = plan_path.with_suffix(".ics")

    # Extract calendar name from plan title
    text = plan_path.read_text()
    title_match = re.search(r"^#\s+(.+?)(?:\s*\(.*\))?$", text, re.MULTILINE)
    cal_name = title_match.group(1).strip() if title_match else "Training Plan"

    events = parse_plan(plan_path)
    if not events:
        print("Error: No events parsed from plan file")
        sys.exit(1)

    generate_ics(events, output_path, cal_name)


if __name__ == "__main__":
    main()
