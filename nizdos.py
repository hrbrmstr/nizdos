#!/usr/bin/python
#
# nizdos.py - Ancient Indo-European word for "Nest"
#
# Version 0.1 - 2013-09-04
#
# Script to:
#
# - Read heat/AC status from your nest
# - Log those variables to Mongo (so you can analyze/visualize it later!)
# - Alert you (via Pushover) when heat or AC changes status, whic is 
#   primarily why I wrote it
#
# What's Nest? Awesome, stylish thermostat that require hacking to get 
# to YOUR data #sigh
#
#              http://nest.com/
#
# Never heard of Pushover? Think #spiffy & easy iOS/Android notifications
#
#              https://pushover.net/
#
# NOT possible without Scott Baker's most excellent pynest interface:
#
#              https://github.com/smbaker/pynest
#
# (I've cut out all but the necessary components of it for use here)
# 
# Example usage: Run in cron every ~5 mins:
#
#              */5 * * * * /opt/nest/nizdos.py
#
# MIT License
#
# Copyright (c) 2013 Bob Rudis (@hrbrmstr) bob@rudis.net
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import urllib
import urllib2
import sys
import datetime
import ConfigParser

import pushover
import redis
import pymongo

try:
   import json
except ImportError:
   try:
       import simplejson as json
   except ImportError:
       print "No json library available. I recommend installing either python-json"
       print "or simpejson."
       sys.exit(-1)

class Nest:
    def __init__(self, username, password, serial=None, index=0, units="F"):
        self.username = username
        self.password = password
        self.serial = serial
        self.units = units
        self.index = index

    def loads(self, res):
        if hasattr(json, "loads"):
            res = json.loads(res)
        else:
            res = json.read(res)
        return res

    def login(self):
        data = urllib.urlencode({"username": self.username, "password": self.password})

        req = urllib2.Request("https://home.nest.com/user/login",
                              data,
                              {"user-agent":"Nest/1.1.0.10 CFNetwork/548.0.4"})

        res = urllib2.urlopen(req).read()

        res = self.loads(res)

        self.transport_url = res["urls"]["transport_url"]
        self.access_token = res["access_token"]
        self.userid = res["userid"]

    def get_status(self):
        req = urllib2.Request(self.transport_url + "/v2/mobile/user." + self.userid,
                              headers={"user-agent":"Nest/1.1.0.10 CFNetwork/548.0.4",
                                       "Authorization":"Basic " + self.access_token,
                                       "X-nl-user-id": self.userid,
                                       "X-nl-protocol-version": "1"})

        res = urllib2.urlopen(req).read()

        res = self.loads(res)

        self.structure_id = res["structure"].keys()[0]

        if (self.serial is None):
            self.device_id = res["structure"][self.structure_id]["devices"][self.index]
            self.serial = self.device_id.split(".")[1]

        self.status = res

# get items we need from the config file
#
# in general, it's a HORRID idea to store creds in a script
# especially when every scripting language has a dirt simple way to 
# use a config file
#
# ALSO: DON'T STORE THE CONFIG FILE IN THE DIRECTORY YOU'RE USING
# AS A PRIVATE OR PUBLIC GIT REPO!!!! #pls
#
# make the location whatever you want, but it has to be readable by the script

CONFIG_FILE = "/home/bob/.nizdos.conf"
Config = ConfigParser.ConfigParser()
Config.read(CONFIG_FILE)

# initialize pushover

pushover.init(Config.get("pushover","AppKey"))
pushoverClient = pushover.Client(Config.get("pushover","UserKey"))

# setup redis
#
# technically, sqlite, mongo or even a dbm or text file could have
# been used. I <3 redis and have it running for many things
# including stuff like this :-) Feel free to swap it out for
# something else (memcache, mebbe?)

red = redis.StrictRedis(host="localhost", port=6379, db=0)

# setup mongo
# could use MySQL or sqlite. Mongo is what the cool kids use, tho
# and it can send the JSON I need to D3 w/o modification :-)

client = pymongo.MongoClient()
mdb = client['nest']
nestdb = mdb['readings']

# get last readings for AC on & heat on
# value comes back from [py]redis as a string O_o so
# we hack it to be a bool

lastAC = red.get("lastAC") 
lastHeat = red.get("lastHeat")

# initialize connection to Nest

nst = Nest(Config.get("nest","Username"),
           Config.get("nest","Password"), None, 0, units="F")
nst.login()

# get current readings

nst.get_status()

currdate = datetime.datetime.utcnow()
currTemp = nst.status["shared"][nst.serial]["current_temperature"] * 1.8 + 32.0
currHumid = nst.status["device"][nst.serial]["current_humidity"]
currAC = nst.status["shared"][nst.serial]["hvac_ac_state"]
currHeat = nst.status["shared"][nst.serial]["hvac_heater_state"]

# store them in redis

red.set("lastAC",str(currAC))
red.set("lastHeat",str(currHeat))

# setup mongo "reading"

reading = { "date"    : currdate,
            "temp"    : currTemp,
            "humid"   : currHumid,
            "cooling" : currAC,
            "heating" : currHeat }

# store readings in mongo

rId = nestdb.insert(reading)

# send a message to pushover if heat or AC flipped value
# could be more Pythonic

if (lastAC != str(currAC)):
    pushoverClient.send_message("A/C is ON" if (currAC == "True") else "A/C is OFF", title="Nizdos", priority=1)

if (lastHeat != str(currHeat)):
    pushoverClient.send_message("Heat is ON" if (currAC == "True") else "Heat is OFF", title="Nizdos", priority=1)
