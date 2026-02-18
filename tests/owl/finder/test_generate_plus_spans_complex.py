#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Docs: docs/architecture.md


import unittest

from mutato.finder.singlequery.svc import GeneratePlusSpans

class TestSpanGeneration(unittest.TestCase):

    def setUp(self) -> None:
        self.generate = GeneratePlusSpans().process

    def tearDown(self) -> None:
        self.generate = None

    def test_generate(self) -> None:

        result = self.generate({
            "penetrating_eye_trauma":
                [
                    "penetrating eye trauma",
                    "eye+penetrate",
                    "eye_trauma+penetrating_wound",
                    "eye+penetrating_wound",
                    "penetrate+eye_trauma",
                    "stab+eye_trauma"
                ]
        })

        assert result == {
            "eye": [
                {
                    "canon": "penetrating_eye_trauma",
                    "content": [
                        "penetrate"
                    ],
                    "distance": 4,
                    "forward": True,
                    "reverse": True
                },
                {
                    "canon": "penetrating_eye_trauma",
                    "content": [
                        "penetrating_wound"
                    ],
                    "distance": 4,
                    "forward": True,
                    "reverse": True
                }
            ],
            "eye_trauma": [
                {
                    "canon": "penetrating_eye_trauma",
                    "content": [
                        "penetrating_wound"
                    ],
                    "distance": 4,
                    "forward": True,
                    "reverse": True
                }
            ],
            "penetrate": [
                {
                    "canon": "penetrating_eye_trauma",
                    "content": [
                        "eye_trauma"
                    ],
                    "distance": 4,
                    "forward": True,
                    "reverse": True
                }
            ],
            "stab": [
                {
                    "canon": "penetrating_eye_trauma",
                    "content": [
                        "eye_trauma"
                    ],
                    "distance": 4,
                    "forward": True,
                    "reverse": True
                }
            ]
        }


if __name__ == '__main__':
    unittest.main()
