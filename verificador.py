
import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone

USER_IDS = [4843826368, 5683524981]
TARGET_PLACE_ID = 109629391874197
WEBHOOK = os.environ["WEBHOOK_URL"]

def api(url, data=None):
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode() if data is not None else None,
        headers=headers,
        method="POST" if data is not None else "GET"
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())

def get_experience_name():
    try:
        universe = api(
            f"https://apis.roblox.com/universes/v1/places/{TARGET_PLACE_ID}/universe"
        )
        universe_id = universe["universeId"]

        games = api(
            f"https://games.roblox.com/v1/games?universeIds={universe_id}"
        )
        return games["data"][0]["name"]
    except Exception:
        return f"Experiencia {TARGET_PLACE_ID}"

def get_profiles():
    result = api(
        "https://users.roblox.com/v1/users",
        {"userIds": USER_IDS}
    )
    return {u["id"]: u for u in result["data"]}

def get_avatars():
    ids = ",".join(map(str, USER_IDS))
    url = (
        "https://thumbnails.roblox.com/v1/users/avatar-headshot"
        f"?userIds={ids}&size=150x150&format=Png&isCircular=false"
    )
    result = api(url)
    return {
        item["targetId"]: item["imageUrl"]
        for item in result.get("data", [])
        if item.get("imageUrl")
    }

def send_discord(profile, avatar, experience, presence):
    username = profile["name"]
    display = profile["displayName"]
    user_id = profile["id"]
    job_id = presence.get("gameId") or "No disponible"

    embed = {
        "title": "🎮 Usuario detectado en la experiencia",
        "color": 5763719,
        "thumbnail": {"url": avatar} if avatar else None,
        "fields": [
            {"name": "Usuario", "value": f"`{username}`", "inline": True},
            {"name": "Display Name", "value": f"`{display}`", "inline": True},
            {"name": "User ID", "value": str(user_id), "inline": True},
            {"name": "Experiencia", "value": experience, "inline": False},
            {"name": "Place ID", "value": str(TARGET_PLACE_ID), "inline": True},
            {"name": "Job ID", "value": f"`{job_id}`", "inline": False},
            {
                "name": "Perfil",
                "value": f"https://www.roblox.com/users/{user_id}/profile",
                "inline": False
            }
        ],
        "footer": {"text": "Roblox Presence Monitor"},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    embed = {k: v for k, v in embed.items() if v is not None}

    payload = {"embeds": [embed]}

    req = urllib.request.Request(
        WEBHOOK,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=20) as r:
        r.read()

def main():
    experience = get_experience_name()
    profiles = get_profiles()
    avatars = get_avatars()

    result = api(
        "https://presence.roblox.com/v1/presence/users",
        {"userIds": USER_IDS}
    )

    for presence in result.get("userPresences", []):
        uid = presence.get("userId")

        if (
            presence.get("userPresenceType") == 2
            and presence.get("placeId") == TARGET_PLACE_ID
        ):
            profile = profiles.get(uid)

            if profile:
                send_discord(
                    profile,
                    avatars.get(uid),
                    experience,
                    presence
                )
                print(f"Detectado: {profile['name']}")

if __name__ == "__main__":
    main()
