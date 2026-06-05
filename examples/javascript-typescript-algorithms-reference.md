# JavaScript / TypeScript - Algorithms and built-ins (intensive reference)

Audience: senior developers who want a dense, scan-friendly JS/TS crash course for algorithmic work: arrays, graphs, dynamic programming, strings, heaps, intervals, and related patterns.

---

## 1. Complexity cheat sheet

| Structure / op | Average | Worst | Notes |
| ---------------- | ------- | ----- | ----- |
| `array.push` / `pop` | O(1) | push may resize | amortized push; pop end is O(1) |
| `array.shift` / `unshift` | O(n) | O(n) | avoid for queues |
| `Map` / `Set` get/add/has | O(1) | O(n) | pathological collisions are rare |
| heap (implemented) | O(log n) | O(log n) | not in language core |
| binary search | O(log n) | O(log n) | roll your own |
| `array.sort` | O(n log n) | O(n log n) | mutates; stable in modern engines |
| repeated string `+` | O(n^2) | - | collect chunks, then `join` |

---

## 2. JS/TS syntax crash course

```typescript
const fixed = 1;
let mutable = 0;

if (x === null || x === undefined) {
  // nullish
} else if (x > 0) {
  // positive
}

if (items.length > 0) {
  // explicit emptiness check
}

const name = user.profile?.name ?? "anonymous";
const copy = [...nums];
const [first, ...rest] = nums;
const { id, status = "new" } = order;
const square = (x: number): number => x * x;
```

Use `===` / `!==` unless coercion is deliberate. Use `??` for nullish defaults; `||` treats `0`, `""`, and `false` as missing too.

---

## 3. Core patterns

```typescript
for (const [i, x] of nums.entries()) { ... }
for (let i = 0; i < nums.length; i++) { ... }

const sorted = [...nums].sort((a, b) => a - b);
pairs.sort((a, b) => a[0] - b[0] || b[1] - a[1]);
const order = nums.map((_, i) => i).sort((i, j) => nums[i] - nums[j]);

nums.reduce((acc, x) => acc ^ x, 0);
nums.some((x) => x > 0);
nums.every((x) => x >= 0);
```

---

## 4. `Map`, `Set`, and compact counts

```typescript
const freq = new Map<string, number>();
for (const ch of s) freq.set(ch, (freq.get(ch) ?? 0) + 1);

const seen = new Set<number>();
seen.add(x);

const g = new Map<number, number[]>();
if (!g.has(u)) g.set(u, []);
g.get(u)!.push(v);

const count = new Int32Array(26);
count[s.charCodeAt(i) - 97]++;
```

Use `Map` for arbitrary keys and `Record` / object for fixed string keys.

---

## 5. Priority queues

There is no stdlib heap. Implement a binary heap for portable snippets.

```typescript
function heapPush<T>(h: T[], x: T, cmp: (a: T, b: T) => number): void {
  h.push(x);
  let i = h.length - 1;
  while (i > 0) {
    const p = (i - 1) >> 1;
    if (cmp(h[i], h[p]) >= 0) break;
    [h[i], h[p]] = [h[p], h[i]];
    i = p;
  }
}
```

For max-heaps, invert the comparator or priority.

---

## 6. Binary search on sorted arrays

```typescript
function lowerBound(n: number, ok: (i: number) => boolean): number {
  let lo = 0;
  let hi = n;
  while (lo < hi) {
    const mid = lo + Math.floor((hi - lo) / 2);
    if (ok(mid)) hi = mid;
    else lo = mid + 1;
  }
  return lo;
}

const i = lowerBound(arr.length, (j) => arr[j] >= x);
```

Avoid bitwise midpoint (`>> 1`) for generic numeric ranges; it coerces to 32-bit signed integers.

---

## 7. Graphs and grids

```typescript
function bfs(start: number, g: Map<number, number[]>): Map<number, number> {
  const dist = new Map<number, number>([[start, 0]]);
  const q: number[] = [start];

  for (let head = 0; head < q.length; head++) {
    const u = q[head];
    for (const v of g.get(u) ?? []) {
      if (!dist.has(v)) {
        dist.set(v, dist.get(u)! + 1);
        q.push(v);
      }
    }
  }

  return dist;
}
```

