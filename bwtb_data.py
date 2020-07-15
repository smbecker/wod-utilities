# coding=utf8

import csv
import re
import requests
from lxml import html
import datetime
from time import strptime
from enum import Enum
from typing import NamedTuple, List, Union

def get_authenticity_token(session):
	text = session.get('https://beyondthewhiteboard.com/signin').text
	tree = html.fromstring(text)
	token = tree.xpath('//input[@name="authenticity_token"]')[0]
	return token.attrib['value']

def signin(username, password, session):
	token = get_authenticity_token(session)
	session.post('https://beyondthewhiteboard.com/session',
		headers={'User-Agent': 'Mozilla/5.0'},
		data={
			'utf8': '✓',
			'authenticity_token': token,
			'login': username,
			'password': password,
			'commit': 'Sign In'
		})
	if (session.cookies.get('_btwb_session_id') == None):
		raise Exception('Failed to signin. Check your credentials')

def get_member_id(session):
	text = session.get('https://beyondthewhiteboard.com/whiteboard').text
	tree = html.fromstring(text)
	avatar = tree.xpath('//a[@class="avatar"]')[0]
	memberUrl = avatar.attrib['href']
	return memberUrl[len('/members/'):]

def get_workout_csv(memberId, session):
	r = session.get(f'https://beyondthewhiteboard.com/members/{memberId}/workout_sessions.csv')
	return r.text

def export_workout_csv(memberId, output, session):
	with open(output, 'w+') as f:
		content = get_workout_csv(memberId, session)
		f.write(content)

def _parse_workout_csv(csvreader):
	parsedHeaders = False
	for row in csvreader:
		if (parsedHeaders == False):
			parsedHeaders = True
			continue

		yield WorkoutResult.from_row(row)

def parse_workout_csv(csvpath):
	with open(csvpath, 'r', encoding='utf8', newline=None) as csvfile:
		reader = csv.reader(csvfile)
		for result in _parse_workout_csv(reader):
			yield result

class MeasurementUnit(str, Enum):
	REPS = 'reps',
	ROUNDS = 'rounds',
	INCHES = 'in',
	FEET = 'ft',
	MILES = 'mi',
	METERS = 'm',
	CALORIES = 'cal',
	SECONDS = 'sec',
	POUNDS = 'lb',
	KILOGRAMS = 'kg'

class Measurement:
	def __init__(self, value, unit):
		self.value = value
		self.unit = unit

	def __repr__(self):
		return f'MeasurementUnit({self.value}, {self.unit})'

	def __int__(self):
		return int(self.value)

	def __float__(self):
		return float(self.value)

	@staticmethod
	def parse(text):
		return Measurement._parse(text)

	@staticmethod
	def parse_list(text):
		if (text == None or len(text) == 0):
			return None

		return [Measurement._parse(part.strip(), MeasurementUnit.REPS) for part in text.split('+')]

	@staticmethod
	def _normalize(text):
		if (text.endswith(':')):
			text = text[:-1]
		return text

	@staticmethod
	def _parse(text, defaultUnit = None):
		text = Measurement._normalize(text)
		result = Measurement._parse_specialcase(text)
		if (result == None):
			result = Measurement._parse_with_unit(text, defaultUnit)

		if (result == None):
			raise Exception(f'Failed to parse {text}')

		return result

	@staticmethod
	def _parse_unit_and_factor(value):
		if (value.endswith(' each')):
			value = value[0:len(value) - len(' each')]

		if (value.endswith(' per station')):
			value = value[0:len(value) - len(' per station')]

		value = value.lower()
		if (value == 'sec' or value == 'secs' or value == 's'):
			return (MeasurementUnit.SECONDS, 1.0)

		if (value == 'min' or value == 'mins'):
			return (MeasurementUnit.SECONDS, 60.0)

		if (value == 'kg'):
			return (MeasurementUnit.KILOGRAMS, 1.0)

		if (value == 'pood'):
			return (MeasurementUnit.KILOGRAMS, 16)

		if (value == 'cal' or value == 'cals'):
			return (MeasurementUnit.CALORIES, 1.0)

		if (value == 'in'):
			return (MeasurementUnit.INCHES, 1.0)

		if (value == 'ft' or value == 'f'):
			return (MeasurementUnit.FEET, 1.0)

		if (value == 'mi'):
			return (MeasurementUnit.MILES, 1.0)

		if (value == 'm'):
			return (MeasurementUnit.METERS, 1.0)

		if (value == 'km'):
			return (MeasurementUnit.METERS, 1000.0)

		if (value == 'lb' or value == 'lbs'):
			return (MeasurementUnit.POUNDS, 1.0)

		if (value == 'rep' or value == 'reps' or value.endswith('rm')):
			return (MeasurementUnit.REPS, 1.0)

		if (value == 'round' or value == 'rounds'):
			return (MeasurementUnit.ROUNDS, 1.0)

		return (None, 0.0)

	@staticmethod
	def _parse_time(value):
		try:
			t = strptime(value, '%M:%S')
			return (t.tm_min * 60) + t.tm_sec
		except:
			try:
				t = strptime(value, '%H:%M:%S')
				return (t.tm_hour * 3600) + (t.tm_min * 60) + t.tm_sec
			except:
				return None

	@staticmethod
	def _parse_with_unit(value, defaultUnit = None):
		factor = 1.0
		parts = value.split(' ', 1)
		unit = MeasurementUnit.REPS
		if (len(parts) > 1):
			(parsedUnit, parsedFactor) = Measurement._parse_unit_and_factor(parts[1])
			if (parsedUnit == None):
				if (defaultUnit == None):
					return None
				else:
					unit = defaultUnit
			else:
				unit = parsedUnit
				factor = parsedFactor

		try:
			result = float(parts[0])
			return Measurement(result * factor, unit)
		except:
			if (defaultUnit != None):
				return Measurement(1, defaultUnit)
			return None

	@staticmethod
	def _parse_specialcase(value):
		if ('min' in value and 'sec' in value):
			minIndex = value.find('mins')
			if (minIndex == -1):
				minIndex = value.find('min') + len('min')
			else:
				minIndex += len('mins')
			
			mins = Measurement.parse(value[0:minIndex])
			secs = Measurement.parse(value[minIndex + 1:])
			return Measurement(mins.value + secs.value, MeasurementUnit.SECONDS)

		if (value.lower() == 'completed'):
			return Measurement(0, MeasurementUnit.REPS)

		(unit, _) = Measurement._parse_unit_and_factor(value)
		if (unit != None):
			return Measurement(0, unit)

		if (':' in value):
			time = Measurement._parse_time(value)
			if (time != None):
				return Measurement(time, MeasurementUnit.SECONDS)
		
		return None

