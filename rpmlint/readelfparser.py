from itertools import dropwhile, takewhile
import re
import subprocess


class ElfSection:
    """
    A simple wrapper representing one ELF section.
    """
    def __init__(self, name, size):
        self.name = name
        self.size = int(size, 16)


class ElfProgramHeader:
    """
    A simple wrapper representing one ELF program header.
    """
    def __init__(self, name, flags):
        self.name = name
        self.flags = flags.replace(' ', '')


class ElfSectionInfo:
    """
    Class contains information about ELF sections of an ELF file. The information
    is get with the following command line: readelf -WS.

    Output example:

    There are 12 section headers, starting at offset 0x268:

    Section Headers:
      [Nr] Name              Type            Address          Off    Size   ES Flg Lk Inf Al
      [ 0]                   NULL            0000000000000000 000000 000000 00      0   0  0
      [ 1] .text             PROGBITS        0000000000000000 000040 000015 00  AX  0   0  1
      [ 2] .rela.text        RELA            0000000000000000 0001d8 000018 18   I  9   1  8
      [ 3] .data             PROGBITS        0000000000000000 000055 000000 00  WA  0   0  1
      [ 4] .bss              NOBITS          0000000000000000 000055 000000 00  WA  0   0  1
      [ 5] .comment          PROGBITS        0000000000000000 000055 000041 01  MS  0   0  1
      [ 6] .note.GNU-stack   PROGBITS        0000000000000000 000096 000000 00      0   0  1
      [ 7] .eh_frame         PROGBITS        0000000000000000 000098 000038 00   A  0   0  8
      [ 8] .rela.eh_frame    RELA            0000000000000000 0001f0 000018 18   I  9   7  8
      [ 9] .symtab           SYMTAB          0000000000000000 0000d0 0000f0 18     10   8  8
      [10] .strtab           STRTAB          0000000000000000 0001c0 000011 00      0   0  1
      [11] .shstrtab         STRTAB          0000000000000000 000208 000059 00      0   0  1
    Key to Flags:
      W (write), A (alloc), X (execute), M (merge), S (strings), I (info),
      L (link order), O (extra OS processing required), G (group), T (TLS),
      C (compressed), x (unknown), o (OS specific), E (exclude),
      l (large), p (processor specific)
    """

    section_regex = re.compile(r'.*\] (?P<section>[^\s]*)\s*\w+\s*\w*\s*\w*\w*\s*(?P<size>\w*)')

    def __init__(self, path):
        self.path = path
        self.elf_files = []
        self.parse()
        self.parsing_failed = False

    def parse(self):
        r = subprocess.run(['readelf', '-W', '-S', self.path], encoding='utf8',
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if r.returncode != 0:
            self.parsing_failed = True
            return

        lines = [l for l in r.stdout.split('\n')]

        needle = 'Section Headers:'

        # archive files can contain multiple files
        while len(lines) > 0:
            parsed_sections = []
            lines = list(dropwhile(lambda x: needle not in x, lines))

            # skip header and empty section
            lines = lines[3:]

            sections = list(takewhile(lambda x: 'Key to Flags:' not in x, lines))
            for s in sections:
                r = ElfSectionInfo.section_regex.search(s)
                parsed_sections.append(ElfSection(r.group('section'), r.group('size')))

            lines = lines[len(sections):]
            if len(parsed_sections) > 0:
                self.elf_files.append(parsed_sections)


class ElfProgramHeaderInfo:
    """
    Program Headers:
      Type           Offset   VirtAddr           PhysAddr           FileSiz  MemSiz   Flg Align
      PHDR           0x000040 0x0000000000400040 0x0000000000400040 0x000268 0x000268 R   0x8
      INTERP         0x0002a8 0x00000000004002a8 0x00000000004002a8 0x00001c 0x00001c R   0x1
          [Requesting program interpreter: /lib64/ld-linux-x86-64.so.2]
      LOAD           0x000000 0x0000000000400000 0x0000000000400000 0x000460 0x000460 R   0x1000
      LOAD           0x001000 0x0000000000401000 0x0000000000401000 0x0002ad 0x0002ad R E 0x1000
      LOAD           0x002000 0x0000000000402000 0x0000000000402000 0x0001d0 0x0001d0 R   0x1000
      LOAD           0x002e00 0x0000000000403e00 0x0000000000403e00 0x000230 0x000238 RW  0x1000
      DYNAMIC        0x002e10 0x0000000000403e10 0x0000000000403e10 0x0001e0 0x0001e0 RW  0x8
      NOTE           0x0002c4 0x00000000004002c4 0x00000000004002c4 0x000044 0x000044 R   0x4
      GNU_EH_FRAME   0x002004 0x0000000000402004 0x0000000000402004 0x000054 0x000054 R   0x4
      GNU_STACK      0x000000 0x0000000000000000 0x0000000000000000 0x000000 0x000000 RW  0x10
      GNU_RELRO      0x002e00 0x0000000000403e00 0x0000000000403e00 0x000200 0x000200 R   0x1
    """

    header_regex = re.compile('\\s+(?P<header>\\w+)(\\s+\\w+){5}\\s+(?P<flags>[RWE ]{3}).*')

    def __init__(self, path):
        self.path = path
        self.headers = []
        self.parse()
        self.parsing_failed = False

    def parse(self):
        r = subprocess.run(['readelf', '-W', '-l', self.path], encoding='utf8',
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if r.returncode != 0:
            self.parsing_failed = True
            return

        lines = [l for l in r.stdout.split('\n')]
        needle = 'Program Headers:'

        while len(lines) > 0:
            lines = list(dropwhile(lambda x: needle not in x, lines))

            # skip header
            lines = lines[2:]

            sections = list(takewhile(lambda x: x.strip() != '', lines))
            for s in sections:
                r = ElfProgramHeaderInfo.header_regex.search(s)
                if r is not None:
                    self.headers.append(ElfProgramHeader(r.group('header'), r.group('flags')))

            lines = lines[len(sections):]


class ReadelfParser:
    """
    Class contains all information obtained by readelf command
    in a structured format.
    """

    def __init__(self, path):
        self.section_info = ElfSectionInfo(path)
        self.program_header_info = ElfProgramHeaderInfo(path)

    def parsing_failed(self):
        return self.section_info.parsing_failed or self.program_header_info.parsing_failed
