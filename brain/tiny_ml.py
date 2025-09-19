from typing import List
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.multioutput import MultiOutputClassifier
from sklearn.tree import DecisionTreeClassifier

class TinyML:
    def __init__(self):
        # Node mapping
        self.node_list = ["keyword", "title","content","image","seo","publish"]

        # Sample training data
        train_data = [
            ("Bắt đầu workflow", ["keyword", "title","content","image","seo","publish"]),
            ("Workflow đầy đủ", ["keyword", "title","content","image","seo","publish"]),
            ("Chỉ tiêu đề và nội dung", ["title","content"]),
            ("Chỉ SEO và xuất bản", ["seo","publish"])
        ]
        prompts, sequences = zip(*train_data)

        # Vector hóa prompt
        self.vectorizer = CountVectorizer()
        X = self.vectorizer.fit_transform(prompts)

        # Multi-label encoding
        Y = []
        for seq in sequences:
            y = [1 if node in seq else 0 for node in self.node_list]
            Y.append(y)

        # Train tiny model
        self.clf = MultiOutputClassifier(DecisionTreeClassifier())
        self.clf.fit(X, Y)

    def decide_sequence(self, prompt: str) -> List[str]:
        X_test = self.vectorizer.transform([prompt])
        y_pred = self.clf.predict(X_test)[0]
        sequence = [node for node, active in zip(self.node_list, y_pred) if active]
        return sequence
