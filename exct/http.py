from fastapi import Depends, HTTPException, Header, status, APIRouter
from exct.shared import sendMessage, replyMessage, updateRepo, backupData, channelDict
from games.economy import writeCSV, createFakeCompany, forceUnBusyFunc, grantMoney
import os, discord
import asyncio

global router, startTime
router = APIRouter()


def setStartTime(inputTime):
	global startTime
	startTime = inputTime


class Failiure:
	def __init__(self, why="Generic"):
		self.why = why
	def __repr__(self):
		return f"Failiure: {self.why}"


def verifyToken(authorization: str = Header(None, convert_underscores=False)):
	if authorization != f"Bearer {os.getenv('HTTP_AUTH_CODE')}":
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid or missing authentication token."
		)




async def uptime(data):
	currentTime = time.time()
	elapsedTime = startTime - currentTime
	return str(int(round(elapsedTime)))


async def updateRepoHandler(data):
	updateRepo()
async def backupDataHandler(data):
	backupData()


async def econHandler(data):
	sections = data.split("|")

	def grantMoneyInternal(sections):
		who = sections[1]
		company = sections[2] == "true"
		amount = int(sections[3])
		return grantMoney(who, amount, not company, company)

	def resetEconInternal(sections):
		writeCSV("data/econ.csv", altData={})

	def newFakeCompanyInternal(sections):
		CEO, name = "", ""
		if len(sections) > 1:
			name = sections[1]
		if len(sections) > 2:
			CEO = sections[2]
		company = createFakeCompany(optionalName=name, optionalCEO=CEO)
		return f"Created {company.name} -> {company}"

	def saveHandler(sections):
		writeCSV("data/econ.csv")

	def forceUnBusyHandler(sections):
		return forceUnBusyFunc()






	cmdList = {
		#What to use to call the function, the function, and number of sections the function expects.
		"grant": (grantMoneyInternal, 4),
		"reset": (resetEconInternal, 1),
		"fakeCompany": (newFakeCompanyInternal, 1),
		"save": (saveHandler, 1),
		"forceUnBusy": (forceUnBusyHandler, 1)
	}

	try:
		if sections[0] in cmdList and len(sections) >= cmdList[sections[0]][1]:
			return cmdlist[sections[0]][0](data)
	except TypeError:
		return Failiure(f"ECON::[{sections[2]} was not an integer.]")

	return Failiure("ECON::[Unknown ECON command.]")



def endTTTHandler(data):
	forceEndAllTTT()
def endChessHandler(data):
	forceEndAllChess()


def viewLogs(data):
	def formatLines(lines):
		output = ""
		for line in lines:
			output += line + "|"
		return (output + "|").replace("||", "")

	sections = data.split("|")
	logsToShow = 5
	try:
		if len(sections) > 0 and data != "":
			logsToShow = int(sections[0]) if int(sections[0]) > 0 else 5

	except TypeError:
		pass



	with open("data/logs.txt", "r") as logFile:
		fullLog = logFile.readlines()
	if len(fullLog) <= logsToShow:
		res = formatLines(fullLog)
	else:
		res = formatLines(fullLog[-logsToShow:])

	return res




@router.get("/")
async def root():
	return {
		"message": "DThree is online."
	}


@router.post("/message")
async def recieveData(payload: dict, auth: str=Depends(verifyToken)):
	data = payload.get("content", "")
	reply = {
		"message": ""
	}

	funcMap = {
		"update-repo": updateRepoHandler,
		"backup-data": backupDataHandler,
		"uptime": uptime,
		"econ": econHandler,
		"endTTT": endTTTHandler,
		"endChess": endChessHandler,
		"viewLogs": viewLogs,
	}


	try:
		cmd = data.split("|")[0]
		if cmd not in funcMap:
			raise HTTPException(
					status_code=status.HTTP_400_BAD_REQUEST,
					detail=f"Invalid command '{cmd}'"
				)
		result = await funcMap[cmd](data.replace(cmd + "|", ""))
		if isinstance(result, Failiure):
			reply["message"] = f"Failiure: {result}"
		else:
			reply["message"] = result if result is not None else "Success"
	except Exception as err:
		reply["message"] = f"Failiure: {err}"


	return reply