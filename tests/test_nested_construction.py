"""Construction and serialization of nested dataclass configurations."""

from __future__ import annotations

import json
import unittest
from dataclasses import dataclass, field

from nightjar import dispatch, from_dict, register, to_dict


@dataclass
class Endpoint:
    port: int
    enabled: bool = True


@dataclass
class Group:
    primary: Endpoint
    replicas: list[Endpoint]
    named: dict[str, Endpoint]


@dataclass
class ServiceConfig:
    group: Group
    groups: dict[str, list[Group]]
    indexed: list[dict[int, Endpoint]]
    optional: Endpoint | None = None
    spare: list[Endpoint] = field(default_factory=list)
    kind: str = "service"


@register(kind="service")
@dataclass
class Service:
    config: ServiceConfig


def group_data():
    return {
        "primary": {"port": "8000"},
        "replicas": [{"port": "8001", "enabled": "false"}],
        "named": {"backup": {"port": "8002"}},
    }


class TestNestedConstruction(unittest.TestCase):
    def test_nested_dataclasses_lists_and_dicts(self):
        data = {
            "kind": "service",
            "group": group_data(),
            "groups": {"west": [group_data()]},
            "indexed": [{"1": {"port": "9000"}}],
        }
        service = dispatch(ServiceConfig, data)
        config = service.config
        self.assertIsInstance(config.group, Group)
        self.assertEqual(config.group.primary, Endpoint(8000))
        self.assertEqual(config.group.replicas, [Endpoint(8001, False)])
        self.assertEqual(config.group.named, {"backup": Endpoint(8002)})
        self.assertEqual(config.groups["west"], [config.group])
        self.assertEqual(config.indexed, [{1: Endpoint(9000)}])
        self.assertIsNone(config.optional)
        self.assertEqual(config.spare, [])
        saved = json.loads(json.dumps(to_dict(config)))
        self.assertEqual(dispatch(ServiceConfig, saved).config, config)
        self.assertEqual(data["group"]["primary"]["port"], "8000")

    def test_existing_nested_instances_are_preserved(self):
        endpoint = Endpoint(8000)
        config = from_dict(
            Group,
            {
                "primary": endpoint,
                "replicas": [endpoint],
                "named": {"backup": endpoint},
            },
        )
        self.assertIs(config.primary, endpoint)
        self.assertIs(config.replicas[0], endpoint)
        self.assertIs(config.named["backup"], endpoint)

    def test_unknown_fields_rejected_at_each_nested_position(self):
        for position in ("primary", "replicas", "named"):
            data = group_data()
            invalid = {"port": 8000, "typo": True}
            data[position] = {
                "primary": invalid,
                "replicas": [invalid],
                "named": {"backup": invalid},
            }[position]
            with self.subTest(position=position), self.assertRaisesRegex(
                TypeError, "Undeclared fields for Endpoint include typo"
            ):
                from_dict(Group, data)

    def test_nested_required_field_is_not_defaulted(self):
        data = group_data()
        data["primary"] = {}
        with self.assertRaises(TypeError):
            from_dict(Group, data)

    def test_optional_nested_value_and_empty_containers(self):
        config = from_dict(
            ServiceConfig,
            {
                "group": {
                    "primary": {"port": 8000},
                    "replicas": [],
                    "named": {},
                },
                "groups": {},
                "indexed": [],
                "optional": {"port": "8003"},
            },
        )
        self.assertEqual(config.optional, Endpoint(8003))
        self.assertEqual(config.group.replicas, [])
        self.assertEqual(config.group.named, {})
        self.assertEqual(config.groups, {})
        self.assertEqual(config.indexed, [])


if __name__ == "__main__":
    unittest.main()
