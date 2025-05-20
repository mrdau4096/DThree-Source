import discord, random, csv, datetime, os
from collections import defaultdict
import matplotlib
matplotlib.use("Agg") #Matplotlib config. Writes to file rather than attempting to render onscreen.
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from cycler import cycler
import pandas as pd
import numpy as np
from exct.shared import sendMessage, replyMessage, getTime, timeSinceStr, secondsSince


global invalidDates
previousChoices = {}



def showInvalidData() -> None:
	"""
	Debug for showing invalid results in the CSV files or otherwise.
	"""
	global invalidDates
	print(invalidDates)



async def choiceCommand(messageData: str, message: discord.Message, fileName: str, imgFile: str|None=None) -> bool:
	"""
	Used for handling commands such as "/dau" or "/howitzer".
	If an image name is given, then it can randomly send an image of matching name.
	Draws from [https://github.com/mrdau4096/DThree-Files].
	"""
	global previousChoices

	if fileName not in previousChoices:
		previousChoices[fileName] = [] #Attempts to send a unique line each time.

	if messageData.startswith(f"/{fileName}"):
		with open(f"/opt/render/project/src/textFiles/phrases/{fileName}.txt", "r", encoding="utf-8") as file:
			fileData = file.readlines()
			fileData = [line.strip() for line in fileData]
			if imgFile is not None:
				fileData.append(":img:")

			remainingChoices = [line for line in fileData if line not in previousChoices[fileName]]

			if not remainingChoices:
				#If all lines have been called, revert back to using whole list.
				previousChoices[fileName] = []
				remainingChoices = fileData

			chosenLine = random.choice(remainingChoices)
			previousChoices[fileName].append(chosenLine)

			if chosenLine == ":img:":
				#Reply with imagefile.
				await message.reply(file=discord.File(f"imgs/{imgFile}.png"), mention_author=True)
				with open("/project/src/disk/data/log.txt", "a", encoding="utf-8") as logFile:
					#Manually log occurrence due to lack of use of shared.replyMessage()
					logFile.write("\n" + f"{shared.getTime()} // {message.guild} // REPLY-IMAGE {message.author} // {imgFile}.png".replace('\n', ';'))
			else:
				await replyMessage(message, chosenLine.replace("Â¬", "\n").replace("¬", "\n"), ping=True)
				"""
				"¬" is used to mark a newline in the text files.
				"Â¬" occasionally occurs when files are read via the wrong format; this too is accounted for as a newline.
				"""

			#Found a valid result for the given command.
			return True

	#Did not find any results for this command.
	return False




#Stats [/count]

def occurrencesUpdOccurrences(name: str, words: list[str], filename: str="/project/src/disk/data/wordOccurrences.csv") -> None:
	"""
	Updates the counts in wordOccurrences.csv (or another provided file) for each word in a message.
	Utilises Pandas to speed up data processing.
	Words are organised by person, date, word and stores the number of times relevant to other data.
	"""
	date = datetime.datetime.now().strftime("%Y-%m-%d")

	words = [word.replace("\n", "`").strip().lower() for word in words]

	if os.path.exists(filename):
		#Read contents of file.
		df = pd.read_csv(filename)
	else:
		#If the file does not exist; create it.
		df = pd.DataFrame(columns=["Name", "Word", "Date", "Occurrences"])

	#Clean data
	df["Name"] = df["Name"].astype(str).str.strip().str.lower()
	df["Word"] = df["Word"].astype(str).str.strip().str.lower()
	df["Date"] = df["Date"].astype(str).str.strip()
	name = name.strip().lower()
	date = datetime.datetime.now().strftime("%Y-%m-%d")
	words = [word.strip().lower().replace("\n", "`") for word in words]

	df["Occurrences"] = df["Occurrences"].astype("Int64")

	keyMask = (df["Name"] == name) & (df["Date"] == date)

	updatedRows = []
	for word in words:
		if word == "": continue
		existingRow = df[keyMask & (df["Word"] == word)]
		
		if not existingRow.empty:
			df.loc[existingRow.index, "Occurrences"] += 1
		else:
			updatedRows.append({"Name": name, "Word": word, "Date": date, "Occurrences": 1})

	if updatedRows:
		df = pd.concat([df, pd.DataFrame(updatedRows)], ignore_index=True)

	df = df.groupby(["Name", "Word", "Date"], as_index=False).agg({"Occurrences": "sum"})
	df.to_csv(filename, index=False)



