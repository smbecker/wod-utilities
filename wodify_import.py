if __name__ == "__main__":
	import sys
	import json
	from wodify_data import WorkoutResults, Weighlifting, Gymnastics, Metcon
	from wodify_driver import WodifyDriver

	if (len(sys.argv) < 3):
		raise Exception('Must provide username and password')

	jsonpath = 'wodify.json' if (len(sys.argv) <= 3) else sys.argv[2]
	component = 'all' if (len(sys.argv) <= 4) else sys.argv[3]
	with open(jsonpath, 'r', encoding='utf8', newline=None) as f:
		data = json.load(f)

	gymnastics = [Gymnastics(**g) for g in data.get('gymnastics')]
	weightlifting = [Weighlifting(**w) for w in data.get('weightlifting')]
	metcons = [Metcon(**m) for m in data.get('metcons')]
	results = WorkoutResults(gymnastics=gymnastics, weightlifting=weightlifting, metcons=metcons)

	getattr(WodifyDriver, f'import_{component}')(results, username=sys.argv[1], password=sys.argv[2], onimport=lambda name: print(f'Imported {name}'))
