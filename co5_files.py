"""CO5 - Contiguous allocation on a simulated disk + tree-structured directory."""


class DiskFullError(Exception):
    pass


class FileEntry:
    def __init__(self, path, start, length):
        self.path, self.start, self.length = path, start, length


class Disk:
    def __init__(self, n_blocks=100):
        self.n = n_blocks
        self.bitmap = [0] * n_blocks          # 0 = free, 1 = used
        self.files = {}                       # path -> FileEntry

    def holes(self):
        out, i = [], 0
        while i < self.n:
            if self.bitmap[i] == 0:
                j = i
                while j < self.n and self.bitmap[j] == 0:
                    j += 1
                out.append((i, j - i)); i = j
            else:
                i += 1
        return out

    def allocate(self, path, size):
        for start, length in self.holes():    # first-fit
            if length >= size:
                for b in range(start, start + size):
                    self.bitmap[b] = 1
                entry = FileEntry(path, start, size)
                self.files[path] = entry
                return entry
        free = self.n - sum(self.bitmap)
        largest = max((l for _, l in self.holes()), default=0)
        raise DiskFullError(f"No contiguous run of {size} blocks. Free blocks = {free}, "
                            f"largest hole = {largest}. (External fragmentation!)" if free >= size
                            else f"Disk full: need {size} blocks, only {free} free.")

    def free(self, path):
        e = self.files.pop(path)
        for b in range(e.start, e.start + e.length):
            self.bitmap[b] = 0

    def compact(self):
        """Slide all files to the start of the disk (removes external fragmentation)."""
        self.bitmap = [0] * self.n
        pos = 0
        for e in sorted(self.files.values(), key=lambda e: e.start):
            e.start = pos
            for b in range(pos, pos + e.length):
                self.bitmap[b] = 1
            pos += e.length

    def stats(self):
        used = sum(self.bitmap)
        free = self.n - used
        largest = max((l for _, l in self.holes()), default=0)
        frag = (1 - largest / free) * 100 if free else 0
        return dict(used=used, free=free, largest=largest, frag=frag, holes=self.holes())


class Node:
    def __init__(self, name, is_dir, parent=None):
        self.name, self.is_dir, self.parent = name, is_dir, parent
        self.children = {}
        self.entry = None

    def path(self):
        parts, n = [], self
        while n.parent:
            parts.append(n.name); n = n.parent
        return "/" + "/".join(reversed(parts))


class FileSystem:
    def __init__(self, disk=None):
        self.disk = disk or Disk()
        self.root = Node("root", True)

    @staticmethod
    def _parts(path):
        return [p for p in path.split("/") if p]

    def resolve(self, path):
        node = self.root
        for p in self._parts(path):
            if not node.is_dir or p not in node.children:
                raise FileNotFoundError(f"Path not found: {path}")
            node = node.children[p]
        return node

    def mkdir(self, path):
        node = self.root
        for p in self._parts(path):
            if p not in node.children:
                node.children[p] = Node(p, True, node)
            elif not node.children[p].is_dir:
                raise ValueError(f"{p} is a file")
            node = node.children[p]
        return node

    def create(self, path, size):
        parts = self._parts(path)
        if not parts:
            raise ValueError("Empty file name")
        parent = self.mkdir("/".join(parts[:-1]))
        if parts[-1] in parent.children:
            raise ValueError(f"{path} already exists")
        node = Node(parts[-1], False, parent)
        node.entry = self.disk.allocate(node.path(), size)   # may raise DiskFullError
        parent.children[parts[-1]] = node
        return node

    def delete(self, path):
        node = self.resolve(path)
        if node is self.root:
            raise ValueError("Cannot delete root")
        self._free(node)
        del node.parent.children[node.name]

    def _free(self, node):
        if node.is_dir:
            for c in list(node.children.values()):
                self._free(c)
        else:
            self.disk.free(node.path())

    def ls(self, path="/"):
        node = self.resolve(path)
        if not node.is_dir:
            return [node.name]
        return [c.name + ("/" if c.is_dir else "") for c in sorted(node.children.values(), key=lambda c: c.name)]

    def tree_lines(self):
        lines = ["root/"]

        def walk(node, prefix):
            kids = sorted(node.children.values(), key=lambda c: (not c.is_dir, c.name))
            for i, k in enumerate(kids):
                last = i == len(kids) - 1
                label = k.name + "/" if k.is_dir else f"{k.name}  [blocks {k.entry.start}-{k.entry.start + k.entry.length - 1}]"
                lines.append(prefix + ("└── " if last else "├── ") + label)
                if k.is_dir:
                    walk(k, prefix + ("    " if last else "│   "))
        walk(self.root, "")
        return lines


def build_sample_fs():
    fs = FileSystem()
    for d in ("CSE/Sem3", "CSE/Sem5", "ECE/Sem3", "ECE/Sem5", "MECH/Sem5", "CIVIL/Sem3"):
        fs.mkdir(d)
    fs.create("/CSE/Sem3/hallA_seating.txt", 8)
    fs.create("/CSE/Sem5/hallB_seating.txt", 12)
    fs.create("/ECE/Sem3/hallC_seating.txt", 6)
    fs.create("/ECE/Sem5/hallA_seating.txt", 15)
    fs.create("/MECH/Sem5/hallD_seating.txt", 10)
    fs.create("/CIVIL/Sem3/temp_plan.txt", 7)            # deleted below to leave a hole
    fs.create("/MECH/Sem3/hallB_seating.txt", 10)
    fs.delete("/CIVIL/Sem3/temp_plan.txt")               # sample external fragmentation
    return fs
