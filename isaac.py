import os
import json

courses = []

path = "Carleton Data - Past Terms"
for term in os.listdir(path):
	markdown = open(path + "\\" + term).read()
	json_term = json.loads(markdown)
	courses.extend([course for course in json_term["course_info"]])