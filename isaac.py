from __future__ import division
import os
import json

courses, targets = [], []

def initialize_courses():
	path = "Carleton Data - Past Terms"
	for term in os.listdir(path):
		markdown = open(path + "\\" + term).read()
		for course in json.loads(markdown)["course_info"]:
			try:
				# Since we're predicting on multiple variables in the same matrix,
				# we'll want to make sure that all of our courses have all of said variables
				is_valid = is_valid_course(course)
				
				lab_in_title = "Lab" in course["title"]
				is_music = course["department"] == "MUSC"
				six_credits = course["credits"][0] == "6"
				is_lab = lab_in_title and not is_music and not six_credits
				
				if is_valid and not is_lab:
					courses.append(course)
			except:
				pass
	targets.extend([float(course["registered"]) / float(course["size"]) for course in courses])

def is_valid_course(course):
	for field in ["summary", "start_time", "end_time", "department", "requirements_met", "registered", "size"]:
		try:
			if course[field] == "n/a":
				return False
		except:
			return False
	return float(course["size"]) > 0

def departments():
	pass

def main():
	
	initialize_courses()

	print "Number of courses:", len(courses)
	print "Number of courses filled to capacity:", len([t for t in targets if t >= 1])
	print "Average enrollment (allowing targets greater than 1):", sum(targets) / len(targets)
	print "Average enrollment (capping targets at 1):", sum([t if t < 1 else 1 for t in targets]) / len(targets)
	
	departments()
	
main()