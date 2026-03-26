from cs2api import CS2
from services.steam_ids import STEAM_IDS
from datetime import datetime
import asyncio


def country_flag(code):
    if not code:
        return ""
    return "".join(chr(127397 + ord(c)) for c in code.upper())


class CS2Service:
    def __init__(self):
        self.cs2 = None

    async def _ensure_cs2(self):
        if not self.cs2:
            self.cs2 = CS2()
            await self.cs2.__aenter__()

    async def close(self):
        if self.cs2:
            try:
                await self.cs2.__aexit__(None, None, None)
            except Exception:
                pass
            self.cs2 = None

    # -------------------
    # Player Search
    # -------------------
    async def search_player(self, nickname: str):
        # Easter egg player (skip API completely)
        normalized_name = (
            nickname.lower()
            .strip()
            .replace(" ", "")
            .replace("-", "")
            .replace("_", "")
        )

        if normalized_name == "mrwasheewashee":
            return [{
                "nickname": "Mr Washee Washee",
                "first_name": "Quinn",
                "last_name": "Parker",
                "country": "🇨🇳 China",
                "region": "Asia",
                "steam_link": None,
                "image_url": None,
                "local_image": r"C:\Users\doged\Downloads\All-About-CS\assets\players\washee_washee.jpg",
                "slug": "mrwasheewashee",
                "birthDate": "1974-01-01",
                "team": {
                    "name": "CCP",
                    "slug": None,
                    "logo": None,
                    "time_on_team": "52 years"
                },
                "stats": {
                    "time_on_team": "52 years"
                },
                "prize_pool": "478,273,950,000"
            }]

        await self._ensure_cs2()
        data = await self.cs2.search_players(nickname)

        if not data or data["total"]["count"] == 0:
            return None

        players = []

        for player in data["results"][:10]:
            slug = player.get("slug")

            details = {}
            if slug:
                try:
                    details = await asyncio.wait_for(
                        self.cs2.get_player_details(slug),
                        timeout=5
                    )
                except Exception:
                    details = {}

            team = {
                "name": "No Team",
                "slug": None,
                "logo": None,
                "time_on_team": "N/A"
            }

            current_team = details.get("team")

            if current_team and current_team.get("name"):
                joined_date = details.get("joined_team_at")
                time_on_team = "N/A"

                if joined_date:
                    try:
                        joined_dt = datetime.fromisoformat(
                            joined_date.replace("Z", "")
                        )

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

                    except Exception:
                        pass

                team = {
                    "name": current_team.get("name", "No Team"),
                    "slug": current_team.get("slug"),
                    "logo": current_team.get("image_url"),
                    "time_on_team": time_on_team
                }

            steam_link = None
            if player.get("nickname") in STEAM_IDS:
                steam_link = (
                    f"https://steamcommunity.com/profiles/"
                    f"{STEAM_IDS[player['nickname']]}"
                )

            country_data = player.get("country")
            country_name = None
            country_code = None
            region_name = None

            if isinstance(country_data, dict):
                country_name = country_data.get("name")
                country_code = country_data.get("code")
                region_name = country_data.get("region", {}).get("name")

            country_str = (
                f"{country_flag(country_code)} {country_name}"
                if country_code
                else country_name or "N/A"
            )

            prize_pool = (
                details.get("prize_pool")
                or details.get("total_prize")
                or 0
            )

            players.append({
                "nickname": player.get("nickname"),
                "first_name": player.get("first_name") or details.get("first_name"),
                "last_name": player.get("last_name") or details.get("last_name"),
                "country": country_str,
                "region": region_name or "N/A",
                "steam_link": steam_link,
                "image_url": player.get("image_url") or details.get("image_url"),
                "local_image": None,
                "slug": slug,
                "birthDate": details.get("birthDate") or details.get("birthday"),
                "team": team,
                "stats": {
                    "time_on_team": team.get("time_on_team")
                },
                "prize_pool": prize_pool
            })

        return players

    # -------------------
    # Player Details
    # -------------------
    async def get_player_details(self, slug: str):
        await self._ensure_cs2()

        if not hasattr(self.cs2, "get_player_details"):
            return {}

        try:
            return await asyncio.wait_for(
                self.cs2.get_player_details(slug),
                timeout=5
            )
        except Exception:
            return {}

    # -------------------
    # Player Stats
    # -------------------
    async def get_player_stats(self, slug: str):
        await self._ensure_cs2()

        if not hasattr(self.cs2, "get_player_stats"):
            return {}

        try:
            data = await asyncio.wait_for(
                self.cs2.get_player_stats(slug),
                timeout=5
            )
        except Exception:
            return {}

        if not data:
            return {}

        stats = data.get("results", data) if isinstance(data, dict) else data

        if not isinstance(stats, dict):
            return {}

        general = (
            stats.get("general_stats")
            or stats.get("general")
            or stats.get("stats", {}).get("general_stats")
            or stats.get("stats", {}).get("general")
            or {}
        )

        kills = (
            general.get("kills_sum")
            or general.get("kills")
            or general.get("total_kills")
            or general.get("kills_count")
            or 0
        )

        deaths = (
            general.get("deaths_sum")
            or general.get("deaths")
            or general.get("total_deaths")
            or general.get("deaths_count")
            or 0
        )

        map_stats = (
            stats.get("map_stats")
            or stats.get("maps_stats")
            or stats.get("maps")
            or stats.get("match_stats")
            or []
        )

        normalized_map_stats = []
        if isinstance(map_stats, list):
            for m in map_stats:
                if not isinstance(m, dict):
                    continue

                rating = (
                    m.get("avg_player_rating")
                    or m.get("player_rating")
                    or m.get("rating")
                    or m.get("avg_rating")
                    or 0
                )

                normalized_map_stats.append({
                    **m,
                    "avg_player_rating": rating
                })

        normalized_general = {
            **general,
            "kills_sum": kills,
            "deaths_sum": deaths
        }

        return {
            **stats,
            "general_stats": normalized_general,
            "map_stats": normalized_map_stats
        }

    # -------------------
    # Player Matches
    # -------------------
    async def get_player_matches(self, player_id):
        await self._ensure_cs2()

        if not hasattr(self.cs2, "get_player_matches"):
            return []

        try:
            return await asyncio.wait_for(
                self.cs2.get_player_matches(player_id),
                timeout=8
            )
        except Exception:
            return []

    # -------------------
    # Player Transfers
    # -------------------
    async def get_player_transfers(self, player_id):
        await self._ensure_cs2()

        if not hasattr(self.cs2, "get_player_transfers"):
            return []

        try:
            return await asyncio.wait_for(
                self.cs2.get_player_transfers(player_id),
                timeout=8
            )
        except Exception:
            return []

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
            team_data = await asyncio.wait_for(
                self.cs2.get_team_data(team["slug"]),
                timeout=5
            )

            for p in team_data.get("players", []):
                roster.append(p.get("nickname"))

        except Exception:
            team_data = {}
            roster = []

        country_name = "N/A"
        region_name = "N/A"
        country_code = None

        country_data = team_data.get("country")

        if country_data:
            country_name = country_data.get("name", "N/A")
            country_code = country_data.get("code")
            region_name = country_data.get("region", {}).get("name", "N/A")

        return {
            "name": team.get("name"),
            "logo": team.get("image_url"),
            "country": (
                f"{country_flag(country_code)} {country_name}"
                if country_code
                else country_name
            ),
            "region": region_name,
            "roster": roster,
            "hltv_link": (
                f"https://www.hltv.org/team/{team.get('id')}"
                if team.get("id")
                else None
            ),
            "bo3_link": (
                f"https://bo3.gg/teams/{team.get('slug')}"
                if team.get("slug")
                else None
            )
        }

    # -------------------
    # Team Data
    # -------------------
    async def get_team_data(self, slug: str):
        await self._ensure_cs2()

        if not hasattr(self.cs2, "get_team_data"):
            return {}

        try:
            return await asyncio.wait_for(
                self.cs2.get_team_data(slug),
                timeout=5
            )
        except Exception:
            return {}

    # -------------------
    # Team Stats
    # -------------------
    async def get_team_stats(self, slug: str):
        await self._ensure_cs2()

        if not hasattr(self.cs2, "get_team_stats"):
            return {}

        try:
            return await asyncio.wait_for(
                self.cs2.get_team_stats(slug),
                timeout=5
            )
        except Exception:
            return {}

    # -------------------
    # Team Matches
    # -------------------
    async def get_team_matches(self, team_id):
        await self._ensure_cs2()

        if not hasattr(self.cs2, "get_team_matches"):
            return []

        try:
            return await asyncio.wait_for(
                self.cs2.get_team_matches(team_id),
                timeout=8
            )
        except Exception:
            return []

    # -------------------
    # Team Upcoming Matches
    # -------------------
    async def get_team_upcoming_matches(self, team_id):
        await self._ensure_cs2()

        if not hasattr(self.cs2, "get_team_upcoming_matches"):
            return []

        try:
            return await asyncio.wait_for(
                self.cs2.get_team_upcoming_matches(team_id),
                timeout=8
            )
        except Exception:
            return []

    # -------------------
    # Team News
    # -------------------
    async def get_team_news(self, team_slug):
        await self._ensure_cs2()

        if not hasattr(self.cs2, "get_team_news"):
            return []

        try:
            return await asyncio.wait_for(
                self.cs2.get_team_news(team_slug),
                timeout=8
            )
        except Exception:
            return []

    # -------------------
    # Team Transfers
    # -------------------
    async def get_team_transfers(self, team_id):
        await self._ensure_cs2()

        if not hasattr(self.cs2, "get_team_transfers"):
            return []

        try:
            return await asyncio.wait_for(
                self.cs2.get_team_transfers(team_id),
                timeout=8
            )
        except Exception:
            return []

    # -------------------
    # Live Matches
    # -------------------
    async def get_live_matches(self):
        await self._ensure_cs2()

        if not hasattr(self.cs2, "get_live_matches"):
            return []

        try:
            return await asyncio.wait_for(
                self.cs2.get_live_matches(),
                timeout=8
            )
        except Exception:
            return []

    # -------------------
    # Today's Matches
    # -------------------
    async def get_todays_matches(self):
        await self._ensure_cs2()

        if not hasattr(self.cs2, "get_todays_matches"):
            return []

        try:
            return await asyncio.wait_for(
                self.cs2.get_todays_matches(),
                timeout=8
            )
        except Exception:
            return []

    # -------------------
    # Finished Matches
    # -------------------
    async def finished(self):
        await self._ensure_cs2()

        if not hasattr(self.cs2, "finished"):
            return []

        try:
            return await asyncio.wait_for(
                self.cs2.finished(),
                timeout=8
            )
        except Exception:
            return []

    # -------------------
    # Live Match Snapshot
    # -------------------
    async def get_live_match_snapshot(self, match_id):
        await self._ensure_cs2()

        if not hasattr(self.cs2, "get_live_match_snapshot"):
            return {}

        try:
            return await asyncio.wait_for(
                self.cs2.get_live_match_snapshot(match_id),
                timeout=8
            )
        except Exception:
            return {}

    # -------------------
    # Match Details
    # -------------------
    async def get_match_details(self, slug):
        await self._ensure_cs2()

        if not hasattr(self.cs2, "get_match_details"):
            return {}

        try:
            return await asyncio.wait_for(
                self.cs2.get_match_details(slug),
                timeout=8
            )
        except Exception:
            return {}