from __future__ import annotations

import re
from dataclasses import dataclass


class VXError(Exception):
    pass


@dataclass
class Token:
    kind: str
    value: str
    line: int


class Lexer:
    RULES = [
        ("STRING", r'"(?:\\.|[^"\\])*"'),
        ("NUMBER", r"\d+(?:\.\d+)?"),
        ("ARROW", r"=>"),
        ("EQ", r"=="),
        ("PLUS", r"\+"),
        ("MINUS", r"-"),
        ("LPAREN", r"\("),
        ("RPAREN", r"\)"),
        ("LBRACE", r"\{"),
        ("RBRACE", r"\}"),
        ("COLON", r":"),
        ("AT", r"@"),
        ("IDENT", r"[A-Za-z_][A-Za-z0-9_]*"),
        ("SPACE", r"[ \t]+"),
        ("NEWLINE", r"\n"),
    ]

    def __init__(self, source: str):
        self.source = source

    def tokenize(self):
        tokens = []
        pos = 0
        line = 1

        while pos < len(self.source):
            if self.source[pos] == "#":
                end = self.source.find("\n", pos)
                pos = len(self.source) if end == -1 else end
                continue

            for kind, pattern in self.RULES:
                match = re.match(pattern, self.source[pos:])

                if not match:
                    continue

                value = match.group(0)
                pos += len(value)

                if kind == "NEWLINE":
                    line += 1
                    continue

                if kind == "SPACE":
                    continue

                tokens.append(Token(kind, value, line))
                break
            else:
                raise VXError(
                    f"Unknown character at line {line}: "
                    f"{self.source[pos]!r}"
                )

        tokens.append(Token("EOF", "", line))
        return tokens


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos]

    def advance(self):
        token = self.current()
        self.pos += 1
        return token

    def expect(self, kind):
        token = self.current()

        if token.kind != kind:
            raise VXError(
                f"Expected {kind}, got {token.kind} "
                f"on line {token.line}"
            )

        return self.advance()

    def parse(self):
        program = []

        while self.current().kind != "EOF":
            program.append(self.statement())

        return program

    def statement(self):
        self.expect("AT")

        command = self.expect("IDENT").value

        if command == "mem":
            return self.parse_mem()

        if command == "emit":
            return self.parse_emit()

        if command == "if":
            return self.parse_if()

        raise VXError(f"Unknown command @{command}")

    def parse_mem(self):
        self.expect("COLON")
        name = self.expect("IDENT").value

        self.expect("ARROW")

        value = self.expression()

        return ("mem", name, value)

    def parse_emit(self):
        self.expect("COLON")
        value = self.expression()

        return ("emit", value)

    def parse_if(self):
        self.expect("COLON")

        left = self.expression()

        self.expect("EQ")
        right = self.expression()

        self.expect("ARROW")
        self.expect("LBRACE")

        body = []

        while self.current().kind != "RBRACE":
            body.append(self.statement())

        self.expect("RBRACE")

        return ("if", left, right, body)

    def expression(self):
        token = self.current()

        if token.kind == "STRING":
            self.advance()
            return ("literal", bytes(
                token.value[1:-1],
                "utf-8"
            ).decode("unicode_escape"))

        if token.kind == "NUMBER":
            self.advance()

            if "." in token.value:
                return ("literal", float(token.value))

            return ("literal", int(token.value))

        if token.kind == "IDENT":
            self.advance()
            return ("variable", token.value)

        raise VXError(
            f"Unexpected {token.kind} on line {token.line}"
        )


class VM:
    def __init__(self):
        self.memory = {}

    def evaluate(self, node):
        kind = node[0]

        if kind == "literal":
            return node[1]

        if kind == "variable":
            name = node[1]

            if name not in self.memory:
                raise VXError(
                    f"Undefined variable: {name}"
                )

            return self.memory[name]

        raise VXError(f"Unknown expression: {kind}")

    def execute(self, program):
        for instruction in program:
            self.execute_instruction(instruction)

    def execute_instruction(self, instruction):
        opcode = instruction[0]

        if opcode == "mem":
            _, name, expression = instruction
            self.memory[name] = self.evaluate(expression)
            return

        if opcode == "emit":
            _, expression = instruction
            print(self.evaluate(expression))
            return

        if opcode == "if":
            _, left, right, body = instruction

            if self.evaluate(left) == self.evaluate(right):
                for item in body:
                    self.execute_instruction(item)

            return

        raise VXError(f"Unknown opcode: {opcode}")


def run(source: str):
    tokens = Lexer(source).tokenize()
    program = Parser(tokens).parse()

    vm = VM()
    vm.execute(program)

    return vm
