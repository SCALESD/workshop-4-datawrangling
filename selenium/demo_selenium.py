"""Demo of selenium, with an example of scraping Press Releases from EurekAlert.

Code written by Will Fox (http://github.com/wdfox)

This demo code adapter from project:
https://github.com/wdfox/ConfidenceScanner/
"""

import os
import time
import json
import random
import datetime

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# LISC currently available from:
#   https://github.com/tomdonoghue/lisc
from lisc.core.requester import Requester

###################################################################################################
###################################################################################################

TERM = "brain"

START_DATE = datetime.date(year=2018, month=9, day=16)
END_DATE = datetime.date(year=2018, month=9, day=29)

PATH = os.path.join(os.getcwd(), 'data')

###################################################################################################
###################################################################################################

def main():

    print('\nRUNNING WEB SCRAPE ON EUREKALERT')
    print('\tSEARCH TERM: {}'.format(TERM))
    print('\tSTART  DATE: {}'.format(START_DATE))
    print('\tEND    DATE: {}'.format(END_DATE))
    print('\n')

    collect_prs(TERM, START_DATE, END_DATE)

###################################################################################################

def collect_prs(search_term, start_date, end_date, pr_count=100):
    """Collects a given number of press releases related to a given term

    Parameters
    ----------
    search_term : str
        Term to search for.
    start_date : datetime.date
        Start date for PRs to be collected.
    end_date : datetime.date
        End date for PRs to be collected.
    pr_count : int
        Number of press releases to be collected and saved
    """

    N_SCRAPED = 0

    driver = webdriver.Safari()

    # Initialize the base URL for EurekAlert press releases
    db_url = 'http://www.eurekalert.org/'

    # Initialize a date to begin the scrape from
    scrape_start_date = start_date

    # Get papers from a specific week of dates
    while scrape_start_date < end_date:

        # End date for each batch is one week past the start date
        scrape_end_date = scrape_start_date + datetime.timedelta(days=6)

        # Retrieve press release URLS
        pr_links = pr_crawl(search_term=search_term, start_date=scrape_start_date,
                            end_date=scrape_end_date, driver=driver, pr_count=pr_count)

        # Create a list of press release URLs to be saved
        pr_urls = [db_url+link for link in pr_links]

        print('\tStarting a new page of PRs.')

        # Extract the desired info from each press release and save to JSON
        for ind, url in enumerate(pr_urls):

            print('\t\tScraping individual PR.')

            # Scrape the individual PR page
            pr_dict = scrape_pr_data(url, PATH)

            # Build the path for the individual file to be saved at
            outfile = '{:04d}.json'.format(N_SCRAPED + ind)
            file_path = os.path.join(PATH, outfile)

            # Save information to the path generated, each entry on its own line
            with open(file_path, 'w') as outfile:
                json.dump(pr_dict, outfile)

            # Sleep for a variable time to ensure we don't get an IP blocked
            sleep_time = random.uniform(2.0, 3.0)
            time.sleep(sleep_time)

        N_SCRAPED += len(pr_links)

        # Increment the date to collect the following week's press releases
        scrape_start_date = scrape_start_date + datetime.timedelta(days=7)

        time.sleep(1)

    # End the browser instance
    driver.close()


def scrape_pr_data(url, path):
    """Retrieve the press release from Eurekalert and extract the info.

    Parameters
    ----------
    url : str
        Fetch URL for the desired press release
    path : str
        Path to the save location for scraped data
    """

    # Initialize Requester object for URL requests
    req = Requester()

    # Use Requester() to open the press release URL
    art_page = req.get_url(url)

    # Get press release into a more convenient format for info extraction
    page_soup = BeautifulSoup(art_page.content, 'lxml')

    # Initialize a press release object to store the scraped data and extract info
    #   For this demo - this is a minimized version of the data extraction
    #      Otherwise, there is a whole procedure to pull out all the data from this page
    pr_dict = {'data' : 1,
               'data2': 2}

    # Close the URL request
    req.close()

    return pr_dict


def pr_crawl(driver, pr_count, search_term, start_date, end_date):
    """Collects a given number of press releases related to a given term.

    Parameters
    ----------
    driver : selenium WebDriver
        WebDriver.
    pr_count : int
        Number of press releases to be collected and saved
    search_term : str
        Papers returned will be associated with this term
    start_date : datetime object
        Beginning date for relevant publications
    end_date : datetime object
        End date for relevant publications
    """

    # Parse out individual components from given start & end dates for search
    start_day = str(start_date.day)
    start_month = str(start_date.month)
    start_year = str(start_date.year)
    end_day = str(end_date.day)
    end_month = str(end_date.month)
    end_year = str(end_date.year)

    # Creat the search URL based on the term and dates desired
    crawl_base = 'https://srch.eurekalert.org/e3/query.html?qs=EurekAlert&pw=100.101%25&op0=%2B&fl0=&ty0=w&tx0='
    crawl_middle = '&op1=%2B&fl1=institution%3A&ty1=p&tx1=&op2=%2B&fl2=journal%3A&ty2=p&tx2=&op3=%2B&fl3=meeting%3A&ty3=p&tx3=&op4=%2B&fl4=region%3A&ty4=p&tx4=&op5=%2B&fl5=type%3A&ty5=p&tx5=research&inthe=604800&dt=ba'

    crawl_url = crawl_base + search_term + crawl_middle + '&amo=' + start_month \
                + '&ady=' + start_day + '&ayr=' + start_year + '&bmo=' + end_month \
                + '&bdy=' + end_day + '&byr=' + end_year + '&op6=&fl6=keywords%3A&ty6=p&rf=1'

    # Go to first page containing press releases
    driver.get(crawl_url)

    # Loop through pages containing article links
    pages_continue = True
    page_num = 1

    # Initialize a list to store the pr links as we loop
    pr_links = []
    while pages_continue:

        # Initialize a list to store links from this page of the crawl only
        page_links = []

        # Get the source code for the page
        page = driver.page_source
        page_soup = BeautifulSoup(page, 'lxml')
        results = page_soup.select(".results")
        try:
            links = results[0].find_all("a")
        except:
            links = []

        # Follow / process links
        i = 0
        for link in links[1:]:

            link = link["href"]
            if link[0:2] == 'cs' and len(pr_links) < pr_count:
                try:
                    link_start = link.find('pub_releases')
                    link_end = link.find('php')
                    pr_links.append(link[link_start : link_end + 3])
                except:
                    page_links.append('')

            elif len(pr_links) == pr_count:
                return pr_links

        # Increment the page number to continue search
        page_num += 1

        # Page numbers are a bit gimmicky (single digit different than double), but this works
        if page_num < 10:
            page_str = ' ' + str(page_num)
        else:
            page_str = str(page_num)

        try:
            # Find button for next page
            next_page = driver.find_element(By.LINK_TEXT, page_str)
            next_page.click()

            # No accidental DDoS attacks
            sleep_time = random.uniform(2.0, 3.0)
            time.sleep(sleep_time)

        except:
            pages_continue = False

    return pr_links

###################################################################################################

if __name__ == "__main__":
    main()