class Movement(NamedTuple):
	summary: str
	description: str
	assigned: Measurement
	performed: List[Measurement] = None

	@staticmethod
	def parse(description):
		description = description.replace('Box, Bands', 'Box/Bands').strip()

		if (description.lower().startswith('rest ') or description.lower().startswith('resting ')):
			assigned = description.split(' ', 1)[1].split(' between ')[0]
			return Movement(summary='Rest', description=description, assigned=Measurement.parse(assigned))

		if (', ' in description):
			parts = [part.strip() for part in description.split(',', 1)]
			name = parts[0]
			assigned = parts[1] if len(parts) > 1 else None
			performed = None

			try:
				repCount = int(name.split(' ')[0])
				performed = Measurement.parse_list(assigned.split(',')[0].split('|')[-1])
				assigned = Measurement(repCount, MeasurementUnit.REPS)
			except:
				if (':' in assigned):
					parts = [part.strip() for part in assigned.split(':')]
					assigned = parts[0]
					performed = Measurement.parse_list(parts[1])
				assigned = Measurement.parse(re.split('[,|]', assigned)[0].strip())

			return Movement(summary=name, description=description, assigned=assigned, performed=performed)
		elif ('|' in description):
			parts = [part.strip() for part in description.split('|', 1)]
			movement = parts[0]
			performed = Measurement.parse_list(parts[1] if len(parts) > 1 else None)
			parts = movement.split(' ', 1)
			reps = parts[0].strip()
			name = parts[1] if (len(parts) > 1) else movement

			try:
				assigned = Measurement(int(reps), MeasurementUnit.REPS)
			except:
				assigned = performed[0] if (performed != None and len(performed) > 0) else Measurement(0, MeasurementUnit.REPS)
				name = movement

			return Movement(summary=name, description=description, assigned=assigned, performed=performed)
		else:
			parts = [part.strip() for part in description.split(' ', 1)]
			try:
				assigned = Measurement(int(parts[0]), MeasurementUnit.REPS)
				name=parts[1]
			except:
				assigned = None
				name = description

			return Movement(summary=name, description=description, assigned=assigned)

class RepScheme(NamedTuple):
	summary: str
	sets: int
	reps: int
	weight: int

	@staticmethod
	def _get_reps(movement):
		return int(movement.assigned)

	@staticmethod
	def _get_weight(movement):
		return int(movement.performed[0]) if (movement.performed != None and len(movement.performed) > 0) else 0

	@staticmethod
	def from_movements(movements, sets=None):
		if (len(movements) == 0):
			return None
		
		summary = set([m.summary for m in movements])
		if (len(summary) != 1):
			return None

		if (movements[0].assigned == None or movements[0].assigned.unit != MeasurementUnit.REPS):
			return None

		if (sets == None):
			sets = len(movements)

		summary = movements[0].summary
		weight = RepScheme._get_weight(movements[0])
		reps = RepScheme._get_reps(movements[0])
		for m in movements[1:]:
			if (m.assigned.unit != MeasurementUnit.REPS):
				return None

			assigned = RepScheme._get_reps(m)
			performed = RepScheme._get_weight(m)
			if (performed > weight):
				weight = performed
				reps = assigned
		return RepScheme(summary=summary, sets=sets, reps=reps, weight=weight)

