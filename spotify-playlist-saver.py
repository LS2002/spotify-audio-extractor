#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import urllib2
import shutil
import os
import time
import re
import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

def main():

    spotify_playlist_user = '<replace-with-playlist-username>'

    url_playlist = 'https://play.spotify.com/user/'+spotify_playlist_user+'/playlist/0SPKCBmcMSnTEpUM2jBxFt'

    # profile = webdriver.FirefoxProfile()
    # profile.accept_untrusted_certs = True
    # driver = webdriver.Firefox(firefox_profile=profile)
    driver = webdriver.Firefox()

    driver.get(url_playlist)

    driver.find_element_by_id('has-account').click()

    username = driver.find_element_by_name('username')
    username.send_keys('<replace-with-spotify-login-username>')
    password = driver.find_element_by_name('password')
    password.send_keys('<replace-with-spotify-login-password>')
    password.send_keys(Keys.RETURN)

    time.sleep(15)
    iframe_element = driver.find_element_by_xpath("//iframe[starts-with(@id,'browse-app-spotify:app:user:"+spotify_playlist_user+"')]")
    driver.switch_to.frame(iframe_element)
    time.sleep(10)
    page_content_playlist = driver.page_source
    driver.close()

    entry_all = BeautifulSoup(page_content_playlist).find_all("tr",attrs={"data-ta-id":"track-playable"})
    spotify_list = []
    index = 0
    for entry in entry_all:
        # https://play.spotify.com/track/5KONnBIQ9LqCxyeSPin26k
        spotify_track_pattern = r'"(spotify:track:.+?)"'
        spotify_track_url = re.compile(spotify_track_pattern).search(str(entry)).group(1)
        # spotify_track_url += "#0:30"

        if entry.find("td",attrs={"class":"tl-cell tl-artists"}) != None and entry.find("td",attrs={"class":"tl-cell tl-name"}) != None and entry.find("td",attrs={"class":"tl-cell tl-albums"}) != None:
            spotify_artist_name = entry.find("td",attrs={"class":"tl-cell tl-artists"}).get_text().strip().replace('\r','').replace('\n','')
            spotify_track_title = entry.find("td",attrs={"class":"tl-cell tl-name"}).get_text().strip().replace('\r','').replace('\n','')
            spotify_album_name = entry.find("td",attrs={"class":"tl-cell tl-albums"}).get_text().strip().replace('\r','').replace('\n','')
            spotify_track_duration = entry.find("td",attrs={"class":"tl-cell tl-time"}).get_text().strip().replace('\r','').replace('\n','')
            spotify_single = []
            spotify_single.append(spotify_track_url)
            spotify_single.append(spotify_artist_name)
            spotify_single.append(spotify_track_title)
            spotify_single.append(spotify_album_name)
            spotify_single.append(spotify_track_duration)
            spotify_list.append(spotify_single)
            index += 1
            # print ','.join([str(index), spotify_track_url, spotify_artist_name, spotify_track_title, spotify_album_name, spotify_track_duration])


    country = "<replace-with-artist-or-whaterever>"

    createFolder(country)
    time.sleep(2)

    debug = False
    for index, value in enumerate(spotify_list):
        audioUrl =  value[0]
        artistName = value[1].replace(' ','_')
        trackTitle = value[2].replace(' ','_').replace('\'','').replace('$','').replace('-','_').replace(',','_')
        albumName = value[3].replace(' ','_').replace('(','').replace(')','')
        duration = value[4]

        print ','.join([str(index+1), audioUrl, artistName, trackTitle, albumName, duration])

        timeToStopSpotify = getDurationInSeconds(duration)
        setAudioInputOutput('soundflower')

        if debug == True: print str(datetime.datetime.now()),'playAudioFile start'
        playAudioFile(audioUrl, timeToStopSpotify)
        if debug == True: print str(datetime.datetime.now()),'playAudioFile end'

        audioFilePathIn = country+'/'+country+'_'+str(index+1).zfill(3)+".wav"
        audioFilePathOut = country+'/'+str(index+1).zfill(3)+'_'+trackTitle+".mp3"

        if debug == True: print str(datetime.datetime.now()),'saveAudioFile start'
        saveAudioFile(audioFilePathIn, timeToStopSpotify)
        if debug == True: print str(datetime.datetime.now()),'saveAudioFile end'

        time.sleep(2)

        if debug == True: print str(datetime.datetime.now()),'convertToMP3 start'
        convertToMP3(audioFilePathIn,audioFilePathOut)
        if debug == True: print str(datetime.datetime.now()),'convertToMP3 end'

        time.sleep(2)

    setAudioInputOutput("reset")

def playAudioFile(audio_path, timeToStopSpotify):
    spotify_path= '/Applications/Spotify.app'
    run_command_with_timeout(['/usr/bin/open','-a',spotify_path,audio_path],timeToStopSpotify)

def setAudioInputOutput(audioSource):
    if "soundflower" in audioSource:
        run_command(['audiodevice','input',"\"Soundflower (2ch)\""])
        run_command(['audiodevice','output',"\"Soundflower (2ch)\""])
    else:
        # run_command(['audiodevice','input',"\"Internal Microphone\""])
        run_command(['audiodevice','input',"\"External Microphone\""])
        run_command(['audiodevice','output',"\"Headphones\""])

def createFolder(folderName):
    if not os.path.exists(folderName):
        os.makedirs(folderName)


def getDurationInSeconds(audioDuration):
    duration = audioDuration.split(':')
    return int(duration[0])*60+int(duration[1])

def convertToMP3(audioFilePathIn,audioFilePathOut):
    # run_command(['ffmpeg','-i',audioFilePathIn,'-ab','16','-f','mp2',audioFilePathOut])
    run_command(['lame',audioFilePathIn,audioFilePathOut])
    time.sleep(1)
    run_command(['rm',audioFilePathIn])
    time.sleep(1)


def saveAudioFile(audioFilePath, timeToSaveSpotifyAudio):
    run_command_with_timeout(['sox','-b','16','-d',audioFilePath],timeToSaveSpotifyAudio)

def run_command(command):
    import subprocess
    subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)

def run_command_with_timeout(command, timeout):
    """call shell-command and either return its output or kill it
    if it doesn't normally exit within timeout seconds and return None"""
    import subprocess, datetime, os, time, signal
    start = datetime.datetime.now()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while process.poll() is None:
        time.sleep(0.1)
        now = datetime.datetime.now()
        if (now - start).seconds > timeout:
            os.kill(process.pid, signal.SIGKILL)
            os.waitpid(-1, os.WNOHANG)
            return None
    return process.stdout.read()

def writeXML(line,country):
    with open(country+"_entry.xml", "a+") as xml_file:
        xml_file.write(line.encode('utf8'))

def writeYAML(line,country):
    with open(country+"_masterlist.yaml", "a+") as yaml_file:
        yaml_file.write(line.encode('utf8'))


def getWebPageContent(url):
    html_page = urllib2.urlopen(url).read()
    return BeautifulSoup(html_page)

def getElementValue(bs_content, elementName, attrElementName, attrElementValue, valueElement):
    return BeautifulSoup(bs_content).find(elementName, attrs={attrElementName:attrElementValue}).get(valueElement)


def writeFile(content, fileName, extension):
    with open(fileName + "." + extension, "a+") as the_file:
        the_file.write(content.encode('utf8'))


if __name__=='__main__':
    main()
