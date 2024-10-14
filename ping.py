import os,threading, time
# Function to ping the server and log the RTT
def ping_and_log_rtt(server_ip, log_file):
    while True:
        response = os.popen(f"ping -c 1 {server_ip}").read()
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

if __name__ == "__main__":
    #print('Waiting 1 second....')
    print('Started after 3 sec... ')
    time.sleep(3)
   
    ping_and_log_rtt('200.18.102.9','my_ping.txt')
