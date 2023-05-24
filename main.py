
'''
author: Roberto Scalas 
date:   2023-05-17 12:32:10.720930

streamlit run main.py

---
- need to define when a shift is a double shift, since there's a single format for both 
    -> if shift is greater than 10 hours ? 
    -> In the double shifts there's a 30 minutes break?
    -> We need to divide the shifts in two parts, if they are double shifts, keeping the break between 4 and 5 pm
    -> In the double shifts there are multiple "roles" ?
- the division is not very clear anymore, now we have "Group", "Type", "workdepartment". 
    ex: "Group": "F&B Team Leaders"
        "Type": "Till"
        "workdepartment": "Bar"
- 
'''

import streamlit as st
import pandas as pd


class BriefSheetHelper:
    def __init__(self):
        self.path = None
        self.df = None
        self._get_data()
        self.run()

    def _get_data(self):
        self.path = st.sidebar.file_uploader("Import the csv file from Rota Ready", type=["csv"])
        if self.path is not None:
            self.df = pd.read_csv(self.path)
        else:
            st.info("Please upload a file of type: " + ", ".join(["csv"]))
            st.stop()

    def process_data(self):
        # keep only hour from the column "start"
        self.df["start"] = pd.to_datetime(self.df["start"]).dt.time
        # keep only hour from the column "end"
        self.df["end"] = pd.to_datetime(self.df["end"]).dt.time
        # create a column with start hour and end hour
        self.df["start_hour"] = self.df["start"].apply(lambda x: x.hour)
        self.df["end_hour"] = self.df["end"].apply(lambda x: x.hour)
        # if end hour is less than start hour, add 24 to end hour
        self.df["end_hour"] = self.df.apply(
            lambda x: x["end_hour"] + 24 if x["end_hour"] < x["start_hour"] else x["end_hour"], axis=1)
        # create a column with the shift duration
        self.df["shift_duration"] = self.df.apply(
            lambda x: x["end_hour"] - x["start_hour"], axis=1)
        
        # create a column with the shift type if the shift is greater than 10 hours
        self.df["shift_type"] = self.df.apply(
            lambda x: "double" if x["shift_duration"] > 10 else "single", axis=1)
        
        # am or pm shift
        def get_shift(x, am_limit = 15):
            if x["start_hour"] < am_limit:
                return "am"
            elif x["start_hour"] >= am_limit:
                return "pm"
            
        self.df["shift_period"] = self.df.apply(get_shift, axis=1)

        
        # create now columns start1 and end1 for am shift and start2 and end2 for pm shift
        def get_start1(x):
            return str(x["start"])
        
        def get_end1(x):
            if x["shift_type"] == "single":
                return str(x["end"])
            elif x["shift_type"] == "double":
                return "16:00:00"
            
        def get_start2(x):
            if x["shift_type"] == "single":
                return None
            elif x["shift_type"] == "double":
                return "17:00:00"
            
        def get_end2(x):
            if x["shift_type"] == "single":
                return None
            elif x["shift_type"] == "double":
                return str(x["end"])

        self.df["start1"] = self.df.apply(get_start1, axis=1)
        self.df["end1"] = self.df.apply(get_end1, axis=1)
        self.df["start2"] = self.df.apply(get_start2, axis=1)
        self.df["end2"] = self.df.apply(get_end2, axis=1)

        # if shift is pm then start2 = start1 and end2 = end1 and start1 = None and end1 = None

        self.df["start2"] = self.df.apply(lambda x: x["start1"] if x["shift_period"] == "pm" else x["start2"], axis=1)
        self.df["end2"] = self.df.apply(lambda x: x["end1"] if x["shift_period"] == "pm" else x["end2"], axis=1)

        # if shift is pm then  start1 = None and end1 = None
        self.df["start1"] = self.df.apply(lambda x: None if x["shift_period"] == "pm" else x["start1"], axis=1)
        self.df["end1"] = self.df.apply(lambda x: None if x["shift_period"] == "pm" else x["end1"], axis=1)


    
    def run(self):
        st.image("assets/logo.png", width=200)
        self.process_data()
        # rename the column "group" to "Group"
        self.df.rename(columns={"group": "Division"}, inplace=True)
        # rename user to name
        self.df.rename(columns={"user": "Name"}, inplace=True)
        # create a surname columns splitting the name at space when there are two words
        self.df["Surname"] = self.df["Name"].apply(lambda x: x.split(" ")[1] if len(x.split(" ")) > 1 else None) 
        # create a empty section column
        self.df["Section"] = None
        # sort by hour start
        self.df.sort_values(by=["start_hour"], inplace=True)
        columns = ['Division', 'Name', 'Surname', 'start1', 'end1','Section', 'start2', 'end2']
        self.df = self.df[columns]

        # take unique values of the column "Group"
        groups = self.df["Division"].unique()
        for g in groups:
            with st.expander(f"{g} : {len(self.df[self.df['Division'] == g])}"):
                group = self.df[self.df["Division"] == g]
                # reset index
                group.reset_index(drop=True, inplace=True)
                st.write(group)


if __name__ == "__main__":
    briefsheet = BriefSheetHelper()
