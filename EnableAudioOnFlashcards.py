"""
Anki Audio Enabler

This script automatically enables audio for Anki flashcards that meet certain criteria.
It finds cards in the "Polish_English" deck using the "Word" template with intervals > 14 days
and sets their "Audio Enabled" field to "Yes".

Requirements:
- Anki must be running
- AnkiConnect addon must be installed in Anki
- The deck "Polish_English" must exist with "Words" model containing "Word" template
"""

import requests
from typing import List, Dict, Any, Optional

ANKI_CONNECT_URL = "http://localhost:8765"

def invoke(action: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Send a request to AnkiConnect API."""
    try:
        response = requests.post(ANKI_CONNECT_URL, json={
            "action": action,
            "version": 6,
            "params": params or {}
        })
        response.raise_for_status()
        result = response.json()
        
        if result.get("error"):
            raise RuntimeError(f"AnkiConnect error: {result['error']}")
            
        return result["result"]
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Could not connect to AnkiConnect. Is Anki running with AnkiConnect addon installed?")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Request failed: {e}")

def find_notes(deck_name: str) -> List[int]:
    """Find all note IDs in the specified deck."""
    return invoke("findNotes", {"query": f'deck:"{deck_name}"'})

def get_note_info(note_ids: List[int]) -> List[Dict[str, Any]]:
    """Get detailed information for the specified notes."""
    return invoke("notesInfo", {"notes": note_ids})

def get_card_info(card_ids: List[int]) -> List[Dict[str, Any]]:
    """Get detailed information for the specified cards."""
    return invoke("cardsInfo", {"cards": card_ids})

def get_model_templates(model_name: str) -> Dict[str, str]:
    """Get template names and content for a given model."""
    return invoke("modelTemplates", {"modelName": model_name})

def update_note_fields(note_ids: List[int], field_name: str, new_value: str) -> None:
    """Update a specific field for multiple notes."""
    for note_id in note_ids:
        invoke("updateNoteFields", {
            "note": {
                "id": note_id,
                "fields": {field_name: new_value}
            }
        })


def unlock_audio_cards() -> None:
    """
    Main function that enables audio for qualifying cards.
    
    Finds all cards in the Polish_English deck using the "Word" template
    with intervals > 14 days and enables audio for them.
    """
    try:
        # Get the template information for the "Words" model
        templates_dict = get_model_templates("Words")
        template_names = list(templates_dict.keys())

        # Get the order of the "Word" template in the templates list
        if "Word" not in template_names:
            print("Warning: 'Word' template not found in the 'Words' model")
            return
            
        word_template_ord = template_names.index("Word")

        # Get all notes in the Polish_English deck
        note_ids = find_notes("Polish_English")
        if not note_ids:
            print("No notes found in Polish_English deck")
            return
            
        notes = get_note_info(note_ids)

        # Get the notes with the model name "Words"
        notes = [note for note in notes if note["modelName"] == "Words"]
        if not notes:
            print("No notes found with 'Words' model in Polish_English deck")
            return

        # Create a list of all of the cardIDs in the notes
        card_ids = [card_id for note in notes for card_id in note["cards"]]

        # Get the card information for all cards
        card_infos = get_card_info(card_ids)

        # Create a dictionary mapping card IDs to their information
        card_info_dict = {card["cardId"]: card for card in card_infos}

        # Find cards that need audio enabled
        eligible_card_ids = []
        for card_id, card in card_info_dict.items():
            if (card["ord"] == word_template_ord and 
                card["interval"] > 14 and 
                card.get("fields", {}).get("Audio Enabled", {}).get("value") != "Yes"):
                eligible_card_ids.append(card_id)

        # Get notes that contain eligible cards
        notes_to_update = [
            note for note in notes 
            if any(card_id in eligible_card_ids for card_id in note["cards"])
        ]

        # Update the notes
        if notes_to_update:
            note_ids_to_update = [note["noteId"] for note in notes_to_update]
            update_note_fields(note_ids_to_update, "Audio Enabled", "Yes")
            print(f"Enabled audio for {len(notes_to_update)} notes")
        else:
            print("No notes found that meet the criteria for audio enablement")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    unlock_audio_cards()
