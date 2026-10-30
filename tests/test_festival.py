from datetime import datetime

import pytest

from artist import Artist
from festival import Festival
from lineup import Lineup
from performance import Performance
from solo import Solo
from venue import Venue


class MemoryJsonConnection:
    def __init__(self, data):
        self.data = data

    @property
    def venues(self):
        return self.data["venues"]

    @property
    def performances(self):
        return self.data["performances"]

    def save(self):
        pass


@pytest.fixture
def festival_factory():
    def make():
        data = {
            "name": "Test Festival",
            "first_day": "2027-06-10",
            "last_day": "2027-06-13",
            "venues": [
                {"name": "Grand Casino", "capacity": 100, "address": "A"},
                {"name": "Le Kiosque", "capacity": 50, "address": "B"},
            ],
            "artists": [
                {"name": "Alex Artist", "bio": "", "photo_url": ""},
                {"name": "Sam Host", "bio": "", "photo_url": ""},
            ],
            "performances": [
                {
                    "kind": "solo",
                    "title": "Existing Show",
                    "venue": "grand-casino",
                    "start": "2027-06-11T20:00",
                    "duration_minutes": 60,
                    "description": "",
                    "artist": "alex-artist",
                    "min_age": 0,
                }
            ],
        }
        return Festival(MemoryJsonConnection(data))
    return make


def solo(festival, *, venue="le-kiosque", artist="alex-artist",
         start="2027-06-11T22:00", duration=45, title="New Show"):
    return Solo(
        title=title,
        venue=festival.get_venue(venue),
        start=start,
        duration_minutes=duration,
        description="",
        artist=festival.get_artist(artist),
        min_age=0,
    )


def test_artist_equality_uses_slug():
    assert Artist("Élodie Marchal", "", "") == Artist("Elodie Marchal", "", "")


def test_performance_order_uses_start_then_venue():
    early = Venue("A Venue", 10, "")
    later = Venue("Z Venue", 10, "")
    first = Performance("First", later, "2027-06-11T20:00", 30, "")
    second = Performance("Second", early, "2027-06-11T20:00", 30, "")
    assert sorted([first, second]) == [second, first]


def test_performance_string_is_cli_programme_line():
    venue = Venue("Grand Casino", 10, "")
    performance = Solo(
        "Comedy", venue, "2027-06-11T20:00", 60, "",
        Artist("Alex Artist", "", ""), 0
    )
    assert str(performance) == (
        "20:00-21:00 | Grand Casino | Comedy (solo)"
    )


def test_venue_busy(festival_factory):
    festival = festival_factory()
    candidate = solo(
        festival, venue="grand-casino", artist="sam-host",
        start="2027-06-11T20:45"
    )
    with pytest.raises(ValueError, match="Grand Casino is busy"):
        festival.add_performance(candidate)


def test_artist_busy_in_another_venue(festival_factory):
    festival = festival_factory()
    candidate = solo(
        festival, venue="le-kiosque", artist="alex-artist",
        start="2027-06-11T20:45"
    )
    with pytest.raises(ValueError, match="Alex Artist is on stage"):
        festival.add_performance(candidate)


def test_artist_busy_as_lineup_act(festival_factory):
    festival = festival_factory()
    candidate = Lineup(
        "New Lineup",
        festival.get_venue("le-kiosque"),
        "2027-06-11T20:45",
        45,
        "",
        festival.get_artist("sam-host"),
        [festival.get_artist("alex-artist")],
    )
    with pytest.raises(ValueError, match="Alex Artist is on stage"):
        festival.add_performance(candidate)


def test_one_am_performance_belongs_to_previous_programme_day(festival_factory):
    festival = festival_factory()
    candidate = solo(
        festival, artist="sam-host", start="2027-06-12T01:00"
    )
    festival.add_performance(candidate)
    assert candidate in festival.programme_for_day("2027-06-11")
    assert candidate not in festival.programme_for_day("2027-06-12")


@pytest.mark.parametrize("duration", [0, 361])
def test_invalid_duration(festival_factory, duration):
    festival = festival_factory()
    with pytest.raises(ValueError, match="Duration must be between 1 and 360"):
        festival.add_performance(solo(
            festival, artist="sam-host", start="2027-06-12T10:00",
            duration=duration
        ))


def test_day_outside_festival(festival_factory):
    festival = festival_factory()
    with pytest.raises(ValueError, match="is not a day of the festival"):
        festival.add_performance(solo(
            festival, artist="sam-host", start="2027-06-14T10:00"
        ))


def test_unknown_venue(festival_factory):
    festival = festival_factory()
    candidate = Solo(
        "Unknown Venue Show", "missing-venue", "2027-06-12T10:00",
        30, "", festival.get_artist("sam-host"), 0
    )
    with pytest.raises(ValueError, match="Unknown venue"):
        festival.add_performance(candidate)


def test_unknown_artist(festival_factory):
    festival = festival_factory()
    candidate = Solo(
        "Unknown Artist Show", festival.get_venue("le-kiosque"),
        "2027-06-12T10:00", 30, "",
        Artist("Unknown Person", "", ""), 0
    )
    with pytest.raises(ValueError, match="Unknown artist"):
        festival.add_performance(candidate)


def test_now_playing_and_next_three(festival_factory):
    festival = festival_factory()
    moment = datetime.fromisoformat("2027-06-11T20:30")
    assert [p.title for p in festival.now_playing(moment)] == ["Existing Show"]
    assert festival.up_next(moment, limit=3) == []
