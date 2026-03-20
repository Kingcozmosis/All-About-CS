from cs2api import CS2
from services.steam_ids import STEAM_IDS
from datetime import datetime


class CS2Service:

    def __init__(self):
        self.cs2 = None

    async def _ensure_cs2(self):
        if not self.cs2:
            self.cs2 = CS2()
            await self.cs2.__aenter__()

    # -------------------
    # Player Search
    # -------------------
    async def search_player(self, nickname: str):
        await self._ensure_cs2()

        data = await self.cs2.search_players(nickname)
        if not data or data["total"]["count"] == 0:
            return None

        player = data["results"][0]
        slug = player.get("slug")

        # Fetch detailed info
        details = {}
        if slug:
            try:
                details = await self.cs2.get_player_details(slug)
            except:
                details = {}

        # -------------------
        # Team info
        # -------------------
        team = {"name": "No Team", "slug": None, "logo": None, "time_on_team": "N/A"}
        current_team = details.get("team")

        if current_team and current_team.get("name"):

            joined_date = details.get("joined_team_at")
            time_on_team = "N/A"

            if joined_date:
                try:
                    joined_dt = datetime.fromisoformat(joined_date.replace("Z", ""))
                    today = datetime.today()

                    years = today.year - joined_dt.year
                    months = today.month - joined_dt.month
                    days = today.day - joined_dt.day

                    if days < 0:
                        months -= 1
                        days += 30

                    if months < 0:
                        years -= 1
                        months += 12

                    time_on_team = f"{years}y {months}m {days}d"

                except:
                    time_on_team = "N/A"

            team = {
                "name": current_team.get("name", "No Team"),
                "slug": current_team.get("slug"),
                "logo": current_team.get("image_url"),
                "time_on_team": time_on_team
            }

        # -------------------
        # Steam link
        # -------------------
        steam_link = None
        nickname_key = player.get("nickname")

        if nickname_key in STEAM_IDS:
            steam_link = f"https://steamcommunity.com/profiles/{STEAM_IDS[nickname_key]}"

        # -------------------
        # Age
        # -------------------
        birth_date = details.get("birthDate") or details.get("birthday")

        # -------------------
        # Prize pool
        # -------------------
        prize_pool = details.get("prize_pool") or details.get("total_prize") or 0

        return {
            "nickname": player.get("nickname"),
            "first_name": player.get("first_name") or details.get("first_name"),
            "last_name": player.get("last_name") or details.get("last_name"),
            "country": player.get("country", {}).get("name") if isinstance(player.get("country"), dict) else player.get("country", "N/A"),
            "steam_link": steam_link,
            "image_url": player.get("image_url") or details.get("image_url"),
            "slug": slug,
            "birthDate": birth_date,
            "team": team,
            "stats": {"time_on_team": team.get("time_on_team")},
            "prize_pool": prize_pool
        }

    # -------------------
    # Team Search
    # -------------------
    async def search_team(self, name: str):
        await self._ensure_cs2()

        data = await self.cs2.search_teams(name)
        if not data or data["total"]["count"] == 0:
            return None

        team = data["results"][0]

        roster = []
        try:
            team_data = await self.cs2.get_team_data(team["slug"])
            for p in team_data.get("players", []):
                roster.append(p.get("nickname"))
        except:
            roster = []

        return {
            "name": team.get("name"),
            "logo": team.get("image_url"),
            "roster": roster,
            "hltv_link": f"https://www.hltv.org/team/{team.get('id')}" if team.get("id") else None,
            "bo3_link": f"https://bo3.gg/teams/{team.get('slug')}" if team.get("slug") else None
        }

    # -------------------
    # Live Matches
    # -------------------
    async def get_live_matches(self):
        await self._ensure_cs2()
        return await self.cs2.get_live_matches()