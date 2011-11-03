# What
A mostly-working iCal exporter for Technion student schedules.
The script scrapes the Technion's website and (poorly) converts the html to an
iCal file.

# Why?
Because the alternative to scraping is copying your schedule by hand.

# Usage
Not yet. But if you really want, add your username/password to the bottom of the file
and run it. The output is test.ics in your home directory. Classes are still
non-recurring. Look for them at the end of October 2011.

# TODO
* Recurring classes 
* Properly parse table cells
* Fix BiDi corner cases
* Use lxml instead of BeautifulSoup
* Command line parameters

