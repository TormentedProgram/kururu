import requests
import utils.config

import json
import subprocess

def show_message_box(title, message):
    subprocess.run(['kdialog', '--error', message, '--title', title])

def error_checking(data):
    try:
        if 'errors' in data and len(data['errors']) > 0:
            error_message = data['errors'][0]['message']
            show_message_box("KerOrO Progress Updater", f"Anilist Error: {error_message}")
    except json.JSONDecodeError as e:
        show_message_box("KerOrO Progress Updater", f"Failed to parse JSON: {str(e)}")

def anilist_call(query, variables, errorPopup=True):
    config_dict = utils.config.get_config()
    url = 'https://graphql.anilist.co'
    response = requests.post(
        url,
        headers = {'Authorization': 'Bearer ' + config_dict["token"], 'Content-Type': 'application/json', 'Accept': 'application/json'},
        json = {'query': query, 'variables': variables}
    )
    if errorPopup:
      error_checking(response.json())
    return response.json()

def get_watching_list(pageNumber=1):
    config_dict = utils.config.get_config()
    anilist_user = config_dict["anilist_user"]
    variables = {
        "userName": anilist_user,
        "pageNumber": pageNumber
    }
    query = '''
    query ($userName: String, $pageNumber: Int) {
      Page(page: $pageNumber, perPage: 50) {
        mediaList(userName: $userName, type: ANIME) {
          progress
          status
          media {
            id
            title {
              userPreferred
            }
          }
        }
      }
    }
    '''
    result = anilist_call(query, variables)
    
    if "errors" in result:
        print(f"Error in API call: {result['errors']}")
        return {}

    watchlist = result["data"]["Page"]["mediaList"]
    
    if not watchlist:
        print(f"No watchlist found for page {pageNumber}")
        return {}
    
    cleaned_up = {}
    for item in watchlist:
        cleaned_up[item["media"]["id"]] = {
            "title": item["media"]["title"]["userPreferred"],
            "progress": item["progress"],
            "status": item["status"],
            "id": item["media"]["id"]
        }

    if len(watchlist) == 50:
        next_page_watchlist = get_watching_list(pageNumber + 1)
        cleaned_up.update(next_page_watchlist)
    
    return cleaned_up

def get_search_results(searchTerm, page):
    variables = {
        "searchTerm": searchTerm,
        "page": page
    }
    query = '''
    query ($searchTerm: String, $page: Int) {
      Page(page: $page, perPage: 5) {
        media(search: $searchTerm, type: ANIME) {
          title {
            english
          }
          id
        }
      }
    }
    '''
    result = anilist_call(query, variables)
    cleaned_up = []
    watchlist = result["data"]["Page"]["media"]
    for item in watchlist:
        cleaned_up.append([item["title"]["english"], item["id"]])
    return cleaned_up

def update_progress(mediaId, progress, length):
    mediaStatus = "CURRENT"
    if length != 0 and progress >= length:
        mediaStatus = "COMPLETED"
    variables = {
        "mediaId": mediaId,
        "mediaStatus": mediaStatus,
        "progress": progress
    }
    query = '''
    mutation ($mediaId: Int, $progress: Int, $mediaStatus: MediaListStatus) {
      SaveMediaListEntry (mediaId: $mediaId, status: $mediaStatus, progress: $progress) {
          progress
      }
    }
    '''
    anilist_call(query, variables)

def get_status(mediaId):
    config_dict = utils.config.get_config()   
    variables = {
        "userName": config_dict["anilist_user"],
        "mediaId": mediaId
    }
    query = '''
    query ($userName: String, $mediaId: Int) {
      MediaList(userName: $userName, mediaId: $mediaId) {
          status
      }
    }
    '''
    result = anilist_call(query, variables)
    try:
        return result["data"]["MediaList"]["progress"]
    except Exception as e:
        return 0

def get_progress(mediaId):
    config_dict = utils.config.get_config()   
    variables = {
        "userName": config_dict["anilist_user"],
        "mediaId": mediaId
    }
    query = '''
    query ($userName: String, $mediaId: Int) {
      MediaList(userName: $userName, mediaId: $mediaId) {
          progress
      }
    }
    '''
    result = anilist_call(query, variables, False)
    if 'errors' in result and len(result['errors']) > 0:
        return 0
    if result["data"]["MediaList"] == None:
        return 0
    try:
        if result["data"]["MediaList"]["progress"] < 1:
          return 0
        else:
          return result["data"]["MediaList"]["progress"]
    except Exception as e:
        return 0

def get_anime_details(anilist_id):
    variables = {
        "id": anilist_id
    }
    query = '''
    query ($id: Int) {
      Media(id: $id) {
        title {
          english
        },
        siteUrl,
        coverImage {
          medium
        }
        episodes
        idMal
      }
    }
    '''
    result = anilist_call(query, variables)
    return result["data"]