#!/usr/bin/env python
# encoding: utf8
#
# See README.md for docs

import datetime
import os
import requests
from icalendar import Calendar, Event, UTC
from bidi.algorithm import get_display
from BeautifulSoup import BeautifulSoup

gtds = []
gc = []

class Semester:
    Winter, Spring, Summer = ("01", "02", "03")

class Days:
    Sunday, Monday, Tuesday, Wednesday, Thursday = range(5)
    Named = ("Sunday", "Monday", "Tuesday", "Wednesday", "Thursday")

# Unused
def get_schedule_url (user_id, year=2011, semester=Semester.Winter):
    """
    Get the url for a user's schedule.
    You must known the user's id, which is unique and permanent
    """

    semester_id = "%d%s" % (year, semester)
    return "http://ug.technion.ac.il/rishum/weekplan.php?RGS=%s&SEM=%s" % (user_id, semester_id)

def get_schedule_html (tz, password):
    """Gets a user's schedule for the current semester as an html table"""
    # OP and NEXTOP seem to be the original page and the destination page
    login_url = "http://techmvs.technion.ac.il:100/cics/wmn/wmnnut02?OP=LI&NEXTOP=WK"

    # Post data - I'm not sure what Login.x and Login.y represent
    post_data = { "UID":tz, "PWD":password, "Login.x":"22","Login.y":"20"}

    # Request the page
    r = requests.post(login_url, post_data)

    # Convert Hebrew to utf8
    html = r.content.decode('iso-8859-8').encode('utf-16')
    #html = get_display(r.content, encoding='iso-8859-8')
    #f = open(os.path.expanduser("~/out.txt"), "w")
    #f.write(html + "\n\n\n" + html2)
    #f.close()
    #print html2

    # Get the right <table> and clean the html
    table = str(BeautifulSoup(html).findAll("table", width="100%")[1])
    table = table.replace("&nbsp;", " ")
    table = table.replace("<br />", "\n")
    table = table.replace("'", "")
    #table = table.replace("תרגול ", "תרגול ")
    #table = table.replace("הרצאה ", "הרצאה ")
    return table

def html_table_to_matrice (html):
    """
    Converts an html table to a 2d array of [DAYS] by [SLOTS]
    Each entry is ("Class information", # of slots)
    """
    # Initialize schedule to an empty 5X23 array of empty lists
    DAILY_SLOTS = 23	# Slots in schedule per day
    WEEKDAYS = 5
    schedule = [[None for i in xrange(DAILY_SLOTS)] for j in xrange(WEEKDAYS)]

    # Parse html table
    # items on the schedule can span multiple rows
    # when that happens, the next row will be missing tds in the html
    #
    # for example, len(row2) = 3 because item2 repeats
    # row1: | item1 | item2 | item3 | item4 |
    #        -------         ----------------
    # row2  | item5 | item2 | item6 | item7 |
    soup = BeautifulSoup(html)
    rows = soup.findAll("tr")[1:] # skip the header
    for i, tr in enumerate(rows):	
        cols = tr.findAll("td")
        j = 0 	# horizontal location in tr
        for td in cols[:-1]:
            attributes = dict(td.attrs) or {} # don't use attrMap (doesn't always exist)

            # how many rows does this item span
            rowspan = int(attributes.get("rowspan", 1))
            
            # find first empty entry in current row
            while schedule[j][i]:
                j += 1

            # add item to schedule if it's not empty
            if td.text != "":
                gtds.append(td)
                schedule[j][i] = (str(td), rowspan)
                rowspan -= 1
                while rowspan > 0:
                    schedule[j][i+rowspan] = ("Continuation", 0)
                    rowspan -= 1
            else:
                schedule[j][i] = ("", 0)

            j += 1

    return schedule

class Activity:
    """
    A tirgul or a lecture
    """

    def __init__ (self, text, start, length):
        """
        text: text from the html table
        starg: starg slot #
        length: length of activity in slots
        """
        self.text = text
        self.start = start
        self.length = length
                  
class Schedule (list):
    """
    An list of lists such that Schedule[0][2] is the 3rd class on
    Sunday is an instance of Activity
    """
    # TODO: Use an ordered dict for days

    def __init__ (self, matrice):
        """Initialize from a matrice of crappy html data"""
        for day in matrice:
            l = []
            self.insert(0, l) # we reverse the order of the days in the matrice
            # loop over all slots in current day
            for (i, slot) in enumerate(day):
                if slot is not None:
                    text, length = slot
                    if text not in ["Continuation", ""]:
                        gc.append(text)
                        soup = BeautifulSoup(text)
                        course_names = map(lambda x: x.text.replace("\n", "\n"), soup.findAll("a"))
                        course_names = "\nOVERLAPS\n".join(course_names)
                        course_info = soup.text
                        course_info = course_info.replace(course_names, "")
                        l.append(Activity(course_names + "\n\n" + course_info, i, length))

    def split_slot (self, slot):
        """Takes a slot and returns it's time as (hours, minutes, seconds)"""
        # calculate hours - each day starts at 8:30
        hours = 8 + slot // 2
        # calculate minutes - either 0 or 30
        if slot % 2:
            minutes = 0
        else:
            minutes = 30
        return (hours, minutes, 0)
    
    def export (self):
        """Export to ical format"""
        start_date = datetime.date(2011, 10, 30) # first sunday of semester
        
        cal = Calendar()
        cal.add("prodid", "-//NHY//Technion Students' Schedule 1.0//EN")
        cal.add("version", 2.0)

        for (day_num, activities) in enumerate(self):
            for (activity_num, activity) in enumerate(activities):
                # date and time
                date = start_date + datetime.timedelta(day_num)
                time = datetime.time(*self.split_slot(activity.start))
                dt_start = datetime.datetime.combine(date, time)
                
                time = datetime.time(*self.split_slot(activity.start + activity.length))
                dt_end = datetime.datetime.combine(date, time)

                # add event to calendar file
                event = Event()
                event.add("summary", activity.text)
                event.add("dtstart", dt_start)
                event.add("dtend", dt_end)
                event.add("dtstamp", datetime.datetime.today())
                event["uid"] = "NHY-TECHNION-STUDENTS-SCHEDULE-%d%d" % (day_num, activity_num)
                cal.add_component(event)

        f = open(os.path.expanduser("~/test.ics"), "w")
        f.write(get_display(cal.as_string())) 
        #f.write((cal.as_string())) 
        f.close()
        
    def dump (self):
        for (num, day) in enumerate(self):
            print "Daily Schedule for " + Days.Named[num]
            for activity in day:
                print activity.text, activity.start, activity.length

html = get_schedule_html("USERNAME", "PASSWORD")
matrice = html_table_to_matrice(html)
Activity(matric).export()

#sunday = matrice[Days.Sunday]
#print parse_schedule(html)
