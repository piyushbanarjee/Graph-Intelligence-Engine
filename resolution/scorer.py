from rapidfuzz import fuzz
from ingestion.store import entities_doc_id

def name_similarity_score(name1, name2):
    similarity_score = (fuzz.token_sort_ratio(name1, name2))/100
    return similarity_score

def cooccurrence_score(name1, name2):
    n1 = set(entities_doc_id(name1))
    n2 = set(entities_doc_id(name2))

    intersection = n1 & n2 
    union  = n1| n2

    if len(union) == 0:
        return 0.0
    score = len(intersection) / len(union)
    return score

def build_feature_vector(name1, name2):
    return [name_similarity_score(name1, name2), cooccurrence_score(name1, name2)]

if __name__ == "__main__":
    print(name_similarity_score("Zakit okemfadsnfklnklfaeklm","Piyush Banarjee"),
    name_similarity_score("Ajay Bhattacharya","Piyush Banarjee"),
    name_similarity_score("Piyush","Piyush Banarjee"))