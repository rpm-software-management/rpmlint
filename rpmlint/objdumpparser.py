import subprocess

from rpmlint.helpers import ENGLISH_ENVIROMENT


class ObjdumpParser:
    """
    Class contains all information obtained by objdump command. Right now, we
    are interested in DW_TAG_compile_unit of debug info.

    Example output of objdump:

    <0><b>: Abbrev Number: 1 (DW_TAG_compile_unit)
       <c>   DW_AT_stmt_list   : 0x0
       <10>   DW_AT_low_pc      : 0x927840
       <18>   DW_AT_high_pc     : 0x92786b
       <20>   DW_AT_name        : (indirect string, offset: 0x0): ../sysdeps/x86_64/start.S
       <24>   DW_AT_comp_dir    : (indirect string, offset: 0x1a): /home/abuild/rpmbuild/BUILD/glibc-2.31/csu
       <28>   DW_AT_producer    : (indirect string, offset: 0x45): GNU AS 2.33.1
       <2c>   DW_AT_language    : 32769    (MIPS assembler)
     Compilation Unit @ offset 0x2e:
      Length:        0x3c (32-bit)
    """

    dw_at_prefix = 'DW_AT_'

    def __init__(self, pkgfile_path, path):
        self.pkgfile_path = pkgfile_path
        self.compile_units = []
        self.parsing_failed_reason = None
        self.parse_dwarf_compilation_units()

    def parse_dwarf_compilation_units(self):
        r = subprocess.run(['objdump', '--dwarf=info', '--dwarf-depth=1', self.pkgfile_path], encoding='utf8',
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENGLISH_ENVIROMENT)
        # here ldd should always return 0
        if r.returncode != 0:
            self.parsing_failed_reason = r.stderr
            return

        lines = r.stdout.splitlines()
        for i, line in enumerate(lines):
            if 'DW_TAG_compile_unit' in line:
                # We parse all DW_at_ flags that follow the DW_TAG_compile_unit
                i += 1
                cu_data = {}
                while self.dw_at_prefix in lines[i]:
                    current_line = lines[i]
                    current_line = current_line[current_line.find(self.dw_at_prefix) + len(self.dw_at_prefix):]
                    parts = [t.strip() for t in current_line.split(':')]
                    cu_data[parts[0]] = parts[-1]
                    i += 1
                self.compile_units.append(cu_data)
