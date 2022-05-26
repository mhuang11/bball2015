# Python Queries For Analyzing The 2015 MLB Games
In this project, game statistics and athletes associated with the MLB 2015 season were gathered and imported into python for data analysis.

Functions were created in a .py file that could read queries and retrieve necessary information.

Example questions are to test if queries worked successfully. 

## The Data
The data was web scraped from [baseball-reference.com](https://www.baseball-reference.com/)

Each MLB game from the 2015 season was collected. There are over 1,400 games. The data is provided in .zip folders "bb2015_1", "bb2015_2", "bb2015_3", and "bb2015_4".

Extract all of the folders and put the contents into one folder called "bb2015". 

If you would prefer to web scrape the data yourself, the functions needed are in baseball.py

## Queries
Open `bball_questions.ipynb`. 

The folder containing all of the data, `bb2015`, should be in the current working directory along with `baseball.py`. 

Import `baseball.py` and use functions GetOutsBasesOR(), ToInningsOR(), and GetCountsOR(). These functions read the files and returns them in a dictionary so that they can work smoothly with python.

## Example Questions

Multiple functions from `baseball.py` were used to make a new function and help answer the questions.
