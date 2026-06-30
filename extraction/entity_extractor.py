import ollama
from pydantic import BaseModel, Field
from typing import Literal
from ingestion.embedder import collection
from ingestion.store import save_entites, save_relationships, save_entity_alias
from resolution.classifier import resolve_entity
from graph.builder import add_all_entities, add_all_relationships, save_graph

class ER_entity(BaseModel):
    name: str = Field(description="Name of the entity")
    role: str = Field(description="What is the entity? is it a person, organization, something else")

class EntityList(BaseModel):
    entities: list[ER_entity] = Field(description="all the major entities of the data")

def extract_entities(text, known_names: list[str] = None, hint_names: list[str] = None):
    known_names = known_names or []
    hint_names = hint_names or []

    exclusion_note = f"\nDo not re-list these already-found entities: {known_names}" if known_names else ""
    hint_note = (
        f"\nIn particular, make sure to identify and classify these specific entities, "
        f"which were referenced but not yet captured: {hint_names}"
        if hint_names else ""
    )

    response = ollama.generate(
        model='llama3.1',
        prompt=f"""
        Extract all major entities such as people, organizations etc, from this text.
        {exclusion_note}
        {hint_note}
        Text: {text}
        """,
        format=EntityList.model_json_schema(),
        options={'temperature': 0, 'num_ctx': 8192},
        stream=False
    )
    return EntityList.model_validate_json(response['response'])

def build_relation_model(entity_names: list[str]):
    LabelType = Literal[tuple(entity_names)] if entity_names else str

    class ER_relation(BaseModel):
        origin: LabelType           # type: ignore[reportInvalidTypeForm]
        destination: LabelType      # type: ignore[reportInvalidTypeForm]
        label: str = Field(description="Why/what is the relation between origin and destination")

    class RelationList(BaseModel):
        relationships: list[ER_relation] = Field(description="Major direct relations between the entities")
        unrecognized_entities: list[str] = Field(
            default_factory=list,
            description="Any entity name you needed for a relation but that was NOT in the allowed entity list. Log it here instead of forcing it into a wrong label."
        )

    return RelationList

def extract_relations(text, entity_names: list[str]):
    RelationList = build_relation_model(entity_names)

    response = ollama.generate(
        model='llama3.1',
        prompt=f"""
        Given these entities: {entity_names}
        Extract all major relations between them from this text.
        origin and destination must be exact names from the entity list above.
        If a relation involves someone/something NOT in that list, do not force a wrong name —
        instead add that missing name to unrecognized_entities.
        Text: {text}
        """,
        format=RelationList.model_json_schema(),
        options={'temperature': 0, 'num_ctx': 8192},
        stream=False
    )
    return RelationList.model_validate_json(response['response'])

def entity_json(text, max_retries=2):
    entity_result = extract_entities(text)
    entity_names = [e.name for e in entity_result.entities]

    relation_result = extract_relations(text, entity_names)

    retries = 0
    while relation_result.unrecognized_entities and retries < max_retries:
        missing_result = extract_entities(
            text,
            known_names=entity_names,
            hint_names=relation_result.unrecognized_entities
        )
        new_entities = [e for e in missing_result.entities if e.name not in entity_names]

        if not new_entities:
            break

        entity_result.entities.extend(new_entities)
        entity_names = [e.name for e in entity_result.entities]

        relation_result = extract_relations(text, entity_names)
        retries += 1

    return entity_result, relation_result


def extract_from_document(document_id):
    document_chunks = collection.get(where={"document_id": document_id})
    chunk_ids = document_chunks['ids']
    chunk_texts = document_chunks["documents"]
    resolution_cache = {}  # raw_name -> (canonical_name, confidence)

    for id, chunk in zip(chunk_ids, chunk_texts):
        try:
            entity_result, relation_result = entity_json(text=chunk)
        except Exception as e:
            print(f"Chunk Number {id} failed, continuing to next chunk \n Error: \n {e}")
            continue

        for entity in entity_result.entities:
            if entity.name not in resolution_cache:
                resolution_cache[entity.name] = resolve_entity([], entity.name)
            canonical_name, confidence = resolution_cache[entity.name]
            final_name = canonical_name if canonical_name else entity.name
            
            # Save the entity with its canonical name
            save_entites(
                document_id=document_id,
                name=final_name,
                role=entity.role
            )
            
            # If this is an alias (different from canonical), save the alias mapping
            if canonical_name and entity.name != canonical_name:
                save_entity_alias(canonical_name, entity.name, confidence)

        for relationship in relation_result.relationships:
            origin_canonical, _ = resolution_cache.get(relationship.origin, (None, 0.0))
            dest_canonical, _ = resolution_cache.get(relationship.destination, (None, 0.0))
            save_relationships(
                document_id=document_id,
                origin=origin_canonical if origin_canonical else relationship.origin,
                destination=dest_canonical if dest_canonical else relationship.destination,
                label=relationship.label
            )

    # Rebuild and persist the graph now that this document's data is saved
    add_all_entities()
    add_all_relationships()
    save_graph()

if __name__ == "__main__":
    print(entity_json(""" So, I was looking over the file for Clara Vance—she's 42 this year,
                     born in '84 if my math holds up. Her supervisor, 
                    Marcus, mentioned she's been absolutely crushing it at her current gig as a Lead Data Architect over at FinTech Corp,
                     where she's already clocked in 4 years.
                     Before that, she spent 3 years grinding as a Senior Analyst at DataGlobe Inc. Skill-wise,
                     she's a powerhouse; she practically lives in SQL and Python, and lately, 
                    she's been doing a ton of cloud orchestration with AWS. Write a quick snippet summarizing red her profile. """))