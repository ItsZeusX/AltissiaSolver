import requests
import time
import json
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome import options
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from pathlib import Path
from selenium.webdriver.common.keys import Keys

filename = "headers.json"
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

externalHeaders = json.load(open(resource_path(filename) , "r"))


headers = {
  'x-device-uuid': externalHeaders["x-device-uuid"] ,
  'x-altissia-token': externalHeaders["x-altissia-token"]
}

options = webdriver.ChromeOptions()
options.add_argument("--user-data-dir=/profile")
options.add_argument('log-level=3')
s=Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=s , options=options)
driver.get("https://app.ofppt-langues.ma/")

def FormatUrl(url) :
    formatedUrl = "https://app.ofppt-langues.ma/gw//lcapi/main/api/lc/lessons/"+"/".join(url.split("/")[9 : -3]).replace("activity" , "activities")
    if "GRAMMAR_RULE" in url :
        return "GRAMMAR_RULE" 
    if "MISE_EN_PRATIQUE" in url :
        return "MISE_EN_PRATIQUE"
    if url[-6:] == "/video" :
        return "VIDEO"
    return formatedUrl

def GetAnswers(url) :
    u = FormatUrl(url)
    try :
        if u == "MISE_EN_PRATIQUE" :
            return {"activityType" : "MISE_EN_PRATIQUE" , "count" : 1}
        if u == "GRAMMAR_RULE" :
            return {"activityType" : "GRAMMAR_RULE" , "count" : 1}
        if u == "VIDEO" :
            return {"activityType" : "VIDEO" , "count" : 1}
            
        response = requests.request("GET", u, headers=headers)
        if response.json()["activityType"] != "EXERCISE" and  response.json()["activityType"] != "SUMMARY_TEST":
            return {"activityType":response.json()["activityType"], "count" : len(response.json()["content"]["items"])}
        Starteranswers = [A["correctAnswers"] for A in response.json()["content"]["items"]]
        answers = []
        for answer in Starteranswers :
            for subanswer in answer :
                answers.append(subanswer[0])
        return {"activityType":response.json()["activityType"] , "type" : response.json()["content"]["items"][0]["type"] ,"count" : len(response.json()["content"]["items"]), "answers" : answers}
    except : 
        pass
def Exercise_Open(anwser) :
    resp = anwser
    answers = resp["answers"]
    length = resp["count"]
    for i in range(length) : 
        fields = driver.find_elements(By.CLASS_NAME , "question-input")
        for f in fields :
            f.send_keys(answers.pop(0))
        driver.execute_script('document.getElementsByClassName("footer-button-bar-btn")[0].click()')
        driver.execute_script('document.getElementsByClassName("footer-button-bar-btn")[0].click()')
    time.sleep(1)
    driver.execute_script('document.getElementsByClassName("altissia-main-button")[0].click()')


def Exercise_Multiple_Choice(anwser) :
    resp = anwser
    answers = resp["answers"]
    length = resp["count"]
    for i in range(length) : 
        choices = driver.find_elements(By.CLASS_NAME , "multiple-choice-btn")
        current_anwser = answers.pop(0)
        for c in choices :
           if c.text.strip() == current_anwser :
               c.click()
        driver.execute_script('document.getElementsByClassName("footer-button-bar-btn")[0].click()')
        driver.execute_script('document.getElementsByClassName("footer-button-bar-btn")[0].click()')
    time.sleep(1)
    driver.execute_script('document.getElementsByClassName("altissia-main-button")[0].click()')

def Exercise_Drag_And_Drop(anwser) :
    resp = anwser
    for i in range(resp["count"]):
        answers = resp["answers"].pop(0).split()
        length = len(answers)
        for j in range(length) : 
            choices = driver.find_elements(By.CLASS_NAME , "droppable-item-not-dragged")
            current_anwser = answers.pop(0)
            for c in choices :
                if c.text.strip() == current_anwser :
                   c.click()
        driver.execute_script('document.getElementsByClassName("footer-button-bar-btn")[0].click()')
        driver.execute_script('document.getElementsByClassName("footer-button-bar-btn")[0].click()')
    time.sleep(1)
    driver.execute_script('document.getElementsByClassName("altissia-main-button")[0].click()')
                

def Exercise_Drag_And_Drop3(anwser) :
    for page in range(len(anwser["answers"])) :
        a = anwser["answers"].pop(0)
        for i in range(20) :
            choices = driver.find_elements(By.CLASS_NAME , "droppable-item-not-dragged")
            for choice in choices :
                
                t = choice.text
                if a.startswith(t) :
                    a = a.replace(t , "").strip()
                    try :
                        choice.click()  
                    except :
                        pass      
        driver.execute_script('document.getElementsByClassName("footer-button-bar-btn")[0].click()')
        driver.execute_script('document.getElementsByClassName("footer-button-bar-btn")[0].click()')
    time.sleep(1)
    driver.execute_script('document.getElementsByClassName("altissia-main-button")[0].click()')

def Skipper(anwser) :
    for i in range(anwser["count"]) :
        driver.execute_script('document.getElementsByClassName("altissia-main-button")[0].click()')
    time.sleep(1)
    driver.execute_script('document.getElementsByClassName("altissia-main-button")[0].click()')
def ExrciseDetector() :
    anwsers = GetAnswers(driver.current_url) 
    
    if anwsers["activityType"] == "MISE_EN_PRATIQUE" :
        print("• [MISE_EN_PRATIQUE] Page Detected")
        return
    if anwsers["activityType"] == "VIDEO" :
        print("• [VIDEO] Detected")
        driver.execute_script('document.getElementsByTagName("video")[0].currentTime = 9999')
        time.sleep(1)
        driver.execute_script('document.getElementsByTagName("video")[0].play()')
        time.sleep(3)
        driver.execute_script('document.getElementsByClassName("altissia-main-button")[0].click()')

    if anwsers["activityType"] == "SUMMARY_TEST" :
        print("• [TEST] Page Detected")
        Exercise_Open(anwsers)

    if anwsers["activityType"] == "EXERCISE" :
        if anwsers["type"] == "OPEN" :
            print("• [OPEN] Exercise Detected")
            Exercise_Open(anwsers)

        if anwsers["type"] == "MULTIPLE_CHOICE" :
            print("• [MULTIPLE_CHOICE] Exercise Detected")
            Exercise_Multiple_Choice(anwsers)
  
        if anwsers["type"] == "DRAG_AND_DROP" :
            print("• [DRAG_AND_DROP] Exercise Detected")
            Exercise_Drag_And_Drop3(anwsers)

    if anwsers["activityType"] == "VOCABULARY_LIST" or anwsers["activityType"] == "PRONUNCIATION" or anwsers["activityType"] == "GRAMMAR_RULE":
        Skipper(anwsers)
        print("• [Skippable] Detected")

def looper() :
    try :
        ExrciseDetector()
        looper()
    except :
        print("• Waiting ..." , end='\r')
        time.sleep(1)
        looper()
        
looper()