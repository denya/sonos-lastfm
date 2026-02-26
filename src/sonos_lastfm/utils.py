# Copyright (c) 2025 Denis Moskalets
# Licensed under the MIT License.

"""Utility functions for the Sonos Last.fm scrobbler."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

# Set up logger
logger = logging.getLogger(__name__)

# Track display state using a mutable mapping to avoid global statements
_display_state: dict[str, Any] = {
    "last_line_count": 0,
    "display_started": False,
    "log_lines_since_last_display": 0,
}


class LogLineCounter(logging.Handler):
    """Handler that counts log lines for display management."""

    def __init__(self) -> None:
        """Initialize the handler with shared display state."""
        super().__init__()
        self._state = _display_state

    def emit(self, _record: logging.LogRecord) -> None:
        """Process a log record by incrementing the line counter."""
        self._state["log_lines_since_last_display"] += 1


# Add our custom handler to the root logger
logging.getLogger().addHandler(LogLineCounter())


def custom_print(message: str, level: str = "INFO") -> None:
    """Custom print function that tracks lines and formats output consistently.

    Args:
        message: The message to print
        level: The log level (INFO, WARNING, ERROR, etc.)
    """
    # Count how many newlines are in the message
    newline_count: int = message.count("\n")

    # Format the message with timestamp and level
    timestamp: str = logging.Formatter("%(asctime)s").format(
        logging.LogRecord("", 0, "", 0, None, None, None),
    )
    formatted_message: str = f"{timestamp[:-4]} - {level} - {message}"

    # Print the message
    print(formatted_message, flush=True)  # noqa: T201

    # Update the line counter
    _display_state["log_lines_since_last_display"] += 1 + newline_count


def reset_log_line_counter() -> None:
    """Reset the counter for log lines since last display update."""
    _display_state["log_lines_since_last_display"] = 0


def create_progress_bar(
    current: int,
    total: int,
    threshold: int,
    width: int = 50,
) -> str:
    """Create an ASCII progress bar showing current position and scrobble threshold.

    Args:
        current: Current position in seconds
        total: Total duration in seconds
        threshold: Scrobble threshold in seconds
        width: Width of the progress bar in characters

    Returns:
        A string containing the progress bar
    """
    if total == 0:
        return "[" + " " * width + "] 0%"

    # Calculate exact percentage and positions
    percentage: int = (current * 100) // total if total > 0 else 0
    progress: int = int((current * width) / total) if total > 0 else 0
    threshold_pos: int = int((threshold * width) / total) if total > 0 else 0

    # Create the bar
    bar: list[str] = list("." * width)

    # Add threshold marker
    if 0 <= threshold_pos < width:
        bar[threshold_pos] = "|"

    # Fill progress
    for i in range(progress):
        if i < width:
            bar[i] = "="

    # Add position marker (only if within bounds)
    if 0 <= progress < width:
        bar[progress] = ">"

    return f"[{''.join(bar)}] {percentage}%"


def update_all_progress_displays(speakers_info: Mapping[str, dict[str, Any]]) -> None:
    """Update progress display for all speakers in a coordinated way.

    Args:
        speakers_info: Dictionary mapping speaker IDs to their current track info
            Each track info should contain:
            - speaker_name: str
            - artist: str
            - title: str
            - position: int (seconds)
            - duration: int (seconds)
            - threshold: int (seconds)
            - state: str
    """
    # Prepare the display content
    lines: list[str] = []

    # Generate display for each speaker
    for speaker_info in speakers_info.values():
        current: int = speaker_info["position"]
        total: int = speaker_info["duration"]

        # Format time as MM:SS
        current_time: str = f"{current // 60:02d}:{current % 60:02d}"
        total_time: str = f"{total // 60:02d}:{total % 60:02d}"

        # Create status lines
        status: str = (
            f"{speaker_info['speaker_name']}: "
            f"{speaker_info['artist']} - {speaker_info['title']} "
            f"[{speaker_info['state']}]"
        )
        progress: str = create_progress_bar(current, total, speaker_info["threshold"])
        percentage: int = (current * 100) // total if total > 0 else 0
        time_display: str = f"Time: {current_time}/{total_time} ({percentage}%)"

        # Add this speaker's display
        lines.extend([status, progress, time_display, ""])

    # Calculate total lines including header
    display_lines: list[str] = ["=== Progress Display ===", *lines]
    total_lines: int = len(display_lines)

    if not _display_state["display_started"]:
        # First time display
        print("\n".join(display_lines), flush=True)  # noqa: T201
        _display_state["display_started"] = True
        _display_state["last_line_count"] = total_lines
    else:
        # BEGIN OF IMPORTANT CODE #
        clean_up_lines: int = int(_display_state["last_line_count"])
        total_move_up: int = int(
            _display_state["log_lines_since_last_display"] + clean_up_lines,
        )

        # Move cursor up by total_move_up lines
        sys.stdout.write(f"\033[{total_move_up}A")
        # Clear all previous display lines
        for _ in range(clean_up_lines):
            sys.stdout.write("\033[K")  # Clear current line
            sys.stdout.write("\033[1B")  # Move down 1 line
        # Move back to start position
        sys.stdout.write(f"\033[{clean_up_lines}A")
        # END of IMPORANT CODE #

        # Write new display
        print("\n".join(display_lines), flush=True)  # noqa: T201
        _display_state["last_line_count"] = total_lines

    # Reset the log line counter
    reset_log_line_counter()
