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

async def browseMemes(userDisplayName, messageData, message):
	global userDirs, initialDirs, supportedExtensions, defaultPath

	userID = message.author.id

	if userID not in userDirs:
		initialDirs[userID] = defaultPath  # Replace with your initial directory
		userDirs[userID] = initialDirs[userID]

	currentDir = userDirs[userID]

	if messageData.startswith("/browse"):
		folder = messageData.replace("/browse", "").strip().capitalize()

		if folder == "current" or not folder:
			folders = [f for f in os.listdir(currentDir) if os.path.isdir(os.path.join(currentDir, f))]

			displayDir = currentDir.replace(defaultPath, "..")
			if folders:
				await sendMessage(message, f"**Folders in {displayDir}:**\n" + "\n".join(folders))
			else:
				await sendMessage(message, f"No subfolders in {displayDir}. Type `/browse` to search for media.")
		else:
			newDir = os.path.join(currentDir, folder)
			if os.path.isdir(newDir):
				userDirs[userID] = newDir
				displayDir = newDir.replace(defaultPath, "..")
				await sendMessage(message, f"Changed directory to: {displayDir}")

				subfolders = [f for f in os.listdir(newDir) if os.path.isdir(os.path.join(newDir, f))]
				if subfolders:
					await sendMessage(message, f"**Subfolders in {displayDir}:**\n" + "\n".join(subfolders))
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
						await sendMessage(message, f"Sending random file {randomFile} // {files.index(randomFile)+1} of {len(files)};\n-# *Use `/again` to send another random meme from this directory*")
						await message.channel.send(file=discord.File(os.path.join(newDir, randomFile)))
					else:
						await sendMessage(message, "No images or videos found in this directory.")
			else:
				displayDir = currentDir.replace(defaultPath, "..")
				await sendMessage(message, f"Folder '{folder}' not found in {currentDir}   {newDir}.")

	elif messageData.startswith("/back"):
		if currentDir != initialDirs[userID]:
			parentDir = os.path.dirname(currentDir)
			if parentDir.startswith(initialDirs[userID]):
				userDirs[userID] = parentDir
				await sendMessage(message, f"Moved back to: {parentDir}")

				# List folders in the parent directory
				folders = [f for f in os.listdir(parentDir) if os.path.isdir(os.path.join(parentDir, f))]
				if folders:
					await sendMessage(message, f"**Folders in {parentDir.replace(defaultPath, '..')}:**\n" + "\n".join(folders))
				else:
					await sendMessage(message, f"No subfolders in {parentDir.replace(defaultPath, '..')}.")
			else:
				await sendMessage(message, "Cannot go back past the initial directory.")
		else:
			await sendMessage(message, "You are already in the initial directory. Cannot go back further.")

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

				await sendMessage(message, f"Sending another random file {randomFile} // {files.index(randomFile)+1} of {len(files)};\n-# *Use `/again` to send another random meme from this directory*")
				await message.channel.send(file=discord.File(os.path.join(lastDir, randomFile)))
			else:
				await sendMessage(message, "No images or videos found in the last directory.")
		else:
			await sendMessage(message, "No directory history found. Please browse to a folder first.")