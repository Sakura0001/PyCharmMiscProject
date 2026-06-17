import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class Python37CompatibilityTests(unittest.TestCase):
    def test_python_sources_do_not_use_dict_union_operator(self):
        offenders = []
        for path in ROOT.glob("*.py"):
            if path.name == Path(__file__).name:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.BitOr):
                    continue
                if isinstance(node.left, ast.Dict) or isinstance(node.right, ast.Dict):
                    offenders.append("%s:%s" % (path.name, node.lineno))

        self.assertEqual(
            offenders,
            [],
            "dict union is Python 3.9+ only; use update/copy for Python 3.7",
        )

    def test_pymysql_dependency_is_capped_to_python37_compatible_series(self):
        requirements = (ROOT / "requirements-largeslb-fuzz.txt").read_text(encoding="utf-8")

        self.assertIn("PyMySQL", requirements)
        self.assertIn("<1.1.2", requirements)


if __name__ == "__main__":
    unittest.main()
