#!/usr/bin/env python

import sys
from getpass import getpass
import requests
from bwtb_data import signin, get_member_id, export_workout_csv, parse_workout_csv
from wodify_data import WorkoutResults
from wodify_driver import WodifyDriver

print('This script will walk you through migrating your workout results from beyondthewhiteboard.com. You will need your beyondthewhiteboard.com username and password as well as your wodify.com username and password.')
print('')

bwtbuser = input('Enter your beyondthewhiteboard.com username: ')
bwtbpass = getpass()

wodifyuser = input('Enter your app.wodify.com username: ')
wodifypass = getpass()

print('')
print('Downloading your workouts results from beyondthewhiteboard.com')

bwtbout = 'workouts.csv'
with requests.session() as s:
	signin(bwtbuser, bwtbpass, s)
	memberId = get_member_id(s)
	export_workout_csv(memberId, bwtbout, s)
	print('Downloaded workouts to', bwtbout)

wodifyresults=WorkoutResults.from_bwtb(parse_workout_csv(bwtbout))
print(f'Found {len(wodifyresults)} workout results to import into Wodify.')

WodifyDriver.import_all(wodifyresults, username=wodifyuser, password=wodifypass, onimport=lambda name: print(f'Imported {name}'))
