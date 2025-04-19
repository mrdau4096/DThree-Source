from fastapi import Depends, HTTPException, Header, status, APIRouter
from exct.shared import sendMessage, replyMessage, updateRepo, backupData
import os

global router, client
router = APIRouter()

def setClient(clientExtern):
	client = clientExtern




def verifyToken(authorization: str = Header(None, convert_underscores=False)):
	if authorization != f"Bearer {os.getenv('HTTP_AUTH_CODE')}":
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid or missing authentication token."
		)



async def echo(data):
	print("Echo")
	pass #Implement later.


async def uptime(data):
	print("Uptime")
	pass #Implement later.1






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
		"echo": echo,
		"update-repo": updateRepo,
		"backup-data": backupData,
		"uptime": uptime,
	}


	try:
		cmd = data.split("|")[0]
		if cmd not in funcMap:
			raise HTTPException(
					status_code=status.HTTP_400_BAD_REQUEST,
					detail=f"Invalid command '{cmd}'"
				)
		result = await funcMap[cmd](data.replace(cmd + "|", ""))
		reply["message"] = result if result is not None else "Success"
	except Exception as err:
		reply["message"] = f"Faliure: {err}"


	return reply