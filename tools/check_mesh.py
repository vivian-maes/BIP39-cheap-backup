"""
Report the connected components of an exported STL.

A counter-plate is riddled with traps: the middle of every o, a, e, 8 is enclosed
by its letter and, without a bridge tying it to the rest of the plate, prints as
a loose speck. Nothing in the .scad says so and no preview image shows it — only
counting the components of the finished mesh does.

Components thinner than a nozzle are reported separately: they are slivers the
clearance offset pinched off inside tight apertures, the slicer will not lay them
down, and they are not what this check is hunting. A *printable* loose component
is the real defect.

    python3 tools/check_mesh.py <file.stl> [...]

Exit status is 1 if any printable loose component is found, so it can gate a
build.
"""

import sys

NOZZLE_MM = 0.4


def load_triangles(path):
    """
    Read vertices out of an ASCII STL, rounded so that coincident corners match.
    """
    triangles = []
    current = []
    with open(path) as handle:
        for line in handle:
            line = line.strip()
            if line.startswith('vertex'):
                current.append(tuple(round(float(v), 4) for v in line.split()[1:4]))
                if len(current) == 3:
                    triangles.append(tuple(current))
                    current = []
    return triangles


def components(triangles):
    """
    Union-find over vertices shared by a triangle.

    Returns:
        list[list[tuple]]: the vertices of each connected component.
    """
    parent = {}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for triangle in triangles:
        for vertex in triangle:
            parent.setdefault(vertex, vertex)
        union(triangle[0], triangle[1])
        union(triangle[1], triangle[2])

    grouped = {}
    for vertex in parent:
        grouped.setdefault(find(vertex), []).append(vertex)
    return list(grouped.values())


def extent(vertices):
    xs = [v[0] for v in vertices]
    ys = [v[1] for v in vertices]
    return (max(xs) - min(xs), max(ys) - min(ys))


def check(path):
    """
    Returns the number of printable loose components, printing a summary.
    """
    groups = components(load_triangles(path))
    sized = sorted(((extent(g), g) for g in groups), key=lambda s: s[0][0] * s[0][1])
    main, loose = sized[-1], sized[:-1]

    printable = [s for s, _ in loose if min(s) >= NOZZLE_MM]
    slivers = len(loose) - len(printable)

    name = path.rsplit('/', 1)[-1]
    print(f"{name}: pièce principale {main[0][0]:.1f} x {main[0][1]:.1f} mm, "
          f"{len(loose)} composant(s) détaché(s)")
    if slivers:
        print(f"  {slivers} plus fin(s) qu'une buse de {NOZZLE_MM} mm — éclats pincés "
              f"par le jeu, le trancheur ne les posera pas")
    for size in printable:
        print(f"  ⚠ {size[0]:.2f} x {size[1]:.2f} mm détaché et IMPRIMABLE : "
              f"il tombera de la pièce")
    return len(printable)


def main(paths):
    failures = sum(check(path) for path in paths)
    if failures:
        print(f"\n{failures} composant(s) imprimable(s) détaché(s) : à corriger "
              f"avant d'imprimer.")
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
