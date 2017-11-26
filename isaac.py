from __future__ import division
from sklearn import linear_model, metrics
from sklearn.naive_bayes import BernoulliNB, GaussianNB
import os
import json
import numpy as np

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


def learn_departments():
	
	# Construct sorted list of departments
	department_set = set()
	for course in courses:
		if course["department"] not in department_set:
			department_set.add(course["department"])
	departments = sorted(department_set)

	# Analysis: Average course enrollment rate by department
	enrollment_by_dep = []
	for dep in departments:
		dep_targets = [targets[i] for i, course in enumerate(courses) if course["department"] == dep]
		enrollment_by_dep.append((dep, sum(dep_targets) / len(dep_targets)))
	enrollment_by_dep.sort(key=lambda x : x[1], reverse=True)
	print "===== Average Course Enrollment by Department =====\n"
	for dep, enroll_rate in enrollment_by_dep:
		print dep, round(enroll_rate, 3),
	print "\n\n"

	# Construct 1D course-department matrix
	dep_nums = {dep : i for i, dep in enumerate(departments)}
	matrix = np.array([dep_nums[course["department"]] for course in courses]).reshape(-1, 1)

	# Train and predict
	model = linear_model.LinearRegression()
	predictions_same_data = model.fit(matrix, targets).predict(matrix)
	
	# These models both produce "Unknown label type" ValueErrors.
	# I think certain models can only work with certain input, e.g. Bern is 0 or 1.
	# I think Naive Bayes is actually the one we'd want if predicting on just departments.
	# While regression tries to fit a line to the average enrollment rates, I think 
	# Naive Bayes would assume independence between departments and just use those averages.
	# model = GaussianNB()
	# model = BernoulliNB() 
	
	# Analyze predictions
	print "===== Regressing on Departments =====\n"
	print "Mean squared error:", metrics.mean_squared_error(targets, predictions_same_data), "\n"
	for i, course in enumerate(courses):
		print course["term"], course["title"], targets[i], predictions_same_data[i]

def main():
	
	initialize_courses()

	print "\n===== Initial Analysis =====\n"
	print "Number of courses:", len(courses)
	print "Number of courses filled to capacity:", len([t for t in targets if t >= 1])
	print "Average enrollment (allowing targets greater than 1):", sum(targets) / len(targets), "\n\n"
	
	learn_departments()
	
main()