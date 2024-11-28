import cv2
import os
import socket
import time
import pandas as pd
from datetime import datetime
from pyzbar import pyzbar
from collections import deque

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

# UDP Socket setup
cg_server_ip = "200.18.102.25"
cg_server_port = 5508
player_ip = "200.18.102.7"
player_port = 5000
my_command_port = 5555

# set the game type to emulate
game = {'Forza': '/home/alireza/CG_Simulation/autocommands_forza.txt', 
        'Kombat': '/home/alireza/CG_Simulation/autocommands_kombat.txt' , 
        'Fortnite':'/home/alireza/CG_Simulation/autocommands_fortnite.txt'}

game_name = 'Forza'
auto_commands_file_addr = game[game_name]
#'/home/alireza/CG_Simulation/autocommands_forza.txt' #"/home/alireza/CG_Simulation/Phase4_Player_Command/autocommands_forza.txt"



rate_log = "/home/alireza/CG_Simulation/Phase4_Player_Command/mylog/ratelog.txt"
time_log = "/home/alireza/CG_Simulation/Phase4_Player_Command/mylog/timelog.txt"
my_forza_frame_addr = "./rcv_forza"

# Load autocommand.txt
autocommands_df = load_autocommands(auto_commands_file_addr)
#print("Loaded autocommands:")
#print(autocommands_df)
print(f"palyer is ready to receive {player_port} & command sent on {my_command_port}")

# Function to send command to server
def send_command(frame_id, encrypted_cmd, interface_name="enp0s31f6", type='command', number = 0, fps = 0, cps = 0): # #"enp0s31f6" wlp0s20f3
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, interface_name.encode()) #interface_name.encode())
    sock.bind((player_ip, player_port))
    timestamp = time.perf_counter() #time.time() * 1000
    message = f"{timestamp},{encrypted_cmd},{frame_id},{type},{number},{fps},{cps}"
    # port setup
    #my_test_port = 5555
    sock.sendto(message.encode(),(cg_server_ip, my_command_port))
    #print(f"Sent command for Frame ID {frame_id}: {message}") //commented
    sock.close()

# Function to read the QR code from the frame
def read_qr_code_from_frame(frame):
    """Reads the QR code from a given frame and extracts its data."""
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred_frame = cv2.GaussianBlur(gray_frame, (5, 5), 0)
    qr_codes = pyzbar.decode(blurred_frame)

    for qr in qr_codes:
        qr_data = qr.data.decode('utf-8')
        print(f"Detected QR Code Data: {qr_data}")
        data_parts = qr_data.split(',')
        frame_id = None
        for part in data_parts:
            if "ID:" in part:
                frame_id = part.split(':')[1].strip()
                break
        if frame_id:
            return int(frame_id), qr_data

    return None, None

# GStreamer pipeline to receive video stream from port 5000
gstreamer_pipeline = (
     f"udpsrc port={player_port} ! application/x-rtp, payload=96 ! "
    "queue max-size-time=1000000000 ! rtph264depay ! avdec_h264 ! videoconvert ! appsink"

)
'''(
    f"udpsrc port={player_port} ! application/x-rtp, payload=96 ! "
    "rtph264depay ! avdec_h264 ! videoconvert ! appsink"
)'''

# Open the video stream using OpenCV and GStreamer
cap = cv2.VideoCapture(gstreamer_pipeline, cv2.CAP_GSTREAMER)

if not cap.isOpened():
    print("Error: Could not open video stream")
    exit()

# frame_buffer = deque(maxlen=30)  # Buffer to store frames
frame_counter = 1
#timeout_duration = 0.0001
previous_command = None
next_frame = 1
cmd_previoustime =frm_previoustime = time.perf_counter()
currrent_cps = 0
current_fps = 0

while True:
    start_time = time.perf_counter() # time.time()

    # Try to receive the next frame
    ret, frame = cap.read()
    frm_rcv = time.perf_counter() # time.time() * 1000
    #test_timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
    #print("Debug:***************",test_timestamp)

    # Read QR code from the buffered frame
    frame_id, qr_data = read_qr_code_from_frame(frame)
    current_fps = 1/(frm_rcv-frm_previoustime)
    frm_previoustime = frm_rcv
    #print(f"{frame_id}-fps:{current_fps}")
    

    if frame_id and frame_id == next_frame:
        print(f"Detected Frame ID: {frame_id}")
        frame_counter = frame_id
        next_frame = int(frame_id) + 1
        if (frame_counter%30)==0:
            send_command(frame_id,current_fps,"enp0s31f6",type='Ack', fps = current_fps, cps = currrent_cps )
        else:
            pass
        
    else:
        print("No QR code detected in this frame.")
        send_command(0,"Downgrade",type='Nack',fps = current_fps, cps = currrent_cps )   # Send NacK
        send_command(frame_counter, previous_command,type='command',fps = current_fps, cps = currrent_cps ) # Send the Previous Command
        #continue
        frame_counter+=1
        pass 
    
    
    # Save the current frame to a file
    frame_filename = f"{my_forza_frame_addr}/{frame_counter:04d}_{frm_rcv}.png"
    cv2.imwrite(frame_filename, frame)
    #print(f"Saved {frame_filename}") /// Commented

    # Display the frame
    cv2.imshow("CG Player Client (LERIS)", frame)
    matching_command = [] # new edit 
    # Check if there's a matching command for this frame
    matching_command = autocommands_df[autocommands_df['ID'] == frame_counter]
    cmd_number = matching_command.shape[0]
    encrypted_cmds = matching_command['encrypted_cmd'].values
    #print(f"####Debug \n {autocommands_df['ID'][1]}####")
    print('********************************')
    if not matching_command.empty:
        #print(f"Match found for Frame {frame_counter}")
        
        send_command(frame_counter, encrypted_cmds,type ='command', number = cmd_number, fps = current_fps, cps= currrent_cps)
        cmd_sent = time.perf_counter() # time.time() * 1000
        currrent_cps = 1/(cmd_sent - cmd_previoustime)
        cmd_previoustime = cmd_sent
        #matching_command.apply(lambda row: send_command(frame_counter, encrypted_cmds,number = cmd_number), axis=1)  #row['encrypted_cmd'],number = cmd_number), axis=1)
        previous_command = encrypted_cmds.copy() # matching_command.iloc[0]['encrypted_cmd']
        
            # Log frame received time
        with open(rate_log, "a") as f: # fID - fps - cps
            f.write(f"{frame_id},{current_fps},{currrent_cps}\n")


        with open(time_log, "a") as f: # FID - F timestamp - CMD Timestamp
            f.write(f"{frame_id},{frm_rcv},{cmd_sent}\n")

    #frame_counter += 1
    

    if frame_counter == 1000:
        break

    # Press 'q' to exit the video display window
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
