
import random
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# 1. Generate sample training data
random.seed(42)

X, y = [], []

for _ in range(1000):
    live_range = random.randint(1, 20)
    use_count = random.randint(1, 15)
    next_use_distance = random.randint(1, 20)
    interference_degree = random.randint(0, 10)

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

# 2. Train and test the ML model
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = DecisionTreeClassifier(max_depth=5, random_state=42)
model.fit(X_train, y_train)

predictions = model.predict(X_test)

print("Model accuracy:",
      round(accuracy_score(y_test, predictions) * 100, 2), "%")

# 3. Variables and their features
variables = {
    "a": [3, 8, 2, 1],
    "b": [15, 2, 12, 8],
    "c": [5, 10, 3, 2],
    "d": [18, 3, 15, 9],
    "e": [7, 6, 4, 3]
}

# 4. Predict register allocation
registers = ["R1", "R2", "R3"]
allocation = {}

print("\nREGISTER ALLOCATION RESULTS")
print("-" * 35)

for var, features in variables.items():
    decision = model.predict([features])[0]

    if decision == 0 and registers:
        reg = registers.pop(0)
        allocation[var] = reg
        print(f"{var} -> {reg} (Register allocated)")
    else:
        allocation[var] = "MEMORY"
        print(f"{var} -> MEMORY (Spilled)")

# 5. Display intermediate code
three_address_code = [
    "a = x + y",
    "b = a * z",
    "c = a + b",
    "d = b - c",
    "e = c * d"
]

print("\nINTERMEDIATE CODE")
for instruction in three_address_code:
    print(instruction)

# 6. Display illustrative target code
print("\nILLUSTRATIVE TARGET CODE")

for var, reg in allocation.items():
    if reg == "MEMORY":
        print(f"STORE {var}, [MEMORY]")
    else:
        print(f"MOV {reg}, {var}")

print("\nFINAL ALLOCATION TABLE")
for var, reg in allocation.items():
    print(f"{var}: {reg}")
