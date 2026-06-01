This is a quick project I made for home-use to test if we could have our family could use a new app, during virtual schooling to help limit the various websites the kids would have to browse to:
+ Track movie requests
+ Track board game requests
+ Practice multiplication
+ Listen to curated music (mp3)
+ Ask for help
+ Timer
+ Chore Tracking
+ Behavior Tracking

This is a Flask app that uses Jinja Templates and JSON flat file storage.

## Requirements

- Python 3.x
- Dependencies: `flask`, `notifypy`, `werkzeug`
- A [BoardGameGeek](https://boardgamegeek.com) account and API token (for the games feature)

Install dependencies:
```
pip install flask notifypy werkzeug
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `BGG_TOKEN` | BoardGameGeek API token |
| `BGG_USER` | BoardGameGeek username (used to fetch your game collection) |

## Configuration

Before running, edit `main.py` to match your household:

- **`user_ips`** — map each family member's local IP address to their display name
- **`chores_list`** — the rotating chore assignments
- **`helping_list`** / **`bad_list`** — positive and negative behavior tracking items
- **`kid_names`** — list of children's display names

## Required Directory & File Structure

Create these before first run:

```
ticks/               # daily behavior tracking (auto-populated)
goals/               # daily goals tracking (auto-populated)
review_questions/    # math quiz results (auto-populated)
static/songs/        # drop .mp3 files here for the music player
movie_list.json      # seed file for the movie list
leaderboard.json     # seed file for quiz leaderboard (start with {})
```

## Running

```bash
python main.py
```

App runs on port `6543`, accessible at `http://<host>:6543`.

To run with gunicorn:
```bash
gunicorn -c gunicorn.conf.py main:app
```