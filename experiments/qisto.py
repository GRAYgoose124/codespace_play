import numpy as np
import torch, torch.nn as nn, torch.optim as optim
from qiskit import Aer, QuantumCircuit, transpile, assemble, execute


class QcDSL:
    aer = Aer.get_backend("aer_simulator")

    def __init__(self, dsl, C):
        self.C = C
        self.dsl = dsl

    def new_qc_from_dsl(self, dsl, argvals):
        qc = QuantumCircuit(self.C["in"])

        for line in dsl.splitlines():
            line = line.strip()
            if line:
                tokens = line.split(",")
                method = tokens[0].strip()
                args = [eval(arg.strip(), argvals) for arg in tokens[1:]]
                getattr(qc, method)(*args)

        return qc

    def get_quantum_output(self, argvals, n_shots=2048):
        qc = self.new_qc_from_dsl(self.dsl, argvals=argvals)

        t_qc = transpile(qc, QcDSL.aer)
        result = QcDSL.aer.run(t_qc, shots=n_shots).result()

        counts = result.get_counts(qc)
        probs = [
            counts.get(bin_str, 0) / n_shots
            for bin_str in [str(bin(i))[2:].zfill(2) for i in range(self.C["out"])]
        ]

        return probs


class QcNet(nn.Module):
    def __init__(self, C):
        super(QcNet, self).__init__()
        self.fc1 = nn.Linear(C["in"], 10)
        self.fc2 = nn.Linear(10, 10)
        self.fc3 = nn.Linear(10, C["out"])

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return torch.softmax(self.fc3(x), dim=1)


def main():
    # init QcDSL and QcNet
    C = {"in": 2, "out": 4}

    dsl = """
    ry, theta1, int(0)
    ry, theta2, int(1)
    cx, int(0), int(1)
    measure_all
    """

    Q = QcDSL(
        dsl,
        C,
    )
    N = QcNet(C)

    # inputs and labels
    thetas = np.linspace(0, 2 * np.pi, 50)
    data = [
        Q.get_quantum_output(argvals={"theta1": theta1, "theta2": theta2})
        for theta1 in thetas
        for theta2 in thetas
    ]
    inputs = torch.tensor(
        [[theta1, theta2] for theta1 in thetas for theta2 in thetas],
        dtype=torch.float32,
    )
    labels = torch.tensor(data, dtype=torch.float32)

    optimizer = optim.Adam(N.parameters(), lr=0.01)
    criterion = nn.MSELoss()

    # train
    for epoch in range(5000):
        optimizer.zero_grad()
        outputs = N(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

    # inference
    with torch.no_grad():
        test_theta1, test_theta2 = np.pi / 4, np.pi / 3
        prediction = N(torch.tensor([[test_theta1, test_theta2]]))
        print(
            f"For theta1 = {test_theta1} and theta2 = {test_theta2}, predicted probabilities: {prediction.numpy()[0]}\n"
            f"Actual probabilities: {Q.get_quantum_output({'theta1': test_theta1, 'theta2': test_theta2})}"
        )


if __name__ == "__main__":
    main()
