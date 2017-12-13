#! python3
# -*- coding: utf-8 -*-
import os
import re
import sys
import glob
import praw
import requests
import logging
from bs4 import BeautifulSoup
from unidecode import unidecode
sys.path.append('C:/Users/IBM_ADMIN/Dropbox/_Programs/__pycache__/Modules/')
import Net


# MIN_SCORE = 2000       # the default minimum score before it is downloaded
Subreddit = {'pics': 10000, 'EarthPorn': 2000}

log_file_path = "RedditDownloader.log"
logging.basicConfig(level=logging.INFO,
                    filename=log_file_path,
                    format='%(asctime)s    : %(message)s')
# logging.disable(logging.CRITICAL)

os.chdir('./RedditDowns/')


def remove_non_ascii(text):
    return unidecode(text)


def downloadImage(imageUrl, localFileName):
    '''Definition to download the image from the URL'''
    try:
        localFileName = remove_non_ascii(localFileName)
        print('Downloading : %s' % (localFileName))
        logging.info('Downloading : %s' % (localFileName))
        response = requests.get(imageUrl)
        if response.status_code == 200:
            with open(localFileName, 'wb') as fo:
                for chunk in response.iter_content(50000):
                    fo.write(chunk)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        lineNo = str(exc_tb.tb_lineno)
        logging.info('Error: %s : %s at Line %s.\n' %
                     (type(e), e, lineNo))
        print('Error: %s : %s at Line %s.' %
              (type(e), e, lineNo))
        pass


def downloader():
    for targetSubreddit, MIN_SCORE in Subreddit.items():
        # Find the URL with this pattern
        imgurUrlPattern = re.compile(r'(i.imgur.com/(.*))(\?.*)?')
        redditUrlPattern1 = re.compile(r'(i.reddituploads.com/(.*))(\?.*)?')
        redditUrlPattern2 = re.compile(r'(i.redd.it/(.*))(\?.*)?')
        # nasaUrlPattern = re.compile(r'(*nasa.gov/(.*))(\?.*)?')

        # Connect to reddit and download the subreddit front page
        # Note: Be sure to change the user-agent to something unique.
        r = praw.Reddit(user_agent='android:com_useragent')
        submissions = r.get_subreddit(targetSubreddit).get_top_from_week(limit=100)

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

            if "gif" in submission.url:
                # skip gif
                continue
            if submission.score < MIN_SCORE:
                # skip submissions that haven't even reached the Minimum Score
                continue
            if len(glob.glob('*%s*' % (submission.id))) > 0:
                # We've already downloaded files for this reddit submission
                continue
            try:
                if len(glob.glob('*%s*' % (submission.title))) > 0:
                    # We've already downloaded files for this reddit submission
                    continue
            except:
                pass

            if len(submission.title) > 185:
                # Maximum char limit
                continue
            print(submission.url)
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

            # This is an i reddit upload
            if ('i.reddituploads.com') in submission.url:
                mo = redditUrlPattern1.search(submission.url)
                localFileName = '%s_%s_%s%s' % (
                    targetSubreddit, submission.title, submission.id, '.jpg')
                downloadImage(submission.url, localFileName)

            if ('i.redd.it') in submission.url:
                mo = redditUrlPattern2.search(submission.url)
                localFileName = '%s_%s_%s%s' % (
                    targetSubreddit, submission.title, submission.id, '.jpg')
                downloadImage(submission.url, localFileName)

            # This is an Nasa upload
            if ('nasa.gov') in submission.url:
                # mo = nasaUrlPattern.search(submission.url)
                if '.jpg' or '.png' in submission.url:
                    localFileName = '%s_%s_%s%s' % (
                        targetSubreddit, submission.title, submission.id, '.jpg')
                    downloadImage(submission.url, localFileName)

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
                    localFileName = '%s_album_%s_%s_%s' % (
                        targetSubreddit, submission.title, submission.id, imgFilename)
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
                localFileName = '%s_%s_%s_%s' % (
                    targetSubreddit, submission.title, submission.id, imgurFilename)
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
                try:
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

                    localFileName = '%s_%s_%s_%s' % (
                        targetSubreddit, submission.title, submission.id, imageFile)
                    downloadImage(imageUrl, localFileName)
                except:
                    continue


def main():
    logging.info('-----ReDown.py Script Run Begin-----')
    if Net.connect('https://www.reddit.com', 20) is False:
        logging.info('Unable to connect to Reddit.')
    else:
        logging.info('Internet Connection Successful.')
        try:
            downloader()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            lineNo = str(exc_tb.tb_lineno)
            logging.info('Error: %s : %s at Line %s.\n' %
                         (type(e), e, lineNo))
            print('Error: %s : %s at Line %s.' %
                  (type(e), e, lineNo))

    logging.info('-----ReDown.py Script Run Ended-----\n')


if __name__ == '__main__':
    main()
