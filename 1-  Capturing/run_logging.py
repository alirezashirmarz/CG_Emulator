import subprocess
import time

# Path to your scripts
script1 = './Capture_Joystick.py'
script2 = './Capture_Screen.py'

try:
    print("Waiting 10 seconds to start logging .... ")
    time.sleep(10)
    # Start the Python scripts
    process1 = subprocess.Popen(['python3', script1])
    process2 = subprocess.Popen(['python3', script2])

    # Start tshark command to capture network traffic
    process3 = subprocess.Popen(['sudo', 'tshark', '-i', 'wlp0s20f3', '-a', 'duration:300' ,'-w', 'out_Forza_W.pcap'])


    # Wait for the Python scripts to finish
    process1.wait()
    process2.wait()

    # Optionally wait for tshark to finish (if needed)
    process3.wait()

    print("All processes finished successfully.")

except subprocess.CalledProcessError as e:
    print(f"An error occurred: {e}")
except KeyboardInterrupt:
    print("Processes interrupted by user.")
finally:
    # Make sure to terminate tshark and other processes if necessary
    process1.terminate()
    process2.terminate()
    process3.terminate()
    print("All processes terminated.")
