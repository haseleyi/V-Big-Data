import os
import json

courses_with_labs, courses = [], []
path = "Carleton Data - Past Terms"

for term in os.listdir(path):
	markdown = open(path + "\\" + term).read()
	json_term = json.loads(markdown)
	courses_with_labs.extend([course for course in json_term["course_info"]])

def is_valid_course(course, fields):
	for field in fields:
		try:
			if course[field] == "n/a":
				return False
		except:
			return False
	return True

for course in courses_with_labs:
	
	try:
		# Since we're predicting on multiple variables in the same matrix,
		# we'll want to make sure that all of our courses have all of said variables
		components_desired = ["summary", "start_time", "end_time", "department", "requirements_met"]
		is_valid = is_valid_course(course, components_desired)
		
		lab_in_title = "Lab" in course["title"]
		is_music = course["department"] == "MUSC"
		six_credits = course["credits"][0] == "6"
		is_lab = lab_in_title and not is_music and not six_credits
		
		if is_valid and not is_lab:
			courses.append(course)
	
	except:
		pass

for course in courses:
	print course["term"], course["course_num"], course["title"]