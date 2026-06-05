# Python 3 - Algorithms and standard library (intensive reference)

Audience: senior developers who want a dense, scan-friendly Python crash course for algorithmic work: arrays, graphs, dynamic programming, strings, heaps, intervals, and related patterns. Assumes Python 3.10+ unless noted.

---

## 1. Complexity cheat sheet

| Structure / op | Average | Worst | Notes |
| ---------------- | ------- | ----- | ----- |
| `list` append / pop end | O(1) | append may resize | append is amortized; pop end is O(1) |
| `list` insert(0) / pop(0) | O(n) | O(n) | use `deque` for queues |
| `dict` / `set` get/add | O(1) | O(n) | pathological collisions are rare |
| `heapq` push/pop | O(log n) | O(log n) | min-heap |
| `bisect` lookup | O(log n) | O(log n) | locating only; insertion into list is O(n) |
| sort `n` items | O(n log n) | O(n log n) | Timsort, stable |
| string slice / repeated concat | O(k) / O(n^2) | - | build with list + `join` |

---

## 2. Python syntax crash course

```python
if x is None:
    ...
elif x > 0:
    ...
else:
    ...

for i in range(0, n, 2):  # start inclusive, stop exclusive
    ...

squares = [x * x for x in nums if x >= 0]
positions = {x: i for i, x in enumerate(nums)}
unique_lengths = {len(word) for word in words}

head = a[:k]
tail = a[k:]
rev = a[::-1]

first, *middle, last = items
a[i], a[j] = a[j], a[i]
label = "even" if x % 2 == 0 else "odd"
```

Use `is` / `is not` for identity (`None`, sentinels), `==` for value equality. Avoid mutable defaults:

```python
def add_item(x: int, acc: list[int] | None = None) -> list[int]:
    if acc is None:
        acc = []
    acc.append(x)
    return acc
```

---

## 3. Core builtins

```python
for i, x in enumerate(nums):
    ...

for a, b in zip(nums, flags):  # truncates to shortest
    ...

nums.sort(key=lambda x: (x[0], -x[1]))
sorted_indices = sorted(range(len(nums)), key=nums.__getitem__)

from functools import reduce
from operator import xor

reduce(xor, nums, 0)
sum(nums)
any(x > 0 for x in nums)
all(x >= 0 for x in nums)
q, r = divmod(total, width)

min(range(len(nums)), key=nums.__getitem__)
```

---

## 4. `collections`

```python
from collections import Counter, defaultdict, deque

q = deque([start])
while q:
    u = q.popleft()

g: dict[int, list[int]] = defaultdict(list)
g[u].append(v)

cnt = Counter(s)
cnt.most_common(3)

dp = defaultdict(int)
dp[(i, mask)] += 1
```

`deque(maxlen=n)` automatically drops items from the opposite end.

---

## 5. `heapq`

```python
import heapq

h = []
heapq.heappush(h, (priority, tie_breaker, payload))
priority, _, payload = heapq.heappop(h)

heapq.nlargest(k, iterable, key=None)
heapq.nsmallest(k, iterable, key=None)
```

Python heaps are min-heaps. For max-heaps, negate priority or invert the sort key. Tuple comparison continues to later fields on ties, so add a numeric `tie_breaker` before non-comparable payloads.

---

## 6. `bisect`

```python
import bisect

i = bisect.bisect_left(arr, x)   # first index with arr[i] >= x
j = bisect.bisect_right(arr, x)  # first index with arr[j] > x
count_x = j - i
```

---

## 7. `itertools`

```python
from itertools import accumulate, chain, groupby, product

list(accumulate(nums, initial=0))

for state in product(range(2), repeat=n):
    ...

for key, group in groupby(sorted(nums)):
    ...

list(chain.from_iterable(lists))
```

---

## 8. Bit manipulation

```python
x & (x - 1)       # clear lowest set bit
x & -x            # isolate lowest set bit
bin(x).count("1") # popcount for modest n

mask = (1 << n) - 1
sub = mask
while True:
    # use sub
    if sub == 0:
        break
    sub = (sub - 1) & mask
```

---

