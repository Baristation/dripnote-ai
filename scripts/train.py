import argparse
from pathlib import Path

from src.services.training_service import TrainingService


def main() -> None:
    parser = argparse.ArgumentParser(description="간단한 학습 스텁 실행")
    parser.add_argument("--train-path", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    # CLI에서 받은 학습 경로를 서비스 계층으로 전달한다.
    service = TrainingService()
    service.start_training(train_path=args.train_path, output_dir=args.output_dir)
    print(f"training artifacts created in {Path(args.output_dir)}")


if __name__ == "__main__":
    main()
