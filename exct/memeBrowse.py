import discord, random, os
from discord.ext import commands
from exct.shared import sendMessage, replyMessage

userDirs = {}
initialDirs = {}
prevFiles = {}
defaultPath = r"/project/src/disk"
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
		# Initialize user with a base directory
		initialDirs[userID] = defaultPath  # Replace with your initial directory
		userDirs[userID] = initialDirs[userID]

	currentDir = userDirs[userID]

	if messageData.startswith("/browse"):
		folder = messageData.replace("/browse", "").strip()

		if folder == "current" or not folder:
			# List folders in the current directory
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

				# Check for subfolders
				subfolders = [f for f in os.listdir(newDir) if os.path.isdir(os.path.join(newDir, f))]
				if subfolders:
					await sendMessage(message, f"**Subfolders in {displayDir}:**\n" + "\n".join(subfolders))
				else:
					# If no subfolders, pick a random file
					files = [f for f in os.listdir(newDir) if f.lower().endswith(supportedExtensions)]
					if files:
						if message.author not in prevFiles:
							prevFiles[message.author] = []

						randomFile = random.choice(files)

						#Loop to ensure the selected file hasn't been chosen before
						while randomFile in prevFiles[message.author]:
							if len(prevFiles[message.author]) == len(files):
								# If all files have been used, reset the list and break
								prevFiles[message.author] = []
								break
							randomFile = random.choice(files)
						userDirs[userID] = newDir  # Store the directory where the file was selected
						await sendMessage(message, f"Sending random file {randomFile} // {files.index(randomFile)+1} of {len(files)};\n-# *Use `/again` to send another random meme from this directory*")
						await message.channel.send(file=discord.File(os.path.join(newDir, randomFile)))
					else:
						await sendMessage(message, "No images or videos found in this directory.")
			else:
				displayDir = currentDir.replace(defaultPath, "..")
				await sendMessage(message, f"Folder '{folder}' not found in {displayDir}.")

	elif messageData.startswith("/back"):
		# Prevent going back past the initial directory
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
		# Send another random file from the last used directory
		if userID in userDirs:
			lastDir = userDirs[userID]
			files = [f for f in os.listdir(lastDir) if f.lower().endswith(supportedExtensions)]
			if files:
				if message.author not in prevFiles:
					prevFiles[message.author] = []

				randomFile = random.choice(files)

				# Loop to ensure the selected file hasn't been chosen before
				while randomFile in prevFiles[message.author]:
					if len(prevFiles[message.author]) == len(files):
						# If all files have been used, reset the list and break
						prevFiles[message.author] = []
						break
					randomFile = random.choice(files)

				# Append the selected file to the user's previous file list
				prevFiles[message.author].append(randomFile)

				await sendMessage(message, f"Sending another random file {randomFile} // {files.index(randomFile)+1} of {len(files)};\n-# *Use `/again` to send another random meme from this directory*")
				await message.channel.send(file=discord.File(os.path.join(lastDir, randomFile)))
			else:
				await sendMessage(message, "No images or videos found in the last directory.")
		else:
			await sendMessage(message, "No directory history found. Please browse to a folder first.")