import os
import torch


class SimplePredictor(torch.nn.Module):
    def __init__(self, input_size, output_size):
        super(SimplePredictor, self).__init__()
        self.linear = torch.nn.Linear(input_size, output_size)

    def forward(self, x):
        return self.linear(x)

    def predict(self, x):
        return self.forward(x)

    def train(self, x, y):
        y_pred = self.forward(x)
        loss = torch.nn.functional.mse_loss(y_pred, y)
        loss.backward()
        return loss.item()

    def fit(self, x, y, epochs=5000, lr=0.01):
        optimizer = torch.optim.Adam(self.parameters(), lr=lr)
        for _ in range(epochs):
            optimizer.zero_grad()
            loss = self.train(x, y)
            optimizer.step()
        return loss

    def evaluate(self, x, y):
        y_pred = self.predict(x)
        return torch.nn.functional.mse_loss(y_pred, y).item()

    def score(self, x, y):
        return self.evaluate(x, y)


def main():
    if os.path.exists("model.pt"):
        model = SimplePredictor(1, 1)
        model.load_state_dict(torch.load("model.pt"))
        print("Model loaded")
    else:
        # Create a model
        model = SimplePredictor(1, 1)

    # Create data
    x = torch.arange(0, 10, 0.1).reshape(-1, 1)
    y = x * 2 + 1

    # Train the model
    loss = model.fit(x, y)
    print(f"Loss: {loss}")

    # Evaluate the model
    score = model.evaluate(x, y)
    print(f"Score: {score}")

    # Predict
    y_pred = model.predict(x)
    # zip x, y, y_pred
    for x_i, y_i, y_pred_i in zip(x, y, y_pred):
        print(f"{x_i.item():.2f} {y_i.item():.2f} {y_pred_i.item():.2f}")

    # Save the model
    torch.save(model.state_dict(), "model.pt")


if __name__ == "__main__":
    main()
