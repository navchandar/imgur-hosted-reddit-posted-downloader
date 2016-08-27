#! python3
# -*- coding: utf-8 -*-
import re
import os
import glob
import praw
import requests
from bs4 import BeautifulSoup
from unidecode import unidecode

os.chdir('./RedditDowns/')

MIN_SCORE = 2500       # the default minimum score before it is downloaded
Subreddit = ['EarthPorn', 'itookapicture']


def remove_non_ascii(text):
    return unidecode(text)

for targetSubreddit in Subreddit:

    # Find the URL with this pattern
    imgurUrlPattern = re.compile(r'(i.imgur.com/(.*))(\?.*)?')

    # Definition to download the image
    def downloadImage(imageUrl, localFileName):
        localFileName = remove_non_ascii(localFileName)
        print('Downloading : %s' % (localFileName))
        response = requests.get(imageUrl)
        if response.status_code == 200:
            with open(localFileName, 'wb') as fo:
                for chunk in response.iter_content(50000):
                    fo.write(chunk)

    # Connect to reddit and download the subreddit front page
    # Note: Be sure to change the user-agent to something unique.
    r = praw.Reddit(user_agent='android:com.app.automated_Reddit_Imgur_Downloader')
    submissions = r.get_subreddit(targetSubreddit).get_top_from_week(limit=25)
    # Or use one of these functions:        .get_hot(limit=25)
    #                                       .get_top_from_year(limit=25)
    #                                       .get_top_from_month(limit=25)
    #                                       .get_top_from_week(limit=25)
    #                                       .get_top_from_day(limit=25)
    #                                       .get_top_from_hour(limit=25)
    #                                       .get_top_from_all(limit=25)

    # Process all the submissions from the extracted list
    # Check for all the cases where we will skip a submission:
    for submission in submissions:
        if "imgur.com/" not in submission.url:
            # skip non-imgur submissions
            continue
        if submission.score < MIN_SCORE:
            # skip submissions that haven't even reached the Minimum Score
            continue
        if len(glob.glob('*%s*' % (submission.id))) > 0:
            # We've already downloaded files for this reddit submission
            continue

        if '/' in submission.title:
            submission.title = (submission.title).replace('/', ' and ')
        if '\\' in submission.title:
            submission.title = (submission.title).replace('\\', ' and ')
        if "'" in submission.title:
            submission.title = (submission.title).replace("'", "")
        if '"' in submission.title:
            submission.title = (submission.title).replace('"', '')
        if '?' in submission.title:
            submission.title = (submission.title).replace('?', '')

        # This is an album submission.
        if ('imgur.com/a/') in submission.url:
            # print (submission.url)
            htmlSource = requests.get(submission.url).text
            soup = BeautifulSoup(htmlSource, 'html.parser')
            matches = soup.select('.post-image img')
            for match in matches:
                match = str(match)
                match = match.split('//')[1]
                imageUrl = match.split('"')[0]
                imgFilename = imageUrl.split('/')[1]
                if '?' in imgFilename:
                    # The regex doesn't catch a "?" at the end of the filename, so we
                    # remove it here.
                    imgFilename = imgFilename[:imgFilename.find('?')]
                localFileName = '%s_album_%s_%s_%s' % (targetSubreddit, submission.title, submission.id, imgFilename)
                downloadImage('http://' + imageUrl, localFileName)

        # The URL is a direct link to the image.
        elif ('i.imgur.com/') in submission.url:
            print(submission.url)
            # using regex here instead of BeautifulSoup because we are pasing a
            # url, not html
            mo = imgurUrlPattern.search(submission.url)
            imgurFilename = mo.group(2)
            if '?' in imgurFilename:
                # The regex doesn't catch a "?" at the end of the filename, so we
                # remove it here.
                imgurFilename = imgurFilename[:imgurFilename.find('?')]
            localFileName = '%s_%s_%s_%s' % (targetSubreddit, submission.title, submission.id, imgurFilename)
            downloadImage(submission.url, localFileName)

        elif ('.jpg') in submission.url:
            print(submission.url)
            localFileName = '%s_%s_%s.jpg' % (
                targetSubreddit, submission.title, submission.id)
            downloadImage(submission.url, localFileName)

        elif ('//imgur.com/') in submission.url and not ('.jpg') in submission.url:
            print(submission.url)
            # This is an Imgur page with a single image.
            # download the image's page
            htmlSource = requests.get(submission.url).text
            soup = BeautifulSoup(htmlSource, 'html.parser')
            imageUrl = soup.select('div.post-image a.zoom')[0]['href']
            # if no schema is supplied in the url, prepend 'https:' to it
            if imageUrl.startswith('//'):
                imageUrl = 'https:' + imageUrl
            imageId = imageUrl[imageUrl.rfind('/') + 1:imageUrl.rfind('.')]

            if '?' in imageUrl:
                imageFile = imageUrl[imageUrl.rfind(
                    '/') + 1:imageUrl.rfind('?')]
            else:
                imageFile = imageUrl[imageUrl.rfind('/') + 1:]
            localFileName = '%s_%s_%s_%s' % (targetSubreddit, submission.title, submission.id, imageFile)
            downloadImage(imageUrl, localFileName)