def occurrencesPreProcessing(filename: str, userword: str) -> tuple[dict[str, dict[datetime.datetime, float]]|None, datetime.datetime|None, datetime.datetime|None]:
	"""
	Pre-processes data to be drawn to the graph.
	userword is the word to search entries for.
	Entries are grouped by name, and then dates and number of times.
	"""
	global invalidDates
	today = datetime.datetime.strptime(datetime.datetime.now().strftime("%d-%m-%Y"), "%d-%m-%Y")
	sept1 = datetime.datetime.strptime("01-09-2024", "%d-%m-%Y") #Data was first recorded on 01/09/2024

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
		daily_occurrences = group.groupby("Date")["Occurrences"].sum()
		userSeries = daily_occurrences.reindex(allDates, fill_value=np.nan)
		
		if np.isnan(userSeries.iloc[0]):
			userSeries.iloc[0] = 0

		userSeries.interpolate(method="linear", inplace=True) #Linearly interpolate data between points if no data exists.

		userData[name] = userSeries.to_dict()
		#name is the user's account name (i.e. "__dau__" or "worldofrice")
		#userSeries.to_dict() is a dictionary of dates, and number of times on that date.

	return userData, earliestDate, latestDate



async def occurrencesSaveGraph(word: str, message: discord.Message, filename: str="/project/src/disk/data/wordOccurrences.csv") -> None:
	"""
	Creates the graph to be shown to the user, then sends it.
	Uses occurrencesPreProcessing() to organise data by name, then by date to get number of times.
	"""
	today = datetime.datetime.strptime(datetime.datetime.now().strftime("%d-%m-%Y"), "%d-%m-%Y")
	sept1 = datetime.datetime.strptime("01-09-2024", "%d-%m-%Y") #Data was first recorded on 01/09/2024
	plt.clf()
	plt.gca().cla()


	nameColours = {
		"__dau__": "#b22225",
		"tornadoteam_the_t": "#860897",
		"themightyhowitzer": "#117b66",
		"hamez_boi": "#c27c0e",
		"randomuser78": "#72b0db",
		"shabbles": "#63d4b2",
		"boogie152": "#f1f0a1",
		"meltedpuddingwx": "#526b77",
		"ultrawolk": "#3498db",
		"worldofrice": "#0239eb",
		"brtrainfan46": "#ffffff",
		"dalt7744": "#f1f0a1",
		"howitzertwo587": "#f1f0a1",
		"duckson1124": "#ffffff",
	}


	#Read and preprocess the data
	data, earliestDate, latestDate = occurrencesPreProcessing(
		filename,
		word.strip().replace("\n","`").lower()
	)

	if data is None and earliestDate is None and latestDate is None:
		#Pre-processing could not find any relevant data for any user.
		await sendMessage(message, f'No occurrences of "{word}" found.')
		return



	fig, ax = plt.subplots(
		figsize=(10, 6), dpi=150,
		facecolor="#1a1a1e"
	)
	ax.set_facecolor("#1a1a1e")



	for name, series in data.items():
		dates = list(series.keys())
		counts = list(series.values())
		if name in nameColours:
			colour = nameColours[name]
		else:
			colour = "#FF00FF"

		ax.plot(dates, counts, label=reformatName(name, mpl=True), color=colour)


	ax.set_title(f'Occurrences of "{word}"', color="white")
	ax.set_xlabel("Date", color="white")
	ax.set_ylabel("Occurrences", color="white")
	ax.tick_params(colors="white")


	ax.legend(loc="upper right", facecolor="#1a1a1e", edgecolor="white", labelcolor="white")


	ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%y"))
	ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
	#Dates are displayed on the X-Axis in 1 month intervals.
	#As time progresses, this may need to be increased or adapted - too many dates will show with enough time passing.
	ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
	fig.autofmt_xdate()


	ax.grid(True, linestyle="--", linewidth=0.5, color="gray")

	# Save
	fig.savefig(
		"/project/src/disk/data/graph.png",
		facecolor=fig.get_facecolor(),
		transparent=False
	)
	plt.close(fig)


	await sendMessage(message, f'Collating data for "{word}"')
	await message.channel.send(file=discord.File("/project/src/disk/data/graph.png"))
	#If multiple people request a graph simultaneously; it gets overwritten. Consider fixing.



