from xml.dom.minidom import parse
from urllib.parse import unquote

from rpmlint.checks.AbstractCheck import AbstractFilesCheck


class ProductCheck(AbstractFilesCheck):
    """
    Validate that product files are correct. currently only cpeid.
    """

    def __init__(self, config, output):
        super().__init__(config, output, r'/etc/products.d/.*\.prod$')

    def check_file(self, pkg, filename):
        cpeid_provider_found = None
        cpeid_xml_found = None
        for provide in pkg.provides:
            if provide.name == 'product-cpeid()' and len(provide.version) > 1:
                if cpeid_provider_found:
                    self.output.add_info('E', pkg, 'product-cpeid-multiple-provider', 'multiple product-cpeid() provider, this is not specified yet', filename)
                    return
                cpeid_provider_found = unquote(provide.version[1])

        if not cpeid_provider_found:
            self.output.add_info('E', pkg, 'product-cpeid-no-provider', 'no product-cpeid() provider', filename)
            return

        lf = pkg.dir_name() + filename

        try:
            xml = parse(lf)
        except xml.parsers.expat.ExpatError:
            self.output.add_info('E', pkg, 'product-parsing-exception', 'Failed to parse: ', lf)
            return

        cpeids = xml.getElementsByTagName('cpeid')
        if len(cpeids) != 1:
            self.output.add_info('E', pkg, 'product-cpeid-unavailable', 'cpeid must be defined as singleton in prod file', lf)
            return

        cpeid_xml_found = cpeids[0].firstChild.data

        if not cpeid_xml_found:
            self.output.add_info('E', pkg, 'product-cpeid-no-prod-definition', 'no cpeid defined in prod file', lf)
            return

        if cpeid_xml_found != cpeid_provider_found:
            self.output.add_info('E', pkg, 'product-cpeid-provider-mismatch', 'cpeid defined different in prod file to rpm provides', lf)

        for file in pkg.files:
            if file != "/etc/os-release":
                continue

            # Found base system
            with open(pkg.dir_name() + '/etc/os-release', encoding='utf8') as f:
                cpe_name = None
                for line in f:
                    if line.startswith("CPE_NAME="):
                        cpe_name = line[10:].strip().strip('"').strip("'")

                if not cpe_name:
                    self.output.add_info('E', pkg, 'product-cpe_name-missing', 'no CPE_NAME defined in /etc/os-release file')
                    return

                if cpe_name != cpeid_xml_found and cpe_name.startswith("cpe:2.3:"):
                    # convert to 2.2 style for now for comparing
                    cpe_name = "cpe:/" + cpe_name.removeprefix("cpe:2.3:")
                    while True:
                        new_cpe_name = cpe_name.removesuffix(":*")
                        if new_cpe_name == cpe_name:
                            break
                        cpe_name = new_cpe_name

                if cpe_name != cpeid_xml_found:
                    self.output.add_info('E', pkg, 'product-cpe_name-mismatch', 'CPE_NAME defined in /etc/os-release file is not matching', cpe_name, " vs ", cpeid_xml_found)
