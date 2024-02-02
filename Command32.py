from constants import reg


class Command32:

    def __init__(self, byte_code: bytes):
        assert len(byte_code) == 4
        self.bits = ["0" for _ in range(32)]
        for i in range(4):
            for j in range(8):
                self.bits[8 * i + j] = "1" if byte_code[3 - i] & (1 << (7 - j)) else "0"
        self.opcode = "".join(self.bits[25:])
        self.rd = "".join(self.bits[20:25])
        self.funct3 = "".join(self.bits[17:20])
        self.rs1 = "".join(self.bits[12:17])
        self.reversed_bits = self.bits[::-1]
        self.imm = "".join(self.bits[0:12])

    def __str__(self):
        return "opcode: {}\nrd: {}\nfunc: {}\nrs1: {}\nimm: {}\n".format(self.opcode, self.rd, self.funct3,
                                                                         self.rs1, self.imm)

    def write_bits(self) -> str:
        return "".join(self.bits)

    def get_meaning(self) -> [str, bool, int, bool]:
        operation = "invalid_instruction"
        match self.opcode:
            case "0110111":
                imm = int(self.imm + self.rs1 + self.funct3, 2) - ((1 << 20) * (self.bits[0] == "1"))  # << 12
                if imm < 0:
                    imm += (1 << 32)
                imm = hex(imm)
                operation = "lui"
                return '%7s\t%s, %s' % (operation, reg[int(self.rd, 2)], imm), False, 0, False
#                return "{} {}, {}".format(operation, reg[int(self.rd, 2)], imm), False, 0
            case "0010111":  # I'm not sure because this command is never used, so I couldn't test it
                imm = hex(int(self.imm + self.rs1 + self.funct3, 2) - (1 << (19 + 1)) * (self.imm[0] == "1"))  # << 12
                operation = "auipc"
                return '%7s\t%s, %s' % (operation, reg[int(self.rd, 2)], imm), False, 0, False
            case "1101111":
                imm = (int(self.bits[0] + "".join(self.bits[12: 20]) +
                           self.bits[11] + "".join(self.bits[1: 11]), 2) * 2
                       - (1 << 21) * int(self.bits[0]))
                operation = "jal"
                return '%7s\t%s' % (operation, reg[int(self.rd, 2)]), True, imm, True
            case "1100111":
                operation = "jalr"
                return ('%7s\t%s, %d(%s)' % (operation, reg[int(self.rd, 2)],
                                             int(self.imm, 2) - (1 << (11 + 1)) * int(self.bits[0]),
                                             reg[int(self.rs1, 2)]),
                        False, 0, False)
            case "1100011":
                imm = int(self.bits[0] + self.bits[24] + "".join(self.bits[1:7]) +
                          "".join(self.bits[20:24]), 2) * 2 - (1 << (12 + 1)) * int(self.bits[0])

                rs2 = int("".join(self.bits[7:12]), 2)
                match self.funct3:
                    case "000": operation = "beq"
                    case "001": operation = "bne"
                    case "100": operation = "blt"
                    case "101": operation = "bge"
                    case "110": operation = "bltu"
                    case "111": operation = "bgeu"
                return '%7s\t%s, %s' % (operation, reg[int(self.rs1, 2)], reg[rs2]), True, imm, False
            case "0000011":
                match self.funct3:
                    case "000": operation = "lb"
                    case "001": operation = "lh"
                    case "010": operation = "lw"
                    case "100": operation = "lbu"
                    case "101": operation = "lhu"
                return ('%7s\t%s, %d(%s)' % (operation, reg[int(self.rd, 2)],
                                             int(self.imm, 2) - (1 << 12) * (self.imm[0] == "1"),
                                             reg[int(self.rs1, 2)]),
                        False, 0, False)
            case "0010011":
                imm = int(self.imm, 2) - (1 << (11 + 1)) * (self.imm[0] == "1")  # 11 + 1 !!!
                match self.funct3:
                    case "000": operation = "addi"
                    case "001":
                        imm = int(self.imm[-5:], 2)  # shamt
                        operation = "slli"
                    case "010": operation = "slti"
                    case "011": operation = "sltiu"
                    case "100": operation = "xori"
                    case "110": operation = "ori"
                    case "111": operation = "andi"
                    case "101":
                        imm = int(self.imm[-5:], 2)  # shamt
                        operation = "srli" if self.bits[1] == "0" else "srai"
                return ('%7s\t%s, %s, %s' % (operation, reg[int(self.rd, 2)], reg[int(self.rs1, 2)], imm),
                        False, 0, False)
            case "0100011":
                imm = int(self.imm[:7] + self.rd, 2) - (1 << 12) * (self.imm[0] == "1")
                rs2 = int(self.imm[7:], 2)
                match self.funct3:
                    case "000": operation = "sb"
                    case "001": operation = "sh"
                    case "010": operation = "sw"
                return '%7s\t%s, %d(%s)' % (operation, reg[rs2], imm, reg[int(self.rs1, 2)]), False, 0, False
            case "0110011":
                rs2 = int(self.imm[-5:], 2)
                if "".join(self.imm[:7]) != "0000001":
                    match self.funct3:
                        case "000": operation = "add" if self.imm[1] == "0" else "sub"
                        case "001": operation = "sll"
                        case "010": operation = "slt"
                        case "011": operation = "sltu"
                        case "100": operation = "xor"
                        case "101": operation = "srl" if self.imm[1] == "0" else "sra"
                        case "110": operation = "or"
                        case "111": operation = "and"
                else:
                    match self.funct3:
                        case "000": operation = "mul"
                        case "001": operation = "mulh"
                        case "010": operation = "mulhsu"
                        case "011": operation = "mulhu"
                        case "100": operation = "div"
                        case "101": operation = "divu"
                        case "110": operation = "rem"
                        case "111": operation = "remu"
                return '%7s\t%s, %s, %s' % (operation, reg[int(self.rd, 2)],
                                            reg[int(self.rs1, 2)], reg[rs2]), False, 0, False
            case "1110011":
                operation = "ecall" if int(self.imm, 2) == 0 else "ebreak"
                return '%7s' % operation, False, 0, False
            case "0001111":
                if self.bits == "00000001000000000000000000001111":
                    return '%7s' % "pause", False, 0, False
                if self.bits == "10000011001100000000000000001111":
                    return '%7s' % "fence.tso", False, 0, False
                operation = "fence"
                pred = (("i" if self.bits[4] == "1" else "") + ("o" if self.bits[5] == "1" else "") +
                        ("r" if self.bits[6] == "1" else "") + ("w" if self.bits[7] == "1" else ""))
                succ = (("i" if self.bits[8] == "1" else "") + ("o" if self.bits[9] == "1" else "") +
                        ("r" if self.bits[10] == "1" else "") + ("w" if self.bits[11] == "1" else ""))
                return '%7s\t%s, %s' % (operation, pred, succ), False, 0, False
        return operation, False, 0, False
