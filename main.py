# Andrew Ratkov, 22b05, December 2023
from ElfParser import *
import sys


def solve(filename) -> str:
    with (open(filename, 'rb') as file):
        elf_parameters = ElfParser(file)

#        print(elf_parameters.__str__())
#       section_info = elf_parameters.get_section_info()
#        print(section_info)  # just for debug

        return elf_parameters.parse_text() + "\n\n" + elf_parameters.parse_symtab()


if __name__ == '__main__':
    with open(sys.argv[2], 'w') as output_file:
        output_file.write(solve(sys.argv[1]))
