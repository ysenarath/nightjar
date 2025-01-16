from __future__ import annotations

from typing import ClassVar

from nightjar import AutoModule, BaseConfig, BaseModule


class ModelConfig(BaseConfig, dispatch=["type"]):
    type: ClassVar[str]


class Model(BaseModule):
    config: ModelConfig

    def __post_init__(self) -> None:
        print("Model.__post_init__")

    def train(self, x, y):
        raise NotImplementedError

    def predict(self, x):
        raise NotImplementedError


class AutoModel(AutoModule):
    def __new__(cls, config: ModelConfig) -> Model:
        approach = super().__new__(cls, config)
        if not isinstance(approach, Model):
            msg = (
                f"expected {Model.__name__}, got {approach.__class__.__name__}"
            )
            raise TypeError(msg)
        return approach


# define the models


class LinearSVCConfig(ModelConfig):
    type: ClassVar[str] = "SVM"
    penalty: str = "l2"
    loss: str = "squared_hinge"
    dual: bool = True
    tol: float = 1e-4
    C: float = 1.0
    multi_class: str = "ovr"
    fit_intercept: bool = True
    intercept_scaling: float = 1
    class_weight: dict = None
    verbose: int = 0
    random_state: int = None
    max_iter: int = 1000


class LinearSVC(Model):
    config: LinearSVCConfig

    def __post_init__(self) -> None:
        super().__post_init__()
        self.state = "not trained"

    def train(self, x, y):
        print(f"LinearSVC.train (state: {self.state})")
        print(f"Using config: {self.config}")

    def predict(self, x):
        print(f"LinearSVC.predict (state: {self.state})")


class RandomForestClassifierConfig(ModelConfig):
    type: ClassVar[str] = "RF"
    n_estimators: int = 100
    criterion: str = "gini"
    max_depth: int = None
    min_samples_split: int = 2
    min_samples_leaf: int = 1
    min_weight_fraction_leaf: float = 0.0
    max_features: str = "sqrt"
    max_leaf_nodes: int = None
    min_impurity_decrease: float = 0.0
    bootstrap: bool = True
    oob_score: bool = False
    n_jobs: int = None
    random_state: int = None
    verbose: int = 0
    warm_start: bool = False
    class_weight: dict = None
    ccp_alpha: float = 0.0
    max_samples: int = None


class RandomForestClassifier(Model):
    config: RandomForestClassifierConfig

    def __post_init__(self) -> None:
        super().__post_init__()
        self.state = "not trained"

    def train(self, x, y):
        print(f"RandomForest.train (state: {self.state})")
        print(f"Using config: {self.config}")

    def predict(self, x):
        print(f"RandomForest.predict (state: {self.state})")


def main():
    config = ModelConfig.from_dict({"type": "SVM"})
    model = AutoModel(config)
    model.train([1, 2, 3], [4, 5, 6])
    model.predict([7, 8, 9])

    config = ModelConfig.from_dict({"type": "RF"})
    model = AutoModel(config)
    model.train([1, 2, 3], [4, 5, 6])
    model.predict([7, 8, 9])


if __name__ == "__main__":
    main()
