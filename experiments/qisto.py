import itertools
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
                args = []
                for arg in tokens[1:]:
                    arg = arg.strip()
                    if arg.isnumeric():
                        if "." in arg:
                            args.append(float(arg))
                        else:
                            args.append(int(arg))
                    else:
                        if arg in argvals:
                            args.append(argvals[arg])
                        else:
                            args.append(arg)
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


class QcNetTrainer:
    def __init__(self, C):
        self.C = C
        self.model = QcNet(C)
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.01)
        self.criterion = nn.MSELoss()

        self._qcdsls = []

    @property
    def circuits(self):
        return self._qcdsls

    def add_dsl(self, dsl):
        self._qcdsls.append(QcDSL(dsl, self.C))

    def train(self, inputs, labels):
        for epoch in range(5000):
            self.optimizer.zero_grad()
            outputs = self.model(inputs)
            loss = self.criterion(outputs, labels)
            loss.backward()
            self.optimizer.step()

    def infer(self, circuit, **kwargs):
        # figure out arg order by inspecting the dsl for kwargs
        args = []
        for line in self.circuits[circuit].dsl.splitlines():
            line = line.strip()
            if line:
                tokens = line.split(",")
                for token in tokens[1:]:
                    token = token.strip()
                    if token in kwargs:
                        args.append(kwargs[token])

        # infer
        with torch.no_grad():
            prediction = self.model(torch.tensor([args]))
            print(
                f"For {args=}, predicted probabilities: {prediction.numpy()[0]}\n"
                f"Actual probabilities: {self.circuits[circuit].get_quantum_output(kwargs)}\n"
            )

    def gen_data_from_linspace(self, circuit, linspaces, mapping):
        """
        Generate inputs and labels using multiple linspaces and a given mapping.

        Args:
        - circuit: The circuit for which the data is being generated.
        - linspaces: A list of linspaces. Each linspace corresponds to an input.
        - mapping: A function that maps values from linspaces to desired argument values.

        Returns:
        - inputs: Torch tensor of input values.
        - labels: Torch tensor of labels generated from the circuit.
        """

        data = []
        inputs_list = []

        # Using itertools.product to generate all combinations of values from linspaces
        for values in itertools.product(*linspaces):
            data.append(
                self.circuits[circuit].get_quantum_output(argvals=mapping(*values))
            )
            inputs_list.append(values)

        inputs = torch.tensor(inputs_list, dtype=torch.float32)
        labels = torch.tensor(data, dtype=torch.float32)

        return inputs, labels


def main():
    # init QcDSL and QcNet
    C = {"in": 2, "out": 4}

    T = QcNetTrainer(C)
    T.add_dsl(
        """
    ry, theta1, 0
    ry, theta2, 1
    cx, 0, 1
    measure_all
    """
    )
    T.add_dsl(
        """
    h, 0
    ry, theta1, 1
    cx, 0, 1
    ry, theta2, 0
    cx, 1, 0
    measure_all
    """
    )

    # inputs and labels
    selC = 0
    inputs, labels = T.gen_data_from_linspace(
        selC,
        [np.linspace(0, 2 * np.pi, 50), np.linspace(0, 2 * np.pi, 50)],
        mapping=lambda theta1, theta2: {"theta1": theta1, "theta2": theta2},
    )

    # train
    T.train(inputs, labels)

    # inference
    T.infer(selC, theta1=np.pi / 4, theta2=np.pi / 3)


if __name__ == "__main__":
    main()
