import numpy as np
import networkx as nx
import itertools
import collections
from constants import BLACK, WHITE


class GoGame:
    def __init__(self, size):
        """
        Инициализация игры Го.

        :param size: Размер доски (например, 9 для доски 9x9).
        """
        self.size = size
        self.board = np.zeros((size, size), dtype=int)
        self.black_turn = True
        self.prisoners = collections.defaultdict(int)
        self.history = []  # История ходов для отмены
        self.prev_boards = []  # Предыдущие состояния доски для проверки правила ко

    def is_valid_move(self, col, row):
        """
        Проверяет, допустим ли ход.

        :param col: Номер столбца.
        :param row: Номер строки.
        :return: True, если ход допустим, иначе False.
        """
        if col < 0 or col >= self.size or row < 0 or row >= self.size:
            return False  # Ход за пределами доски
        if self.board[col, row] != 0:
            return False  # Клетка уже занята
        return True

    def place_stone(self, col, row):
        """
        Размещает камень на доске и обновляет состояние игры.

        :param col: Номер столбца.
        :param row: Номер строки.
        :return: True, если ход выполнен, иначе False.
        """
        if not self.is_valid_move(col, row):
            return False  # Недопустимый ход

        # Сохраняем текущее состояние доски и счетчик пленных
        self.history.append((self.board.copy(), self.prisoners.copy()))
        self.prev_boards.append(self.board.copy())

        # Размещаем камень (1 - черные, 2 - белые)
        self.board[col, row] = 1 if self.black_turn else 2

        # Проверяем и захватываем камни противника
        self.capture_stones(col, row)

        # Проверяем правило ко
        if self.is_ko_violation():
            self.board[col, row] = 0  # Отменяем ход, если нарушено правило ко
            return False

        # Меняем очередь хода
        self.black_turn = not self.black_turn
        return True

    def capture_stones(self, col, row):
        """
        Проверяет и захватывает камни противника после размещения камня.

        :param col: Номер столбца.
        :param row: Номер строки.
        """
        self_color = "black" if self.black_turn else "white"  # Цвет текущего игрока
        other_color = "white" if self.black_turn else "black"  # Цвет противника

        # Проверяем все группы камней противника
        for group in list(self.get_stone_groups(other_color)):
            if self.has_no_liberties(group):  # Если у группы нет либерти
                for x, y in group:
                    self.board[x, y] = 0  # Удаляем камни группы
                self.prisoners[self_color] += len(group)  # Увеличиваем счетчик пленных

    def has_no_liberties(self, group):
        """
        Проверяет, есть ли у группы камней либерти (дыхание).

        :param group: Группа камней (список координат).
        :return: True, если у группы нет либерти, иначе False.
        """
        for x, y in group:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # Проверяем соседние клетки
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.size and 0 <= ny < self.size:
                    if self.board[nx, ny] == 0:  # Если соседняя клетка пуста
                        return False
        return True

    def get_stone_groups(self, color):
        """
        Возвращает все группы камней заданного цвета.

        :param color: Цвет камней ("black" или "white").
        :return: Список групп камней (каждая группа - это набор координат).
        """
        color_code = 1 if color == "black" else 2  # Код цвета камней
        xs, ys = np.where(self.board == color_code)  # Координаты всех камней этого цвета
        graph = nx.grid_graph(dim=[self.size, self.size])  # Создаем граф для поиска групп
        stones = set(zip(xs, ys))  # Множество координат камней
        all_spaces = set(itertools.product(range(self.size), range(self.size)))  # Все клетки доски
        stones_to_remove = all_spaces - stones  # Клетки без камней
        graph.remove_nodes_from(stones_to_remove)  # Удаляем пустые клетки из графа
        return nx.connected_components(graph)  # Возвращаем связанные компоненты (группы камней)

    def is_ko_violation(self):
        """
        Проверяет, нарушено ли правило ко.

        :return: True, если правило ко нарушено, иначе False.
        """
        if len(self.prev_boards) >= 2:
            return np.array_equal(self.board, self.prev_boards[-2])  # Сравниваем с предпоследним состоянием
        return False

    def calculate_score(self):
        """
        Подсчитывает очки в конце игры.

        :return: Словарь с очками черных и белых.
        """
        black_score = self.prisoners['black']
        white_score = self.prisoners['white'] + 6.5  # Коми для белых
        return {'black': black_score, 'white': white_score}

    def undo_move(self):
        """
        Отменяет последний ход.
        """
        if self.history:
            self.board, self.prisoners = self.history.pop()
            self.black_turn = not self.black_turn