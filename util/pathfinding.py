from collections import defaultdict


def _heuristic(node, target):
    return node.get_distance(target)


def _cost(node):
    return 1


def _get_neighbors(node):
    return node.neighbors


def _get_full_path(node, came_from):
    full_path = [node]
    while node in came_from:
        node = came_from[node]
        full_path.insert(0, node)
    return tuple(full_path[1:])


def a_star(origin, target,
        get_neighbors=_get_neighbors,
        heuristic=_heuristic,
        cost=_cost,
        debug=False,
        ):
    if origin is target:
        return None

    open_set = {origin}
    came_from = {}
    partial_score = defaultdict(lambda: float('inf'))
    partial_score[origin] = 0
    guess_score = defaultdict(lambda: float('inf'))
    guess_score[origin] = heuristic(origin, target)

    while open_set:
        best_nodes = sorted(open_set, key=lambda x: guess_score[x])
        current = best_nodes[0]
        if current is target:
            return _get_full_path(current, came_from)
        open_set.remove(current)
        if debug:
            open_set_str = '\n'.join(f'- {n}' for n in best_nodes[:10])
            print('\n'.join([
                '_'*50,
                f'Best nodes score:',
                *(f'- {n}: {guess_score[n]}' for n in best_nodes[:10]),
                f'Best nodes distance from origin:',
                *(f'- {n}: {partial_score[n]}' for n in best_nodes[:10]),
                '_'*50,
                f'Current: {current}',
            ]))
        for neighbor in get_neighbors(current):
            tentative_partial_score = partial_score[current] + cost(neighbor)
            if debug:
                print(f'Neighbor: {neighbor} ({tentative_partial_score})')
            if tentative_partial_score < partial_score[neighbor]:
                came_from[neighbor] = current
                partial_score[neighbor] = tentative_partial_score
                guess_score[neighbor] = tentative_partial_score + heuristic(neighbor, target)
                if neighbor not in open_set:
                    open_set.add(neighbor)
    return None
