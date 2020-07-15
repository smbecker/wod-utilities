if __name__ == "__main__":
	import sys
	import json
	from bwtb_data import parse_workout_csv
	from wodify_data import WorkoutResults

	csvpath = 'workouts.csv' if (len(sys.argv) <= 1) else sys.argv[1]
	outpath = 'wodify.json' if (len(sys.argv) <= 2) else sys.argv[2]
	output=WorkoutResults.from_bwtb(parse_workout_csv(csvpath))._asdict()
	with open(outpath, 'w+', encoding='utf8', newline=None) as f:
		json.dump(output, f, indent=4)
