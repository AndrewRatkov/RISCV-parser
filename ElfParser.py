from constants import *
from Command32 import *


class ElfParser:

    def __init__(self, elf_file):
        elf_file.seek(0)
        elf_header = elf_file.read(52)

        # Extract the section header table's offset and entry size from the ELF header
        self.e_shoff: int = int.from_bytes(elf_header[32:36], 'little')
        self.e_shentsize: int = int.from_bytes(elf_header[46:48], 'little')
        self.e_shnum = int.from_bytes(elf_header[48:50], 'little')
        self.e_shstrndx = int.from_bytes(elf_header[50:], 'little')

        # extracting section header from the end of file
        elf_file.seek(self.e_shoff)
        self.header: bytes = elf_file.read()

        # extracting .shstrtab section
        elf_file.seek(self.e_shoff + self.e_shstrndx * self.e_shentsize)
        shstrtab_header: bytes = self.header[self.e_shstrndx * self.e_shentsize:
                                             (self.e_shstrndx + 1) * self.e_shentsize]
        shstrtab_offset: int = int.from_bytes(shstrtab_header[16:20], 'little')
        shstrtab_size: int = int.from_bytes(shstrtab_header[20:24], 'little')
        elf_file.seek(shstrtab_offset)
        self.shstrtab_section: bytes = elf_file.read(shstrtab_size)

        # extracting .text, .symtab, .strtab sections
        for section_idx in range(self.e_shnum):
            section_header = self.header[section_idx * self.e_shentsize: (section_idx + 1) * self.e_shentsize]
            sh_name = int.from_bytes(section_header[0:4], 'little')
            sh_offset = int.from_bytes(section_header[16:20], 'little')
            sh_size = int.from_bytes(section_header[20:24], 'little')

            idx = sh_name
            name = ""
            while self.shstrtab_section[idx] != 0:
                name += chr(self.shstrtab_section[idx])
                idx += 1
            if name == ".text":
                elf_file.seek(sh_offset)
                self.text_section = elf_file.read(sh_size)
            elif name == ".symtab":
                elf_file.seek(sh_offset)
                self.symtab_section = elf_file.read(sh_size)
            elif name == ".strtab":
                elf_file.seek(sh_offset)
                self.strtab_section = elf_file.read(sh_size)

        self.symtab_block_size = 16
        self.cmd_len = 4  # in bytes

        self.default_addr: int = -1
        self.value2func: dict[int, str] = dict()

        for i in range(len(self.symtab_section) // self.symtab_block_size):
            byte_section = self.symtab_section[i * self.symtab_block_size: (i + 1) * self.symtab_block_size]

            # name constructing
            name_idx: int = int.from_bytes(byte_section[0:4], 'little')
            name: str = ""
            while self.strtab_section[name_idx] != 0:
                name += chr(self.strtab_section[name_idx])
                name_idx += 1

            value = int.from_bytes(byte_section[4:8], 'little')
            type_ = TYPES[int.from_bytes(byte_section[12:13], 'little') % 16]

            if type_ == "FUNC":
                self.value2func[value] = name
                if self.default_addr == -1 or value < self.default_addr:
                    self.default_addr = value

    def __str__(self):
        s: str = ""
        s += "e_shoff: {}\n".format(self.e_shoff)
        s += "e_shentsize: {}\n".format(self.e_shentsize)
        s += "e_shnum: {}\n".format(self.e_shnum)
        s += "e_shstrndx: {}\n".format(self.e_shstrndx)
        s += "strtab: {}\n".format(self.strtab_section)
        s += "shstrtab: {}\n".format(self.shstrtab_section)
        s += "default addr: {}\n".format(self.default_addr)
        s += "value to func: {}\n".format(self.value2func)
        return s

    def get_section_info(self) -> str:
        section_info: str = ""
        for section_idx in range(self.e_shnum):
            section_info += "Section number: {}\n".format(section_idx)
            section_header: bytes = self.header[section_idx * self.e_shentsize: (section_idx + 1) * self.e_shentsize]
            sh_name: int = int.from_bytes(section_header[0:4], 'little')
            sh_offset: int = int.from_bytes(section_header[16:20], 'little')
            sh_size: int = int.from_bytes(section_header[20:24], 'little')

            idx: int = sh_name
            name: str = ""
            while self.shstrtab_section[idx] != 0:
                name += chr(self.shstrtab_section[idx])
                idx += 1
            section_info += " sh_name: {}, name: {}\n".format(sh_name, name)
            section_info += " sh_offset: {}, sh_size: {}\n".format(sh_offset, sh_size)
        return section_info

    def parse_symtab(self) -> str:
        assert len(self.symtab_section) % self.symtab_block_size == 0, ".symtab is incorrectly encoded"
        symtab_string: str = ".symtab\n"
        symtab_string += "\nSymbol Value              Size Type     Bind     Vis       Index Name\n"
        for i in range(len(self.symtab_section) // self.symtab_block_size):
            byte_section = self.symtab_section[i * self.symtab_block_size: (i + 1) * self.symtab_block_size]

            # name constructing
            name_idx: int = int.from_bytes(byte_section[0:4], 'little')
            name: str = ""
            while self.strtab_section[name_idx] != 0:
                name += chr(self.strtab_section[name_idx])
                name_idx += 1

            value = "0x" + str(hex(int.from_bytes(byte_section[4:8], 'little')))[2:].upper()
            size = int.from_bytes(byte_section[8:12], 'little')

            bind_and_type_byte = int.from_bytes(byte_section[12:13], 'little')
            type_ = TYPES[bind_and_type_byte % 16]
            bind = BINDS[bind_and_type_byte >> 4]

            vis = VISES[int.from_bytes(byte_section[13:14], 'little') & 3]

            index = int.from_bytes(byte_section[14:], 'little')
            if index in SPECIAL_INDEXES:
                index = SPECIAL_INDEXES[index]

            symtab_string += '[%4i] %-17s %5i %-8s %-8s %-8s %6s %s\n' % (i, value, size, type_, bind, vis, index, name)
        return symtab_string

    def parse_text(self) -> str:
        text_string: str = ".text\n"
        commands_strings: list[str] = []
        index_of_least_unused_L: int = 0

        for i in range(len(self.text_section) // self.cmd_len):
            block_bytes = self.text_section[i * self.cmd_len: (i + 1) * self.cmd_len]
            code = hex(int.from_bytes(block_bytes, 'little'))
            code_str = '0' * (2 * self.cmd_len + 2 - len(code)) + str(code[2:])

            offset = str(hex(self.default_addr + i * self.cmd_len))[2:]
            cmd: Command32 = Command32(block_bytes)
            parsed_cmd = cmd.get_meaning()

            if not parsed_cmd[1]:
                temp_str = '   %05s:\t%08s\t%s' % (offset, code_str, parsed_cmd[0])
            else:
                jump_to_addr = parsed_cmd[2] + self.default_addr + i * self.cmd_len
                if jump_to_addr not in self.value2func:
                    self.value2func[jump_to_addr] = "L{}".format(index_of_least_unused_L)
                    index_of_least_unused_L += 1
                if not parsed_cmd[3]:
                    temp_str = '   %05s:\t%08s\t%s, %s, <%s>' % (offset, code_str, parsed_cmd[0], hex(jump_to_addr),
                                                                 self.value2func[jump_to_addr])
                else:
                    temp_str = '   %05s:\t%08s\t%s, %s <%s>' % (offset, code_str, parsed_cmd[0], hex(jump_to_addr),
                                                                self.value2func[jump_to_addr])

            commands_strings.append(temp_str + "\n")
        for i in range(len(self.text_section) // self.cmd_len):
            offset_val = self.default_addr + i * self.cmd_len
            if offset_val in self.value2func:
                text_string += "\n%08x \t<%s>:\n" % (offset_val, self.value2func[offset_val])
            text_string += commands_strings[i]
        return text_string
