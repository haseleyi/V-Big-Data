from __future__ import division
from sklearn import linear_model, metrics
from sklearn.naive_bayes import BernoulliNB, GaussianNB
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.feature_selection import SelectFromModel
import os
import json
import numpy as np
import math

courses, targets, departments, distros, starts = [], [], [], [], []

def initialize_courses():
	path = "Carleton Data - Past Terms"
	for term in os.listdir(path):
		markdown = open(path + "\\" + term).read()
		for course in json.loads(markdown)["course_info"]:
			try:
				# Since we're predicting on multiple variables in the same matrix,
				# we'll want to make sure that all of our courses have all of said variables
				has_components = prediction_variables_present(course)

				is_ai = "Argument & Inquiry Seminar" in course["requirements_met"].split("\n")
				is_pe = course["department"] == "PE"
				
				lab_in_title = "Lab" in course["title"]
				is_music = course["department"] == "MUSC"
				six_credits = course["credits"][0] == "6"
				is_lab = lab_in_title and not is_music and not six_credits
				
				if has_components and not is_lab and not is_ai and not is_pe:
					courses.append(course)
			except:
				pass
	targets.extend([float(course["registered"]) / float(course["size"]) for course in courses])


def prediction_variables_present(course):
	for field in ["summary", "start_time", "end_time", "department", "requirements_met", "registered", "size"]:
		try:
			if course[field] == "n/a":
				return False
		except:
			return False
	return float(course["size"]) > 0


def analyze():

	print "\n===== Initial analysis =====\n"
	print "Number of courses:", len(courses)
	print "Number of courses filled to capacity:", len([t for t in targets if t >= 1])
	print "Average enrollment (allowing targets greater than 1):", sum(targets) / len(targets), "\n\n"

	# Construct sorted list of departments
	department_set = set()
	for course in courses:
		if course["department"] not in department_set:
			department_set.add(course["department"])
	departments.extend(sorted(department_set))

	# Analyze average course enrollment rate by department
	enrollment_by_dep = []
	for dep in departments:
		dep_targets = [targets[i] for i, course in enumerate(courses) if course["department"] == dep]
		enrollment_by_dep.append((dep, sum(dep_targets) / len(dep_targets)))
	enrollment_by_dep.sort(key=lambda x : x[1], reverse=True)
	print "===== Average Course Enrollment by Department =====\n"
	for dep, enroll_rate in enrollment_by_dep:
		print dep, round(enroll_rate, 3),
	print "\n\n"

	# Construct sorted list of distros
	distro_set = set()
	for course in courses:
		for distro in course["requirements_met"].split("\n"):
			if distro:
				distro_set.add(distro)
	distros.extend(sorted(distro_set))

	# Analyze average course enrollment rate by distro
	enrollment_by_distro = []
	for distro in distros:
		distro_targets = [targets[i] for i, course in enumerate(courses) if distro in course["requirements_met"].split("\n")]
		enrollment_by_distro.append((distro, sum(distro_targets) / len(distro_targets)))
	enrollment_by_distro.sort(key=lambda x : x[1], reverse=True)
	print "===== Average Course Enrollment by Distro =====\n"
	for distro, enroll_rate in enrollment_by_distro:
		print distro, round(enroll_rate, 3),
	print "\n\n"

	# Input is a course's start time as a string
	# Returns number of hours past 8am in decimal format
	def time_string_to_float(time):
		time_list = time.split(":")
		hour = int(time_list[0])
		minute = round(float(time_list[1][:2]) / 60, 3)
		ampm = time_list[1][-2:]
		if ampm == "am" or hour == 12:
			hour -= 8
		elif ampm == "pm":
			hour += 4
		return float(str(hour) + str(minute)[1:])
	
	start_set = {time_string_to_float(course["start_time"]) for course in courses}
	starts.extend(start_set)

	normal_academic_times = {"8:30am", "9:50am", "11:10am", "12:30pm", "1:50pm", "3:10pm", "8:15am", "10:10am", "1:15pm"}
	for course in courses:
		if course["start_time"] not in normal_academic_times:
			print course["department"], course["title"], course["start_time"]

	# Analyze average course enrollment rate by start time
	enrollment_by_start = []
	for start in starts:
		start_targets = [targets[i] for i, course in enumerate(courses) if start == time_string_to_float(course["start_time"])]
		enrollment_by_start.append((start, sum(start_targets) / len(start_targets)))
	enrollment_by_start.sort(key=lambda x : x[0], reverse=True)
	print "===== Average Course Enrollment by Start =====\n"
	for start, enroll_rate in enrollment_by_start:
		print start, round(enroll_rate, 3)
	print "\n\n"


def predict():

	# Construct map for each variable
	dep_nums = {dep : i + 1 for i, dep in enumerate(departments)}
	distro_nums = {distro : i + 1 for i, distro in enumerate(distros)}

	# Construct training matrix
	matrix = np.zeros((len(courses), 5))
	for i, course in enumerate(courses):
		
		# One column for department classification
		matrix[i][0] = dep_nums[course["department"]]
		
		# Four columns for possible distros
		course_distros = course["requirements_met"].split("\n")
		course_distros = filter(lambda distro : distro, course_distros)
		for j, distro in enumerate(course_distros):
			matrix[i][1 + j] = distro_nums[distro]

	# Standardize the data
	# ...(to do once there are more variables involved)
	# center data at 0 and divide by variance (standardization)

	# Create and train random forest classifier
	rfr = RandomForestRegressor(n_estimators = 200, oob_score = True)
	predictions_same_data = rfr.fit(matrix, np.array(targets).ravel()).predict(matrix)

	print "===== RandomForestRegressor Results =====\n"
	print "Mean error:", math.sqrt(metrics.mean_squared_error(targets, predictions_same_data)), "\n"
	

def main():
	
	initialize_courses()
	analyze()
	predict()
	
main()

'''
=== V BIG DATA ===
Get multiple variables into a prediction matrix by Thursday so you can ask Ulf about the shaping error
Put in how many course spots?
Try a different error function of (mean squared error) * P(t) <- For P(t), make histogram of t's and normalize, take value at t bucket

random forest (could overfit on floats)
support vector machine (svm) -> center data at 0 and divide by variance (standardization) (prefers floats)
multi-layer perceptron (mlp) (100 hidden states, 10 hidden states -> same deal as forest's n_estimators) (prefers floats)

Try excluding courses at odd times and see if model improves