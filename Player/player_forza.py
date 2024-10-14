import cv2 , os, threading
import socket
import time
import pandas as pd
from datetime import datetime
import struct

# UDP Socket setup
cg_server_ip = "200.18.102.25"  # IP address of the server (or the target machine)
cg_server_port = 5501        # Port number to send commands to

player_ip = "200.18.102.9" #'200.18.102.9'  # This Machine Port '172.17.0.1'
player_port = 5000  # Now both GStreamer and UDP socket will use port 5000

auto_commands_file_addr = "/home/alireza/CG_Simulation/Phase4_Player_Command/autocommands_forza.txt"

'''
# Function to ping the server and log the RTT
def ping_and_log_rtt(server_ip, log_file):
    while True:
        response = os.popen(f"ping -c 1 -s 0 {server_ip}").read()
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        if "time=" in response:
            rtt_start = response.find("time=") + 5
            rtt_end = response.find(" ms", rtt_start)
            rtt = response[rtt_start:rtt_end]
            log_line = f"{timestamp} - RTT: {rtt} ms\n"
        else:
            log_line = f"{timestamp} - RTT: N/A\n"
        with open(log_file, "a") as log:
            log.write(log_line)
        print(log_line, end="")
        time.sleep(1)  # Wait for 1 second before next ping

# Start the pinging in a separate thread
def start_ping_thread(server_ip, log_file):
    ping_thread = threading.Thread(target=ping_and_log_rtt, args=(server_ip, log_file))
    ping_thread.daemon = True
    ping_thread.start()

'''

# Custom function to load autocommands.txt while handling the complex 'command' field
def load_autocommands(file_path):
    autocommands = []
    with open(file_path, 'r') as file:
        next(file)  # Skip the header line
        for line in file:
            # Split only on the last comma to avoid splitting inside the 'command' field
            parts = line.rsplit(',', 1)
            if len(parts) == 2:
                id_and_command, encrypted_cmd = parts
                # Split the ID from the command part
                id_str, command_str = id_and_command.split(',', 1)
                autocommands.append((int(id_str), command_str, encrypted_cmd.strip()))
    return pd.DataFrame(autocommands, columns=['ID', 'command', 'encrypted_cmd'])

# Load autocommand.txt
autocommands_df = load_autocommands(auto_commands_file_addr)

# Debug: Print the content of autocommand.txt
print("Loaded autocommands:")
print(autocommands_df)

# Function to send command to server
def send_command(frame_id, encrypted_cmd,interface_name= "wlp0s20f3"):  #"enp0s31f6" wlp0s20f3
    # Create the UDP socket and allow address reuse
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, interface_name.encode())
    # Bind the socket to port 5000 for sending (reusing the port)
    sock.bind((player_ip, player_port))  # Bind to port 5000 for sending
    # UDP Socket setup
    timestamp = time.time() * 1000  # Get current timestamp in nano second /old was milliseconds (*1000)
    message = f"{timestamp},{encrypted_cmd}"   
    # Send the message over UDP
    sock.sendto(message.encode(), (cg_server_ip, cg_server_port))
    print('Alireza socket port===========',sock.getsockname(),(cg_server_ip, cg_server_port))
    # Close the socket after sending
    sock.close()
    
    print(f"Sent command for Frame ID {frame_id}: {message}")
# Example usage:
# send_command(100, "example_encrypted_command")



# GStreamer pipeline to receive video stream from port 5000

gstreamer_pipeline = (
    f"udpsrc port={player_port} ! application/x-rtp, payload=96 ! "
    "rtph264depay ! avdec_h264 ! videoconvert ! appsink"
)

'''(
    f"udpsrc port={player_port} buffer-size=100000 ! application/x-rtp, payload=96 ! "
    "rtph264depay ! avdec_h264 ! videoconvert ! appsink"
)'''

'''(
    f"udpsrc port={player_port} ! application/x-rtp, payload=96 ! "
    "rtph264depay ! avdec_h264 ! videoconvert ! appsink"
)'''
''' buffer-size=100000
gstreamer_pipeline = (
    f"udpsrc port={player_port} ! application/x-rtp, payload=96 ! "
    "rtph264depay ! avdec_h264 ! tee name=t "
    "t. ! queue ! videoconvert ! autovideosink "  # Display branch
    "t. ! queue ! x264enc bitrate=5000 ! mp4mux ! filesink location= CG_Received_Video.mp4"  # Save to file branch
)
'''
# Open the video stream using OpenCV and GStreamer
cap = cv2.VideoCapture(gstreamer_pipeline, cv2.CAP_GSTREAMER)

'''
Testing binding the port
'''
##########################################################################
# Create UDP socket and enable address/port reuse
#sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
#sock.bind((player_ip, player_port))  # Bind to port 5000



if not cap.isOpened():
    print("Error: Could not open video stream")
    exit()

frame_counter = 1
timeout_duration = 0.001  # 5 seconds timeout for frame reception
previous_command = None

while True:
    start_time = time.time()  # Start the timer for timeout

    # Try to receive the next frame
    ret, frame = cap.read()

    # If no frame is received within the timeout, resend the previous command
    if not ret:
        while not ret and time.time() - start_time < timeout_duration:
            # Wait for a bit before trying again
            time.sleep(0.1)
            ret, frame = cap.read()
        
        if not ret:  # If still no frame after timeout, resend the command
            if previous_command:
                print(f"Timeout occurred, resending the previous command for Frame {frame_counter}")
                send_command(frame_counter - 1, previous_command)
            continue

    frm_rcv = time.time() * 1000  # Millisecond timestamp for frame received

    # Save the current frame to a file
    frame_filename = f"./rcv_forza/{frame_counter:04d}_{frm_rcv}.png"
    cv2.imwrite(frame_filename, frame)
    print(f"Saved {frame_filename}")

    # Log frame received time
    with open("forza_frame_received_log.txt", "a") as f:
        f.write(f"{frame_counter},{frm_rcv}\n")

    # Display the frame
    cv2.imshow("CG Player Client (LERIS)", frame)

    # Check if there's a matching command for this frame
    matching_command = autocommands_df[autocommands_df['ID'] == (frame_counter+1)]

    if not matching_command.empty:
        print(f"Match found for Frame {frame_counter}")  # Debug print

        # Send the command for the current frame
        matching_command.apply(lambda row: send_command(frame_counter, row['encrypted_cmd']), axis=1)

        # Store the command to resend if the next frame isn't received
        previous_command = matching_command.iloc[0]['encrypted_cmd']

        cmd_sent = time.time() * 1000  # Millisecond timestamp for command sent
        with open("forza_command_sent_log.txt", "a") as f:
            f.write(f"{frame_counter},{cmd_sent}\n")
    
    else:
        print(f"Frame with no action {frame_counter}")

    frame_counter += 1

    # Press 'q' to exit the video display window
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
cap.release()
cv2.destroyAllWindows()

