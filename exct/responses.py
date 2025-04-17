import discord, random, csv, datetime, os
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from exct.shared import sendMessage, replyMessage, getTime

global invalidDates
previousChoices = {}

def showInvalidData():
	global invalidDates
	print(invalidDates)

async def choiceCommand(messageData, message, fileName, imgFile=None):
	return
	global previousChoices

	if fileName not in previousChoices:
		previousChoices[fileName] = []

	if messageData. startswith(f"/{fileName}"):
		with open(f"C:/Users/User/Documents/GitHub/DThree/phrases/{fileName}.txt", "r", encoding="utf-8") as file:
			fileData = file.readlines()
			fileData = [line.strip() for line in fileData]
			if imgFile is not None:
				fileData.append(":img:")

			remainingChoices = [line for line in fileData if line not in previousChoices[fileName]]

			if not remainingChoices:
				previousChoices[fileName] = []
				remainingChoices = fileData

			chosenLine = random.choice(remainingChoices)
			previousChoices[fileName].append(chosenLine)

			if chosenLine != ":img:":
				await replyMessage(message, chosenLine.replace("Â¬", "\n").replace("¬", "\n"), ping=True)
			else:
				await message.reply(file=discord.File(f"imgs/{imgFile}.png"), mention_author=True)




#Stats

def occurrences_updateOccurrences(name, words, filename="data/wordOccurrences.csv"):
	date = datetime.datetime.now().strftime("%Y-%m-%d")

	words = [word.replace("\n", "`").strip().lower() for word in words]

	if os.path.exists(filename):
		df = pd.read_csv(filename)
	else:
		df = pd.DataFrame(columns=["Name", "Word", "Date", "Occurrences"])

	df["Occurrences"] = df["Occurrences"].astype("Int64")

	keyMask = (df["Name"] == name) & (df["Date"] == date)

	updatedRows = []
	for word in words:
		existingRow = df[keyMask & (df["Word"] == word)]
		
		if not existingRow.empty:
			df.loc[existingRow.index, "Occurrences"] += 1
		else:
			updatedRows.append({"Name": name, "Word": word, "Date": date, "Occurrences": 1})

	if updatedRows:
		df = pd.concat([df, pd.DataFrame(updatedRows)], ignore_index=True)

	df.to_csv(filename, index=False)


def occurrences_preprocess_data(filename, userword):
	global invalidDates
	today = datetime.datetime.strptime(datetime.datetime.now().strftime("%d-%m-%Y"), "%d-%m-%Y")
	sept1 = datetime.datetime.strptime("01-09-2024", "%d-%m-%Y")

	data = defaultdict(lambda: defaultdict(dict))

	# Read CSV
	if os.path.exists(filename):
		df = pd.read_csv(filename)
	else:
		return None, None, None

	invalidDates = df[~df["Date"].str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)]
	df = df[df["Date"].str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)]
	df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")
	
	# Filter data for the given word
	df = df[df["Word"] == userword]


	if df.empty:
		return None, None, None

	earliestDate = df["Date"].min()
	latestDate = today

	allDates = pd.date_range(start=sept1, end=today)

	userData = {}
	for name, group in df.groupby("Name"):
		userSeries = group.set_index("Date")["Occurrences"].reindex(allDates, fill_value=np.nan)
		
		if np.isnan(userSeries.iloc[0]):
			userSeries.iloc[0] = 0

		userSeries.interpolate(method="linear", inplace=True)

		userData[name] = userSeries.to_dict()

	return userData, earliestDate, latestDate


