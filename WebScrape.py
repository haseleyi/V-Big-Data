''' Sonia Moreno, 9/2017
 Scrapes data from Carleton Enroll website containing course schedule information.
 '''
from collections import defaultdict
from bs4 import BeautifulSoup
import requests
import re
import csv
import sys
import json

''' Returns list of academic terms that user can choose from. Item in list
will be passed to function that returns html link with term info provided.
Example: 'term=18WI' in 'https://apps.carleton.edu/campus/registrar/schedule/enroll/?term=18WI&subject=CS'
'''
def Academic_Term():
	# Homepage showing listings of academic terms and course subjects
	html_enroll = requests.get('https://apps.carleton.edu/campus/registrar/schedule/enroll/').text
	soup2 = BeautifulSoup(html_enroll, 'html5lib')

	# Tag object containing list of academic terms 
	term_summary = soup2.find("select", id = "termElement")

	# Each term name such as "Winter 2018" has tag "option"
	terms = term_summary.find_all("option")

	# We want the value attribute; example: <option value="18WI">
	# Create list with all value attributes; this will be list of terms available to choose from
	term_list = []
	for option in terms:
		term_list.append(option['value'])
	return term_list


''' Returns list of course subjects. Each will be passed to function that returns
appropriate html link which contains specific course information for the subject
Example: 'subject=CS' in 'https://apps.carleton.edu/campus/registrar/schedule/enroll/?term=18WI&subject=CS'
'''
def Subject(): 
	html_enroll = requests.get('https://apps.carleton.edu/campus/registrar/schedule/enroll/').text
	soup2 = BeautifulSoup(html_enroll, 'html5lib')


	# Tag object containing list of subjects
	subject_summary = soup2.find("select", id = "subjectElement")

	# Each subject within summary has tag "option"
	# Create a list with subjects, excluding 'Selected' tag (1st item)
	subjects = subject_summary.find_all("option")[1:]

	# Only get the associated text, excluding the tag itself and add them to list
	subj_list = []
	for item in subjects:
		subj_list.append(item.get_text())

	# print subj_list

	# Each item in subj_list is currently in the form: 'Computer Science (CS)'
	# We only want the abbrevation in the parentheses so that we can use this in the html link
	# We use regular expressions to achieve this.
	subj_abbrev = []
	for i in subj_list:
		subj_abbrev.append(re.search('\((.*?)\)', i).group(1))

	# print subj_abbrev
		
	return subj_abbrev



''' Returns dict object with course number, course name, and start/end times for each course
Finds course info based on the academic term and subject chosen (in this case, Winter 2018)
'''

def Specific_Course_Info(term):
	# Creates dict object with course number as key and list containing name and times for course as values
	course_info = defaultdict(list)

	subjects = Subject()

	for subject in subjects:
		html_string = 'https://apps.carleton.edu/campus/registrar/schedule/enroll/?term=' + term + '&subject=' + subject

		# Course listings for subject during term provided
		html = requests.get(html_string).text

		soup = BeautifulSoup(html, 'html5lib')

		# Creates list of all items with course as class attribute, excluding related courses
		course_summary = soup.find_all("div", class_="course")
		for course in course_summary:
			course_num = course.find(class_= "coursenum").get_text()
			# Finds title attribute within each course
			title = course.find(class_ = "title").get_text()
			# Only takes the actual name of the course
			# which is next to the coursenum attribute but not within its own tag
			for item in title:
				course_name = course.find(class_= "coursenum").next_sibling	

			# Add info to list associated with key
			specific_info = {}
			# Ensures that no related courses are added
			if course_num.find(subject) > -1:
				specific_info['department'] = subject
				specific_info['term'] = term
				specific_info['course_num'] = course_num
				specific_info['title'] = course_name
				if course.find(class_ = "faculty") != None:
					faculty = course.find(class_ = "faculty").get_text()
					specific_info['faculty'] = faculty
					if course.find(class_ ="faculty").next_sibling != None:
							summary = course.find(class_ = "faculty").next_sibling
							summary = summary.encode("utf-8")
							specific_info['summary'] = summary
					else:
							specific_info['summary'] = "n/a"
				else:
					specific_info['faculty'] = "n/a"
				if course.find(class_ = "status") != None:
					enrollment = course.find(class_ = "status").get_text()
					# specific_info['enrollment'] = enrollment
					registered = re.findall(r'(?<=Registered: ).*?(?=\,)', enrollment)[0]
					size = re.findall(r'(?<=Size: ).*?(?=\,)', enrollment)[0]
					# print registered
					specific_info['registered'] = registered
					specific_info['size'] = size
					# print enrollment
				else:
					specific_info['registered'] = "n/a"
					specific_info['size'] = "n/a"
				if course.find(class_ = "credits") != None:
					credits = course.find(class_ = "credits").get_text()
					specific_info['credits'] = credits
				else:
					specific_info['credits'] = "n/a"
				if course.find(class_ = "codes overlays"):
					requirements = course.find(class_ = "codes overlays").get_text()
					specific_info['requirements_met'] = requirements


				# course_info[0].append({})	
				# Start and end times for courses that have set times
				# Account for classes without set times
				if course.find(class_ = "start") != None:
					start_time = course.find("span", {"class": "start"}).get_text()
					end_time = course.find(class_ = "end").get_text()
					specific_info['start_time'] = start_time
					specific_info['end_time'] = end_time

				else:
					specific_info['start_time'] = "n/a"
					specific_info['end_time'] = "n/a"
					# course_info[0][0].append(start_time)
				course_info['course_info'].append(specific_info)
					# course_info[0][0].append(end_time)
	
	# Creates csv file with course info
	# with open('course_info7.csv', 'w') as f: 
	# 	w = csv.DictWriter(f, course_info.keys())
	# 	w.writeheader()
	# 	w.writerow(course_info)

	# output_file = open('courses_table.csv', 'w')
	# writer = csv.writer(output_file)
	# for course in course_info['course_info']:
	# 	course_row = [course['course_num'].encode("utf-8"), course['title'].encode("utf-8"), course['start_time'].encode("utf-8"), course['end_time'].encode("utf-8")]
	# 	writer.writerow(course_row)
	# output_file.close()
	# print course_info
	filename = 'course_data_' + term + '.json'
	with open(filename, 'w') as fp:
		json.dump(course_info, fp)
	return course_info
# ''' Adds lists together from Specific_Course_Info so that each csv file will contain info 
# for ALL subjects in one term
# ''' 
# def Append_Dicts(a_dict, b_dict):
# 	return


''' Returns HTML string that Specific Course Info will use to provide information
for every term and subject combination.
'''
def Generate_HTML():
	terms = Academic_Term()[1:3]
	subjects = Subject()[1:3]
	html = []
	for term in terms:
		for subject in subjects:
			print term
			print subject
		Specific_Course_Info(term, subject)





