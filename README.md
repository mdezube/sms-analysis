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

Note: none of your data is modified nor sent anywhere during execution

# Dependencies easy install
Run `pip install -r requirements.txt`

If you don't have pip, see https://pip.pypa.io/en/stable/installing/

## Dependencies with details

1. [Pandas](http://pandas.pydata.org)
2. [IPython](http://ipython.org/)
3. An iPhone, having synced with this computer
4. If running on a Mac, code will work out of the box. If running on a PC, change the variable `BASE_DIR` in
`table_connector.py` to the directory of your backups
    * This [post](http://www.iphonefaq.org/comment/70608#comment-70608) seems to specify the location of backups on Windows.
5. Internet connection to load the google visualization API, it's a very small file though

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
