
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
---
Probelm 1:
- need to keep only name in name column
- Check format of time in start and end column
- Need to fix double shift logic
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

    def cleaning(self):
        '''
        Here we are going to clean the dataframe
        1. Rename the column "group" to "Division" and "user" to "Name"
        2. Create a Surname column, and modify the Name column keeping only the name
        3. Create a empty section column
        '''
        self.df.rename(columns={"group": "Division"}, inplace=True)
        self.df.rename(columns={"user": "Name"}, inplace=True)
        # create a surname columns splitting the name at space when there are two words
        self.df["Surname"] = self.df["Name"].apply(lambda x: x.split(" ")[1] if len(x.split(" ")) > 1 else None) 
        self.df["Name"] = self.df["Name"].apply(lambda x: x.split(" ")[0])
        # create a empty section columnx
        self.df["Section"] = None

    def transformation0(self):
        '''
        With this method we are going to create a new dataframe with the following columns:
        1. Make the column "start" and "end" datetime format keeping
        2. Create a column with the hour of the start and end
        3. Create a column with the shift duration
        4. Create a column with the shift type if the shift is greater than 10 hours
        '''
        # 1. Make the column "start" and "end" datetime format keeping
        self.df["start"] = pd.to_datetime(self.df["start"]).dt.time
        self.df["end"] = pd.to_datetime(self.df["end"]).dt.time
        # 2. Create a column with the hour of the start and end
        self.df["start_hour"] = self.df["start"].apply(lambda x: x.hour)
        self.df["end_hour"] = self.df["end"].apply(lambda x: x.hour)
        # if end hour is less than start hour, add 24 to end hour
        self.df["end_hour"] = self.df.apply(
            lambda x: x["end_hour"] + 24 if x["end_hour"] < x["start_hour"] else x["end_hour"], axis=1)
        # 3. Create a column with the shift duration
    
    def transformation1(self):
        '''
        Here we create shift_type column and shift_duration column
        The shift type is "single" if the shift is less than 10 hours, "double" otherwise

        '''
        self.df["shift_duration"] = self.df.apply(
            lambda x: x["end_hour"] - x["start_hour"], axis=1)
        # create a column with the shift type if the shift is greater than 10 hours
        self.df["shift_type"] = self.df.apply(
            lambda x: "double" if x["shift_duration"] > 12 else "single", axis=1)
        
                # am or pm shift
        def get_shift(x, am_limit = 14):
            minutes = x["start"].minute
            if x["start_hour"] < am_limit:
                return "am"
            elif x["start_hour"] == am_limit and minutes == 0:
                return "am"
            elif x["start_hour"] == am_limit and minutes > 0:
                return "pm"
            elif x["start_hour"] > am_limit:
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

        # sort by hour start
        self.df.sort_values(by=["start_hour", "shift_period"], inplace=True)
        columns = ['Division', 'Name', 'Surname', 'start1', 'end1','Section', 'start2', 'end2']
        self.df = self.df[columns]

    
    def run(self):
        st.image("assets/logo.png", width=200)
        self.cleaning()
        self.transformation0()
        self.transformation1()

        
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
