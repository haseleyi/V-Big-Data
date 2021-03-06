from __future__ import division
from sklearn import linear_model, metrics
from sklearn.naive_bayes import BernoulliNB, GaussianNB
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.feature_selection import SelectFromModel
from sklearn.neural_network import MLPRegressor
from sklearn import linear_model
from sklearn import svm
from collections import defaultdict
from afinn import Afinn
import os
import json
import numpy as np
import math
import random

courses, targets, departments, distros, starts, profs, titles, durations = [], [], [], [], [], [], [], []
dep_map, distro_map, start_map, prof_map, title_map, duration_map, dep_to_enroll, profs_to_ratings  = {}, {}, {}, {}, {}, {}, {}, {}


def prediction_variables_present(course):
    for field in ["summary", "start_time", "end_time", "department", "requirements_met", 
                  "registered", "size", "faculty", "title"]:
        try:
            if course[field] == "n/a":
                return False
        except:
            return False
    return float(course["size"]) > 0


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


def initialize_data():
    
    # Read in data from Enroll
    path = "Carleton Data - Past Terms"
    for term in os.listdir(path):
        markdown = open(path + "\\" + term).read()
        for course in json.loads(markdown)["course_info"]:
            
            # Exclude courses that aren't appropriate for analysis
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
    
    # Read in data from RateMyProfessors
    markdown = open("RatingsData.json").read()
    for prof in json.loads(markdown)["ratings"]:
        first = prof["teacherfirstname_t"]
        last = prof["teacherlastname_t"]
        rating = prof["averageratingscore_rf"]
        num_ratings = prof["total_number_of_ratings_i"]
        profs.append((first, last, rating, num_ratings))
    profs.sort(key = lambda prof : prof[3])
    profs.sort(key = lambda prof : prof[2])


