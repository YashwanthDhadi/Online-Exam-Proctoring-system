"""
Exam question bank.
Easily replaceable with a real database/API-backed question set.
"""

EXAM_QUESTIONS = [
    {
        "id": 1,
        "type": "mcq",
        "question": "What is Artificial Intelligence?",
        "options": {
            "A": "A type of machine learning algorithm only",
            "B": "Intelligence demonstrated by machines, simulating human cognition",
            "C": "A programming language developed by MIT",
            "D": "A data storage technology"
        },
        "marks": 2
    },
    {
        "id": 2,
        "type": "mcq",
        "question": "Which of the following is a supervised learning algorithm?",
        "options": {
            "A": "K-Means Clustering",
            "B": "Principal Component Analysis (PCA)",
            "C": "Linear Regression",
            "D": "DBSCAN"
        },
        "marks": 2
    },
    {
        "id": 3,
        "type": "mcq",
        "question": "What does CNN stand for in deep learning?",
        "options": {
            "A": "Central Neural Node",
            "B": "Convolutional Neural Network",
            "C": "Computed Numeric Network",
            "D": "Connected Node Network"
        },
        "marks": 2
    },
    {
        "id": 4,
        "type": "mcq",
        "question": "Which Python library is primarily used for machine learning?",
        "options": {
            "A": "NumPy",
            "B": "Pandas",
            "C": "Scikit-learn",
            "D": "Matplotlib"
        },
        "marks": 2
    },
    {
        "id": 5,
        "type": "mcq",
        "question": "What is overfitting in machine learning?",
        "options": {
            "A": "Model performs well on training data but poorly on new data",
            "B": "Model is too simple to capture patterns",
            "C": "Training dataset is too small",
            "D": "Learning rate is too low"
        },
        "marks": 2
    },
    {
        "id": 6,
        "type": "mcq",
        "question": "What activation function outputs values between 0 and 1?",
        "options": {
            "A": "ReLU",
            "B": "Tanh",
            "C": "Sigmoid",
            "D": "Softmax"
        },
        "marks": 2
    },
    {
        "id": 7,
        "type": "short_answer",
        "question": "Explain the difference between supervised and unsupervised learning. "
                    "Provide one real-world example of each.",
        "marks": 5
    },
    {
        "id": 8,
        "type": "short_answer",
        "question": "What is the role of a loss function in training a neural network? "
                    "Describe how gradient descent minimizes it.",
        "marks": 5
    },
    {
        "id": 9,
        "type": "short_answer",
        "question": "Define precision and recall in the context of a classification model. "
                    "When would you prioritize recall over precision?",
        "marks": 5
    },
    {
        "id": 10,
        "type": "short_answer",
        "question": "Briefly describe what a Transformer architecture is and why it "
                    "revolutionized Natural Language Processing (NLP).",
        "marks": 6
    },
]

TOTAL_MARKS = sum(q['marks'] for q in EXAM_QUESTIONS)