#Other

def reformatName(name: str, mpl: bool=False) -> str:
	r"""
	Another hacky fix for my username (dau -> __dau__ -> \_\_dau\_\_)
	The underscores cause issues with discord formatting.
	Used in showTotalWords() and showLeaderboard().
	"""
	reformatted = name.replace("_", "\_")
	if mpl:
		reformatted = f"${reformatted}$"
	return reformatted


def reformatNumber(value: int) -> str:
	"""
	Takes an integer value and re-formats it to fit the standard in showTotalWords() and showLeaderboard().
	1000000 -> "1,000,000"
	"""
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


async def showTotalWords(message: str) -> None:
	"""
	Called via /counttotal.
	Shows an ordered list from highest word count to lowest, along with a percentage.
	"""
	nameData = {}
	nameList = []
	unsortedList = []
	sortedList = []
	totalWords = 0
	
	#Read and aggregate occurrences from the CSV file
	with open('/project/src/disk/data/wordOccurrences.csv', 'r') as csvfile:
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

async def showLeaderboard(message: str) -> None:
	"""
	Called via /countall
	Shows the top 5 people with most words.
	"""
	nameData = {}
	nameList = []
	unsortedList = []
	sortedList = []
	
	#Also read and aggregate occurrences from the CSV file
	with open('/project/src/disk/data/wordOccurrences.csv', 'r') as csvfile:
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





