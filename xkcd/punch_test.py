"""Tests for users.aiuto.xkcd.punch."""

import os
import subprocess
import unittest

class PunchTest(unittest.TestCase):

  def testPunchApp(self):
    test_file_name = os.path.join(os.path.dirname(__file__), 'tests.txt')
    with open(test_file_name, 'r', encoding='utf-8') as f:
      while True:
        text = f.readline().strip()
        if not text:
          break
        print('checking: %s' % text)
        expect = ''.join([f.readline() for i in range(12)])
        result = subprocess.check_output(['python3', 'punch.py', text]).decode('utf-8')
        self.assertEqual(expect, result)


if __name__ == '__main__':
  unittest.main()
