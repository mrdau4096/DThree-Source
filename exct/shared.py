import discord, datetime, os, subprocess
from dateutil.relativedelta import relativedelta



def getTime(dateOnly: bool=False) -> str:
	"""
	Gets current date/time, returns as a nicely formatted string. [HH:MM:SS, YYYY-MM-DD] formatting.
	"""
	FULL_TIME = str(datetime.datetime.now())
	UNFORMATTED_DATE, TIME = FULL_TIME[:10], FULL_TIME[11:-7]
	DATE = f"{UNFORMATTED_DATE[8:]}-{UNFORMATTED_DATE[5:7]}-{UNFORMATTED_DATE[:4]}"
	return f"{TIME}, {DATE}" if not dateOnly else DATE



def timeSinceStr(dateStr: str, onlyDate: bool=False) -> str:
	"""
	Takes [YYYY-MM-DD HH:MM:SS] format.
	Returns a proper sentence version denoting time since input.
	"""
	then = datetime.datetime.strptime(dateStr, "%Y-%m-%d %H:%M:%S")
	now = datetime.datetime.now()
	delta = relativedelta(now, then)
	parts = []
	if delta.years:
		parts.append(f"{delta.years} year{'s' if delta.years != 1 else ''}")
	if delta.months:
		parts.append(f"{delta.months} month{'s' if delta.months != 1 else ''}")
	if delta.days:
		parts.append(f"{delta.days} day{'s' if delta.days != 1 else ''}")
	if delta.hours and not onlyDate:
		parts.append(f"{delta.hours} hour{'s' if delta.hours != 1 else ''}")
	if delta.minutes and not onlyDate:
		parts.append(f"{delta.minutes} minute{'s' if delta.minutes != 1 else ''}")
	if delta.seconds and not onlyDate and not parts:
		parts.append(f"{delta.seconds} second{'s' if delta.seconds != 1 else ''}")

	return ', '.join(parts[:-1]) + (' and ' if len(parts) > 1 else '') + parts[-1] + ' ago' if parts else 'Undetermined'


def secondsSince(dateStr: str) -> int:
	"""
	Returns integer number of seconds since a given date.
	"""
	then = datetime.datetime.strptime(dateStr, "%Y-%m-%d %H:%M:%S")
	now = datetime.datetime.now()
	return int((now - then).total_seconds())



def formatNumber(num: int|float, seperator: str=",", delimiter: str=".") -> str:
	"""
	Formats a number, for econ.py
	The seperator lies between every set of 3 digits.
	The delimiter lies between the units and tenths (1 and 0.1 places.)
	"""
	formatted = ""
	if isinstance(num, float):
		formatted = f"{num:,.2f}"
	else:
		formatted = f"{num:,}"

	return formatted.replace(",", "__TMP__").replace(".", delimiter).replace("__TMP__", seperator)



async def sendMessage(message: discord.Message, messageText: str) -> None:
	with open("/project/src/disk/data/log.txt", "a", encoding="utf-8") as logFile:
		if "*An error occurred;*" not in messageText:
			logFile.write("\n" + f"{getTime()} // {message.guild} // SEND {message.author} // {messageText}".replace('\n', ';'))

	await message.channel.send(messageText)



async def replyMessage(message: discord.Message, messageText: str, ping: bool=True) -> None:
	"""
	Replies to a given discord.Message instance with text and optional mention [ping].
	Also logs this in log.txt.
	"""
	if messageText == "":
		#Cannot send zero-length messages.
		return

	with open("/project/src/disk/data/log.txt", "a", encoding="utf-8") as logFile:
		if "*An error occurred;*" not in messageText:
			logFile.write("\n" + f"{getTime()} // {message.guild} // REPLY {message.author} // {messageText.strip()}")

	await message.reply(messageText, mention_author=ping)



async def updateRepo(message: discord.Message|None=None) -> None:
	"""
	Updates the textfiles from [https://github.com/mrdau4096/DThree-Files].
	This is called every time DThree is deployed, and also whenever "/updaterepo" is called.
	If called via "/updaterepo", it sends a reply to that message for confirmation.
	Otherwise prints confirmation to console.
	"""
	os.chdir("/opt/render/project/src/textFiles")
	subprocess.run(["git", "fetch", "--all"])  #Fetch all branches
	subprocess.run(["git", "reset", "--hard", "origin/main"])  #Reset local branch
	subprocess.run(["git", "pull", "origin", "main"])  #Pull changes
	
	if message is not None:
		await replyMessage(message, "Files are now up to date.", ping=True)
	else:
		print("Files are now up to date.")



def backupData() -> None:
	"""
	Pushes datafiles to external backup repo
	"""
	dataDir = "/project/src/disk/data"
	github_token = os.getenv("GITHUB_TOKEN")
	repo_url = f"https://{github_token}@github.com/mrdau4096/DThree-Data-Backups.git"

	if not os.path.exists(os.path.join(dataDir, ".git")): #Ensure folder is a valid git repo location
		subprocess.run(["git", "init"], cwd=dataDir)
		subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=dataDir)

	subprocess.run(["git", "config", "user.email", "d3@render.com"], cwd=dataDir)
	subprocess.run(["git", "config", "user.name", "DThree"], cwd=dataDir)

	subprocess.run(["git", "add", "."], cwd=dataDir)
	subprocess.run(["git", "commit", "-m", f"{datetime.datetime.now()}"], cwd=dataDir)
	subprocess.run(["git", "branch", "-M", "main"], cwd=dataDir)
	subprocess.run(["git", "push", "-u", "origin", "main"], cwd=dataDir)



def pullData() -> None:
	"""
	Pulls datafiles from external backup repo.
	"""
	dataDir = "/project/src/disk/data"
	github_token = os.getenv("GITHUB_TOKEN")
	repo_url = f"https://{github_token}@github.com/mrdau4096/DThree-Data-Backups.git"

	if not os.path.exists(os.path.join(dataDir, ".git")): #Ensure folder is a valid git repo location
		subprocess.run(["git", "init"], cwd=dataDir)
		subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=dataDir)

	else:
		subprocess.run(["git", "fetch", "origin", "main"], cwd=dataDir)
		subprocess.run(["git", "reset", "--hard", "origin/main"], cwd=dataDir)



def removeNonASCII(text: str) -> str:
	"""
	Removes all non-ASCII characters from a string.
	"""
	return ''.join(char for char in text if ord(char) < 128)



async def sendMessageInChannel(client: discord.Client, text: str, guild: str, channel: str) -> None:
	"""
	Sends message in a given channel without the need for a parent discord.Message instance.
	Useful for echo, when not called via a text channel command.
	"""
	guildList = dict([(g.name, g) for g in client.guilds])
	guild = guildList[guild]

	if guild is not None:
		channelList = dict([(ch.name, ch) for ch in guild.text_channels])
		channel = list(channelList.values())[channel]

		if channel is not None:
			await channel.send(text)
		else:
			raise ValueError("Invalid Channel")

	else:
		raise ValueError("Invalid Guild")