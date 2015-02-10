#!/usr/bin/env python
# Created by Joe Ellis
# Columbia University DVMM Lab

# Standard Libs
import os
import json

# Extended Libs
import argparse
from bs4 import BeautifulSoup
import requests

class IMDBUtils():
    def __init__(self, imdb_id=False):
        """ This function contains the initlialization for the 
        """
        self.imdb_query_url = "http://www.imdb.com/search/title"
        self.imdb_base = "http://www.imdb.com/"
        self.genres = ["action", "animation", "comedy", "documentary",
          "family", "film-noir", 'horror', "musical",
          "romance", "sport", "war", "adventure",
          "biography", "crime", "drama", "fantasy",
          "history", "music", "mystery", "sci-fi",
          "thriller", "western"]
        self.query_base = "http://www.imsdb.com/scripts/"
        if imdb_id == False:
            self.movie_base = False
        else:
            self.movie_base = self.imdb_base + "title/" + imdb_id + "/"


    def grab_movie_script(self, title):
        """ grab the movie script for a given title of a movie
        The title must be exact, if the html doesn't exist this doesn't work"""
        query_url = query_base + title.replace(" ", "-") + ".html"
        resp = requests.get(query_url)
        if resp.ok:
            parsed_script = self.parse_html()
        else:
            print "ERROR URL DOES NOT EXIST:", query_url
            print "PROGRAM BREAKING"
            quit()
        return parsed_script 

    def parse_html(self, text):
        """ This function uses beautiful soup to parse the html file
        here and then make these two things work well together"""
        
        # Create the soup object
        soup = BeautifulSoup(text)

        # Create the soup object 
        pre_obj = soup.find("pre")
        script_text = pre_obj.find("pre")

        if script_text is not None:
            script_text = script_text.text
        else:
            script_text = pre_obj.text

        # Now we need to parse the pre_obj line by line
        # We will define each line with either description, words, name, etc.
        # Split the lines using the "\n" character
        lines = script_text.split("\n")
        line_spaces = {}
        total = 0
        for line in lines:
            length = count_spaces_beg(line)
            if not (length in line_spaces.keys()):
                line_spaces[length] = 1
                total += 1
            else:
                line_spaces[length] += 1
                total += 1

        # Now we have the lines that we want let's get what each one is
        good_vals = []
        for key, val in line_spaces.iteritems():
            if (key is not 0) and (val > 0.1 * total):
                good_vals.append(key)

        # Sort the values
        good_vals.sort()
        desc_start = good_vals[0]
        speech_start = good_vals[1]
        name_start = good_vals[2]

        # Now that we have the start of each val, let's create a 
        # setup of the script
        script_parse = []
        for line in lines:
            length = count_spaces_beg(line)
            if length in good_vals:

                # Now check through each section and then add them
                if length is desc_start:
                    if not line[length:].isupper():
                        script_parse.append(('desc', line[length:]))
                elif length is speech_start:
                    script_parse.append(('speech', line[length:]))
                elif length is name_start:
                    script_parse.append(('name', line[length:]))

        # Debug print out our script
        return script_parse

    def grab_genre_movies(self, genre1,limit=1000,genre2=None):
        """ This function returns the ids, and movie titles
        of the movies that are most related to this genre"""
        
        # Create the query
        #imdb_query_url = "http://www.imdb.com/search/title"
        
        if not genre2:
            q_parameters = {"count": 100,
                            "genres": genre1,
                            "num_votes": "100,",
                            "title_type": "feature"}
        else:
            q_parameters = {"count": 100,
                            "genres": ",".join((genre1, genre2)),
                            "num_votes": "100,",
                            "title_type": "feature"}

        # Get the queries
        title_and_links = []
        for i in range(1, limit, 100):

            # Go through these pages then parse the html
            q_parameters['start'] = i
            r = requests.get(self.imdb_query_url, params=q_parameters)

            if not r.ok:
                print "Something wrong with the request"
                print r.url
            else:
                soup = BeautifulSoup(r.text)
                rows = soup.find_all("tr")

                if len(rows) == 3:
                    break  # This breaks out of the request cycle

                for row in rows[1:-1]:
                    tds = row.find_all("td")
                    if len(tds) > 1:
                        title_td = tds[2]
                        link = title_td.find("a")
                        title_and_links.append((link.get("href"), link.string))

        return title_and_links

    def grab_IMDB_keywords(self, movie_id=False):
        """ This function grabs the keywords and how relvant they are for a
        a given movie url"""
        
        # Check to see if we initialized the class with a movie title
        if movie_id != False:
            r_url = self.imdb_base + "/title/" + movie_id + "/keywords"
        elif self.movie_base != False:
            r_url = self.movie_base + "keywords"
        else:
            print "No Supplied URL"
            print "Program Breaking"
            quit()
        r = requests.get(r_url)

        # Check to make sure that the requests went through
        if not r.ok:
            print "Couldn't grab keywords, breaking"
            return 0
        else:
            # Beautiful Soup
            soup = BeautifulSoup(r.text)
            sodatext_divs = soup.find_all("div", {"class" : "sodatext"})
            interesting_divs = soup.find_all("div", {"class" : "interesting-count-text"})
            text_words = []
            for sd,ind in zip(sodatext_divs,interesting_divs):
                # Grab the keyword
                a_string = sd.find("a").string
                keyword = a_string.encode('ascii', 'ignore')

                # Grab the relevance of each
                a_string = ind.find("a").string.strip()
                relevance_sentence = a_string.encode('ascii', 'ignore')

                # These are the text keywords
                text_words.append((keyword, relevance_sentence))

        return text_words

    def grab_actors(self, movie_id=False):
        """ This function grabs the actors for a given movie """
        # Check to see if we initialized the class with a movie title
        if movie_id != False:
            r_url = self.imdb_base + "/title/" + movie_id + "/fullcredits"
        elif self.movie_base != False:
            r_url = self.movie_base + "fullcredits"
        else:
            print "No Supplied URL"
            print "Program Breaking"
            quit()
        r = requests.get(r_url)

        if not r.ok:
            print "Couldn't grab keywords, breaking"
            return 0
        else:
            soup = BeautifulSoup(r.text)
            div_fullcredit = soup.find("div", {"id": "fullcredits_content"})
            table = div_fullcredit.find("table", {"class": "cast_list"})
            td_text_divs = table.find_all("td", {"itemprop": "actor"})
            actors_and_links = []
            for td in td_text_divs:
                person_link = td.find("a")['href']
                person_name = td.find("span").string
                actors_and_links.append((person_name, person_link))

        return actors_and_links

    def grab_actor_info(self, actor_id):
        """ Not implemented """
        pass


