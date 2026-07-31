# B4 Raw Data Field Inventory

## Step 1: All Available Fields

### games_2024.json
```
{'attendance': 'NoneType', 'awayClassification': 'NoneType', 'awayConference': 'NoneType', 'awayId': 'int', 'awayLineScores': 'list', 'awayPoints': 'int', 'awayPostgameElo': 'NoneType', 'awayPostgameWinProbability': 'NoneType', 'awayPregameElo': 'NoneType', 'awayTeam': 'str', 'completed': 'bool', 'conferenceGame': 'bool', 'excitementIndex': 'NoneType', 'highlights': 'str', 'homeClassification': 'str', 'homeConference': 'str', 'homeId': 'int', 'homeLineScores': 'list', 'homePoints': 'int', 'homePostgameElo': 'NoneType', 'homePostgameWinProbability': 'NoneType', 'homePregameElo': 'NoneType', 'homeTeam': 'str', 'id': 'int', 'neutralSite': 'bool', 'notes': 'NoneType', 'season': 'int', 'seasonType': 'str', 'startDate': 'str', 'startTimeTBD': 'bool', 'venue': 'NoneType', 'venueId': 'NoneType', 'week': 'int'}
```

### lines_2024.json
```
{'awayClassification': 'str', 'awayConference': 'str', 'awayScore': 'int', 'awayTeam': 'str', 'awayTeamId': 'int', 'homeClassification': 'str', 'homeConference': 'str', 'homeScore': 'int', 'homeTeam': 'str', 'homeTeamId': 'int', 'id': 'int', 'lines': 'list', 'season': 'int', 'seasonType': 'str', 'startDate': 'str', 'week': 'int'}
```

## Step 2: Candidate Feature Availability (in specified order)

1. **`week`** - AVAILABLE (int in both games_2024.json and lines_2024.json)
2. **`neutralSite`** - AVAILABLE (bool in games_2024.json)
3. **`conferenceGame`** - AVAILABLE (bool in games_2024.json)
4. **`fcs_dog`** - AVAILABLE (can be computed: check if underdog's conference field is None/missing; games_2024.json has awayConference, homeConference; lines_2024.json has awayConference, homeConference)
5. **`home_dog`** - Would require computing underdog position from betting lines (not a raw field)

### Selection Summary (first 4 supported, in order)
- [x] week
- [x] neutralSite
- [x] conferenceGame
- [x] fcs_dog

**Total selected: 4 features** (Bonferroni budget reached)
