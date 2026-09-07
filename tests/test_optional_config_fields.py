from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import ClassVar

from nightjar import dispatch, from_dict, register


@dataclass
class KnowledgeGraphConfig:
    type: ClassVar[str]


@dataclass
class WikkipediaGraphConfig(KnowledgeGraphConfig):
    type: ClassVar[str] = "wikkipedia"
    # parameters specific to KnowledgeGraph
    predicates: list[str] | None


@register(WikkipediaGraphConfig, type="wikkipedia")
@dataclass
class WikkipediaGraph:
    config: WikkipediaGraphConfig


class TestKnowledgeGraph(unittest.TestCase):
    def test_without_predicates(self):
        config = {
            "type": "wikkipedia",
            "predicates": None,
        }
        kg_cfg = from_dict(WikkipediaGraphConfig, config)
        kg = dispatch(kg_cfg)
        self.assertIsInstance(kg, WikkipediaGraph)
        assert isinstance(kg, WikkipediaGraph)  # for type checkers
        self.assertIsNone(kg.config.predicates)

    def test_with_predicates(self):
        expected_predicates = ["related_to", "part_of"]
        config = {
            "type": "wikkipedia",
            "predicates": expected_predicates,
        }
        kg_cfg = from_dict(WikkipediaGraphConfig, config)
        kg = dispatch(kg_cfg)
        self.assertIsInstance(kg, WikkipediaGraph)
        assert isinstance(kg, WikkipediaGraph)  # for type checkers
        self.assertEqual(kg.config.predicates, expected_predicates)


if __name__ == "__main__":
    unittest.main()
