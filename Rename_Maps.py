import os
import pandas as pd

file_list = os.listdir("2.5 Map Files")
reference = pd.read_csv("License_Keys.csv")

for file in file_list:
    call_sign = reference.loc[reference['License Key'] == int(file.split("-")[2]), "Call Sign"].iloc[0]
    os.rename("2.5 Map Files\\" + file, "2.5 Map Files\\" + call_sign + ".kml")

# do after renaming + adding radio service to License_Keys.csv
for file in file_list:
    if "." in file:
        radio_service = reference.loc[reference['Call Sign'] == file.split(".")[0], "Radio Service"].iloc[0]
        os.rename("2.5 Map Files\\" + file, "2.5 Map Files\\" + radio_service + "\\" + file)