def analyze():

    print "\n===== Initial analysis =====\n"
    print "Number of courses:", len(courses)
    print "Number of courses filled to capacity:", len([t for t in targets if t >= 1])
    print "Average enrollment (allowing targets greater than 1):", sum(targets) / len(targets), "\n\n"

    # Construct department data structures
    department_set = {course["department"] for course in courses}
    departments.extend(sorted(department_set))
    for i, dep in enumerate(departments):
        dep_map[dep] = i

    # Analyze average course enrollment rate by department
    enrollment_by_dep = []
    for dep in departments:
        dep_targets = [targets[i] for i, course in enumerate(courses) if course["department"] == dep]
        enrollment_by_dep.append((dep, sum(dep_targets) / len(dep_targets)))
    enrollment_by_dep.sort(key = lambda x : x[1], reverse = True)
    print "===== Average Course Enrollment by Department =====\n"
    for dep, enroll_rate in enrollment_by_dep:
        dep_to_enroll[dep] = enroll_rate
        print dep, round(enroll_rate, 3),
    print "\n\n"

    # Construct distro data structures
    distro_set = set()
    for course in courses:
        for distro in course["requirements_met"].split("\n"):
            if distro:
                distro_set.add(distro)
    distros.extend(sorted(distro_set))
    for i, distro in enumerate(distros):
        distro_map[distro] = i

    # Analyze average course enrollment rate by distro
    enrollment_by_distro = []
    for distro in distros:
        distro_targets = [targets[i] for i, course in enumerate(courses) if distro in course["requirements_met"].split("\n")]
        enrollment_by_distro.append((distro, sum(distro_targets) / len(distro_targets)))
    enrollment_by_distro.sort(key = lambda x : x[1], reverse = True)
    print "===== Average Course Enrollment by Distro =====\n"
    for distro, enroll_rate in enrollment_by_distro:
        print distro, round(enroll_rate, 3),
    print "\n\n"
    
    # Construct start time data structures
    start_set = {time_string_to_float(course["start_time"]) for course in courses}
    starts.extend(start_set)
    for i, start in enumerate(starts):
        start_map[start] = i

    # Analyze average course enrollment rate by start time
    enrollment_by_start = []
    for start in starts:
      start_targets = [targets[i] for i, course in enumerate(courses) if start == time_string_to_float(course["start_time"])]
      enrollment_by_start.append((start, sum(start_targets) / len(start_targets)))
    enrollment_by_start.sort(key = lambda x : x[0], reverse = True)
    print "===== Average Course Enrollment by Start (hours after 8am : enrollment) =====\n"
    for start, enroll_rate in enrollment_by_start:
      print start, round(enroll_rate, 3)
    print "\n\n"

    # Construct prof data structures
    for course in courses:
        for prof in profs:
            if prof[0] in course["faculty"] and prof[1] in course["faculty"]:
                # Enroll name : (rating, number of ratings, department)
                profs_to_ratings[course["faculty"]] = (prof[2], prof[3], course["department"])
    profs_to_targets = {}
    for prof in profs_to_ratings.keys():
        prof_targets = [targets[i] for i, course in enumerate(courses) if course["faculty"] == prof]
        profs_to_targets[prof] = sum(prof_targets) / len(prof_targets)
    prof_set = {course["faculty"] for course in courses}
    for i, prof in enumerate(list(prof_set)):
        prof_map[prof] = i

    # Find average enrollments of highest-rated profs
    golden_prof_targets = []
    prof_items = profs_to_ratings.items()
    prof_items.sort()
    prof_items.sort(key = lambda prof : prof[1][1], reverse = True)
    prof_items.sort(key = lambda prof : prof[1][0], reverse = True)
    print "===== Enrollment for Highest-Rated Professors =====\n"
    for prof in prof_items:
        # Find profs with rating > 4.7 and number of ratings > 4
        if prof[1][0] > 4.7 and prof[1][1] > 4 and len(prof[0].split(",")) == 1:
            # Print department, Enroll name, rating, number of ratings, average enrollment
            print prof[1][2], prof[0][1:], prof[1][0], prof[1][1], profs_to_targets[prof[0]]
            golden_prof_targets.append(profs_to_targets[prof[0]])
    print sum(golden_prof_targets) / len(golden_prof_targets)
    print "\n\n"

    # Construct course data structures
    title_set = {course["title"] for course in courses}
    titles.extend(sorted(title_set))
    for i, title in enumerate(titles):
        title_map[title] = i

    # Find most-enrolled course by department
    enrollment_by_title = defaultdict(list)
    for title in titles:
        title_targets = []
        department = ""
        for i, course in enumerate(courses):
            if course["title"] == title:
                title_targets.append(targets[i])
                department = course["department"]
        enrollment_by_title[department].append((title, sum(title_targets) / len(title_targets)))
    print "===== Most-Enrolled Course by Department =====\n"
    for pair in enrollment_by_title.items():
        most_popular = pair[1]
        most_popular.sort(key = lambda x : x[1], reverse = True)
        print pair[0], most_popular[0]
    print "\n"

    # Construct course duration data structures
    duration_set = {round(time_string_to_float(course["end_time"]) - time_string_to_float(course["start_time"]), 2) for course in courses}
    durations = sorted(duration_set)
    for i, duration in enumerate(durations):
        duration_map[duration] = i

    # Analyze enrollment by course duration
    enrollment_by_duration = []
    for dur in durations:
        dur_targets = []
        for i, course in enumerate(courses):
            if round(time_string_to_float(course["end_time"]) - time_string_to_float(course["start_time"]), 2) == dur:
                dur_targets.append(targets[i])
        enrollment_by_duration.append((dur, sum(dur_targets) / len(dur_targets)))
    enrollment_by_duration.sort(key = lambda x : x[0], reverse = True)
    print "===== Average Course Enrollment by Course Duration (hours : enrollment) =====\n"
    for dur, enroll_rate in enrollment_by_duration:
        print dur, round(enroll_rate, 3)
    print "\n"

    # Analyze course description sentiment
    afinn = Afinn()
    sentiment_to_targets = defaultdict(list)
    upper_bounds = [-.025, -.02, -.015, -.01, -.005, 0, .005, .01, .015, .02, .025, .03]
    for i, course in enumerate(courses):
        sentiment = afinn.score(course["summary"]) / len(course["summary"])
        for bound in upper_bounds:
            if sentiment < bound:
                sentiment_to_targets[bound].append(targets[i])
                break
    print "===== Average Enrollment by Description Sentiment (upper bound : # courses : enrollment) =====\n"
    for item in sorted(sentiment_to_targets.items()):
        print item[0], len(item[1]), sum(item[1]) / len(item[1])
    print "\nMost course descriptions feature a slightly positive sentiment. No observable enrollment pattern.\n\n"

    # Analyze course description length
    lengths_to_targets = defaultdict(list)
    upper_bounds = [50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400]
    for i, course in enumerate(courses):
        l = len(course["summary"])
        for bound in upper_bounds:
            if l < bound:
                lengths_to_targets[bound].append(targets[i])
                if bound < 150:
                    print course["department"], course["title"]
                break
    print "===== Average Enrollment by Description Length (upper bound : # courses : enrollment) =====\n"
    for item in sorted(lengths_to_targets.items()):
        print item[0], len(item[1]), sum(item[1]) / len(item[1])
    print "\n"

    # Analyze key words in course descriptions
    words_to_targets = defaultdict(list)
    key_words = ["sex", "gender", "collab", "internet", "food", "introduction", "asia", "europe", "africa", "middle east", "america", "advanced", "essay", "assignment", "science", "novel", "non-fiction", "data", "love", "democracy", "project", "team"]
    # key_words = ["extra time"]
    for word in key_words:
        for i, course in enumerate(courses):
            if word in course["summary"].lower():
                words_to_targets[word].append(targets[i])
                # print course["department"], course["title"]
    print "===== Average Enrollment by Description Key Word (word : # descriptions : enrollment) =====\n"
    word_target_items = words_to_targets.items()
    word_target_items.sort(key = lambda x : sum(x[1]) / len(x[1]), reverse = True)
    for item in word_target_items:
        print item[0], len(item[1]), sum(item[1]) / len(item[1])
    print "\n"

