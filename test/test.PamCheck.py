import unittest
import Testing
import PamCheck
import Pkg
# FIXME harcode

class TestPamCheck(unittest.TestCase):
    def setUp(self):
        self.pkg = Testing.getTestedPackage('PamCheck')
        Testing.startTest()
    def testcheck(self):
        PamCheck.check.check(self.pkg)
        self.assertEqual( Testing.getOutput(), ['E: PamCheck use-old-pam-stack /etc/pam.d/PamCheck'])

# enjoy \o/
if __name__ == '__main__':
    unittest.main()

#print Testing.getOutput()
