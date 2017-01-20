# sms-analysis
Python/IPython code to analyze one's text messages.  Intended to work out of the box.
<br><br>
Author: Michael Dezube \<michael dezube at gmail dot com\>

For further discussions:
[![Join the chat at https://gitter.im/mdezube/sms-analysis](https://badges.gitter.im/mdezube/sms-analysis.svg)](https://gitter.im/mdezube/sms-analysis?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

# Overview of code
This code will:

1. Find your latest iPhone sync (currently only supports doing this automatically on Macs), for PCs edit
`table_connector.py` to find the file
2. Load up the messages database and address book database locally
3. Merge the databases together into `fully_merged_messages_df` which you can freely play with
4. Visualize a word tree of your text messages with a specific contact, see [word tree screenshot](#example-word-tree)
5. Show you who you text the most
6. Create an interactive streamgraph to visualize how your texting with people has trended over time, see [steamgraph screenshot](#example-steamgraph)
7. Create a word cloud of the words you use, and those used by your contacts, see [word cloud screenshot](#example-word-cloud)
8. Use TFIDF to understand what words identify your contacts' verbiage
9. Use TFIDF to understand what words identify the difference between contacts' verbiage.  For example: how do high school friends talk differently from college friends, see [tfidf contact comparison](#example-tfidf-contact-comparison)
10. Use TFIDF to show you what topics were popular in texts you sent, or texts sent to you, and how this progressed over the years

Note: none of your data is modified nor sent anywhere during execution

# Dependencies easy install
If you don't have pip, see https://pip.pypa.io/en/stable/installing/

Another option on Mac OS X is to use `sudo easy_install pip`

Then run `pip install -r requirements.txt` and `pip install "matplotlib>=1.4"`

If the second comamnd fails, then you'll have to follow these [detailed Matplotlib install instructions](https://github.com/rueckstiess/mtools/wiki/matplotlib-Installation-Guide-for-Mac-OS-X)

## Dependencies with details

1. [Pandas](http://pandas.pydata.org)
2. [IPython](http://ipython.org/)
3. [Matplotlib](https://github.com/rueckstiess/mtools/wiki/matplotlib-Installation-Guide-for-Mac-OS-X)
    * The majority of the code will work without this, but certain graphs will fail
4. An iPhone, having synced with this computer
5. If running on a Mac, code will work out of the box. If running on a PC, change the variable `BASE_DIR` in
`table_connector.py` to the directory of your backups
    * This [post](http://www.iphonefaq.org/comment/70608#comment-70608) seems to specify the location of backups on Windows.
6. Internet connection to load the google visualization API, it's a very small file though

# Quick Start - Jupyter Notebook 
1. Start the IPython notebook like so: `jupyter notebook sms_analysis.ipynb`
2. Under the menu choose Cell --> Run All
3. Edit the `CONTACT_NAME` and `ROOT_WORD` in the last cell to alter the visualization and then re-run
that cell, under menu choose: Cell --> Run Cell

# Quick Start - Command Line
* Run `python table_connector.py` to see a sample of the messages and address book data
* Run `python table_connector.py --full` to see a sample of the messages and address book data with all of their columns
* Run `python table_connector.py <output directory>` to output the messages and address book data into CSV files
* Run `python table_connector.py --full <output directory>` to output the messages and address book data into CSV files with all of their columns
* SEE THE ARGS DOCUMENTATION: `python table_connector.py --help` to see the arguments and their options

# Screenshots from running the code

## Example word tree

<div align="center">
    <img height="400" src="https://raw.githubusercontent.com/mdezube/sms-analysis/master/example%20word%20tree.png"></img>
</div>

## Example steamgraph
<div align="center">
    <img height="400" src="https://raw.githubusercontent.com/mdezube/sms-analysis/master/steamgraph_screenshot.png"></img>
</div>

## Example word cloud
<div align="center">
    <img height="400" src="https://raw.githubusercontent.com/mdezube/sms-analysis/master/wordcloud_screenshot.png"></img>
</div>

## Example TFIDF contact comparison
<div align="center">
    <img height="400" src="https://raw.githubusercontent.com/mdezube/sms-analysis/master/tfidf_diff_screenshot.png"></img>
</div>
