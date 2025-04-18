import discord, random, os
from discord.ext import commands
from exct.shared import sendMessage, replyMessage

userDirs = {}
initialDirs = {}
prevFiles = {}
defaultPath = r"/project/src/disk/Discmemes"
supportedExtensions = (
	".png",
	".jpg",
	".jpeg",
	".gif",
	".mp4",
	".mp3",
	".mov",
	".avi",
	".webm",
	".webp"
)
commonMistakes = {
	"Edit": "Edits",
	"Game": "Games",
	"Misc": "Miscellaneous", "Miscelaneous": "Miscellaneous",
	"Titanfall": "TitanFall", "Titan fall": "TitanFall", "Titan": "TitanFall",
	"Valve": "VALVe",
	"War thunder": "War Thunder", "Wt": "War Thunder",
	"Half life": "Half Life", "Hl": "Half Life",
	"Left 4 dead": "Left 4 Dead", "L4d": "Left 4 Dead",
	"Other or mixed": "Other OR Mixed", "Mixed": "Other OR Mixed",
	"Tf2": "Team Fort the Second", "Team fortress 2": "Team Fort the Second", "Team Fortress": "Team Fort the Second",
	"Hl1 or bm": "HL1 OR BM", "Half life 1": "HL1 OR BM", "Black mesa": "HL1 OR BM",
	"Hl2": "HL2", "Half life 2": "HL2",
	"Virtual end": "In the Virtual End", "In the virtual end": "In the Virtual End", "Virtual": "In the Virtual End",
	"History or combat": "History OR Combat", "History": "History OR Combat", "Combat": "History OR Combat",
}

async def browseMemes(userDisplayName, messageData, message):
	global userDirs, initialDirs, supportedExtensions, defaultPath

	userID = message.author.id

	if userID not in userDirs:
		initialDirs[userID] = defaultPath
		userDirs[userID] = initialDirs[userID]

	currentDir = userDirs[userID]

	if messageData.startswith("/commonMistakes"):
		reply = "Frequent mistakes and their corrections:\n"
		for key, data in commonMistakes.items():
			if (key.lower()) == (data.lower()): continue
			reply += f"{key} -> {data}\n"
		replyMessage(message, reply)

	elif messageData.startswith("/browse"):
		folder = message.content.replace("/browse", "").strip().lower().capitalize()
		if folder in list(commonMistakes.keys()):
			folder = commonMistakes[folder]

		if folder == "current" or not folder:
			folders = [f for f in os.listdir(currentDir) if os.path.isdir(os.path.join(currentDir, f))]

			displayDir = currentDir.replace(defaultPath, "..")
			if folders:
				await replyMessage(message, f"**Folders in {displayDir}:**\n" + "\n".join(folders))
			else:
				await replyMessage(message, f"No subfolders in {displayDir}. Type `/browse` to search for media.")
		else:
			newDir = os.path.join(currentDir, folder)
			if os.path.isdir(newDir):
				userDirs[userID] = newDir
				displayDir = newDir.replace(defaultPath, "..")
				await replyMessage(message, f"Changed directory to: {displayDir}")

				subfolders = [f for f in os.listdir(newDir) if os.path.isdir(os.path.join(newDir, f))]
				if subfolders:
					await replyMessage(message, f"**Subfolders in {displayDir}:**\n" + "\n".join(subfolders))
				else:
					files = [f for f in os.listdir(newDir) if f.lower().endswith(supportedExtensions)]
					if files:
						if message.author not in prevFiles:
							prevFiles[message.author] = []

						randomFile = random.choice(files)

						while randomFile in prevFiles[message.author]:
							if len(prevFiles[message.author]) == len(files):
								prevFiles[message.author] = []
								break
							randomFile = random.choice(files)
						userDirs[userID] = newDir
						await replyMessage(message, f"Sending random file {randomFile} // {files.index(randomFile)+1} of {len(files)};\n-# *Use `/again` to send another random meme from this directory*")
						await message.channel.send(file=discord.File(os.path.join(newDir, randomFile)))
					else:
						await replyMessage(message, "No images or videos found in this directory.")
			else:
				displayDir = currentDir.replace(defaultPath, "..")
				await replyMessage(message, f"Folder '{folder}' not found in {displayDir}.")

	elif messageData.startswith("/back"):
		if currentDir != initialDirs[userID]:
			parentDir = os.path.dirname(currentDir)
			if parentDir.startswith(initialDirs[userID]):
				userDirs[userID] = parentDir
				await replyMessage(message, f"Moved back to: {parentDir}")

				# List folders in the parent directory
				folders = [f for f in os.listdir(parentDir) if os.path.isdir(os.path.join(parentDir, f))]
				if folders:
					await replyMessage(message, f"**Folders in {parentDir.replace(defaultPath, '..')}:**\n" + "\n".join(folders))
				else:
					await replyMessage(message, f"No subfolders in {parentDir.replace(defaultPath, '..')}.")
			else:
				await replyMessage(message, "Cannot go back past the initial directory.")
		else:
			await replyMessage(message, "You are already in the initial directory. Cannot go back further.")

	elif messageData.startswith("/again"):
		if userID in userDirs:
			lastDir = userDirs[userID]
			files = [f for f in os.listdir(lastDir) if f.lower().endswith(supportedExtensions)]
			if files:
				if message.author not in prevFiles:
					prevFiles[message.author] = []

				randomFile = random.choice(files)

				while randomFile in prevFiles[message.author]:
					if len(prevFiles[message.author]) == len(files):
						prevFiles[message.author] = []
						break
					randomFile = random.choice(files)

				prevFiles[message.author].append(randomFile)

				await replyMessage(message, f"Sending another random file {randomFile} // {files.index(randomFile)+1} of {len(files)};\n-# *Use `/again` to send another random meme from this directory*")
				await message.channel.send(file=discord.File(os.path.join(lastDir, randomFile)))
			else:
				await replyMessage(message, "No images or videos found in the last directory.")
		else:
			await replyMessage(message, "No directory history found. Please browse to a folder first.")