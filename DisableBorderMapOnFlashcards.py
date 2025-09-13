from EnableAudioOnFlashcards import (
    get_model_templates,
    find_notes,
    get_note_info,
    get_card_info,
    update_note_fields
)
import logging

logger = logging.getLogger(__name__)

def disable_border_maps_on_cards() -> None:
    """
    Main function that disables border maps for qualifying cards.

    Finds all cards in the Other deck using the "Regions" template
    with intervals > 45 days and disables their border maps.
    """
    try:
        logger.info("Starting border map disabling process for Other deck")

        # Get the template information for the "Regions" model
        logger.debug("Retrieving template information for 'Regions' model")
        templates_dict = get_model_templates("Regions")
        template_names = list(templates_dict.keys())
        logger.debug(f"Found templates: {template_names}")

        # Get the order of the "Neighbours" template in the templates list
        if "Neighbours" not in template_names:
            logger.warning("'Neighbours' template not found in the 'Regions' model")
            return

        neighbours_template_ord = template_names.index("Neighbours")
        logger.debug(f"'Neighbours' template order: {neighbours_template_ord}")

        # Get all notes in the Other deck
        logger.info("Searching for notes in Other deck")
        note_ids = find_notes("Other")
        if not note_ids:
            logger.warning("No notes found in Other deck")
            return

        logger.info(f"Found {len(note_ids)} notes in Other deck")
        notes = get_note_info(note_ids)

        # Get the notes with the model name "Regions"
        logger.debug("Filtering notes by 'Regions' model")
        notes = [note for note in notes if note["modelName"] == "Regions"]
        if not notes:
            logger.warning("No notes found with 'Regions' model in Other deck")
            return

        logger.info(f"Found {len(notes)} notes with 'Regions' model")

        # Create a list of all of the cardIDs in the notes
        card_ids = [card_id for note in notes for card_id in note["cards"]]
        logger.debug(f"Found {len(card_ids)} total cards across all notes")

        # Get the card information for all cards
        logger.debug("Retrieving detailed card information")
        card_infos = get_card_info(card_ids)

        # Create a dictionary mapping card IDs to their information
        card_info_dict = {card["cardId"]: card for card in card_infos}

        # Find cards that need border maps disabled
        logger.info("Analyzing cards for border map disabling criteria")
        eligible_card_ids: list[int] = []
        for card_id, card in card_info_dict.items():
            if (card["ord"] == neighbours_template_ord and 
                card["interval"] > 45 and 
                card.get("fields", {}).get("No Border Map", {}).get("value") != "Yes"):
                eligible_card_ids.append(card_id)

        logger.info(f"Found {len(eligible_card_ids)} cards eligible for border map disabling")

        # Get notes that contain eligible cards
        notes_to_update = [
            note for note in notes 
            if any(card_id in eligible_card_ids for card_id in note["cards"])
        ]

        # Update the notes
        if notes_to_update:
            note_ids_to_update = [note["noteId"] for note in notes_to_update]
            logger.info(f"Updating {len(notes_to_update)} notes with border map disabling")
            update_note_fields(note_ids_to_update, "No Border Map", "Yes")
            logger.info(f"Successfully disabled border maps for {len(notes_to_update)} notes")
        else:
            logger.info("No notes found that meet the criteria for border map disabling")

    except Exception as e:
        logger.error(f"Error during border map disabling process: {e}", exc_info=True)

if __name__ == "__main__":
    # Configure logging with more detailed format
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # To enable debug logging, uncomment the line below:
    # logger.setLevel(logging.DEBUG)

    logger.info("=== Starting Anki Border Map Disabler ===")
    disable_border_maps_on_cards()
    logger.info("=== Anki Border Map Disabler completed ===")
