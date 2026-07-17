import torch
import torch.nn as nn


class ChessMoveCNN(nn.Module):
    """Compact CNN for chess move prediction from 18-plane board input."""

    def __init__(self, num_classes: int = 4272):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(18, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * 2 * 2, 128),
            nn.ReLU(inplace=True),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        return self.classifier(x)


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def verify_model() -> None:
    torch.manual_seed(0)
    model = ChessMoveCNN()
    model.eval()

    batch_size = 32
    dummy_input = torch.randn(batch_size, 18, 8, 8)
    with torch.no_grad():
        logits = model(dummy_input)

    print(f"Input shape: {tuple(dummy_input.shape)}")
    print(f"Output shape: {tuple(logits.shape)}")
    print(f"Trainable parameters: {count_parameters(model)}")
    print(f"Logits per sample: {logits.shape[1]}")
    print(f"Expected logits per sample: 4272")
    print(f"Output matches expected classes: {logits.shape[1] == 4272}")

    if torch.cuda.is_available():
        device = torch.device("cuda")
        model.to(device)
        dummy_input_cuda = dummy_input.to(device)
        with torch.no_grad():
            cuda_logits = model(dummy_input_cuda)
        print(f"CUDA forward pass successful: {tuple(cuda_logits.shape)}")


if __name__ == "__main__":
    verify_model()
