import cv2
import socket
import time
import pandas as pd
from datetime import datetime

# UDP Socket setup
cg_server_ip = '200.18.102.25'  # IP address of the server (or the target machine)
cg_server_port = 5501        # Port number to send commands to

player_ip = '0.0.0.0'  # This Machine Port '172.17.0.1'  200.18.102.9
player_port = 5000  # Now both GStreamer and UDP socket will use port 5000



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
autocommands_df = load_autocommands('/home/alireza/CG_Simulation/Phase2_Ordering/autocommands_kombat.txt')

# Debug: Print the content of autocommand.txt
print("Loaded autocommands:")
print(autocommands_df)

# Function to send command to server
def send_command(frame_id, encrypted_cmd):
    # Create the UDP socket and allow address reuse
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    
    # Bind the socket to port 5000 for sending (reusing the port)
    sock.bind((player_ip, player_port))  # Bind to port 5000 for sending
    # UDP Socket setup
    timestamp = time.time() * 1000  # Get current timestamp in nano second /old was milliseconds (*1000)
    message = f"{timestamp},{encrypted_cmd}"   
    # Send the message over UDP
    sock.sendto(message.encode(), (cg_server_ip, cg_server_port))
    print('Alireza socket port===========',sock.getsockname()[1])
    # Close the socket after sending
    sock.close()
    
    print(f"Sent command for Frame ID {frame_id}: {message}")


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

# Create UDP socket and enable address/port reuse
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
# sock.bind((client_ip, client_port))  # Bind to port 5000


if not cap.isOpened():
    print("Error: Could not open video stream")
    exit()

# Variables reset
frame_counter = 1
total_buffer_bytes = 0  # Accumulate the total bytes received
buffer_frame_count = 0  # Number of frames currently in the buffer


# Open the log file to store buffer information
buffer_log_file = open("client_buffer_log.txt", "w")
buffer_log_file.write("ID,Frames in Buffer,Occupied Buffer in Bytes\n")  # Header for the log file



while True:
    ret, frame = cap.read()
    frm_rcv = time.time() * 1000 # millisecond
    if not ret:
        print(f"Failed to grab frame {frame_counter + 1}")
        break
    
    
    # Calculate the size of the current frame in bytes
    frame_size_bytes = frame.nbytes  # Get the size of the frame in bytes
    total_buffer_bytes += frame_size_bytes  # Accumulate the total buffer size
    buffer_frame_count += 1  # Increment the number of frames in the buffer



    # Display the frame
    cv2.imshow("CG Player Client (LERIS)", frame)

    # Save the current frame to a file ./rcv/frame{frame_counter:04d}_{frm_rcv}.png
    frame_filename = f"./rcv_Kombat/{frame_counter:04d}_{frm_rcv}.png"  # Save as PNG with zero-padded frame number
    cv2.imwrite(frame_filename, frame)
    print(f"Saved {frame_filename}")

    #frame_filename = f"./rcv_Kombat/{frame_counter:04d}_{frm_rcv}.png"  # Save as PNG with zero-padded frame number

    frame_counter += 1  # Increment frame counter to track which frame we are on
    with open("kombat_frame_received.txt", "a") as f: f.write(f"{frame_counter},{frm_rcv}\n")

    print(f"Processing frame {frame_counter}")  # Debug print



    # Log ID, number of frames in the buffer, and occupied buffer size in bytes to the log file
    buffer_log_file.write(f"{frame_counter},{buffer_frame_count},{total_buffer_bytes} bytes\n")
    buffer_log_file.flush()

    print(f"Processing frame {frame_counter}, Frames in Buffer: {buffer_frame_count}, "
          f"Occupied Buffer: {total_buffer_bytes} bytes")  # Debug print


    # Check if there's a matching command for this frame
    matching_command = autocommands_df[autocommands_df['ID'] == frame_counter]
    if not matching_command.empty:
        print(f"Match found for Frame {frame_counter}")  # Debug print

        # Iterate through each row of matching_command and send each encrypted command
        matching_command.apply(lambda row: send_command(frame_counter, row['encrypted_cmd']), axis=1)
    
        # Log each command sent with a timestamp in milliseconds and the encrypted command
        # matching_command.apply(lambda row: open("received.txt", "a").write(f"{int(time.time() * 1000)},{row['encrypted_cmd']}\n"),axis=1)
    else:
        print(f"Frame With No action {frame_counter}")  # Debug print

# Press 'q' to exit the video display window
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up
cap.release()
cv2.destroyAllWindows()
sock.close()
buffer_log_file.close()