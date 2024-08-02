import subprocess
import time
import threading
import tkinter as tk
from tkinter import messagebox  # Import the messagebox explicitly
import json

output_file = 'network_info_python.txt'
data_point = 1
stop_thread = False
previous_bssid = ""

# Function to get network information
def get_network_info():    
    try:        
        netsh_output = subprocess.check_output('netsh wlan show interfaces', shell=True)   
        return netsh_output.decode('utf-8') 
    except subprocess.CalledProcessError as e:        
        print(f"An error occurred while trying to fetch network information: {e}")        
        return ""

# Function to run speedtest-cli and get results
def get_speedtest_results():
    try:
        # Run the speedtest-cli command and capture its JSON output
        speedtest_output = subprocess.check_output('speedtest-cli --json', shell=True)
        return json.loads(speedtest_output)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running speedtest-cli: {e}")
        return {}

# Function to save network and speedtest information to a file
def save_data(data, file_name):
    try:
        with open(file_name, 'a') as file:
            file.write(data + "\n")
    except Exception as e:
        print(f"An error occurred while saving data to file: {e}")

# Function to run the network survey
def run_survey():
    global data_point, stop_thread, previous_bssid
    while not stop_thread:
        current_time = time.strftime("%H:%M:%S", time.localtime())
        network_info = get_network_info()
        speedtest_results = get_speedtest_results()
        # Process network information
        network_info_lines = network_info.split('\n')
        filtered_info = "\n".join([line for line in network_info_lines if any(keyword in line for keyword in
            ["Signal", "SSID", "BSSID", "State", "Radio type", "Authentication", "Channel"])])
        # Check for a new BSSID
        bssid_line = next((line for line in network_info_lines if "BSSID" in line), None)
        if bssid_line:
            current_bssid = bssid_line.split(":")[1].strip()
            if previous_bssid and current_bssid!= previous_bssid:
                # A new BSSID detected, indicate a handover has happened
                handover_message = "Handover has happened"
                #print(handover_message)
                
                window.after(0, messagebox.showinfo, "Data Collection", f"{handover_message}\nNetwork data has been collected and saved.")
                # If system should stop survey at handover
                #stop_thread = True
            previous_bssid = current_bssid
        # Compiling all data to save
        data_to_save = (
            f"[Data Point {data_point}] - Time: {current_time}\n"
            f"{filtered_info}\n"
            f"Download Speed: {speedtest_results.get('download', 0) / 1e6:.2f} Mbps\n"
            f"Upload Speed: {speedtest_results.get('upload', 0) / 1e6:.2f} Mbps\n"
            f"Latency: {speedtest_results.get('ping', 0)} ms\n\n"
        )
        save_data(data_to_save, output_file)
        # Notify the user of the data collection without handover
        window.after(0, messagebox.showinfo, "Data Collection", f"Data point {data_point} has been collected and saved.")
        tk.Label(window, text= f"Data point {data_point} has been collected and saved.").pack()

        # Ask if user wants to continue or stop
        response = messagebox.askyesno("Continue?", "Do you want to continue collecting data?")
        if not response:
            stop_thread = True
            break
        data_point += 1
        time.sleep(5)  # Wait for 5 seconds before the next survey

# Function to stop the survey from the GUI
def stop_survey():
    global stop_thread
    stop_thread = True
    print('User chose to stop...')
    window.quit()

# Creating the GUI window
window = tk.Tk()
window.title("Network Survey")
# Stop button in the GUI
stop_button = tk.Button(window, text="Stop Survey", command=stop_survey)
stop_button.pack()
# Start the survey in a separate thread
survey_thread = threading.Thread(target=run_survey)
survey_thread.start()
# Start the GUI loop
window.mainloop()
# Ensure the survey thread stops when the GUI is closed
stop_thread = True
survey_thread.join()
print(f'Network information has been saved to {output_file}.')