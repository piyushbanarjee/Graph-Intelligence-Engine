training_pairs1 = [
    # --- Same person: clear name variants (label 1) ---
    ("P. Banarjee", "Piyush Banarjee", 1),
    ("Piyush B.", "Piyush Banarjee", 1),
    ("Tarun Wig", "T. Wig", 1),
    ("Abhishek Sharma", "A. Sharma", 1),
    ("Clara Vance", "C. Vance", 1),
    ("Marcus Chen", "Marcus C.", 1),

    # --- Same person: harder variants - nicknames, reordering, initials (label 1) ---
    ("Piyush Banarjee", "Banarjee, Piyush", 1),
    ("Clara Vance", "Clara V.", 1),
    ("Tarun Wig", "Tarun W.", 1),
    ("Abhishek Sharma", "Abhishek S.", 1),
    ("Marcus Chen", "M. Chen", 1),

    # --- Different people: obviously unrelated names (label 0) ---
    ("Piyush Banarjee", "Tarun Wig", 0),
    ("Clara Vance", "Marcus Chen", 0),
    ("Abhishek Sharma", "Clara Vance", 0),
    ("Tarun Wig", "Marcus Chen", 0),
    ("Piyush Banarjee", "Abhishek Sharma", 0),

    # --- Different people: adversarial, similar-sounding names (label 0) ---
    ("Piyush Banarjee", "Pratyush Bansal", 0),
    ("Piyush Banarjee", "Pratyush Banerjee", 0),
    ("Clara Vance", "Clara Vince", 0),
    ("Marcus Chen", "Marcus Chan", 0),
    ("Tarun Wig", "Tarun Vig", 0),

    # --- Different organizations posing as similar (label 0) ---
    ("Innefu Labs", "Infinity Labs", 0),
    ("FinTech Corp", "FinTech Global", 0),
    ("DataGlobe Inc", "DataGlobal Inc", 0),

    # --- Same organization: variants (label 1) ---
    ("Innefu Labs", "Innefu", 1),
    ("FinTech Corp", "FinTech Corporation", 1),
    ("Ministry of Home Affairs", "MHA", 1),
]

training_pairs2 = [
    # --- Same person: LOW similarity matches (mononym / first-name-only) ---
    ("Piyush Banarjee", "Piyush", 1),
    ("Clara Vance", "Clara", 1),
    ("Marcus Chen", "Marcus", 1),
    ("Abhishek Sharma", "Abhishek", 1),
    ("Tarun Wig", "Wig", 1),

    # --- Same person: title/role prefix variants ---
    ("Abhishek Sharma", "Mr. Sharma", 1),
    ("Clara Vance", "Ms. Vance", 1),

    # --- Different people: SAME surname (the real gap — high-ish similarity, label 0) ---
    ("Piyush Banarjee", "Ajay Banarjee", 0),
    ("Clara Vance", "Marcus Vance", 0),
    ("Tarun Wig", "Priya Wig", 0),
    ("Abhishek Sharma", "Rohan Sharma", 0),

    # --- Different people: SAME first name, different surname ---
    ("Piyush Banarjee", "Piyush Mehta", 0),
    ("Clara Vance", "Clara Bhatt", 0),
    ("Marcus Chen", "Marcus Whitfield", 0),

    # --- Same org: abbreviation/acronym edge cases ---
    ("Innefu Labs", "IL", 1),
    ("Ministry of Home Affairs", "Ministry of Home Affairs, India", 1),

    # --- Different orgs: acronym collision (label 0) ---
    ("Ministry of Home Affairs", "Mental Health Association", 0),

    # --- Same person: case/spacing noise (label 1) ---
    ("piyush banarjee", "Piyush Banarjee", 1),
    ("CLARA VANCE", "Clara Vance", 1),

    # --- Different people: completely unrelated, low similarity (label 0) ---
    ("Zakit Okemfa", "Piyush Banarjee", 0),
    ("FinTech Corp", "Clara Vance", 0),
]
training_pairs = training_pairs1+ training_pairs2

''
if __name__ == "__main__":

    for pair in training_pairs:
        print(pair)
    print(f"\nTotal pairs: {len(training_pairs)}")
    same = sum(1 for p in training_pairs if p[2] == 1)
    diff = sum(1 for p in training_pairs if p[2] == 0)
    print(f"Same person/entity (1): {same}")
    print(f"Different person/entity (0): {diff}")