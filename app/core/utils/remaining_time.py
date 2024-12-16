from datetime import timedelta


def get_formatted_remaining_time(remaining_time: timedelta) -> str:
    hours, remainder = divmod(remaining_time.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    display_time: str  # In $HH:$MM:$SS format
    if remaining_time.days > 0:
        day_str: str = "days" if remaining_time.days > 1 else "day"
        display_time = f"{remaining_time.days} {day_str}, {hours:02}:{minutes:02}:{seconds:02}"
    else:
        display_time = f"{hours:02}:{minutes:02}:{seconds:02}"

    return display_time
