
import random
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# --------------------------------------------------
# 1. Generate training data for the ML model
# Features:
# [live_range, use_count, next_use_distance, interference_degree]
# Target: 0 = Allocate Register, 1 = Spill to Memory
# --------------------------------------------------

random.seed(42)

X = []
y = []

for _ in range(1000):
    live_range = random.randint(1, 20)
    use_count = random.randint(1, 15)
    next_use_distance = random.randint(1, 20)
    interference_degree = random.randint(0, 10)

    # Training label based on a heuristic for this prototype
    spill = int(
        (live_range > 12 and use_count < 5)
        or (interference_degree > 7 and next_use_distance > 10)
    )

    X.append([
        live_range,
        use_count,
        next_use_distance,
        interference_degree
    ])
    y.append(spill)

# --------------------------------------------------
# 2. Train the Machine Learning model
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = DecisionTreeClassifier(max_depth=5, random_state=42)
model.fit(X_train, y_train)

predictions = model.predict(X_test)

print("ML Model Accuracy:",
      round(accuracy_score(y_test, predictions) * 100, 2), "%")

# --------------------------------------------------
# 3. Intermediate representation (three-address code)
# --------------------------------------------------

variables = {
    "a": [3, 8, 2, 1],
    "b": [15, 2, 12, 8],
    "c": [5, 10, 3, 2],
    "d": [18, 3, 15, 9],
    "e": [7, 6, 4, 3]
}

three_address_code = [
    "a = x + y",
    "b = a * z",
    "c = a + b",
    "d = b - c",
    "e = c * d"
]

# --------------------------------------------------
# 4. Predict allocation decisions
# --------------------------------------------------

print("\nRegister Allocation Predictions")
print("-" * 60)

registers = ["R1", "R2", "R3"]
available_registers = registers.copy()
allocation = {}

for var, features in variables.items():
    decision = model.predict([features])[0]

    if decision == 0 and available_registers:
        reg = available_registers.pop(0)
        allocation[var] = reg
        print(f"{var} -> {reg} (Register allocated)")
    else:
        allocation[var] = "MEMORY"
        print(f"{var} -> MEMORY (Spilled)")

# --------------------------------------------------
# 5. Generate illustrative target code
# --------------------------------------------------

print("\nIntermediate Code:")
for instruction in three_address_code:
    print(instruction)

print("\nGenerated Target Code (illustrative):")

for var in variables:
    destination = allocation[var]

    if destination == "MEMORY":
        print(f"STORE {var}, [MEMORY]")
    else:
        print(f"MOV {destination}, {var}")

print("\nFinal Allocation Table")
print("-" * 30)
for var, reg in allocation.items():
    print(f"{var:5} : {reg}")
