# Anki Audio Enabler

This script automatically enables audio for Anki flashcards that meet certain criteria. It finds cards in the "Polish_English" deck using the "Word" template with intervals greater than 14 days and sets their "Audio Enabled" field to "Yes".

## Requirements

- Python 3.6+
- Anki must be running
- [AnkiConnect](https://ankiweb.net/shared/info/2055492159) addon must be installed in Anki
- The deck "Polish_English" must exist with "Words" model containing "Word" template

## Installation

1. Clone this repository or download the script
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Make sure Anki is running with the AnkiConnect addon installed

## Usage

Simply run the script:
```bash
python EnableAudioOnFlashcards.py
```

The script will:
1. Connect to Anki via AnkiConnect
2. Find all notes in the "Polish_English" deck
3. Look for cards using the "Word" template
4. Enable audio for cards with intervals > 14 days
5. Print a summary of how many notes were updated

## Configuration

You can modify the following constants in the script to customize behavior:
- Deck name (currently "Polish_English")
- Model name (currently "Words") 
- Template name (currently "Word")
- Minimum interval (currently 14 days)
- Field name (currently "Audio Enabled")

## License

This project is open source and available under the MIT License.
