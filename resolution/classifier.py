from xgboost import XGBClassifier
import pickle
from resolution.scorer import build_feature_vector
from resolution.training_data import training_pairs
from ingestion.store import get_all_entity_names


def train_classifier():
    x = []
    y = []

    for i in training_pairs:
        x.append(build_feature_vector(i[0], i[1]))
        y.append(i[2])

    model = XGBClassifier()
    model.fit(x,y)

    with open ('resolution/XGB_entity_model.pkl', 'wb') as file:
        pickle.dump(model, file)


def resolve_entity(new_name):
    with open ('resolution/XGB_entity_model.pkl', 'rb') as file:
        model = pickle.load(file)

    names = get_all_entity_names()
    same_person_probability = {}

    for name in names:
        x = model.predict_proba([build_feature_vector(name, new_name)])
        is_same_person = x[0][1]
        same_person_probability.update({name: is_same_person})
    
    if not same_person_probability:
        return None, 0.0
    
    best_match = max(same_person_probability, key = same_person_probability.get)
    best_value = same_person_probability[best_match]

    return best_match, best_value

if __name__ == "__main__":
    train_classifier()