async def occurrences_saveGraph(word, message, filename="data/wordOccurrences.csv"):
	today = datetime.datetime.strptime(datetime.datetime.now().strftime("%d-%m-%Y"), "%d-%m-%Y")
	sept1 = datetime.datetime.strptime("01-09-2024", "%d-%m-%Y")
	plt.clf()
	plt.gca().cla()

	#Read and preprocess the data
	data, earliestDate, latestDate = occurrences_preprocess_data(filename, word.strip().replace("\n","`").lower())

	if data is None and earliestDate is None and latestDate is None:
		await sendMessage(message, f"No occurrences of '{word}' found.")
		return

	#Plot each user's data
	for name, entries in data.items():
		dates = [date for date, _ in entries.items()]
		occurrences = list(entries.values())

		plt.plot(dates, occurrences, label=name.replace("__dau__", r"$\_\_dau\_\_$"))

	#Plot settings
	plt.xlabel('Date')
	plt.ylabel('Occurrences')
	plt.title(f'Occurrences of {word} over time, per user')
	plt.legend()

	plt.xlim(left=sept1, right=today)
	plt.ylim(bottom=0)
	plt.gca().yaxis.get_major_locator().set_params(integer=True)
	plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%y'))

	dateRange = latestDate - sept1
	plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=1))

	plt.gcf().autofmt_xdate()
	plt.grid(True, which='both', linestyle='--', linewidth=0.7, color='gray')

	#Save the plot as an image file
	plt.savefig('imgs/graph.png')
	plt.close()

	await sendMessage(message, f"Collating data for {word}")
	await message.channel.send(file=discord.File("imgs/graph.png"))



#Other

def reformatName(name):
	return name.replace("_", "\_")


def reformatNumber(value):
	reformattedNum = ""
	strValue = str(value)
	i, o = 0, 0
	while True:
		i += 1
		reformattedNum += strValue[-i]
		o += 1
		if o % 3 == 0 and i != len(strValue):
			reformattedNum += ","
		if i == len(strValue):
			break

	return reformattedNum[::-1]


async def getTotalWords(message):
	nameData = {}
	nameList = []
	unsortedList = []
	sortedList = []
	totalWords = 0
	
	#Read and aggregate occurrences from the CSV file
	with open('data/wordOccurrences.csv', 'r') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			name = row['Name']
			word = row['Word']
			date = row['Date']
			occurrences = int(row['Occurrences'] if row["Occurrences"] is not None else 0)
			if name in nameData:
				nameData[name] += occurrences
			else:
				nameData[name] = occurrences
			totalWords += occurrences


	for user, occurrences in nameData.items():
		sortedList.append(occurrences)
		unsortedList.append(occurrences)
		nameList.append(user)

	sortedList.sort()


	reformattedTotal = reformatNumber(totalWords)


	formatted = f"# Number of words spoken, per user (Of {reformattedTotal} total);\n"
	for count in sortedList[::-1]:
		index = unsortedList.index(count)
		user = nameList[index]

		counter = "words" if count != 1 else "word"
		percent = round(100 * (count/totalWords), 2)
		if percent < 0.01: continue
		formatted += f"- **{reformatName(user)}:** {reformatNumber(count)} {counter} *({percent}%)*\n"
	formatted += "-# *Calculated based on values in wordOccurrences.csv*"


	await sendMessage(message, formatted)

async def leaderboard(message):
	nameData = {}
	nameList = []
	unsortedList = []
	sortedList = []
	
	#Read and aggregate occurrences from the CSV file
	with open('data/wordOccurrences.csv', 'r') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			name = row['Name']
			word = row['Word']
			date = row['Date']
			occurrences = int(row['Occurrences'] if row["Occurrences"] is not None else 0)
			if name in nameData:
				nameData[name] += occurrences
			else:
				nameData[name] = occurrences


	for user, occurrences in nameData.items():
		sortedList.append(occurrences)
		unsortedList.append(occurrences)
		nameList.append(user)

	sortedList.sort()

	formatted = "# Top 5 most messages sent;\n"
	for i in range(5):
		index = i+1
		if i >= len(sortedList): break
		highestNumber = sortedList[-index]
		highestIndex = unsortedList.index(highestNumber)
		highestUser = nameList[highestIndex]
		th = "th" if index > 3 else "rd" if index == 3 else "nd" if index == 2 else "st" if index == 1 else "Nil"
		counter = "word" if highestNumber == 1 else "words"
		formatted += f"{index}{th} Place; ***{reformatName(highestUser)},*** *with {reformatNumber(highestNumber)} {counter}.*\n"
	formatted += "-# *Calculated based on values in wordOccurrences.csv*"


	await sendMessage(message, formatted)




