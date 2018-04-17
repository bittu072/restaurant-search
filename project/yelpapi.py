import urllib2
import json
import io
import rauth
import time

class SearchQuery():
    def __init__(self):
        print "class started"

    def main(self, locate, search_term):
        self.location = locate
        self.search = search_term
        params = self.search_string(self.search, self.location)
        json_obj = self.api_query(params)
        # print json_obj
        time.sleep(1.0)
        data = json_obj["businesses"]

        return data


    def api_query(self, params):
        with open('yelp_client_secrets.json') as data_file:
            data = json.load(data_file)
        session = rauth.OAuth1Session(
            consumer_key = data["consumer_key"],
            consumer_secret = data["consumer_secret"],
            access_token = data["token"],
            access_token_secret = data["token_secret"])

        request = session.get("http://api.yelp.com/v2/search",params=params)
        #Transforms the JSON API response into a Python dictionary
        data = request.json()
        session.close()
        return data

    def search_string(self, search_term, location):
        #See the Yelp API for more details
        params = {}
        params["term"] = search_term
        params["location"] = location
        params["radius_filter"] = "1000"
        params["limit"] = "10"
        params["sort"] = "1"
        return params

if __name__=="__main__":
    import apimain
    abcd = apimain.SearchQuery()
    print abcd.main("Santa Monica", "food")
