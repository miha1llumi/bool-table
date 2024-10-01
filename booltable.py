import itertools as it

from typing import Union
from string import ascii_letters, digits

from prettytable import PrettyTable


class BoolTable:
    """
    Simple usage:
        bt = BoolTable()
        bt.create_bool_table(<expression>)
    """

    VALUES = {0, 1}
    OPERATIONS = {
        'not': 'отрицание',
        'and': 'коньюнкция',
        'or': 'дизьюнкция',
        '<=': 'импликация',
        '==': 'эквивалентность',
    }

    def __init__(self):
        self._expression = None
        self.enter_expression()
        self._bool_table = {}
        self._all_letters = set()

    def __setitem__(self, key, value):
        key = self.__set_key_index(key)
        self._bool_table[key] = value

    def __getattribute__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            return self._bool_table.__getattribute__(item)

    def __getitem__(self, item: Union[str, int]):
        if str(item) in digits:
            item = self._find_key_by_index(item)
        return self._bool_table[item]

    def __len__(self):
        return len(self._all_letters)

    def __iter__(self):
        return iter(self._bool_table)

    def __set_key_index(self, key):
        if key not in self._all_letters:
            index = key[-2]
            if any(index in k for k in self):
                index = self._find_next_index()
                index_cleaner = slice(key.find('(') - 1)
                key = f"{key[:index_cleaner]} ({index})"
        return key

    def _find_next_index(self) -> str:
        """ Находит следующий индекс """
        index = '0'
        while True:
            if any(index in k for k in self):
                index = str(int(index) + 1)
            else: break
        return index

    def _initialize_vars(self):
        """ Заполняет все переменные в таблице истинности """
        self.__init_bool_table()
        for line in it.product(
                self.VALUES, repeat=len(self)
        ):
            for index, key in enumerate(self):
                column = self[key]
                column.append(line[index])

    def create_bool_table(self):
        self._initialize_vars()
        while self._exp_exist():
            column_index = self.count_expression(self._find_expression())
            self._convert_expression(column_index)
        self._print_bool_table()

    def _convert_expression(self, column_index: int):
        # возвращает индекс последней открывающейся скобки
        # иначе возвращает выражение
        exp = self._find_key_by_index(column_index, not_index=True)
        if self.bracket_cords is not None:
            start_exp_index, over_exp_index = self.bracket_cords
            over_exp_index += 1
            if self._count_operations(self._expression[start_exp_index:over_exp_index]) >= 2:
                start_exp_index += 1
                left_part = self._expression[:start_exp_index]
                central_part = self._expression[start_exp_index:over_exp_index].replace(exp, str(column_index), 1)
                right_part = self._expression[over_exp_index:]
                self._expression = left_part + central_part + right_part
                return
        else:
            start_exp_index = self._expression.rfind(exp)
            over_exp_index = start_exp_index + len(exp)
        self._expression = self._expression[:start_exp_index] + str(column_index) + self._expression[over_exp_index:]

    @classmethod
    def _count_operations(cls, expression):
        return sum(expression.count(op) for op in cls.OPERATIONS)

    def __init_bool_table(self):
        """ Первично инициализирует все переменные в таблице истинности """
        self._all_letters = sorted(self.find_all_letters())
        self._bool_table = {lt: [] for lt in self._all_letters}

    def count_expression(self, exp: str) -> int:
        exp = exp.replace(" ", "")
        if (operation := 'not') in exp:
            index = exp.rfind(operation)
        elif (operation := 'and') in exp:
            index = exp.find(operation)
        elif (operation := 'or') in exp:
            index = exp.find(operation)
        elif (operation := '<=') in exp:
            index = exp.find(operation)
        elif (operation := '==') in exp:
            index = exp.find(operation)
        else:
            raise ValueError
        # operand_1 находится всегда слева
        # operand_2 находится всегда справа
        operand_1, operand_2 = None, None
        if operation == 'not':
            operand_2 = exp[index + 3]
        if operation == 'and':
            operand_1, operand_2 = exp[index - 1], exp[index + 3]
        small_operations = ('or', '<=', '==')
        if operation in small_operations:
            operand_1, operand_2 = exp[index - 1], exp[index + 2]
        column_index = self._create_new_column(
            operation=operation,
            operand_1=operand_1,
            operand_2=operand_2,
        )
        return column_index

    def _create_new_column(
            self, operation: str, operand_1: Union[None, str] = None, operand_2: Union[None, str] = None
    ):
        q_lines = 2**len(self)
        column_index = int(self._find_next_index())
        formula = f"{operation} %s" if operation == 'not' else f"%s {operation} %s"
        key = f"{formula % (operand_2 if operation == 'not' else (operand_1, operand_2))} ({column_index})"
        self[key] = [int(eval(formula % (self[operand_2][i] if operation == 'not'
                              else (self[operand_1][i], self[operand_2][i])))) for i in range(q_lines)]
        return column_index

    def find_all_letters(self, exp=None) -> set[str]:
        obj = self._expression if exp is None else exp
        obj = obj. \
            replace(" ", ""). \
            replace("(", ""). \
            replace(")", ""). \
            replace("or", ""). \
            replace("<=", ""). \
            replace("==", ""). \
            replace("not", ""). \
            replace("and", "")
        return set(obj)

    def _find_expression(self) -> str:
        if not self._is_brackets():
            return self._expression
        open_bracket_index, closed_bracket_index = self.bracket_cords
        brackets_cleaner = slice(open_bracket_index + 1, closed_bracket_index)
        return self._expression[brackets_cleaner]

    def enter_expression(self):
        self._print_bool_lang()
        self._expression = input("Введите выражение: ")
        if not self._validate_expression():
            raise ValueError("Неправильно введенное выражение!")

    @property
    def bracket_cords(self):
        """ ( - 1 | 2 - ) """
        if not self._is_brackets(): return
        open_bracket_index = self._expression.rfind('(')
        closed_bracket_index = open_bracket_index
        while self._expression[closed_bracket_index] != ')':
            closed_bracket_index += 1
        return open_bracket_index, closed_bracket_index

    def _validate_expression(self):
        q_open_brackets = self._expression.count('(')
        q_closed_brackets = self._expression.count(')')
        if q_open_brackets != q_closed_brackets:
            return
        exp = ''.join(self.find_all_letters())
        for letter in ascii_letters:
            exp = exp.replace(letter, "")
        if len(exp):
            return
        return True

    def _is_brackets(self):
        brackets = '( )'
        return all(b in self._expression for b in brackets.split())

    def _exp_exist(self):
        if self._expression is None or len(self._expression) == 1:
            return False
        return len(self._expression)

    def _find_key_by_index(self, index: int, not_index=False):
        index = str(index)
        for k in self.keys():
            if index in k:
                return k[:-4] if not_index else k

    def _print_bool_table(self):
        pt = PrettyTable()
        q_lines = 2**len(self)
        pt.field_names = self.keys()
        for i in range(q_lines):
            pt.add_row([self[key][i] for key in self.keys()])
        print(pt)

    @classmethod
    def _print_bool_lang(cls):
        """ Выводит в консоль язык для выражения """
        print(
            '\n'.join(f"{op} - {cls.OPERATIONS[op]}" for op in cls.OPERATIONS)
        )