#FISH

def fish_updateOccurrences(name, filename):
	date = datetime.datetime.now().strftime("%Y-%m-%d")
	#Read the CSV file into a dictionary
	data = defaultdict(lambda: defaultdict(int))

	try:
		with open('data/fish.csv', 'r') as csvfile:
			reader = csv.DictReader(csvfile)
			for row in reader:
				current_name = row['Name']
				current_date = row['Date']
				occurrences = int(row['Occurrences'] if row["Occurrences"] is not None else 0)
				data[current_name][current_date] = occurrences
	except FileNotFoundError:
		pass  #If the file doesn't exist, start with an empty dataset

	#Update the occurrences for the given name and date
	data[name][date] += 1

	#Write the updated data back to the CSV file
	with open(f'data/fish.csv', 'w', newline='') as csvfile:
		writer = csv.writer(csvfile)
		writer.writerow(["Name", "Date", "Occurrences"])
		for current_name, dates in data.items():
			for current_date, occurrences in dates.items():
				writer.writerow([current_name, current_date, occurrences])


def fish_preprocess_data(filename):
	today = datetime.datetime.strptime(datetime.datetime.now().strftime("%d-%m-%Y"), "%d-%m-%Y")
	sept1 = datetime.datetime.strptime("01-09-2024", "%d-%m-%Y")
	#Read the CSV file into a dictionary
	data = defaultdict(list)

	with open("data/fish.csv", 'r') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			name = row['Name']
			date = row['Date']
			occurrences = int(row['Occurrences'] if row["Occurrences"] is not None else 0)
			data[name].append((date, occurrences))

	#Initialize variables to find the earliest and latest date
	earliest_date = datetime.datetime.strptime("01-09-2024", "%d-%m-%Y")
	latest_date = max(datetime.datetime.strptime(row['Date'], "%Y-%m-%d") for row in csv.DictReader(open("data/fish.csv")))

	#Generate a complete list of all dates between the earliest and latest date
	all_dates = pd.date_range(start=sept1, end=today).strftime("%Y-%m-%d")

	#Ensure all names have an entry for every date in the range with occurrences set to 0 if missing
	for name in data:
		existing_dates = set(date for date, _ in data[name])
		for date in all_dates:
			if date not in existing_dates:
				data[name].append((date, 0))
		#Sort by date after filling in missing dates
		data[name].sort(key=lambda x: datetime.datetime.strptime(x[0], "%Y-%m-%d"))

	return data, earliest_date, latest_date

def fish_saveGraph(filename):
	today = datetime.datetime.strptime(datetime.datetime.now().strftime("%d-%m-%Y"), "%d-%m-%Y")
	plt.clf()
	plt.gca().cla()

	#Read and preprocess the data
	data, earliest_date, latest_date = fish_preprocess_data(filename)

	#Plot each user's data
	for name, entries in data.items():
		dates = [datetime.datetime.strptime(date, "%Y-%m-%d") for date, _ in entries]
		occurrences = [occ for _, occ in entries]
		plt.plot(dates, occurrences, marker='o', label=name)

	#Plot settings
	plt.xlabel('Date')
	plt.ylabel('Occurrences')
	plt.title('Fish occurrences over time, per user')
	plt.legend()

	sept1 = datetime.datetime.strptime("01-09-2024", "%d-%m-%Y")

	plt.xlim(left=sept1, right=today)
	plt.ylim(bottom=0)
	plt.gca().xaxis.set_major_locator(mdates.MonthLocator(interval=1))
	plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

	#Set x-axis intervals based on the range of dates
	date_range = latest_date - earliest_date
	plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=7))

	plt.gcf().autofmt_xdate()
	plt.grid(True, which='both', linestyle='--', linewidth=0.7, color='gray')

	#Save the plot as an image file
	plt.savefig('imgs/graph.png')
	plt.close()






