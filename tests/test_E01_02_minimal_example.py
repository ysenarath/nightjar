import unittest
from typing import ClassVar

from nightjar import AutoModule, BaseConfig, BaseModule


class KnowledgeGraphConfig(BaseConfig, dispatch=["type"]):
    type: ClassVar[str]


class KnowledgeGraph(BaseModule):
    config: KnowledgeGraphConfig


class AutoKnowledgeGraph(AutoModule):
    pass


class WikkipediaGraphConfig(KnowledgeGraphConfig):
    type: ClassVar[str] = "wikkipedia"
    # parameters specific to KnowledgeGraph
    predicates: list[str] | None


class WikkipediaGraph(KnowledgeGraph):
    config: WikkipediaGraphConfig


class TestKnowledgeGraph(unittest.TestCase):
    def test_without_predicates(self):
        config = {
            "type": "wikkipedia",
            "predicates": None,
        }
        kg_cfg = KnowledgeGraphConfig.from_dict(config)
        kg = AutoKnowledgeGraph(kg_cfg)
        self.assertIsInstance(kg, WikkipediaGraph)
        assert isinstance(kg, WikkipediaGraph)  # for type checkers
        self.assertIsNone(kg.config.predicates)

    def test_with_predicates(self):
        expected_predicates = ["related_to", "part_of"]
        config = {
            "type": "wikkipedia",
            "predicates": expected_predicates,
        }
        kg_cfg = KnowledgeGraphConfig.from_dict(config)
        kg = AutoKnowledgeGraph(kg_cfg)
        self.assertIsInstance(kg, WikkipediaGraph)
        assert isinstance(kg, WikkipediaGraph)  # for type checkers
        self.assertEqual(kg.config.predicates, expected_predicates)


if __name__ == "__main__":
    unittest.main()