def test_model(matrix, model):

    test_errors = []

    # Ten iterations of 80/20 cross-validation
    for _ in range(10):
    
        # Randomly partition about 80% of the data for training and the remaining for testing
        training_matrix, training_targets, test_matrix, test_targets = [], [], [], []
        for i in range(len(targets)):
            if random.random() < .8:
                training_matrix.append(matrix[i])
                training_targets.append(targets[i])
            else:
                test_matrix.append(matrix[i])
                test_targets.append(targets[i])

        # Train and predict on test data
        model.fit(training_matrix, training_targets)
        test_predictions = model.predict(test_matrix)
        test_errors.append(metrics.mean_absolute_error(test_targets, test_predictions))
    
    print "Minimum mean error over ten models:", min(test_errors), "\n\n"


def predict():

    # Construct training matrix
    matrix = np.zeros((len(courses), 11))
    for i, course in enumerate(courses):
        
        # Column 0: Department classification
        # Single-var random tree absolute error: .190
        matrix[i][0] = dep_map[course["department"]] 
        
        # Columns 1 - 4: Possible distros
        # Single-var random tree absolute error: .217
        course_distros = course["requirements_met"].split("\n")
        course_distros = filter(lambda distro : distro, course_distros)
        for j, distro in enumerate(course_distros):
            matrix[i][1 + j] = distro_map[distro] 

        # Column 5: Start time
        # Single-var random tree absolute error: .214
        matrix[i][5] = start_map[time_string_to_float(course["start_time"])] 

        # Columns 6 and 7: RateMyProfessors data
        try:
            prof = profs_to_ratings[course["faculty"]]
            matrix[i][6] = prof[0] # Single-var linreg error: .224
            matrix[i][7] = prof[1] # Single-var linreg error: .232
        except:
            pass

        # Column 8: Course title
        # Single-var random tree absolute error: .183
        matrix[i][8] = title_map[course["title"]]

        # Column 9: Course duration
        # Single-var linreg error: .231
        matrix[i][9] = round(time_string_to_float(course["end_time"]) - time_string_to_float(course["start_time"]), 2) 

        # Column 10: Professor
        # Single-var random tree absolute error: .184
        matrix[i][10] = prof_map[course["faculty"]]

    # Standardize the data: center columns at 0 and divide by variance
    for i in range(len(matrix[0])):
        column = np.array(matrix)[:, i]
        column_mean = sum(column) / len(column)
        column_std = np.std(column)
        for j in range(len(matrix)):
            matrix[j][i] -= column_mean
            matrix[j][i] /= column_std

    print "===== Random Forest Regressor Results =====\n"
    test_model(matrix, RandomForestRegressor(n_estimators = 50, oob_score = True))

    print "===== Multilayer Perceptron Results =====\n"
    test_model(matrix, MLPRegressor(hidden_layer_sizes=(100, 10)))

    print "===== Support Vector Machine Results =====\n"
    test_model(matrix, svm.SVR())

    test_model(matrix, linear_model.LinearRegression())

def main():
    
    initialize_data()
    analyze()
    predict()
    
main()

'''
************************* MODEL *************************

Low priority: Try a different error function of (mean squared error) * P(t) <- For P(t), make histogram of t's and normalize, take value at t bucket


************************* START TIMES *************************

Low priority:

Options for start time: 
    Try keeping everything
    Try excluding courses at odd times and see if model improves
    Try bucketting into "before __", "after __"

Results:
    Everything as floats: .1937
    Only normal times as floats: more

'''

# Current best mean error: .1562, from random tree regressor