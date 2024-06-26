import requests
import utils.config

def anilist_call(query, variables):
    config_dict = utils.config.get_config()
    url = 'https://graphql.anilist.co'
    response = requests.post(
        url,
        headers = {'Authorization': 'Bearer ' + config_dict["token"], 'Content-Type': 'application/json', 'Accept': 'application/json'},
        json = {'query': query, 'variables': variables}
    )
    return response.json()

def get_watching_list():
    config_dict = utils.config.get_config()
    anilist_user = config_dict["anilist_user"]
    variables = {
        "userName": anilist_user
    }
    query = '''
    query ($userName: String) {
      Page(page: 1, perPage: 1000) {
        mediaList(userName: $userName, status_in: [CURRENT, REPEATING], type: ANIME) {
          progress
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
    cleaned_up = {}
    watchlist = result["data"]["Page"]["mediaList"]
    for item in watchlist:
        cleaned_up[item["media"]["id"]] = {
            "title": item["media"]["title"]["userPreferred"],
            "progress": item["progress"],
            "id": item["media"]["id"]
        }
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

def update_progress(mediaId, progress):
    variables = {
        "mediaId": mediaId,
        "mediaStatus": "CURRENT",
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
    result = anilist_call(query, variables)
    if result["data"]["MediaList"] == None:
        return 1
    try:
        return result["data"]["MediaList"]["progress"]
    except Exception as e:
        return 1

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
      }
    }
    '''
    result = anilist_call(query, variables)
    return result["data"]