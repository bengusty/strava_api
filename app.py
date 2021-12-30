import json
import os
import requests
from flask import Flask, request, make_response
from flask_api import status

app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route('/exchange_token')
def exchange_token():
    expected_scope = "read,activity:read"
    client_id = 12345
    client_secret = "my_client_secret"

    code = request.args.get("code")
    scope = request.args.get("scope")

    if not scope == expected_scope:
        return make_response("The 'View data about your activities' checkbox must be checked in order to use the app",
                             status.HTTP_400_BAD_REQUEST)

    # Get access token and other response data from the Strava oauth URL
    data = {"client_id": client_id, "client_secret": client_secret, "code": code,
            "grant_type": "authorization_code"}
    response = requests.post("https://www.strava.com/oauth/token", data=data)
    response_data = json.loads(response.text)
    refresh_token = response_data.get("refresh_token")
    access_token = response_data.get("access_token")
    athlete = response_data.get("athlete")

    # Use the token in a request to the Strava Activities URL to get the athlete's actvities
    activities_resp = requests.get(
        "https://www.strava.com/api/v3/athlete/activities?per_page=100&scope={}".format(scope),
        headers={"Authorization": "Bearer {}".format(access_token)})

    if activities_resp.status_code != status.HTTP_200_OK:
        return make_response(activities_resp.reason, activities_resp.status_code)

    # Parse the main activities info from the response text and covert a couple values
    activities = json.loads(activities_resp.text)
    activities_info = [{"id": activity.get("id"),
                        "distance": round(activity.get("distance") / 1609.344, 2),
                        "elevation": int(activity.get("total_elevation_gain") * 3.28084),
                        "name": activity.get("name"),
                        "date": activity.get("start_date_local")} for activity in activities]

    # Spit out the athlete info and activities in the response
    return make_response(str(athlete) + "<br /><br />" + str(activities_info))


if __name__ == '__main__':
    app.run(host=os.getenv('IP', '0.0.0.0'),
            port=int(os.getenv('PORT', 4444)))
