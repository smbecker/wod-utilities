if __name__ == "__main__":
	import sys
	import requests
	from bwtb_data import signin, get_member_id, export_workout_csv

	if (len(sys.argv) < 3):
		raise Exception('Must provide username and password')

	output = 'workouts.csv' if (len(sys.argv) == 3) else sys.argv[3]
	with requests.session() as s:
		signin(sys.argv[1], sys.argv[2], s)
		memberId = get_member_id(s)
		export_workout_csv(memberId, output, s)
		print('Downloaded workouts to', output)