```typescript
const DIRS = [
  [1, 0],
  [-1, 0],
  [0, 1],
  [0, -1],
] as const;

for (const [di, dj] of DIRS) {
  const ni = i + di;
  const nj = j + dj;
  if (ni >= 0 && ni < rows && nj >= 0 && nj < cols) {
    ...
  }
}
```

Use an index-based queue, not `shift()`. JS call stacks are limited, so deep DFS is safer with an explicit stack.

---

## 8. Dynamic programming

```typescript
const memo = new Map<string, number>();

function dfs(i: number, state: number): number {
  const k = `${i},${state}`;
  if (memo.has(k)) return memo.get(k)!;
  const res = 0;
  memo.set(k, res);
  return res;
}
```

Use `number[]` / `number[][]` for bottom-up DP. Roll to two rows when only the previous row matters.

---

## 9. Strings and parsing

```typescript
s.split(",");
s.trim();
s.indexOf("needle");
s.includes("needle");
s.replace("old", "new");
parts.join("");
s.slice(start, end);
s.charCodeAt(i);
String.fromCharCode(97);
[...s];
```

Strings are immutable. Build long output with `array.push` plus `join`.

---

## 10. Numeric notes

`number` is IEEE-754 double precision. Integers are exact only up to `Number.MAX_SAFE_INTEGER`.

```typescript
5 / 2;              // 2.5
Math.trunc(5 / 2);  // 2
Math.floor(-5 / 2); // -3
Math.trunc(-5 / 2); // -2
5 % 2;              // 1
Number.POSITIVE_INFINITY;
Number.isSafeInteger(x);
```

Use `bigint` for arbitrary-size integers, but never mix `bigint` and `number` without conversion.

---

## 11. Common gotchas

| Pitfall | Safer pattern |
| ------- | ------------- |
| `sort()` without comparator | numbers sort lexicographically; use `(a, b) => a - b` |
| comparator returning boolean | return negative / zero / positive number |
| `array.shift()` in hot loops | index-based queue |
| bitwise midpoint `>> 1` | coerces to 32-bit signed; use `Math.floor` |
| `Array(R).fill(Array(C).fill(0))` | aliases rows; use `Array.from({ length: R }, () => Array(C).fill(0))` |
| sparse `Array(n)` | use `Array.from({ length: n }, (_, i) => i)` |
| deep equality | no builtin deep equal for nested structures |

---

## 12. TypeScript

```typescript
function pairWithSum(nums: readonly number[], target: number): [number, number] | null {
  ...
}

type Result<T> = { ok: true; value: T } | { ok: false; reason: string };
```

Use `readonly T[]` for read-only inputs, tuple types for fixed-shape returns, and discriminated unions for explicit outcomes.

---

## 13. Built-ins and globals

| API | Role |
| --- | ---- |
| `Math` | `floor`, `ceil`, `trunc`, `abs`, `min`, `max`, `hypot`, `sign`; no `gcd` |
| `Number` | `isFinite`, `isInteger`, `MAX_SAFE_INTEGER` |
| `BigInt` | arbitrary-size integers; literals `1n` |
| `Intl.Collator` | locale-aware sort keys |
| `structuredClone` | deep clone in modern environments |
| `performance.now()` | micro-benchmarking with care |

---

## 14. Worked example - LeetCode 312 Burst Balloons (Hard)

Interval DP: fix which balloon is burst last inside each open interval.

```typescript
function maxCoins(nums: readonly number[]): number {
  const a = [1, ...nums, 1];
  const n = a.length;
  const dp = Array.from({ length: n }, () => Array(n).fill(0));

  for (let width = 2; width < n; width++) {
    for (let left = 0; left + width < n; left++) {
      const right = left + width;
      let best = 0;

      for (let k = left + 1; k < right; k++) {
        best = Math.max(
          best,
          a[left] * a[k] * a[right] + dp[left][k] + dp[k][right],
        );
      }

      dp[left][right] = best;
    }
  }

  return dp[0][n - 1];
}

console.assert(maxCoins([3, 1, 5, 8]) === 167);
console.assert(maxCoins([1, 5]) === 10);
```

Time `O(n^3)`, space `O(n^2)`.

---

This document is orthogonal to architecture and domain modeling; see `javascript-typescript-design-patterns-ddd.md`.
