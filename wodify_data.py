from typing import NamedTuple, List, Iterable, Union, Callable
from enum import Enum
import datetime
import bwtb_data as bwtb

class Gymnastics(NamedTuple):
	date: str
	name: str
	sets: int
	reps: int
	prescribed: bool
	notes: str

class Weighlifting(NamedTuple):
	date: str
	name: str
	sets: int
	reps: int
	weight: float
	prescribed: bool
	notes: str

class DistanceUnit(str, Enum):
	INCHES = '7',
	FEET = '4',
	MILES = '5',
	METERS = '1',
	KILOMETERS = '3'

def _get_measure(measure, value):
	return {
		'type': measure,
		'value': value
	}

def _get_distance_measure(value, unit):
	return {
		'type': 'distance',
		'value': value,
		'unit': unit
	}

def _get_metcon_measure(measure: bwtb.Measurement):
	value = int(measure.value)
	if (measure.unit == bwtb.MeasurementUnit.INCHES):
		return _get_distance_measure(value, DistanceUnit.INCHES)
	if (measure.unit == bwtb.MeasurementUnit.FEET):
		return _get_distance_measure(value, DistanceUnit.FEET)
	if (measure.unit == bwtb.MeasurementUnit.MILES):
		return _get_distance_measure(value, DistanceUnit.MILES)
	if (measure.unit == bwtb.MeasurementUnit.METERS):
		return _get_distance_measure(value, DistanceUnit.METERS)
	if (measure.unit == bwtb.MeasurementUnit.SECONDS):
		(min, sec) = divmod(value, 60)
		return {
			'type': 'time',
			'min': int(min),
			'sec': int(sec)
		}
	if (measure.unit == bwtb.MeasurementUnit.CALORIES):
		return _get_measure('cal', value)
	if (measure.unit == bwtb.MeasurementUnit.ROUNDS):
		return _get_measure('rounds', value)
	if (measure.unit == bwtb.MeasurementUnit.REPS):
		return _get_measure('reps', value)
	return None

def _get_metcon_measures(measures: List[bwtb.Measurement]):
	if (measures == None or len(measures) == 0):
		return None

	if (len(measures) == 2):
		first = measures[0]
		second = measures[1]
		if (first.unit == bwtb.MeasurementUnit.ROUNDS and second.unit == bwtb.MeasurementUnit.REPS):
			return {
				'type': 'rounds_and_reps',
				'rounds': int(first),
				'reps': int(second)
			}

	return _get_metcon_measure(measures[0])

class Metcon(NamedTuple):
	date: str
	name: str
	measure: any
	prescribed: bool
	notes: str
	benchmark: bool = True

WorkoutResult = Union[Gymnastics, Weighlifting, Metcon]

def _parse_date(date: datetime.datetime) -> str:
	return date.strftime("%m/%d/%Y")

def _append_notes(description: str, notes: str) -> str:
	if (description != None and len(description) > 0):
		if (notes != None and len(notes) > 0):
			return f'{description}\nNotes: {notes}'
		return description
	return notes

def _metcon_from_result(result: bwtb.WorkoutResult, benchmark: bool = True) -> Metcon:
	measure = _get_metcon_measures(result.results)
	date = _parse_date(result.date)
	if (measure != None):
		return Metcon(
			date=_parse_date(result.date), \
			name=result.workout.summary, \
			measure=measure, \
			prescribed=result.prescribed, \
			notes=_append_notes(result.workout.description, result.notes),
			benchmark=benchmark and measure != None
		)
	return None

class WorkoutResults:
	def __init__(self, gymnastics: List[Gymnastics] = [], weightlifting: List[Weighlifting] = [], metcons: List[Metcon] = []):
		self.gymnastics = gymnastics
		self.weightlifting = weightlifting
		self.metcons = metcons

	def _append_metcon(self, result: bwtb.WorkoutResult, benchmark = True):
		metcon = _metcon_from_result(result, benchmark)
		if (metcon != None):
			self.metcons.append(metcon)
			return True
		return False

	def _append_sets(self, result: bwtb.WorkoutResult):
		sets = result.workout.sets if hasattr(result.workout, 'sets') else None
		rep_scheme = bwtb.RepScheme.from_movements(result.workout.movements, sets=sets)
		if (rep_scheme == None):
			return self._append_metcon(result, benchmark=False)

		date = _parse_date(result.date)
		if (rep_scheme.weight == 0):
			self.gymnastics.append(Gymnastics(
				date=date, \
				name=rep_scheme.summary, \
				sets=rep_scheme.sets, \
				reps=rep_scheme.reps, \
				prescribed=result.prescribed, \
				notes=_append_notes(result.workout.description, result.notes)))
			return True

		self.weightlifting.append(Weighlifting(
			date=date, \
			name=rep_scheme.summary, \
			sets=rep_scheme.sets, \
			reps=rep_scheme.reps, \
			weight=rep_scheme.weight, \
			prescribed=result.prescribed, \
			notes=_append_notes(result.workout.description, result.notes)))
		return True

	def _append_from_bwtb(self, result: bwtb.WorkoutResult):
		if (isinstance(result.workout, bwtb.EMOM)):
			return self._append_sets(result)
		if (isinstance(result.workout, bwtb.Sets)):
			return self._append_sets(result)
		return self._append_metcon(result, benchmark=(isinstance(result.workout, bwtb.Tabata) == False))

	def __len__(self):
		return len(self.gymnastics) + len(self.weightlifting) + len(self.metcons)

	def _asdict(self):
		return {
			'gymnastics': [g._asdict() for g in self.gymnastics],
			'weightlifting': [w._asdict() for w in self.weightlifting],
			'metcons': [m._asdict() for m in self.metcons]
		}

	@staticmethod
	def from_bwtb(results: Iterable[bwtb.WorkoutResult], ignored_result: Callable[[bwtb.WorkoutResult], None] = None):
		summary = WorkoutResults()
		for result in results:
			if (summary._append_from_bwtb(result) == False and ignored_result != None):
				ignored_result(result)
		return summary