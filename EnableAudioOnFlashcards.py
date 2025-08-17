"""
Anki Audio Enabler

This script automatically enables audio for Anki flashcards that meet certain criteria.
It finds cards in the "Polish" deck using the "Word" template with intervals > 14 days
and sets their "Audio Enabled" field to "Yes".

Requirements:
- Anki must be running
- AnkiConnect addon must be installed in Anki
- The deck "Polish" must exist with "Words" model containing "Word" template
"""

import requests
from typing import List, Dict, Any, Optional
from tqdm import tqdm

import logging

logger = logging.getLogger(__name__)

ANKI_CONNECT_URL = "http://localhost:8765"

def invoke(action: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """Send a request to AnkiConnect API."""
    try:
        logger.debug(f"Invoking AnkiConnect action: {action} with params: {params}")
        response = requests.post(ANKI_CONNECT_URL, json={
            "action": action,
            "version": 6,
            "params": params or {}
        })
        response.raise_for_status()
        result = response.json()
        
        if result.get("error"):
            logger.error(f"AnkiConnect action '{action}' failed: {result['error']}")
            raise RuntimeError(f"AnkiConnect error: {result['error']}")
            
        logger.debug(f"AnkiConnect action '{action}' completed successfully")
        return result["result"]
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to AnkiConnect - check if Anki is running with AnkiConnect addon")
        raise ConnectionError("Could not connect to AnkiConnect. Is Anki running with AnkiConnect addon installed?")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to AnkiConnect failed: {e}")
        raise RuntimeError(f"Request failed: {e}")

def find_notes(deck_name: str) -> List[int]:
    """Find all note IDs in the specified deck."""
    logger.debug(f"Searching for notes in deck: {deck_name}")
    return invoke("findNotes", {"query": f'deck:"{deck_name}"'})

def get_note_info(note_ids: List[int]) -> List[Dict[str, Any]]:
    """Get detailed information for the specified notes."""
    logger.debug(f"Retrieving info for {len(note_ids)} notes")
    return invoke("notesInfo", {"notes": note_ids})

def get_card_info(card_ids: List[int]) -> List[Dict[str, Any]]:
    """Get detailed information for the specified cards."""
    logger.debug(f"Retrieving info for {len(card_ids)} cards")
    return invoke("cardsInfo", {"cards": card_ids})

def get_model_templates(model_name: str) -> Dict[str, str]:
    """Get template names and content for a given model."""
    logger.debug(f"Retrieving templates for model: {model_name}")
    return invoke("modelTemplates", {"modelName": model_name})

def update_note_fields(note_ids: List[int], field_name: str, new_value: str) -> None:
    """Update a specific field for multiple notes."""
    # Terminal progress bar
    logger.info(f"Updating {len(note_ids)} notes to set '{field_name}' to '{new_value}'")
    if not note_ids:
        logger.warning("No note IDs provided for update.")
        return
    
    with tqdm(total=len(note_ids), desc=f"Updating {field_name}", unit="note") as pbar:
        for note_id in note_ids:
            invoke("updateNoteFields", {
                "note": {
                    "id": note_id,
                    "fields": {field_name: new_value}
                }
            })
            pbar.update(1)  # Update progress bar after each note


def unlock_audio_cards() -> None:
    """
    Main function that enables audio for qualifying cards.
    
    Finds all cards in the Polish deck using the "Word" template
    with intervals > 14 days and enables audio for them.
    """
    try:
        logger.info("Starting audio enablement process for Polish deck")
        
        # Get the template information for the "Words" model
        logger.debug("Retrieving template information for 'Words' model")
        templates_dict = get_model_templates("Words")
        template_names = list(templates_dict.keys())
        logger.debug(f"Found templates: {template_names}")

        # Get the order of the "Word" template in the templates list
        if "Word" not in template_names:
            logger.warning("'Word' template not found in the 'Words' model")
            return
            
        word_template_ord = template_names.index("Word")
        logger.debug(f"'Word' template order: {word_template_ord}")

        # Get all notes in the Polish deck
        logger.info("Searching for notes in Polish deck")
        note_ids = find_notes("Polish")
        if not note_ids:
            logger.warning("No notes found in Polish deck")
            return
            
        logger.info(f"Found {len(note_ids)} notes in Polish deck")
        notes = get_note_info(note_ids)

        # Get the notes with the model name "Words"
        logger.debug("Filtering notes by 'Words' model")
        notes = [note for note in notes if note["modelName"] == "Words"]
        if not notes:
            logger.warning("No notes found with 'Words' model in Polish deck")
            return

        logger.info(f"Found {len(notes)} notes with 'Words' model")

        # Create a list of all of the cardIDs in the notes
        card_ids = [card_id for note in notes for card_id in note["cards"]]
        logger.debug(f"Found {len(card_ids)} total cards across all notes")

        # Get the card information for all cards
        logger.debug("Retrieving detailed card information")
        card_infos = get_card_info(card_ids)

        # Create a dictionary mapping card IDs to their information
        card_info_dict = {card["cardId"]: card for card in card_infos}

        # Find cards that need audio enabled
        logger.info("Analyzing cards for audio enablement criteria")
        eligible_card_ids: list[int] = []
        for card_id, card in card_info_dict.items():
            if (card["ord"] == word_template_ord and 
                card["interval"] > 14 and 
                card.get("fields", {}).get("Audio Enabled", {}).get("value") != "Yes"):
                eligible_card_ids.append(card_id)

        logger.info(f"Found {len(eligible_card_ids)} cards eligible for audio enablement")

        # Get notes that contain eligible cards
        notes_to_update = [
            note for note in notes 
            if any(card_id in eligible_card_ids for card_id in note["cards"])
        ]

        # Update the notes
        if notes_to_update:
            note_ids_to_update = [note["noteId"] for note in notes_to_update]
            logger.info(f"Updating {len(notes_to_update)} notes with audio enablement")
            update_note_fields(note_ids_to_update, "Audio Enabled", "Yes")
            logger.info(f"Successfully enabled audio for {len(notes_to_update)} notes")
        else:
            logger.info("No notes found that meet the criteria for audio enablement")
            
    except Exception as e:
        logger.error(f"Error during audio enablement process: {e}", exc_info=True)

if __name__ == "__main__":
    # Configure logging with more detailed format
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # To enable debug logging, uncomment the line below:
    # logger.setLevel(logging.DEBUG)
    
    logger.info("=== Starting Anki Audio Enabler ===")
    unlock_audio_cards()
    logger.info("=== Anki Audio Enabler completed ===")
