import numpy as np
import torch, torch.nn as nn, torch.optim as optim
from qiskit import Aer, QuantumCircuit, transpile, assemble, execute


class QcDSL:
    def __init__(self, dsl):
        self._qc = QuantumCircuit(2)
        self.dsl = dsl

    @property
    def qc(self):
        return self._qc

    def from_dsl(self, dsl, args_vals=None):
        for line in dsl.splitlines():
            line = line.strip()
            if line:
                tokens = line.split(",")
                method = tokens[0].strip()
                args = [eval(arg.strip(), args_vals or {}) for arg in tokens[1:]]
                getattr(self.qc, method)(*args)

    def new_qc(self, C=[2], args_vals=None):
        self._qc = QuantumCircuit(*C)
        self.from_dsl(self.dsl, args_vals)

    def get_quantum_output(self, argvals):
        self.new_qc(args_vals=argvals)

        aer_sim = Aer.get_backend("aer_simulator")

        t_qc = transpile(self.qc, aer_sim)
        qobj = assemble(t_qc, shots=4096)
        result = aer_sim.run(qobj).result()

        counts = result.get_counts(self.qc)
        probs = [counts.get(bin_str, 0) / 4096 for bin_str in ["00", "01", "10", "11"]]

        return probs


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.fc1 = nn.Linear(2, 10)
        self.fc2 = nn.Linear(10, 10)
        self.fc3 = nn.Linear(10, 4)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return torch.softmax(self.fc3(x), dim=1)


Q = QcDSL(
    """
ry, theta1, int(0)
ry, theta2, int(1)
cx, int(0), int(1)
measure_all"""
)

thetas = np.linspace(0, 2 * np.pi, 50)
data = [
    Q.get_quantum_output(argvals={"theta1": theta1, "theta2": theta2})
    for theta1 in thetas
    for theta2 in thetas
]
inputs = torch.tensor(
    [[theta1, theta2] for theta1 in thetas for theta2 in thetas], dtype=torch.float32
)
labels = torch.tensor(data, dtype=torch.float32)

net = Net()
optimizer = optim.Adam(net.parameters(), lr=0.01)
criterion = nn.MSELoss()

for epoch in range(5000):
    optimizer.zero_grad()
    outputs = net(inputs)
    loss = criterion(outputs, labels)
    loss.backward()
    optimizer.step()

with torch.no_grad():
    test_theta1, test_theta2 = np.pi / 4, np.pi / 3
    prediction = net(torch.tensor([[test_theta1, test_theta2]]))
    print(
        f"For theta1 = {test_theta1} and theta2 = {test_theta2}, predicted probabilities: {prediction.numpy()[0]}\n"
        f"Actual probabilities: {Q.get_quantum_output({'theta1': test_theta1, 'theta2': test_theta2})}"
    )
