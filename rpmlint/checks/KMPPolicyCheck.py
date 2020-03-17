import re

from rpmlint.checks.AbstractCheck import AbstractCheck


class KMPPolicyCheck(AbstractCheck):
    re_kmp_pkg = re.compile(r'(?P<name>\S+)-kmp-(?P<kernel>\S+)')

    def _check_requires(self, pkg, kernel_flavor):
        """
        Check if the kernel has Requires on specific kernel flavor
        """
        pkg_requires = [x.name for x in pkg.requires]
        if kernel_flavor not in pkg_requires:
            self.output.add_info('E', pkg, 'kmp-missing-requires', kernel_flavor)

    def _check_enhances(self, pkg, kernel_flavor):
        """
        Check if kernel has enhnances on the kernel and on one kernel only
        """
        kernel_enhances = []
        for enhance in pkg.enhances:
            if enhance.name.startswith('kernel-'):
                kernel_enhances.append(enhance.name)
        if len(kernel_enhances) > 1:
            self.output.add_info('E', pkg, 'kmp-excessive-enhances', str(kernel_enhances))
        if kernel_flavor not in kernel_enhances:
            self.output.add_info('E', pkg, 'kmp-missing-enhances', kernel_flavor)

    def _check_suplements(self, pkg, kernel_flavor):
        """
        Check supplements for the kernel_flavor

        We need modalias(value) and also suplement the kernel itself.
        """
        have_modalias = False
        have_proper_suppl = False
        for s in pkg.supplements:
            if s.name.startswith('modalias('):
                have_modalias = True
                continue
            if s.name.startswith(f'({kernel_flavor} and'):
                have_proper_suppl = True
                continue
            # if there is sumplement other than the kernel and modalias it is probably wrong
            self.output.add_info('W', pkg, 'kmp-excessive-supplements', s[0])

        if not have_modalias and not have_proper_suppl:
            self.output.add_info('E', pkg, 'kmp-missing-supplements')

    def check(self, pkg):
        if pkg.is_source or not self.re_kmp_pkg.match(pkg.name):
            return

        # figure out what kernel flavor we care for
        kernel_name = self.re_kmp_pkg.match(pkg.name).group('kernel')
        kernel_flavor = f'kernel-{kernel_name}'

        # run the checks
        self._check_requires(pkg, kernel_flavor)
        self._check_enhances(pkg, kernel_flavor)
        self._check_suplements(pkg, kernel_flavor)