#main
async def checkReplies(messageData, message):

	if messageData.startswith("/count "):
		word = messageData.split(" ")[1]
		await occurrences_saveGraph(word, message)
		return

	elif messageData.startswith("/counttotal"):
		await getTotalWords(message)

	elif messageData.startswith("/countall"):
		await leaderboard(message)

	else:
		occurrences_updateOccurrences(str(message.author), messageData.split(" "))


	if (str(message.author) == "tornadoteammrt") and ("mid" in messageData):
		await replyMessage(message, "apathy moment", ping=True)

	if messageData.startswith("/ecom"):
		await replyMessage(message, "hah, typo", ping=True)
	return


	#Reply to command messages
	with open("C:/Users/User/Documents/GitHub/DThree/cmds.txt", "r") as cmdFile:
		commands = cmdFile.readlines()
	for cmd in commands:
		if cmd == "vibe":
			if messageData.startswith("/vibe list"):
				with open(f"C:/Users/User/Documents/GitHub/DThree/phrases/vibe.txt", "r", encoding="utf-8") as file:
					fileData = file.readlines()
					vibeList = ''.join(["- "+vibe.split("¬")[0]+"\n" for vibe in fileData])
					await replyMessage(message, vibeList, ping=True)
				continue
		await choiceCommand(messageData, message, cmd.strip().lower())


	
	specialEmojis = (":heart_hands:", "😘", "❤️")
	specialText = ("love you, hun", "[hug]", "have a nice day!")
	emojiMessage = message.content.strip().lower()
	if ("🫶" in emojiMessage) or ("😘" in emojiMessage) or ("❤️" in emojiMessage) or ("�" in emojiMessage):
		await replyMessage(message, f"{random.choice(specialEmojis)}\n*{random.choice(specialText)}*", ping=True)


	if messageData.startswith("/dthree") or messageData.startswith("/d3"):
		await replyMessage(message, "Beep Boop.")
		return




	if messageData.startswith("/echo"):
		await sendMessage(message, message.content.replace("/echo ", ""))
		return

	fishes = []
	with open(r"C:/Users/User/Documents/GitHub/DThree/phrases/fish.txt", "r") as fishFile:
		rawFishes = fishFile.readlines()
		for fish in rawFishes:
			if fish != "":
				fishes.append(fish.strip().lower())

	skippedWords = ["code", "coding","salmonella","/pescagrafi",]



	if any([fishType in messageData for fishType in fishes]):
		if not any([skipWord in messageData for skipWord in skippedWords]):
			fish_updateOccurrences(str(message.author), "fish")

			with open("C:/Users/User/Documents/GitHub/DThree/phrases/fishLanguages.txt", encoding="utf-8") as fishFile: fishChoices = fishFile.readlines()
			await replyMessage(message, random.choice(fishChoices).upper().strip(), ping=True)
			

	elif (messageData.startswith("/pescagrafi")) or (messageData.startswith("/pescagraphy")):
		"""
		with open("exct/fishCount", "r") as fishFile:
			await sendMessage(message, f"There have been {int(fishFile.readlines()[0].strip())} fish since [15:08, 02/09/24].")
		"""
		fish_saveGraph("fish")
		await replyMessage(message, "Collating data;\nFish occurrences over time, per user")
		await message.channel.send(file=discord.File("imgs/graph.png"))


	elif ("america" in messageData):
		await sendMessage(message, "RAHHH AMERICA MENTIONED :flag_us: :flag_us: :flag_us: :eagle: :eagle:")
	elif ("murica" in messageData):
		await sendMessage(message, "RAHHH 'MURICA MENTIONED :flag_us: :flag_us: :flag_us: :eagle: :eagle:")
	elif ("canada" in messageData):
		await sendMessage(message, "Eh?")
	elif ("england" in messageData) or ("britain" in messageData):
		await sendMessage(message, "innit")
	elif ("budget" in messageData):
		await sendMessage(message, "fr")

