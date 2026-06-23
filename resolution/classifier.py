from xgboost import XGBClassifier
import pickle
from resolution.scorer import build_feature_vector
from resolution.training_data import training_pairs
from ingestion.store import get_all_entity_data


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


# Threshold set to 0.9 to prevent all passthroughs because XGB is giving same scores to all, and not to the correct answer
def resolve_entity(names, new_name, threshold= 0.9):
    with open('resolution/XGB_entity_model.pkl', 'rb') as file:
        model = pickle.load(file)

    if not names:
        names = get_all_entity_data()[0]

    same_person_probability = {}
    for name in names:
        x = model.predict_proba([build_feature_vector(name, new_name)])
        is_same_person = x[0][1]
        same_person_probability.update({name: is_same_person})

    if not same_person_probability:
        return None, 0.0

    best_match = max(same_person_probability, key=same_person_probability.get)
    best_value = same_person_probability[best_match]

    if best_value < threshold:
        return None, 0.0

    return best_match, best_value

if __name__ == "__main__":
    from resolution.training_data import training_pairs

    labels = [pair[2] for pair in training_pairs]
    print(labels)
    print("Positives:", sum(labels), "Total:", len(labels))
    print([build_feature_vector(p[0], p[1]) for p in training_pairs[:5]])