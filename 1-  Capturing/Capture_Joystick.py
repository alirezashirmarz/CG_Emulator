import pygame
import time
import json
from datetime import datetime

# Configuration
LOG_FILE = "Forza_W_joystick_log.txt"
CAPTURE_DURATION = 300  # Duration to capture data (in seconds) (Capture time that is 300 for 5 min)
TICKS_PER_SECOND = 30  # Number of ticks per second (for sampling) (It is rate of sampling that should be match with fps (30 frame per second))

def get_joystick_data():
    """Retrieve current joystick axes and buttons data."""
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        raise RuntimeError("No joystick detected.")

    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    axes = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
    buttons = [joystick.get_button(i) for i in range(joystick.get_numbuttons())]

    # Convert to dictionary format for easy comparison
    return {
        "axes": {i: axes[i] for i in range(len(axes))},
        "buttons": {i: buttons[i] for i in range(len(buttons))}
    }

def log_joystick_data():
    """Log joystick data based on sampling rate and on changes."""
    with open(LOG_FILE, "a") as log_file:
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Remove extra microseconds
        log_file.write(f"Logging started at: {start_time}\n")

        end_time = time.time() + CAPTURE_DURATION
        previous_data = None
        tick_count = 0
        tick_interval = 1.0 / TICKS_PER_SECOND
        next_tick_time = time.time() + tick_interval

        while time.time() < end_time:
            current_time = time.time()

            current_data = get_joystick_data()

            # Check for changes between ticks
            if current_data != previous_data:
                # Log the change immediately
                log_entry = create_log_entry(tick_count, current_data)
                log_file.write(json.dumps(log_entry) + "\n")
                log_file.flush()  # Ensure data is written immediately
                previous_data = current_data  # Update the previous state

            # Log data at the next tick
            if current_time >= next_tick_time:
                tick_count += 1
                next_tick_time += tick_interval
                log_entry = create_log_entry(tick_count, current_data)
                log_file.write(json.dumps(log_entry) + "\n")
                log_file.flush()  # Ensure data is written immediately

            # Short sleep to match the tick rate
            time.sleep(0.01)

        end_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_file.write(f"Logging ended at: {end_time_str}\n")

def create_log_entry(tick_count, data):
    """Helper function to create a log entry with milliseconds."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Accurate to milliseconds
    return {
        "tick": tick_count,
        "timestamp": timestamp,
        "data": data
    }

if __name__ == "__main__":
    print("Joystick logger starts...\n")
    log_joystick_data()
