"""Tests for google3.experimental.users.aiuto.xkcd.punch."""

import os
import subprocess

from google3.testing.pybase import googletest

class PunchTest(googletest.TestCase):

  def testPunchApp(self):
    test_file_name = os.path.join(os.path.dirname(__file__), 'tests.txt')
    with open(test_file_name, 'r') as f:
      while True:
        text = f.readline().strip()
        if not text:
          break
        print 'checking: %s' % text
        expect = ''.join([f.readline() for i in range(12)])
        result = subprocess.check_output(['python', 'punch.py', text])
        self.assertEquals(expect, result)


if __name__ == '__main__':
  googletest.main()
