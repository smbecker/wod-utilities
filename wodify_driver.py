import os
from typing import List, Callable
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from wodify_data import WorkoutResults, Weighlifting, Gymnastics, Metcon

def _ensure_driver(driver, username, password):
	if (driver == None):
		driver = webdriver.Chrome(ChromeDriverManager().install())
		driver.get('https://app.wodify.com')
		_signin(driver, username, password)
		_goto_myperformances(driver)
		return (driver, True)
	return (driver, False)

def _cleanup(driver, destroy):
	if (destroy):
		driver.quit()

def _signin(driver, username, password):
	_send_keys(driver, (By.ID, 'Input_UserName'), username)
	_send_keys(driver, (By.ID, 'Input_Password'), password, skipcheck=True)
	_click(driver, (By.CLASS_NAME, 'signin-btn'))

def _wait_for_element(driver, criteria, timeout = 10, condition=EC.presence_of_element_located):
	criteria = condition(criteria)
	element = WebDriverWait(driver, timeout).until(criteria)
	return element

def _send_keys(driver, criteria, value, timeout = 10, skipcheck = False):
	value = str(value)

	element = _wait_for_element(driver, criteria, timeout)
	element.clear()
	element.send_keys(value)

	if (skipcheck == False):
		waiting = 2
		while (element.get_attribute('value') != value):
			driver.implicitly_wait(waiting)
			if (element.get_attribute('value') != value):
				waiting += 2
				if (waiting > 20):
					break
				if (waiting > 10):
					element.clear()
					element.send_keys(value)

	return element

def _click(driver, criteria, timeout = 10):
	element = _wait_for_element(driver, criteria, timeout, condition=EC.element_to_be_clickable)
	element.click()
	return element

def _select(driver, criteria, value, timeout = 10):
	element = _wait_for_element(driver, criteria, timeout)
	Select(element).select_by_value(value)
	return element

def _goto_myperformances(driver):
	return _click(driver, (By.ID, 'AthleteTheme_wtLayoutNormal_block_wtMenu_AthleteTheme_wt67_block_wt34'))

class _addperformance_condition(object):
	def __call__(self, driver):
		element = None
		try:
			element = driver.find_element_by_id('AthleteTheme_wt1_block_wtSubNavigation_wt14_wt14')
			if (element != None and element.is_displayed() == False):
				element = None
		except:
			element = None

		if (element == None):
			try:
				element = driver.find_element_by_id('AthleteTheme_wt10_block_wtSubNavigation_wt12_wt14')
				if (element != None and element.is_displayed() == False):
					element = None
			except:
				element = None
		
		if (element != None):
			return element
		return False

def _goto_addperformance(driver):
	element = WebDriverWait(driver, 10).until(_addperformance_condition())
	element.click()
	return element

