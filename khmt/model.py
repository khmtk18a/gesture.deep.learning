from pytorch_lightning import LightningModule
from torch import nn, Tensor
from torch.optim import Optimizer, Adam
from torchmetrics.functional import accuracy
from typing import TypedDict

classes = ('Paper', 'Rock', 'Scissors')

class Output(TypedDict):
    y: Tensor
    y_hat: Tensor

class Result(TypedDict):
    loss: Tensor
    output: Output

class Network(LightningModule):
    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(3, 6, 5),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(6, 16, 5),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Flatten(1),
            nn.ReLU(),
            nn.Linear(16*5*5, 120),
            nn.ReLU(),
            nn.Linear(120, 84),
            nn.ReLU(),
            nn.Linear(84, 3)
        )

    def forward(self, x: Tensor) -> Tensor:
        return self.net(x)

    def share_step(self, batch) -> Result:
        x, y = batch
        y_hat = self(x)
        loss = nn.functional.cross_entropy(y_hat, y)
        return {'loss': loss, 'output': {'y': y, 'y_hat': y_hat}}

    def training_step(self, batch, batch_idx):
        return self.share_step(batch)

    def validation_step(self, batch, batch_idx):
        ret = self.share_step(batch)
        self.log("val_loss", ret['loss'])
        return ret

    def test_step(self, batch, batch_idx):
        ret = self.share_step(batch)
        acc = accuracy(ret['output']['y_hat'], ret['output']['y'], task="multiclass", num_classes=len(classes))
        metrics = {"test_acc": acc, "test_loss": ret['loss']}
        self.log_dict(metrics)

        return metrics

    def configure_optimizers(self) -> Optimizer:
        optimizer = Adam(self.parameters(), lr=0.001)

        return optimizer
