import os

path = "Carleton Data - Past Terms"
for term in os.listdir(path):
	markdown = open(path + "\\" + term).read()
	print markdown