#Main reply functions.
async def checkReplies(messageData: str, message: discord.Message) -> None:
	"""
	Checks for any relevant commands to respond to.
	Handles /count related and various older responses (such as author=tornadoteam_the_t -> Reply "mid")

	"""

	if messageData.startswith("/count "):
		word = messageData.split(" ")[1]
		await occurrencesSaveGraph(word, message)
		return

	elif messageData.startswith("/counttotal"):
		await showTotalWords(message)
		return

	elif messageData.startswith("/countall"):
		await showLeaderboard(message)
		return

	else:
		#If none of the above, then record message's words in the csv.
		occurrencesUpdOccurrences(str(message.author), messageData.split(" "))



	if (str(message.author) == "tornadoteam_the_t") and ("mid" in messageData):
		#Old joke response. Replies to Česko with "mid".
		await replyMessage(message, "apathy moment", ping=True)
		return

	if messageData.startswith("/ecom"):
		#Old joke response. "corrects" people's typo.
		await replyMessage(message, "hah, typo", ping=True)
		return


	if messageData.startswith("/serverage"):
		#Command to show length of time users have been on the server.
		#Shown in order from longest to shortest times.
		nameDates = {
			"Dau": "2023-10-18 18:46:00",
			"TornadoTeam": "2023-10-18 17:13:00",
			"Howitzer": "2023-10-18 18:33:00",
			"Ace": "2023-10-18 18:33:00",
			"RandomUser78": "2023-10-18 18:43:00",
			"Shabbles": "2023-10-18 20:53:00",
			"Boogie152": "2024-07-05 12:47:00",
			"MeltedWX": "2023-10-22 20:24:00", #MeltedWX has never interacted with DThree.
			"UltrawolK": "2023-10-23 19:19:00", #Ultrawolk has never interacted when DThree was online.
			"DThree": "2024-09-01 00:09:00", #DThree itself is also recorded. For science.
			"Gitty": "2025-05-07 13:21:00", #Consider updating every time Gitty re-appears.
		}

		timesList = []
		for name, date in nameDates.items():
			timesList.append((name, secondsSince(date)))

		timesList.sort(key=lambda x: x[1], reverse=True) #Organise in descending order.

		finalMessage = "# Time spent on the server:\n```"
		for name, _ in timesList:
			finalMessage += f"\n- {name}:{' '*(12-len(name))} Joined [{nameDates[name][:-3]}], Which was {timeSinceStr(nameDates[name])}."
		finalMessage += "\n```"

		await replyMessage(message, finalMessage, ping=True)
		return



	#Reply to command messages such as "/seapower"
	commands = None
	with open("/opt/render/project/src/textFiles/cmds.txt", "r") as cmdFile:
		commands = [cmd.strip().lower() for cmd in cmdFile.readlines()]
	for cmd in commands:
		if cmd == "vibe":
			if messageData.startswith("/vibe list"):
				with open(f"/opt/render/project/src/textFiles/phrases/vibe.txt", "r", encoding="utf-8") as file:
					fileData = file.readlines()
					vibeList = ''.join(["- "+vibe.split("¬")[0]+"\n" for vibe in fileData])
					await replyMessage(message, vibeList, ping=True)
				break
		validResult = await choiceCommand(messageData, message, cmd.strip().lower())
		if validResult: #End reply checking if resuult found.
			return


	
	#Replies to certain emojis with 
	emojisToLookFor = ("🫶", "😘", "❤️", "�")
	specialEmojis = (":heart_hands:", "😘", "❤️")
	specialText = ("love you, hun", "[hug]", "have a nice day!")
	emojiMessage = message.content.strip().lower()
	if any(emoji in emojiMessage for emoji in emojisToLookFor):
		await replyMessage(message, f"{random.choice(specialEmojis)}\n*{random.choice(specialText)}*", ping=True)
		return


	#Old joke response.
	if messageData.startswith("/dthree") or messageData.startswith("/d3"):
		await replyMessage(message, "Beep Boop.")
		return


	#Old command carried over from terminal; replies with message contents.
	if messageData.startswith("/echo"):
		await sendMessage(message, message.content.replace("/echo ", ""))
		return



	#Temporarily removed due to annoyance
	#This has been missing for a notable amount of time; consider removing this and other similar commands
	"""
	if ("america" in messageData):
		await sendMessage(message, "RAHHH AMERICA MENTIONED :flag_us: :flag_us: :flag_us: :eagle: :eagle:")
	elif ("murica" in messageData):
		await sendMessage(message, "RAHHH 'MURICA MENTIONED :flag_us: :flag_us: :flag_us: :eagle: :eagle:")
	"""
	if ("canada" in messageData):
		await sendMessage(message, "Eh?")
	elif ("england" in messageData) or ("britain" in messageData):
		await sendMessage(message, "innit")
	elif ("budget" in messageData):
		await sendMessage(message, "fr")
	elif ("denmark" in messageData) or ("dane" in messageData):
		await sendMessage(message, "DANSKJÄVLAR")

	if messageData.startswith(("massive","huge","hard","long","big","large","gargantuan")):
		await sendMessage(message, "That's what she said")

		if messageData.startswith("/arm"):
			await sendMessage("armed")
			kill = False

	if messageData.startswith("boom"):
		await sendMessage(message, "10")
		await sendMessage(message, "9")
		await sendMessage(message, "8")
		await sendMessage(message, "7")
		await sendMessage(message, "6")
		await sendMessage(message, "5")
		await sendMessage(message, "4")
		await sendMessage(message, "3")
		await sendMessage(message, "2")
		await sendMessage(message, "1")
		while kill == False:
			await sendMessage(message, "explosion")

	if messageData.startswith("kill"):
		kill = True