def _choose_type(driver, requested):
	return _select(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_wtUserComponent_ComponentTypeId'), requested)

def _search_component(driver, component, skipcheck = False, allowretry = True, id = 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_wtUserComponent_ComponentIdNonMetcon_chosen'):
	container = _click(driver, (By.ID, id))
	searchbox = container.find_element_by_tag_name('input')
	searchbox.clear()
	searchbox.send_keys(component)

	if (skipcheck):
		searchbox.send_keys(Keys.ENTER)
		return True

	try:
		_wait_for_element(driver, (By.CLASS_NAME, 'no-results'), 2)
		searchbox.clear()

		try:
			container.click()
		except:
			pass

		if (component.endswith('s') and allowretry == True):
			return _search_component(driver, component[:-1], skipcheck=False, allowretry=False, id=id)

		return False
	except:
		pass

	try:
		results = _wait_for_element(driver, (By.CLASS_NAME, 'chosen-results'), 2)
		for r in results.find_elements_by_tag_name('li'):
			if (r.text == component):
				r.click()
				return True
	except:
		searchbox.send_keys(Keys.ENTER)
		return True

class MetconMeasure:
	def __init__(self, measure):
		self.type = measure

	def choose(self, driver):
		_select(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_wtComponentEdit_wtWODComponent_ResultTypeId'), self.type)

	def prescribed(self, driver, value):
		if (value):
			_click(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wt214'))

class DistanceMeasure(MetconMeasure):
	def __init__(self, value, unit):
		super().__init__('8')
		self.value = value
		self.unit = unit

	def configure(self, driver, prescribed):
		_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wtPerformanceResult_Distance'), self.value)
		_select(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wtPerformanceResult_DistanceUOM'), self.unit)
		self.prescribed(driver, prescribed)

class TimeMeasure(MetconMeasure):
	def __init__(self, minutes, sec):
		super().__init__('2')
		self.min = minutes
		self.sec = sec

	def configure(self, driver, prescribed):
		_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wtPerformanceResult_Minutes'), self.min)
		_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wtPerformanceResult_Seconds'), self.sec)
		self.prescribed(driver, prescribed)

class RoundsMeasure(MetconMeasure):
	def __init__(self, rounds):
		super().__init__('9')
		self.rounds = rounds

	def configure(self, driver, prescribed):
		_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wtPerformanceResult_Rounds'), self.rounds)
		self.prescribed(driver, prescribed)

class RepsMeasure(MetconMeasure):
	def __init__(self, reps):
		super().__init__('3')
		self.reps = reps

	def configure(self, driver, prescribed):
		_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wtPerformanceResult_Reps'), self.reps)
		self.prescribed(driver, prescribed)

class RoundsAndRepsMeasure(MetconMeasure):
	def __init__(self, rounds, reps):
		super().__init__('4')
		self.rounds = rounds
		self.reps = reps

	def configure(self, driver, prescribed):
		_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wtPerformanceResult_Rounds'), self.rounds)
		_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wtPerformanceResult_Reps'), self.reps)
		self.prescribed(driver, prescribed)

class CaloriesMeasure(MetconMeasure):
	def __init__(self, cals):
		super().__init__('11')
		self.cals = cals

	def configure(self, driver, prescribed):
		_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wtPerformanceResult_Calories'), self.cals)
		self.prescribed(driver, prescribed)

class NoMeasure(MetconMeasure):
	def __init__(self):
		super().__init__('6')

	def configure(self, driver, prescribed):
		pass

def _get_metcon_measure(result:Metcon):
	measure = result.measure
	if (measure == None):
		return NoMeasure()

	t = measure.get('type')
	if (t == 'distance'):
		return DistanceMeasure(measure.get('value'), str(int(measure.get('unit'))))

	if (t == 'time'):
		return TimeMeasure(measure.get('min'), measure.get('sec'))

	if (t == 'cal'):
		return CaloriesMeasure(measure.get('value'))

	if (t == 'rounds'):
		return RoundsMeasure(measure.get('value'))

	if (t == 'reps'):
		return RepsMeasure(measure.get('value'))

	if (t == 'rounds_and_reps'):
		return RoundsAndRepsMeasure(measure.get('rounds'), measure.get('reps'))

	return NoMeasure()

def _add_metcon(result:Metcon, driver):
	metconComponentId = 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_wtUserComponent_ComponentIdMetcon_chosen'

	_goto_addperformance(driver)
	_choose_type(driver, '2')

	measure = _get_metcon_measure(result)

	benchmark = result.benchmark
	if (benchmark):
		benchmark = _search_component(driver, result.name, id=metconComponentId, allowretry=False)

	if (benchmark == False):
		_search_component(driver, 'Non-Benchmark Metcon', id=metconComponentId, skipcheck=True)
		_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_wtComponentEdit_wtWODComponent_Description'), result.name)
		measure.choose(driver)
		_click(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_wtComponentEdit_wt72'))
	else:
		_click(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_wtAddButton'))

	_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_W_Utils_UI_wtDatepicker_block_wtDateInputFrom'), result.date).send_keys(Keys.ESCAPE)

	measure.configure(driver, result.prescribed)

	if (result.notes != None and len(result.notes) > 0):
		_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wtPerformanceResult_Comment'), result.notes)
	
	_click(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wt200'))

	driver.refresh()
	return True

def _add_gymnastics(result: Gymnastics, driver):
	_goto_addperformance(driver)
	_choose_type(driver, '1')

	if (_search_component(driver, result.name) == False):
		_add_metcon(Metcon(
			date=result.date, \
			name=result.name, \
			measure=None, \
			prescribed=True, \
			notes=result.notes, \
			benchmark=False), driver)
		return False

	_click(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_wtAddButton'))
	_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_W_Utils_UI_wtDatepicker_block_wtDateInputFrom'), result.date).send_keys(Keys.ESCAPE)
	_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wtUserComponent_MeasureRepScheme'), result.name)
	_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wtPerformanceResult_Sets'), result.sets)
	_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wtPerformanceResult_Reps'), result.reps)

	if (result.prescribed):
		_click(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wt214'))

	if (result.notes != None and len(result.notes) > 0):
		_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wtPerformanceResult_Comment'), result.notes)
	
	_click(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wt200'))

	driver.refresh()
	return True

def _add_weightlifting(result: Weighlifting, driver):
	_goto_addperformance(driver)
	_choose_type(driver, '5')

	if (_search_component(driver, result.name) == False):
		_add_metcon(Metcon(
			date=result.date, \
			name=result.name, \
			measure=None, \
			prescribed=True, \
			notes=result.notes, \
			benchmark=False), driver)
		return False

	_click(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_wtAddButton'))
	_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_W_Utils_UI_wtDatepicker_block_wtDateInputFrom'), result.date).send_keys(Keys.ESCAPE)
	_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wtUserComponent_MeasureRepScheme'), result.name)
	_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wtPerformanceResult_Sets'), result.sets)
	_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wtPerformanceResult_Reps'), result.reps)
	_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wtPerformanceResult_Weight'), result.weight)

	if (result.notes != None and len(result.notes) > 0):
		_send_keys(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wtPerformanceResult_Comment'), result.notes)
	
	_click(driver, (By.ID, 'AthleteTheme_wt1_block_wtMainContent_WOD_UI_wt2_block_Performance_UI_wtPerformanceResultEdit_block_wt200'))

	driver.refresh()
	return True

def _add_with_retry(result, driver, retry: int, handler):
	for attempt in range(retry - 1):
		try:
			handler(result, driver)
			return
		except:
			if (attempt > 0 and isinstance(result, Metcon) and result.benchmark == True):
				result = result._replace(benchmark=False)
			driver.refresh()
	handler(result, driver)

def _notify(workout, kind, index, onimport:Callable[[str], None] = None, onresumetokenupdated:Callable[[str], None] = None):
	if (onimport != None):
		onimport(f'[{workout.date}] {workout.name}')

	if (onresumetokenupdated != None):
		onresumetokenupdated(f'{kind}:{index + 1}')

def _write_resume_token(file: str, token: str):
	if (token == None):
		if (os.path.exists(file)):
			os.remove(file)
	else:
		with open(file, 'w+', encoding='utf8', newline=None) as f:
			f.write(token)

class WodifyDriver:
	@staticmethod
	def _import_gymnastics(result: Gymnastics, driver, retry):
		_add_with_retry(result, driver, retry, _add_gymnastics)

	@staticmethod
	def import_gymnastics(results: List[Gymnastics], driver = None, username = None, password = None, start_at: int = 0, retry: int = 5, onimport:Callable[[str], None] = None, onresumetokenupdated:Callable[[str], None] = None):
		(driver, destroy) = _ensure_driver(driver, username, password)
		try:
			for index,result in enumerate(results[start_at:], start=start_at):
				WodifyDriver._import_gymnastics(result, driver, retry)
				_notify(result, 'gymnastics', index, onimport, onresumetokenupdated)
		finally:
			_cleanup(driver, destroy)

	@staticmethod
	def _import_weightlifting(result: Weighlifting, driver, retry):
		_add_with_retry(result, driver, retry, _add_weightlifting)

	@staticmethod
	def import_weightlifting(results: List[Weighlifting], driver = None, username = None, password = None, start_at: int = 0, retry: int = 5, onimport:Callable[[str], None] = None, onresumetokenupdated:Callable[[str], None] = None):
		(driver, destroy) = _ensure_driver(driver, username, password)
		try:
			for index,result in enumerate(results[start_at:], start=start_at):
				WodifyDriver._import_weightlifting(result, driver, retry)
				_notify(result, 'weightlifting', index, onimport, onresumetokenupdated)
		finally:
			_cleanup(driver, destroy)

	@staticmethod
	def _import_metcon(result: Metcon, driver, retry):
		_add_with_retry(result, driver, retry, _add_metcon)

	@staticmethod
	def import_metcon(results: List[Metcon], driver = None, username = None, password = None, start_at: int = 0, retry: int = 5, onimport:Callable[[str], None] = None, onresumetokenupdated:Callable[[str], None] = None):
		(driver, destroy) = _ensure_driver(driver, username, password)
		try:
			for index,result in enumerate(results[start_at:], start=start_at):
				WodifyDriver._import_metcon(result, driver, retry)
				_notify(result, 'metcon', index, onimport, onresumetokenupdated)
		finally:
			_cleanup(driver, destroy)

	@staticmethod
	def import_all(results: WorkoutResults, driver = None, username = None, password = None, resumetoken: str = None, retry: int = 5, onimport:Callable[[str], None] = None, onresumetokenupdated:Callable[[str], None] = None):
		(driver, destroy) = _ensure_driver(driver, username, password)
		(kind,index) = resumetoken.split(':') if resumetoken != None and len(resumetoken) > 0 else (None, 0)
		try:
			if (kind == None or kind == 'gymnastics'):
				WodifyDriver.import_gymnastics(results.gymnastics, driver=driver, start_at=int(index), retry=retry, onimport=onimport, onresumetokenupdated=onresumetokenupdated)
				kind = None
				index = 0

			if (kind == None or kind == 'weightlifting'):
				WodifyDriver.import_weightlifting(results.weightlifting, driver=driver, start_at=int(index), retry=retry, onimport=onimport, onresumetokenupdated=onresumetokenupdated)
				kind = None
				inded = 0

			if (kind == None or kind == 'metcon'):
				WodifyDriver.import_metcon(results.metcons, driver=driver, start_at=int(index), retry=retry, onimport=onimport, onresumetokenupdated=onresumetokenupdated)

			if (onresumetokenupdated != None):
				onresumetokenupdated(None)
		finally:
			_cleanup(driver, destroy)

	@staticmethod
	def load_resume_token(file: str):
		if (os.path.exists(file)):
			with open(file, 'r', encoding='utf8', newline=None) as f:
				return f.read()
		return None

	@staticmethod
	def track_resume_token(file: str) -> Callable[[str], None]:
		return lambda token: _write_resume_token(file, token)