## 9. Graphs and grids

Use `dict[int, list[int]]` for sparse graphs and `list[list[int]]` for dense `0..n-1` graphs.

```python
from collections import deque


def bfs(start: int, g: dict[int, list[int]]) -> dict[int, int]:
    dist = {start: 0}
    q = deque([start])
    while q:
        u = q.popleft()
        for v in g.get(u, []):
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist
```

```python
DIRS = (1, 0), (-1, 0), (0, 1), (0, -1)
for di, dj in DIRS:
    ni, nj = i + di, j + dj
    if 0 <= ni < rows and 0 <= nj < cols:
        ...
```

Topological sort: Kahn or DFS postorder. Union-Find: path compression plus union by rank.

---

## 10. Dynamic programming

- Top-down: `functools.cache` or `lru_cache(maxsize=None)`; keys must be hashable.
- Bottom-up: `dp[i]`, `dp[i][j]`, or rolled rows.
- Knapsack: loop direction distinguishes 0/1 vs unbounded.
- Interval DP: fill by increasing segment length.

```python
from functools import cache


@cache
def dfs(i: int, state: int) -> int:
    if i == n:
        return 0
    return dfs(i + 1, state)
```

---

## 11. Strings and parsing

```python
s.split()
s.strip()
s.find("needle")
s.replace("old", "new")
"".join(parts)
s[::-1]
ord("a"), chr(97)
```

Strings are immutable; build large output with `list.append` and `join`.

---

## 12. Numeric notes

```python
5 / 2      # 2.5
5 // 2     # 2
-5 // 2    # -3, floor toward -inf
5 % 2      # 1
float("inf")
```

Prefer integer arithmetic for exactness. Use `decimal.Decimal` only when domain rounding rules matter.

---

## 13. Binary search on answer

```python
lo, hi = 0, 10**18
while lo < hi:
    mid = (lo + hi) // 2
    if ok(mid):
        hi = mid
    else:
        lo = mid + 1
```

---

## 14. Common gotchas

| Pitfall | Safer pattern |
| ------- | ------------- |
| mutating `dict` while iterating | iterate a snapshot or collect changes first |
| float equality | use integers, rationals, or an epsilon |
| recursion depth | use iterative traversal or adjust limit sparingly |
| `grid = [[0] * C] * R` | aliases rows; use `[[0] * C for _ in range(R)]` |
| mutable default args | default to `None`, allocate inside |
| list membership in hot path | use `set` |
| `sort()` mutates | use `sorted(seq)` when original order matters |

---

## 15. Minimal typing

```python
from collections.abc import Sequence


def pair_with_sum(nums: Sequence[int], target: int) -> tuple[int, int] | None:
    ...
```

Use built-in generics (`list[int]`, `dict[str, int]`) and `Sequence[T]` for read-only inputs.

---

## 16. Standard library last mile

| Module | Use |
| ------ | --- |
| `math` | `gcd`, `lcm`, `isqrt`, `comb`, `perm`, `inf` |
| `operator` | `itemgetter`, `attrgetter` |
| `functools` | `cache`, `lru_cache`, `cmp_to_key` |
| `heapq` | min-heap primitives |
| `enum.IntEnum` | finite states |

---

## 17. Worked example - LeetCode 312 Burst Balloons (Hard)

Interval DP: fix which balloon is burst last inside each open interval.

```python
def max_coins(nums: list[int]) -> int:
    a = [1, *nums, 1]
    n = len(a)
    dp = [[0] * n for _ in range(n)]

    for width in range(2, n):
        for left in range(n - width):
            right = left + width
            best = 0
            for k in range(left + 1, right):
                best = max(
                    best,
                    a[left] * a[k] * a[right] + dp[left][k] + dp[k][right],
                )
            dp[left][right] = best

    return dp[0][n - 1]


if __name__ == "__main__":
    assert max_coins([3, 1, 5, 8]) == 167
    assert max_coins([1, 5]) == 10
```

Time `O(n^3)`, space `O(n^2)`.

---

This document is intentionally orthogonal to architecture and domain modeling; see `python3-design-patterns-ddd.md`.