if __name__ == "__main__":
    """ Test the functionality of the IMDBUtilities class """
    # Test the title initialization in the class
    imdb_id = "tt2322441"
    imdb = IMDBUtils(imdb_id)
    actors_and_links = imdb.grab_actors()
    print "TESTING: INITALIZED CLASS WITH TITLE"
    if len(actors_and_links) > 0:
        print "Actors Found: SUCCESS"
    else:
        print "Actors Found: FAIL"
    keywords = imdb.grab_IMDB_keywords()
    if len(keywords) > 0:
        print "Keywords Found: SUCCESS"
    else:
        print "Keywords Found: FAIL"

    print "++++++++++++++++++++++"

    imdb = IMDBUtils()
    actors_and_links = imdb.grab_actors(imdb_id)
    print "TESTING: INITALIZED CLASS WITHOUT TITLE"
    if len(actors_and_links) > 0:
        print "Actors Found: SUCCESS"
    else:
        print "Actors Found: FAIL"
    keywords = imdb.grab_IMDB_keywords(imdb_id)
    if len(keywords) > 0:
        print "Keywords Found: SUCCESS"
    else:
        print "Keywords Found: FAIL"

    print "+++++++++++++++++++++++"

    print "TESTING: FINDING MOVIE WITH GENRE"
    movies = imdb.grab_genre_movies(imdb.genres[0], 100)
    if len(movies) > 0:
        print "Movies Found: SUCCESS"
    else:
        print "Movies Found: FAIL"


    