class Sections(NamedTuple):
	summary: str
	description: str
	sections: List

	@staticmethod
	def parse(summary, description):
		sections = [section.strip('\n') for section in Sections._parse_into_sections(description)]
		return Sections(summary=summary, description=None, sections=[Workout.parse(section, section) for section in sections])

	@staticmethod
	def _parse_into_sections(description):
		lines = []
		first = True
		for line in description.split('\n'):
			if (first and line.endswith(':')):
				continue

			first = False
			if ('then ' in line):
				if (len(lines) > 0):
					yield '\n'.join(lines)
				lines = []
				continue

			lines.append(line)

		if (len(lines) > 0):
			yield '\n'.join(lines)

class EMOM(NamedTuple):
	summary: str
	description: str
	movements: List[Movement]
	interval: Measurement
	total: Measurement
	alternating: bool
	
	@staticmethod
	def parse(summary, description):
		lines = description.split('\n')
		(interval, total) = [Measurement.parse(part) for part in re.split(',|between:', lines[0])[0].replace('Every ', '').split(' for ')]
		alternating = 'alternating between' in description.lower()
		return EMOM(summary=summary, \
			description=description, \
			movements=[Movement.parse(line) for line in lines[1:]], \
			interval=interval, 
			total=total, \
			alternating=alternating)

class AMRAP(NamedTuple):
	summary: str
	description: str
	limit: Measurement
	movements: List[Movement]

	@staticmethod
	def parse(summary, description):
		lines = description.split('\n')
		return AMRAP(summary=summary, \
			description=description, \
			limit=Measurement.parse(lines[0].replace(' AMRAP', '').split(' ')[-1]), \
			movements=[Movement.parse(line) for line in lines[1:]])

class Tabata(NamedTuple):
	summary: str
	description: str
	rounds: int
	work: Measurement
	rest: Measurement
	movements: List[Movement]

	@staticmethod
	def parse(summary, description):
		index = summary.lower().find(' x ')
		roundIndex = summary[0:index].strip().rindex(' ')
		rounds = int(summary[roundIndex:index])
		(work, rest) = [Measurement.parse(part.strip()) for part in summary[index + len(' x '):].split('/')]
		movements = [Movement.parse(part) for part in description.split('\n')]
		return Tabata(summary=summary, \
			description=description, \
			rounds=rounds, \
			work=work, \
			rest=rest, \
			movements=movements)

class Rounds(NamedTuple):
	summary: str
	description: str
	rounds: int
	movements: List[Movement]

	@staticmethod
	def parse(summary, description):
		lines = description.split('\n')
		rounds = 1
		if (' rounds' in lines[0]):
			rounds = int(lines[0].split(' ')[0])
			movements = [Movement.parse(line) for line in lines[1:]]
		else:
			if (lines[0] == 'Intervals'):
				lines = lines[1:]
			movements = [Movement.parse(line) for line in lines]

		return Rounds(summary=summary, description=description, rounds=rounds, movements=movements)

class Sets(NamedTuple):
	summary: str
	description: str
	movements: List[Movement]

	@staticmethod
	def parse(summary, description):
		movements = [Movement.parse(part) for part in description.split('\n')[1:]]
		return Sets(summary=summary, description=description, movements=movements)

class ForTime(NamedTuple):
	summary: str
	description: str
	movements: List[Movement]

	@staticmethod
	def parse(summary, description):
		lines = description.split('\n')
		reps = [int(rep) for rep in lines[0].replace(' reps of:', '').split('-')]
		parsed = [Movement.parse(part) for part in description.split('\n')[1:]]
		movements = []
		for r in reps:
			for mv in parsed:
				copy = Movement(**mv._asdict())._replace(assigned=Measurement(r, MeasurementUnit.REPS), performed=[mv.assigned])
				movements.append(copy)
		return ForTime(summary=summary, description=description, movements=movements)

class Workout:
	@staticmethod
	def parse(summary, description):
		if ('then ' in description):
			return Sections.parse(summary, description)

		if (description.startswith('Sets')):
			return Sets.parse(summary, description)

		if (description.startswith("Every ")):
			return EMOM.parse(summary, description)

		if ('AMRAP' in description):
			return AMRAP.parse(summary, description)

		if (summary.startswith('"Tabata"')):
			return Tabata.parse(summary, description)

		if ('reps of:' in description):
			return ForTime.parse(summary, description)

		return Rounds.parse(summary, description)

class WorkoutResult(NamedTuple):
	date: datetime.datetime
	workout: Union[Sections, Sets, EMOM, AMRAP, Tabata, ForTime, Rounds]
	results: List[Measurement]
	prescribed: bool
	puked: bool
	notes: str

	@staticmethod
	def _parse_date(d):
		return datetime.datetime(int(d[0:4]), int(d[5:7]), int(d[8:10]))

	@staticmethod
	def from_row(row):
		return WorkoutResult( \
			date=WorkoutResult._parse_date(row[0]), \
			workout=Workout.parse(row[1], row[9]), \
			results=Measurement.parse_list(row[7].split('|')[0] if len(row[7]) > 0 else None), \
			prescribed=row[3] == 'true', \
			puked=row[4] == 'true', \
			notes=row[8])