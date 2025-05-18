from duckduckgo_search import DDGS


def lookUp(query: str) -> dict[str, str]:
	"""
	/whatis function.
	Uses DuckDuckGo to search online for query.
	If the title of a result contains a line from bannedTitles.txt, then it is rejected.
	If the URL of a result contains a line from bannedURLs.txt then it is rejected.
	If no meaningful results are found, it returns an empty dictionary. This is then reported as "No meaningful results"
	If results are found, the dictionary is returned with keys as titles and data as urls.
	Youtube results are allowed to embed. No other results are.
	"""
	results_dict = {}
	results = DDGS().text(query, max_results=50)

	headers = { #Presently rate-limited. Will need to be addressed later.
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
	}

	accepted=0
	for result in results:
		try:
			url, title = result["href"], result["title"]
			if title is None or title.lower() == "access denied": title = "[Title Unavailable]"

			disallowed = False
			#Filter blocked words/phrases in title or URL.
			with open("textFiles/bannedTitles.txt", "r") as badTitles:
				badTitleWords = badTitles.readlines()
			with open("textFiles/bannedURLs.txt", "r") as badURLs:
				badURLWords = badURLs.readlines()
			if any(banned.strip() in title.lower() for banned in badTitleWords):
				continue
			if any(banned.strip() in url.lower() for banned in badURLWords):
				continue

			accepted += 1
			results_dict[title] = url
			if accepted >= 3: break #Only allow 3 valid results max.

		except Exception as e:
			print(e)
			pass

	return results_dict