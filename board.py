import random
import copy
from config import BOARD_ROWS, BOARD_COLS, NUM_PIECE_TYPES

class Board:
    def __init__(self, rows=BOARD_ROWS, cols=BOARD_COLS, piece_types=NUM_PIECE_TYPES):
        self.rows = rows
        self.cols = cols
        self.piece_types = piece_types
        self.grid = [[None for _ in range(cols)] for _ in range(rows)]
        self.reset_board()

    def make_piece(self, p_type, special=None):
        return {'type': p_type, 'special': special}

    def get_piece_type(self, cell):
        if cell is None:
            return None
        if isinstance(cell, dict):
            return cell.get('type', None)
        return cell

    def get_piece_special(self, cell):
        if isinstance(cell, dict):
            return cell.get('special', None)
        return None

    def reset_board(self):
        while True:
            for r in range(self.rows):
                for c in range(self.cols):
                    valid = list(range(self.piece_types))
                    if c >= 2 and self.get_piece_type(self.grid[r][c-1]) == self.get_piece_type(self.grid[r][c-2]):
                        t = self.get_piece_type(self.grid[r][c-1])
                        if t in valid:
                            valid.remove(t)
                    if r >= 2 and self.get_piece_type(self.grid[r-1][c]) == self.get_piece_type(self.grid[r-2][c]):
                        t = self.get_piece_type(self.grid[r-1][c])
                        if t in valid:
                            valid.remove(t)
                    self.grid[r][c] = self.make_piece(random.choice(valid))

            if self.has_valid_moves():
                break

    def is_valid_coord(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def can_swap_and_match(self, r1, c1, r2, c2):
        if not (self.is_valid_coord(r1, c1) and self.is_valid_coord(r2, c2)):
            return False
        if abs(r1 - r2) + abs(c1 - c2) != 1:
            return False

        s1 = self.get_piece_special(self.grid[r1][c1])
        s2 = self.get_piece_special(self.grid[r2][c2])

        # Any swap between TWO special items (or Color Bomb + normal tile) is ALWAYS valid!
        if s1 is not None or s2 is not None:
            return True

        temp_grid = [copy.deepcopy(row) for row in self.grid]
        temp_grid[r1][c1], temp_grid[r2][c2] = temp_grid[r2][c2], temp_grid[r1][c1]
        matched_cells, _, _ = self.find_matches_in_grid(temp_grid, last_swap_pair=((r1, c1), (r2, c2)))
        return len(matched_cells) > 0

    def has_valid_moves(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if c + 1 < self.cols and self.can_swap_and_match(r, c, r, c + 1):
                    return True
                if r + 1 < self.rows and self.can_swap_and_match(r, c, r + 1, c):
                    return True
        return False

    def swap_grid_cells(self, r1, c1, r2, c2):
        self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]

    def find_current_matches(self, last_swap_pair=None, swap_dir=None):
        """
        Check for Special Item Combo combinations if last_swap_pair was performed.
        """
        if last_swap_pair:
            (r1, c1), (r2, c2) = last_swap_pair
            p1 = self.grid[r1][c1]
            p2 = self.grid[r2][c2]
            s1 = self.get_piece_special(p1)
            s2 = self.get_piece_special(p2)

            if s1 or s2:
                combo_res = self.process_special_combo(r1, c1, r2, c2, p1, p2, s1, s2, swap_dir)
                if combo_res:
                    return combo_res

        return self.find_matches_in_grid(self.grid, last_swap_pair=last_swap_pair, swap_dir=swap_dir)

    def process_special_combo(self, r1, c1, r2, c2, p1, p2, s1, s2, swap_dir):
        """Processes Item x Item and Color Bomb combinations."""

        # 1. Color Bomb x Color Bomb -> CLEAR ALL 64 TILES!
        if s1 == 'COLOR_BOMB' and s2 == 'COLOR_BOMB':
            matched = set((r, c) for r in range(self.rows) for c in range(self.cols))
            return matched, [list(matched)], {}

        # Helper to check item types regardless of swap order
        specials = set([s1, s2]) - {None}

        # 2. Color Bomb x Line Bomb
        if 'COLOR_BOMB' in specials and ('LINE_H' in specials or 'LINE_V' in specials):
            line_piece = p1 if s1 in ('LINE_H', 'LINE_V') else p2
            target_color = self.get_piece_type(line_piece)
            line_kind = self.get_piece_special(line_piece) or ('LINE_H' if swap_dir == 'H' else 'LINE_V')
            
            created_specials = {}
            matched = set([(r1, c1), (r2, c2)])
            for r in range(self.rows):
                for c in range(self.cols):
                    if self.get_piece_type(self.grid[r][c]) == target_color:
                        created_specials[(r, c)] = self.make_piece(target_color, line_kind)
                        # Detonate line bomb
                        if line_kind == 'LINE_H':
                            for col in range(self.cols):
                                matched.add((r, col))
                        else:
                            for row in range(self.rows):
                                matched.add((row, c))
            return matched, [list(matched)], created_specials

        # 3. Color Bomb x Cross Bomb
        if 'COLOR_BOMB' in specials and 'CROSS' in specials:
            cross_piece = p1 if s1 == 'CROSS' else p2
            target_color = self.get_piece_type(cross_piece)
            created_specials = {}
            matched = set([(r1, c1), (r2, c2)])
            for r in range(self.rows):
                for c in range(self.cols):
                    if self.get_piece_type(self.grid[r][c]) == target_color:
                        created_specials[(r, c)] = self.make_piece(target_color, 'CROSS')
                        for col in range(self.cols):
                            matched.add((r, col))
                        for row in range(self.rows):
                            matched.add((row, c))
            return matched, [list(matched)], created_specials

        # 4. Color Bomb x 3x3 Bomb
        if 'COLOR_BOMB' in specials and 'BOMB_3X3' in specials:
            bomb_piece = p1 if s1 == 'BOMB_3X3' else p2
            target_color = self.get_piece_type(bomb_piece)
            created_specials = {}
            matched = set([(r1, c1), (r2, c2)])
            for r in range(self.rows):
                for c in range(self.cols):
                    if self.get_piece_type(self.grid[r][c]) == target_color:
                        created_specials[(r, c)] = self.make_piece(target_color, 'BOMB_3X3')
                        for dr in [-1, 0, 1]:
                            for dc in [-1, 0, 1]:
                                nr, nc = r + dr, c + dc
                                if self.is_valid_coord(nr, nc):
                                    matched.add((nr, nc))
            return matched, [list(matched)], created_specials

        # Single Color Bomb x Normal Tile
        if 'COLOR_BOMB' in specials:
            normal_piece = p1 if s2 == 'COLOR_BOMB' else p2
            target_color = self.get_piece_type(normal_piece)
            matched = set([(r1, c1), (r2, c2)])
            if target_color is not None:
                for r in range(self.rows):
                    for c in range(self.cols):
                        if self.get_piece_type(self.grid[r][c]) == target_color:
                            matched.add((r, c))
            return matched, [list(matched)], {}

        # 5. 3x3 Bomb x 3x3 Bomb -> 5x5 MEGA EXPLOSION!
        if s1 == 'BOMB_3X3' and s2 == 'BOMB_3X3':
            cr, cc = r2, c2
            matched = set()
            for dr in [-2, -1, 0, 1, 2]:
                for dc in [-2, -1, 0, 1, 2]:
                    nr, nc = cr + dr, cc + dc
                    if self.is_valid_coord(nr, nc):
                        matched.add((nr, nc))
            return matched, [list(matched)], {}

        # 6. 3x3 Bomb x Line Bomb -> Clears 3 Rows or 3 Columns!
        if 'BOMB_3X3' in specials and ('LINE_H' in specials or 'LINE_V' in specials):
            line_piece = p1 if s1 in ('LINE_H', 'LINE_V') else p2
            line_kind = self.get_piece_special(line_piece) or ('LINE_H' if swap_dir == 'H' else 'LINE_V')
            cr, cc = r2, c2
            matched = set()
            if line_kind == 'LINE_H':
                for dr in [-1, 0, 1]:
                    r_target = cr + dr
                    if 0 <= r_target < self.rows:
                        for col in range(self.cols):
                            matched.add((r_target, col))
            else: # LINE_V
                for dc in [-1, 0, 1]:
                    c_target = cc + dc
                    if 0 <= c_target < self.cols:
                        for row in range(self.rows):
                            matched.add((row, c_target))
            return matched, [list(matched)], {}

        # 7. 3x3 Bomb x Cross Bomb -> Clears 3 Rows AND 3 Columns!
        if 'BOMB_3X3' in specials and 'CROSS' in specials:
            cr, cc = r2, c2
            matched = set()
            for dr in [-1, 0, 1]:
                r_target = cr + dr
                if 0 <= r_target < self.rows:
                    for col in range(self.cols):
                        matched.add((r_target, col))
            for dc in [-1, 0, 1]:
                c_target = cc + dc
                if 0 <= c_target < self.cols:
                    for row in range(self.rows):
                        matched.add((row, c_target))
            return matched, [list(matched)], {}

        return None

    def find_matches_in_grid(self, grid, last_swap_pair=None, swap_dir=None):
        matched_cells = set()
        match_groups = []
        created_specials = {}

        last_swap = last_swap_pair[1] if last_swap_pair else None

        horiz_runs = []
        vert_runs = []

        # 1. Horizontal Matches
        for r in range(self.rows):
            c = 0
            while c < self.cols:
                p_type = self.get_piece_type(grid[r][c])
                if p_type is None or p_type < 0 or p_type >= self.piece_types:
                    c += 1
                    continue
                run_len = 1
                while c + run_len < self.cols and self.get_piece_type(grid[r][c + run_len]) == p_type:
                    run_len += 1
                if run_len >= 3:
                    group = [(r, c + i) for i in range(run_len)]
                    horiz_runs.append(group)
                    match_groups.append(group)
                    for item in group:
                        matched_cells.add(item)
                c += run_len

        # 2. Vertical Matches
        for c in range(self.cols):
            r = 0
            while r < self.rows:
                p_type = self.get_piece_type(grid[r][c])
                if p_type is None or p_type < 0 or p_type >= self.piece_types:
                    r += 1
                    continue
                run_len = 1
                while r + run_len < self.rows and self.get_piece_type(grid[r + run_len][c]) == p_type:
                    run_len += 1
                if run_len >= 3:
                    group = [(r + i, c) for i in range(run_len)]
                    vert_runs.append(group)
                    match_groups.append(group)
                    for item in group:
                        matched_cells.add(item)
                r += run_len

        # 3. 2x2 Square Matches
        for r in range(self.rows - 1):
            for c in range(self.cols - 1):
                t1 = self.get_piece_type(grid[r][c])
                t2 = self.get_piece_type(grid[r+1][c])
                t3 = self.get_piece_type(grid[r][c+1])
                t4 = self.get_piece_type(grid[r+1][c+1])
                if t1 is not None and 0 <= t1 < self.piece_types and t1 == t2 == t3 == t4:
                    sq = [(r, c), (r+1, c), (r, c+1), (r+1, c+1)]
                    match_groups.append(sq)
                    for item in sq:
                        matched_cells.add(item)
                    target_pos = (r, c)
                    if last_swap and last_swap in sq:
                        target_pos = last_swap
                    created_specials[target_pos] = self.make_piece(t1, 'BOMB_3X3')

        # 4. Check Intersections (L/T/Cross)
        for h_run in horiz_runs:
            for v_run in vert_runs:
                inter = set(h_run).intersection(set(v_run))
                if inter:
                    inter_pos = list(inter)[0]
                    t_type = self.get_piece_type(grid[inter_pos[0]][inter_pos[1]])
                    target_pos = inter_pos
                    if last_swap and last_swap in (set(h_run) | set(v_run)):
                        target_pos = last_swap
                    created_specials[target_pos] = self.make_piece(t_type, 'CROSS')

        # Process straight line runs (5-in-a-row COLOR_BOMB and 4-in-a-row LINE_H/V)
        all_runs = horiz_runs + vert_runs
        for run in all_runs:
            length = len(run)
            p_type = self.get_piece_type(grid[run[0][0]][run[0][1]])
            target_pos = run[length // 2]
            if last_swap and last_swap in run:
                target_pos = last_swap

            if length >= 5:
                created_specials[target_pos] = self.make_piece(6, 'COLOR_BOMB')
            elif length == 4:
                if target_pos not in created_specials:
                    is_horizontal = (run[0][0] == run[1][0])
                    if swap_dir == 'H' or (swap_dir is None and is_horizontal):
                        special_kind = 'LINE_H'
                    elif swap_dir == 'V' or (swap_dir is None and not is_horizontal):
                        special_kind = 'LINE_V'
                    else:
                        special_kind = 'LINE_H' if is_horizontal else 'LINE_V'
                    created_specials[target_pos] = self.make_piece(p_type, special_kind)

        # 5. Expand explosions for any activated special items
        to_check = set(matched_cells)
        cleared_bomb_cells = set()
        
        while to_check:
            cell = to_check.pop()
            r, c = cell
            piece = grid[r][c]
            special = self.get_piece_special(piece)
            p_type = self.get_piece_type(piece)

            if special and cell not in cleared_bomb_cells:
                cleared_bomb_cells.add(cell)
                bomb_targets = self.get_bomb_explosion_targets(grid, r, c, special, p_type)
                for b_cell in bomb_targets:
                    if b_cell not in matched_cells:
                        matched_cells.add(b_cell)
                        to_check.add(b_cell)

        return matched_cells, match_groups, created_specials

    def get_bomb_explosion_targets(self, grid, r, c, special, piece_type):
        targets = set()
        if special == 'LINE_H':
            for col in range(self.cols):
                targets.add((r, col))
        elif special == 'LINE_V':
            for row in range(self.rows):
                targets.add((row, c))
        elif special == 'CROSS':
            for col in range(self.cols):
                targets.add((r, col))
            for row in range(self.rows):
                targets.add((row, c))
        elif special == 'BOMB_3X3':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r + dr, c + dc
                    if self.is_valid_coord(nr, nc):
                        targets.add((nr, nc))
        elif special == 'COLOR_BOMB':
            target_t = piece_type if (piece_type is not None and piece_type < self.piece_types) else random.randint(0, self.piece_types - 1)
            for row in range(self.rows):
                for col in range(self.cols):
                    if self.get_piece_type(grid[row][col]) == target_t:
                        targets.add((row, col))
        return targets

    def calculate_score_for_groups(self, match_groups, combo_step):
        total_pts = 0
        for group in match_groups:
            length = len(group)
            base_score = 80 + (length - 3) * 80
            total_pts += base_score
            
        if combo_step > 0:
            combo_bonus = combo_step * 40
            total_pts += combo_bonus
            
        return total_pts

    def apply_gravity_step(self):
        drops = []
        for c in range(self.cols):
            empty_row = self.rows - 1
            for r in range(self.rows - 1, -1, -1):
                if self.grid[r][c] is not None:
                    if empty_row != r:
                        drops.append({
                            'from_r': r,
                            'to_r': empty_row,
                            'c': c,
                            'piece': copy.deepcopy(self.grid[r][c])
                        })
                        self.grid[empty_row][c] = self.grid[r][c]
                        self.grid[r][c] = None
                    empty_row -= 1
                    
            new_row_spawn = -1
            for r in range(empty_row, -1, -1):
                new_piece = self.make_piece(random.randint(0, self.piece_types - 1))
                self.grid[r][c] = new_piece
                drops.append({
                    'from_r': new_row_spawn,
                    'to_r': r,
                    'c': c,
                    'piece': copy.deepcopy(new_piece)
                })
                new_row_spawn -= 1
                
        return drops
