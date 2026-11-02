import spacy
import json
import random
from spacy.tokens import DocBin
from pathlib import Path

def train_spacy_model(training_data_path, model_output_path, n_iter=20):
    # Load blank English model
    nlp = spacy.blank("en")

    # Add a text categorizer for intent classification
    # textcat = nlp.add_pipe("textcat_multilabel", last=True) # Use textcat for multi-label
    textcat = nlp.add_pipe("textcat", last=True) # Use textcat for single-label intent
    textcat.add_label("add_item")
    textcat.add_label("modify_item")
    textcat.add_label("remove_item")
    textcat.add_label("query_sides")
    textcat.add_label("query_price")
    textcat.add_label("finalize_order")
    textcat.add_label("clear_order") # Added clear_order intent
    textcat.add_label("unknown") # Default intent for unhandled cases

    # Add a Named Entity Recognizer (NER)
    ner = nlp.add_pipe("ner", last=True)
    ner.add_label("ITEM_NAME")
    ner.add_label("ITEM_TYPE") # e.g., "burger" when specific item name isn't given
    ner.add_label("OPTION_TYPE") # e.g., "cheese", "bread"
    ner.add_label("OPTION_VALUE") # e.g., "cheddar", "brioche bun"
    ner.add_label("TOPPING") # Specific for toppings if distinct from general options
    ner.add_label("SIDE") # For specific side names
    ner.add_label("QUANTITY") # For "two cokes"

    # Load training data
    with open(training_data_path, 'r') as f:
        TRAIN_DATA = json.load(f)

    # Convert training data to SpaCy's DocBin format for efficient training
    db = DocBin()
    for text_data in TRAIN_DATA:
        doc = nlp.make_doc(text_data["text"])
        # Add entities
        ents = []
        for ent in text_data.get("entities", []):
            span = doc.char_span(ent["start"], ent["end"], label=ent["label"])
            if span is not None:
                ents.append(span)
        try:
            doc.ents = ents
        except ValueError as e:
            print(f"Skipping example due to entity overlap or invalid span: {text_data['text']} - {e}")
            continue # Skip this example if entities are problematic

        # Add textcat labels (single label for textcat pipe)
        cats = {label: 0.0 for label in textcat.labels}
        if "intent" in text_data and text_data["intent"] in textcat.labels:
            cats[text_data["intent"]] = 1.0
        else:
            cats["unknown"] = 1.0 # Default to unknown if intent not specified or not in labels
        doc.cats = cats
        db.add(doc)

    # Save DocBin file for training
    train_spacy_path = Path(model_output_path) / "train.spacy"
    db.to_disk(train_spacy_path)
    print(f"SpaCy training data saved to {train_spacy_path}")

    # For actual training, SpaCy recommends using `spacy train` CLI with a config file.
    # This provides more control over pipelines, hyperparameters, and evaluation.
    # Example config generation: `spacy init config en trained_nlu_model --pipeline ner,textcat --optimize efficiency`
    # Then manually edit the config.cfg to point to your train.spacy and dev.spacy (if you have one)
    # Then run: `python -m spacy train config.cfg --output trained_nlu_model --paths.train trained_nlu_model/train.spacy`

    # For a simple in-script training (less robust for production):
    # Disable other pipes for training NER and textcat
    pipe_exceptions = ["ner", "textcat"]
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]
    with nlp.disable_pipes(*other_pipes):
        optimizer = nlp.begin_training()
        for itn in range(n_iter):
            random.shuffle(TRAIN_DATA)
            losses = {}
            for text_data in TRAIN_DATA:
                doc = nlp.make_doc(text_data["text"])
                example = spacy.training.Example(doc, nlp(text_data["text"]))

                # Manually set entities for the reference doc (for NER training)
                example.reference.ents = [
                    doc.char_span(ent["start"], ent["end"], label=ent["label"])
                    for ent in text_data.get("entities", [])
                    if doc.char_span(ent["start"], ent["end"], label=ent["label"]) is not None
                ]

                # Manually set categories for the reference doc (for textcat training)
                example.reference.cats = {label: (1.0 if text_data.get("intent") == label else 0.0) for label in textcat.labels}


                nlp.update([example], drop=0.5, losses=losses)
            print(f"Losses at iteration {itn}: {losses}")

    # Save the trained model
    nlp.to_disk(model_output_path)
    print(f"Trained SpaCy model saved to {model_output_path}")

if __name__ == "__main__":
    # Ensure the output directory for the trained model exists
    output_dir = Path("../backend/trained_nlu_model") # Save directly into backend's model folder
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create a dummy training data file for initial demonstration
    # In a real scenario, you'd expand this significantly.
    dummy_data_path = Path("training_data/nlu_training_data.json")
    dummy_data_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dummy_data_path, "w") as f:
        json.dump([
            {"text": "I want a classic burger", "entities": [{"start": 10, "end": 24, "label": "ITEM_NAME"}], "intent": "add_item"},
            {"text": "Add a coke", "entities": [{"start": 6, "end": 10, "label": "ITEM_NAME"}], "intent": "add_item"},
            {"text": "Veggie burger with cheddar", "entities": [{"start": 0, "end": 13, "label": "ITEM_NAME"}, {"start": 19, "end": 26, "label": "OPTION_VALUE"}], "intent": "add_item"},
            {"text": "Remove the sprite", "entities": [{"start": 11, "end": 17, "label": "ITEM_NAME"}], "intent": "remove_item"},
            {"text": "Clear my order", "intent": "clear_order"},
            {"text": "Finalize my order", "intent": "finalize_order"},
            {"text": "What sides for classic burger", "entities": [{"start": 16, "end": 30, "label": "ITEM_NAME"}], "intent": "query_sides"},
            {"text": "How much is the veggie burger", "entities": [{"start": 15, "end": 28, "label": "ITEM_NAME"}], "intent": "query_price"},
            {"text": "I'll take two cokes", "entities": [{"start": 11, "end": 16, "label": "ITEM_NAME"}, {"start": 7, "end": 10, "label": "QUANTITY"}], "intent": "add_item"},
            {"text": "Can I get a grilled chicken sandwich with BBQ sauce", "entities": [{"start": 10, "end": 33, "label": "ITEM_NAME"}, {"start": 39, "end": 42, "label": "OPTION_TYPE"}, {"start": 43, "end": 46, "label": "OPTION_VALUE"}], "intent": "add_item"},
            {"text": "Add onion rings to my classic burger", "entities": [{"start": 4, "end": 15, "label": "SIDE"}, {"start": 23, "end": 37, "label": "ITEM_NAME"}], "intent": "add_item"},
            {"text": "I want a classic burger with bacon and swiss cheese", "entities": [{"start": 10, "end": 24, "label": "ITEM_NAME"}, {"start": 30, "end": 35, "label": "TOPPING"}, {"start": 40, "end": 45, "label": "OPTION_VALUE"}], "intent": "add_item"}
        ], f, indent=2)

    train_spacy_model(str(dummy_data_path), str(output_dir))
