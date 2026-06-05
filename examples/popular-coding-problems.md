# 50 Most Popular LeetCode & HackerRank Problems

A ranked reference of the coding-interview problems that come up most often, with a minimal Python 3 solution and a short write-up for each. Ranking blends LeetCode's "Top Interview 150" + Blind 75 (where the popularity signal is strongest) with the most-cited HackerRank Interview Preparation Kit classics. Order reflects interview frequency, not difficulty.

## Contents

- **Top 10 — Universal must-knows** *(1–10)*: Two Sum · Valid Parentheses · Merge Two Sorted Lists · Best Time to Buy and Sell Stock · Valid Palindrome · Reverse Linked List · Maximum Subarray · Climbing Stairs · Number of Islands · Linked List Cycle
- **Arrays & Hashing** *(11–18)*: Contains Duplicate · Valid Anagram · Group Anagrams · Top K Frequent Elements · Product of Array Except Self · Move Zeroes · Longest Consecutive Sequence · Encode and Decode Strings
- **Two Pointers & Sliding Window** *(19–24)*: 3Sum · Container With Most Water · Trapping Rain Water · Longest Substring Without Repeating Characters · Longest Repeating Character Replacement · Minimum Window Substring
- **Stack & Linked List** *(25–29)*: Min Stack · Daily Temperatures · LRU Cache · Merge k Sorted Lists · Remove Nth Node From End of List
- **Trees & Graphs** *(30–37)*: Invert Binary Tree · Maximum Depth of Binary Tree · Same Tree · Binary Tree Level Order Traversal · Validate BST · Lowest Common Ancestor of a BST · Course Schedule · Clone Graph
- **Binary Search & Sorting** *(38–40)*: Binary Search · Search in Rotated Sorted Array · Find Median from Data Stream
- **Dynamic Programming** *(41–44)*: House Robber · Coin Change · Longest Increasing Subsequence · Word Break
- **HackerRank Classics** *(45–50)*: Diagonal Difference · Plus Minus · Mini-Max Sum · Time Conversion · Sales by Match · Sparse Arrays

---

## Top 10 — Universal must-knows

### 1. Two Sum *(LeetCode #1 · Easy)*
<https://leetcode.com/problems/two-sum/>

Given an array of integers and a target, return the indices of the two numbers that add up to the target. Exactly one solution is guaranteed and you cannot use the same element twice. The naive double loop is O(n²); the trick is to keep a hash map from value → index as you iterate. For each new number `n`, check whether `target - n` is already in the map — if it is, you have your pair. This is the canonical "use a hash map to trade space for time" problem, which is precisely why it is the most-asked LeetCode question of all time. Complexity: O(n) time, O(n) space.

```python
def twoSum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
```

### 2. Valid Parentheses *(LeetCode #20 · Easy)*
<https://leetcode.com/problems/valid-parentheses/>

Given a string of brackets `()[]{}`, decide whether every opener has a matching closer in the right order. The classic stack problem: push openers, and when you see a closer, the top of the stack must be its match. The string is valid iff the stack ends empty and you never pop a mismatch. A small dictionary mapping closer → opener keeps the code symmetric and short. This problem appears in nearly every "intro to stacks" interview rotation because it generalizes cleanly to expression parsing. Complexity: O(n) time, O(n) space.

```python
def isValid(s):
    pairs = {')': '(', ']': '[', '}': '{'}
    stack = []
    for c in s:
        if c in pairs:
            if not stack or stack.pop() != pairs[c]:
                return False
        else:
            stack.append(c)
    return not stack
```

### 3. Merge Two Sorted Lists *(LeetCode #21 · Easy)*
<https://leetcode.com/problems/merge-two-sorted-lists/>

Merge two sorted linked lists into one sorted linked list. The standard approach uses a dummy head node and a `tail` pointer; at each step, splice in the smaller of the two list heads. When one input runs out, attach the rest of the other. The dummy node removes the special case for the first append. This is the building block of merge sort on linked lists and a frequent warm-up for "merge K sorted lists". Complexity: O(n + m) time, O(1) extra space (the result reuses the input nodes).

```python
def mergeTwoLists(l1, l2):
    dummy = tail = ListNode()
    while l1 and l2:
        if l1.val <= l2.val:
            tail.next, l1 = l1, l1.next
        else:
            tail.next, l2 = l2, l2.next
        tail = tail.next
    tail.next = l1 or l2
    return dummy.next
```

### 4. Best Time to Buy and Sell Stock *(LeetCode #121 · Easy)*
<https://leetcode.com/problems/best-time-to-buy-and-sell-stock/>

Given daily prices, find the maximum profit from a single buy and a later sell. Brute force tries every pair (O(n²)). The linear solution is a one-pass scan that tracks the minimum price seen so far and the best profit if you sold today (`price - min_so_far`). The key observation: at each day, you only care about the lowest price up to that point, not which day it was. This problem teaches "running minimum" thinking and is the gateway to the harder stock variants (multiple transactions, with cooldown, etc.). Complexity: O(n) time, O(1) space.

```python
def maxProfit(prices):
    lo, best = float('inf'), 0
    for p in prices:
        lo = min(lo, p)
        best = max(best, p - lo)
    return best
```

### 5. Valid Palindrome *(LeetCode #125 · Easy)*
<https://leetcode.com/problems/valid-palindrome/>

Decide whether a string is a palindrome after lowercasing and discarding non-alphanumeric characters. The cleanest implementation uses two pointers walking inward, skipping invalid characters and comparing letter/digit pairs case-insensitively. A one-liner with a filtered `s == s[::-1]` works but allocates extra memory; the two-pointer version runs in O(1) extra space and is what interviewers want to see. The point is to test attention to edge cases (empty after filtering, mixed case, punctuation), not algorithmic depth. Complexity: O(n) time.

```python
def isPalindrome(s):
    i, j = 0, len(s) - 1
    while i < j:
        while i < j and not s[i].isalnum(): i += 1
        while i < j and not s[j].isalnum(): j -= 1
        if s[i].lower() != s[j].lower(): return False
        i, j = i + 1, j - 1
    return True
```

### 6. Reverse Linked List *(LeetCode #206 · Easy)*
<https://leetcode.com/problems/reverse-linked-list/>

Reverse a singly linked list in place. Walk the list with three pointers: `prev`, `curr`, and a saved `next`. At each step, flip `curr.next` to point to `prev`, then advance both. When `curr` is None, `prev` is the new head. The recursive variant is elegant but uses O(n) stack — most interviewers prefer the iterative version because it shows pointer fluency. This is the foundational linked-list manipulation; once you know it, problems like "reverse in groups of k" and "palindrome linked list" become straightforward. Complexity: O(n) time, O(1) space.

```python
def reverseList(head):
    prev, curr = None, head
    while curr:
        curr.next, prev, curr = prev, curr, curr.next
    return prev
```

### 7. Maximum Subarray *(LeetCode #53 · Medium)*
<https://leetcode.com/problems/maximum-subarray/>

Find the contiguous subarray with the largest sum (Kadane's algorithm). At each index, the best subarray ending here is either just this element, or this element appended to the best subarray ending at the previous index — whichever is larger. Track that running value and the global maximum. The cleverness is realizing the "extend or restart" decision can be made greedily without backtracking. This is the most-cited 1-D dynamic programming problem and the conceptual ancestor of many sliding-window/DP variants. Complexity: O(n) time, O(1) space.

```python
def maxSubArray(nums):
    cur = best = nums[0]
    for n in nums[1:]:
        cur = max(n, cur + n)
        best = max(best, cur)
    return best
```

### 8. Climbing Stairs *(LeetCode #70 · Easy)*
<https://leetcode.com/problems/climbing-stairs/>

You can take 1 or 2 steps at a time; how many distinct ways to reach step n? The number of ways to reach step n equals the ways to reach n-1 (then take one step) plus ways to reach n-2 (then take two) — i.e., the Fibonacci recurrence. Naive recursion is O(2^n); memoization makes it O(n); but two rolling variables suffice for O(1) space. This is the textbook "your first DP problem" and a great vehicle for showing how to derive a recurrence and then optimize. Complexity: O(n) time, O(1) space.

```python
def climbStairs(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a
```

### 9. Number of Islands *(LeetCode #200 · Medium)*
<https://leetcode.com/problems/number-of-islands/>

Given a 2-D grid of `'1'` (land) and `'0'` (water), count the connected components of land (4-directionally). Iterate every cell; whenever you hit unvisited land, increment the count and flood-fill (DFS or BFS) to mark the whole island visited. The cleanest in-place version overwrites visited land with `'0'` so no separate `visited` set is needed. This is the entry-level grid traversal problem, and the same pattern solves "Max Area of Island", "Surrounded Regions", and "Pacific Atlantic Water Flow". Complexity: O(rows × cols).

```python
def numIslands(grid):
    def dfs(r, c):
        if 0 <= r < len(grid) and 0 <= c < len(grid[0]) and grid[r][c] == '1':
            grid[r][c] = '0'
            for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)): dfs(r+dr, c+dc)
    count = 0
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == '1':
                dfs(r, c); count += 1
    return count
```

### 10. Linked List Cycle *(LeetCode #141 · Easy)*
<https://leetcode.com/problems/linked-list-cycle/>

Detect whether a linked list contains a cycle. The hash-set solution is trivial but uses O(n) memory; the elegant answer is Floyd's "tortoise and hare": advance one pointer one step and another two steps. If they ever meet, there's a cycle; if the fast pointer hits the end, there isn't. Why it works: in a cycle, the fast pointer gains one step on the slow per iteration, so they must collide within the loop's length. Constant extra space, single pass. Complexity: O(n) time, O(1) space.

```python
def hasCycle(head):
    slow = fast = head
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
        if slow is fast: return True
    return False
```

---

## Arrays & Hashing

### 11. Contains Duplicate *(LeetCode #217 · Easy)*
<https://leetcode.com/problems/contains-duplicate/>

Return whether any value appears at least twice. The "minimal" solution is a one-liner that compares the length of the input to the length of its set: if any element repeats, the set will be smaller. This problem is mostly a vehicle for teaching that hash sets give you O(1) membership tests, which is the right primitive an enormous fraction of the time. Sorting also works in O(n log n) but is strictly worse here. Complexity: O(n) time, O(n) space.

```python
def containsDuplicate(nums):
    return len(nums) != len(set(nums))
```

### 12. Valid Anagram *(LeetCode #242 · Easy)*
<https://leetcode.com/problems/valid-anagram/>

Two strings are anagrams iff they contain the same characters with the same multiplicities. The shortest correct answer compares `Counter(s) == Counter(t)`; equivalently, compare sorted strings (O(n log n)). For a fixed alphabet (e.g. lowercase English), a length-26 array is the most space-efficient. The `Counter` version is idiomatic Python and runs in linear time. This problem appears constantly as the warm-up to "Group Anagrams". Complexity: O(n) time, O(n) space.

```python
from collections import Counter
def isAnagram(s, t):
    return Counter(s) == Counter(t)
```

### 13. Group Anagrams *(LeetCode #49 · Medium)*
<https://leetcode.com/problems/group-anagrams/>

Group a list of strings so anagrams are bucketed together. Use a dictionary keyed by a canonical signature of each string — sorting its characters works, and the resulting tuple/string is hashable. Each input gets appended to its signature's bucket. Sorting each string is O(k log k); a length-26 character-count tuple is O(k) and slightly faster but more code. The `defaultdict(list)` pattern is what most interviewers want to see. Complexity: O(n · k log k) total.

```python
from collections import defaultdict
def groupAnagrams(strs):
    buckets = defaultdict(list)
    for s in strs:
        buckets[''.join(sorted(s))].append(s)
    return list(buckets.values())
```

### 14. Top K Frequent Elements *(LeetCode #347 · Medium)*
<https://leetcode.com/problems/top-k-frequent-elements/>

Return the k most frequent values in an array. Count occurrences, then either sort items by frequency (O(n log n)) or — better — use a heap of size k for O(n log k). The truly optimal "bucket sort" approach indexes by frequency in O(n), but `Counter.most_common(k)` is the minimal idiomatic answer and uses heap-based selection internally. Choose between elegance and theoretical optimality based on interviewer signal. Complexity: O(n log k) for the heap solution.

```python
from collections import Counter
def topKFrequent(nums, k):
    return [v for v, _ in Counter(nums).most_common(k)]
```

### 15. Product of Array Except Self *(LeetCode #238 · Medium)*
<https://leetcode.com/problems/product-of-array-except-self/>

Return an array where `out[i]` is the product of all input elements except `nums[i]`, **without using division and in O(n)**. The trick is two passes: first, fill `out[i]` with the product of everything to the left of `i`; second, walk right-to-left multiplying by a running product of everything to the right. The output array doesn't count as extra space, so the result is O(1) auxiliary memory. The "no division" rule rules out the trivial `total / nums[i]` and forces the prefix/suffix idea. Complexity: O(n) time, O(1) extra space.

```python
def productExceptSelf(nums):
    n = len(nums); out = [1] * n
    left = 1
    for i in range(n):
        out[i] = left; left *= nums[i]
    right = 1
    for i in range(n - 1, -1, -1):
        out[i] *= right; right *= nums[i]
    return out
```

### 16. Move Zeroes *(LeetCode #283 · Easy)*
<https://leetcode.com/problems/move-zeroes/>

Move all zeros in an array to the end while preserving the relative order of non-zero elements, in place. Two-pointer technique: a write pointer marks where the next non-zero goes, and a read pointer scans the array. Whenever the read pointer finds a non-zero, swap it into the write slot and advance the write pointer. After the scan, everything from the write pointer onward is zero — and already is, thanks to the swaps. Demonstrates the "stable in-place partition" pattern. Complexity: O(n) time, O(1) space.

```python
def moveZeroes(nums):
    w = 0
    for r in range(len(nums)):
        if nums[r] != 0:
            nums[w], nums[r] = nums[r], nums[w]
            w += 1
```

### 17. Longest Consecutive Sequence *(LeetCode #128 · Medium)*
<https://leetcode.com/problems/longest-consecutive-sequence/>

Find the length of the longest run of consecutive integers in an unsorted array, in O(n). Sorting is O(n log n) and disqualified. The trick: dump everything in a hash set, then for each value `n` only start counting upward if `n-1` is **not** in the set — that guarantees you start at the bottom of each run, so each element is visited at most twice across the whole algorithm. The "skip non-starts" check is what makes the bound linear. Complexity: O(n) time, O(n) space.

```python
def longestConsecutive(nums):
    s = set(nums); best = 0
    for n in s:
        if n - 1 not in s:
            length = 1
            while n + length in s: length += 1
            best = max(best, length)
    return best
```

### 18. Encode and Decode Strings *(LeetCode #271 · Medium)*
<https://leetcode.com/problems/encode-and-decode-strings/>

Design `encode(list[str]) -> str` and `decode(str) -> list[str]` such that `decode(encode(x)) == x` for any list including arbitrary characters. The standard answer is length-prefixing: emit each string as `"<len>#<string>"`. To decode, read until `#` to learn the length, then slice exactly that many characters. Naive separators (commas, spaces) fail because the strings may contain them. This is a frequent system-design-flavored question for serialization. Complexity: O(n) time and space, where n is total characters.

```python
def encode(strs):
    return ''.join(f'{len(s)}#{s}' for s in strs)

def decode(s):
    out, i = [], 0
    while i < len(s):
        j = s.index('#', i)
        n = int(s[i:j])
        out.append(s[j+1:j+1+n])
        i = j + 1 + n
    return out
```

---

## Two Pointers & Sliding Window

### 19. 3Sum *(LeetCode #15 · Medium)*
<https://leetcode.com/problems/3sum/>

Find all unique triplets in an array that sum to zero. The O(n³) brute force is unacceptable; sort the array first, then for each index `i`, use two pointers (`l`, `r`) on the remaining suffix to find pairs that sum to `-nums[i]`. Skip duplicates at every level to avoid emitting the same triplet twice. Sorting plus the two-pointer scan gives O(n²). The duplicate-skipping is the part candidates most often get wrong. Complexity: O(n²) time, O(1) extra space (excluding output).

```python
def threeSum(nums):
    nums.sort(); out = []
    for i in range(len(nums) - 2):
        if i and nums[i] == nums[i-1]: continue
        l, r = i + 1, len(nums) - 1
        while l < r:
            s = nums[i] + nums[l] + nums[r]
            if s < 0: l += 1
            elif s > 0: r -= 1
            else:
                out.append([nums[i], nums[l], nums[r]])
                l += 1; r -= 1
                while l < r and nums[l] == nums[l-1]: l += 1
    return out
```

### 20. Container With Most Water *(LeetCode #11 · Medium)*
<https://leetcode.com/problems/container-with-most-water/>

Given heights, pick two lines that with the x-axis form a container holding the most water. Brute force tries every pair (O(n²)). Optimal: place pointers at both ends and always move the **shorter** line inward. Why this works — the area is bounded by the shorter side, so moving the taller side can only decrease the width without ever increasing the height; the only chance for improvement is to move the shorter side. Each step shrinks the window by one and computes a candidate area. Complexity: O(n) time, O(1) space.

```python
def maxArea(height):
    l, r, best = 0, len(height) - 1, 0
    while l < r:
        best = max(best, (r - l) * min(height[l], height[r]))
        if height[l] < height[r]: l += 1
        else: r -= 1
    return best
```

### 21. Trapping Rain Water *(LeetCode #42 · Hard)*
<https://leetcode.com/problems/trapping-rain-water/>

Given an elevation map, compute how much water it traps. The water above each bar equals `min(maxLeft, maxRight) - height[i]`. The two-pointer solution maintains `maxLeft` and `maxRight` as it walks inward: at each step, advance the side with the smaller running max, because that side's water level is fully determined (bounded by its own max). This avoids precomputing two prefix-max arrays. The cleverness is recognizing that the smaller side's bound cannot be raised by the unseen middle. Complexity: O(n) time, O(1) space.

```python
def trap(height):
    l, r, lmax, rmax, total = 0, len(height) - 1, 0, 0, 0
    while l < r:
        if height[l] < height[r]:
            lmax = max(lmax, height[l]); total += lmax - height[l]; l += 1
        else:
            rmax = max(rmax, height[r]); total += rmax - height[r]; r -= 1
    return total
```

### 22. Longest Substring Without Repeating Characters *(LeetCode #3 · Medium)*
<https://leetcode.com/problems/longest-substring-without-repeating-characters/>

Find the length of the longest substring with all unique characters. Slide a window: keep a map of character → last index seen. When you see a repeat that lies inside the current window, jump the left edge to one past that previous occurrence. Track the running best length. The "jump" step is what makes this strictly linear — naively shrinking by one would still be correct but slower. Pattern: variable-width sliding window with a hash map. Complexity: O(n) time, O(min(n, alphabet)) space.

```python
def lengthOfLongestSubstring(s):
    last, l, best = {}, 0, 0
    for r, c in enumerate(s):
        if c in last and last[c] >= l:
            l = last[c] + 1
        last[c] = r
        best = max(best, r - l + 1)
    return best
```

### 23. Longest Repeating Character Replacement *(LeetCode #424 · Medium)*
<https://leetcode.com/problems/longest-repeating-character-replacement/>

Given a string and an integer `k`, find the longest substring you can turn into all-one-character by replacing at most `k` characters. A window is valid iff `window_length - count_of_most_frequent_char <= k`. Slide right; whenever validity breaks, slide left until it's restored. A subtle optimization: you don't actually need to recompute the max-count when shrinking — keeping a slightly stale `max_count` still produces the correct answer length. Pattern: variable-width window with a frequency map. Complexity: O(n) time.

```python
from collections import Counter
def characterReplacement(s, k):
    cnt = Counter(); l = best = max_f = 0
    for r, c in enumerate(s):
        cnt[c] += 1
        max_f = max(max_f, cnt[c])
        while r - l + 1 - max_f > k:
            cnt[s[l]] -= 1; l += 1
        best = max(best, r - l + 1)
    return best
```

### 24. Minimum Window Substring *(LeetCode #76 · Hard)*
<https://leetcode.com/problems/minimum-window-substring/>

Find the smallest substring of `s` that contains every character of `t` (with multiplicity). Sliding window with two counters: required (from `t`) and current. Track how many *distinct* characters in `t` are currently satisfied. Expand right; once all are satisfied, contract from the left as much as possible while maintaining validity, recording the best window. Resume expanding. The "satisfied count" trick avoids comparing whole counters on every shrink. This is the canonical hard sliding-window problem. Complexity: O(n + m) time.

```python
from collections import Counter
def minWindow(s, t):
    if not t or not s: return ""
    need = Counter(t); have = Counter()
    needed, formed = len(need), 0
    l, best = 0, (float('inf'), 0, 0)
    for r, c in enumerate(s):
        have[c] += 1
        if c in need and have[c] == need[c]:
            formed += 1
        while formed == needed:
            if r - l + 1 < best[0]:
                best = (r - l + 1, l, r)
            have[s[l]] -= 1
            if s[l] in need and have[s[l]] < need[s[l]]:
                formed -= 1
            l += 1
    return "" if best[0] == float('inf') else s[best[1]:best[2]+1]
```

---

## Stack & Linked List

### 25. Min Stack *(LeetCode #155 · Medium)*
<https://leetcode.com/problems/min-stack/>

Design a stack that supports `push`, `pop`, `top`, and `getMin` — all in O(1). The trick: alongside each pushed value, also push the *current* minimum onto a parallel "min stack" (or store `(value, min_so_far)` tuples). Then `getMin` is just looking at the top of that auxiliary stack. The invariant is that the running min at every depth is preserved without scanning. A more space-efficient variant only pushes to the min stack when the new value is ≤ the current min, but the two-stack version is easier to get right under pressure. Complexity: O(1) for all operations.

```python
class MinStack:
    def __init__(self):
        self.s = []
    def push(self, x):
        m = x if not self.s else min(x, self.s[-1][1])
        self.s.append((x, m))
    def pop(self): self.s.pop()
    def top(self): return self.s[-1][0]
    def getMin(self): return self.s[-1][1]
```

### 26. Daily Temperatures *(LeetCode #739 · Medium)*
<https://leetcode.com/problems/daily-temperatures/>

For each day, return the number of days until a warmer temperature (or 0 if none). Brute force is O(n²). The monotonic-stack solution scans left-to-right, keeping a stack of indices whose answer is still pending. For each new day, while the new temperature exceeds the top of the stack, pop and fill in the answer (`current_idx - popped_idx`). Then push the new index. Each index is pushed and popped at most once, so the total work is linear. This is the canonical "next greater element" pattern. Complexity: O(n) time and space.

```python
def dailyTemperatures(t):
    out = [0] * len(t); stack = []
    for i, x in enumerate(t):
        while stack and t[stack[-1]] < x:
            j = stack.pop(); out[j] = i - j
        stack.append(i)
    return out
```

### 27. LRU Cache *(LeetCode #146 · Medium)*
<https://leetcode.com/problems/lru-cache/>

Design a fixed-capacity cache where both `get` and `put` are O(1) and the least-recently-used entry is evicted when full. The textbook design pairs a hash map with a doubly linked list: the map gives O(1) lookup, and the list tracks usage order with O(1) move-to-front and pop-tail operations. Python's `OrderedDict` is essentially this data structure exposed directly — `move_to_end` and `popitem(last=False)` give a minimal solution in ~10 lines. The hand-rolled doubly-linked-list version is what most interviewers ultimately want, but `OrderedDict` is the right answer for the "minimal" version. Complexity: O(1) per operation.

```python
from collections import OrderedDict
class LRUCache:
    def __init__(self, capacity):
        self.cap = capacity
        self.d = OrderedDict()
    def get(self, key):
        if key not in self.d: return -1
        self.d.move_to_end(key)
        return self.d[key]
    def put(self, key, value):
        if key in self.d: self.d.move_to_end(key)
        self.d[key] = value
        if len(self.d) > self.cap: self.d.popitem(last=False)
```

### 28. Merge k Sorted Lists *(LeetCode #23 · Hard)*
<https://leetcode.com/problems/merge-k-sorted-lists/>

Merge `k` sorted linked lists into one. Brute-forcing pairwise merges is O(N·k); the optimal O(N log k) approach uses a min-heap holding the current head of each list. Pop the smallest, append it to the output, and push its `next` if it exists. Python's `heapq` requires items be comparable — wrap each entry with a tiebreaker counter (or `(val, list_idx, node)`) because `ListNode` itself is not orderable. This generalizes the two-list merge from #3 and is a common system-design touchpoint (multi-shard sorted reads). Complexity: O(N log k).

```python
import heapq
def mergeKLists(lists):
    h = []
    for i, node in enumerate(lists):
        if node: heapq.heappush(h, (node.val, i, node))
    dummy = tail = ListNode()
    while h:
        v, i, node = heapq.heappop(h)
        tail.next = node; tail = node
        if node.next: heapq.heappush(h, (node.next.val, i, node.next))
    return dummy.next
```

### 29. Remove Nth Node From End of List *(LeetCode #19 · Medium)*
<https://leetcode.com/problems/remove-nth-node-from-end-of-list/>

Remove the nth-from-end node in a single pass. Use a dummy head and two pointers: advance `fast` n+1 steps ahead, then advance both together until `fast` falls off the end — `slow` now sits just before the node to delete. Splice it out by reassigning `slow.next`. The dummy head removes the special case of deleting the original head. The "n+1 gap" pattern shows up in many linked-list problems. Complexity: O(n) time, O(1) space.

```python
def removeNthFromEnd(head, n):
    dummy = ListNode(0, head)
    slow = fast = dummy
    for _ in range(n + 1): fast = fast.next
    while fast:
        slow, fast = slow.next, fast.next
    slow.next = slow.next.next
    return dummy.next
```

---

## Trees & Graphs

### 30. Invert Binary Tree *(LeetCode #226 · Easy)*
<https://leetcode.com/problems/invert-binary-tree/>

Mirror a binary tree by swapping every node's left and right children. Recursive solution: invert left subtree, invert right subtree, then swap them at the current node. Three lines if you swap inline. Iterative versions (BFS/DFS with a queue or stack) work the same way. Famous for the Max Howell tweet about Google rejecting him for not being able to whiteboard it; today it's the canonical "you should know basic recursion on trees" question. Complexity: O(n) time, O(h) recursion stack.

```python
def invertTree(root):
    if not root: return None
    root.left, root.right = invertTree(root.right), invertTree(root.left)
    return root
```

### 31. Maximum Depth of Binary Tree *(LeetCode #104 · Easy)*
<https://leetcode.com/problems/maximum-depth-of-binary-tree/>

Return the height (number of nodes on the longest root-to-leaf path) of a binary tree. The recursive one-liner says: an empty tree has depth 0; otherwise, depth is one plus the deeper of the two subtrees. This is the simplest possible introduction to recursion on trees and is a frequent warm-up before harder tree problems. The iterative BFS variant counts levels — useful when recursion depth is a concern. Complexity: O(n) time, O(h) space.

```python
def maxDepth(root):
    return 0 if not root else 1 + max(maxDepth(root.left), maxDepth(root.right))
```

### 32. Same Tree *(LeetCode #100 · Easy)*
<https://leetcode.com/problems/same-tree/>

Decide whether two binary trees are structurally identical with equal node values. Recursive: both null → equal; one null → unequal; otherwise compare values and recurse on both pairs of children. The compactness comes from short-circuit `and`. Same template covers "Symmetric Tree" (compare against a mirrored version) and "Subtree of Another Tree". Complexity: O(n) time, O(h) recursion.

```python
def isSameTree(p, q):
    if not p and not q: return True
    if not p or not q: return False
    return p.val == q.val and isSameTree(p.left, q.left) and isSameTree(p.right, q.right)
```

### 33. Binary Tree Level Order Traversal *(LeetCode #102 · Medium)*
<https://leetcode.com/problems/binary-tree-level-order-traversal/>

Return the values of a tree level by level. Standard BFS with a queue: at the start of each iteration, snapshot the current queue size — that's the number of nodes on this level — then process exactly that many, appending their children for the next round. The fixed-size loop is what cleanly separates levels. The same skeleton solves "Right Side View", "Average of Levels", "Zigzag Order Traversal", etc. Complexity: O(n) time and space.

```python
from collections import deque
def levelOrder(root):
    if not root: return []
    out, q = [], deque([root])
    while q:
        level = []
        for _ in range(len(q)):
            n = q.popleft(); level.append(n.val)
            if n.left: q.append(n.left)
            if n.right: q.append(n.right)
        out.append(level)
    return out
```

### 34. Validate Binary Search Tree *(LeetCode #98 · Medium)*
<https://leetcode.com/problems/validate-binary-search-tree/>

Verify that a tree is a valid BST: every node's value strictly greater than all values in its left subtree and less than all values in its right. The naive "check parent vs children" is wrong because BST validity is a *range* constraint over the whole subtree, not a local one. Pass `(low, high)` bounds down recursively, tightening them as you descend. Equivalently, an inorder traversal must produce a strictly increasing sequence. The bounds method is cleaner and shorter. Complexity: O(n) time, O(h) recursion.

```python
def isValidBST(root, lo=float('-inf'), hi=float('inf')):
    if not root: return True
    if not (lo < root.val < hi): return False
    return isValidBST(root.left, lo, root.val) and isValidBST(root.right, root.val, hi)
```

### 35. Lowest Common Ancestor of a BST *(LeetCode #235 · Medium)*
<https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree/>

Find the LCA of two nodes in a BST. The BST property makes this far easier than the general-tree case: the LCA is the first node whose value lies between `p` and `q` (inclusive). Walk down from the root; if both `p` and `q` are smaller, go left; if both larger, go right; otherwise the current node is the LCA — the search paths diverge here. Iterative is fine and saves stack space. Complexity: O(h) time, O(1) space.

```python
def lowestCommonAncestor(root, p, q):
    while root:
        if p.val < root.val and q.val < root.val: root = root.left
        elif p.val > root.val and q.val > root.val: root = root.right
        else: return root
```

### 36. Course Schedule *(LeetCode #207 · Medium)*
<https://leetcode.com/problems/course-schedule/>

Given prerequisite pairs, decide whether all courses can be finished — i.e., whether the prerequisite graph has a cycle. Build the directed graph and run a DFS that classifies nodes as unvisited / on-stack / done. If DFS encounters a node currently on its own recursion stack, there's a cycle and you return False. Equivalently, Kahn's algorithm (BFS topological sort): repeatedly remove indegree-zero nodes; if you don't remove all of them, a cycle exists. Either is acceptable; DFS coloring is a few lines shorter. Complexity: O(V + E).

```python
def canFinish(num, prereqs):
    graph = [[] for _ in range(num)]
    for a, b in prereqs: graph[b].append(a)
    state = [0] * num  # 0 unseen, 1 on stack, 2 done
    def dfs(u):
        if state[u] == 1: return False
        if state[u] == 2: return True
        state[u] = 1
        for v in graph[u]:
            if not dfs(v): return False
        state[u] = 2
        return True
    return all(dfs(i) for i in range(num))
```

### 37. Clone Graph *(LeetCode #133 · Medium)*
<https://leetcode.com/problems/clone-graph/>

Given a node in a connected undirected graph, return a deep copy of the whole graph. The challenge is cycles: you cannot blindly recurse or you'll loop forever. Maintain a `visited` map from original node → clone. On entering a node, create the clone (if it doesn't exist) and register it *before* recursing into neighbors — that way, when a cycle leads back to the same node, you return the already-created clone. Works as DFS or BFS; DFS is more compact. Complexity: O(V + E) time and space.

```python
def cloneGraph(node):
    if not node: return None
    seen = {}
    def dfs(n):
        if n in seen: return seen[n]
        copy = Node(n.val)
        seen[n] = copy
        copy.neighbors = [dfs(nb) for nb in n.neighbors]
        return copy
    return dfs(node)
```

---

## Binary Search & Sorting

### 38. Binary Search *(LeetCode #704 · Easy)*
<https://leetcode.com/problems/binary-search/>

Find a target in a sorted array, returning its index or -1. The trap is off-by-one: use `lo, hi = 0, len(nums) - 1` with the loop condition `lo <= hi` and update `lo = mid + 1` / `hi = mid - 1`. Compute `mid = (lo + hi) // 2`. Python's integer arithmetic avoids the overflow that bit-tricks address in C++/Java. This is the foundation for every "search on a sorted/monotone predicate" problem — including #39 below. Complexity: O(log n) time, O(1) space.

```python
def search(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target: return mid
        if nums[mid] < target: lo = mid + 1
        else: hi = mid - 1
    return -1
```

### 39. Search in Rotated Sorted Array *(LeetCode #33 · Medium)*
<https://leetcode.com/problems/search-in-rotated-sorted-array/>

A sorted array has been rotated at some unknown pivot; find a target in O(log n). The key observation: at every step of binary search, *at least one half* (left or right of `mid`) is still sorted. Determine which half is sorted by comparing `nums[lo]` to `nums[mid]`, then check whether the target lies inside that sorted half — if yes, recurse there; otherwise recurse on the other half. The case analysis is what makes this medium rather than easy. Complexity: O(log n).

```python
def search(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target: return mid
        if nums[lo] <= nums[mid]:
            if nums[lo] <= target < nums[mid]: hi = mid - 1
            else: lo = mid + 1
        else:
            if nums[mid] < target <= nums[hi]: lo = mid + 1
            else: hi = mid - 1
    return -1
```

### 40. Find Median from Data Stream *(LeetCode #295 · Hard)*
<https://leetcode.com/problems/find-median-from-data-stream/>

Support `addNum(x)` and `findMedian()` on a growing stream. Maintain two heaps: a max-heap for the lower half and a min-heap for the upper half. After each insert, balance so their sizes differ by at most 1. The median is the top of the larger heap, or the average of both tops when sizes are equal. Python's `heapq` is a min-heap, so the lower half pushes negated values. Each `addNum` is O(log n); `findMedian` is O(1). This is a foundational streaming-statistics question.

```python
import heapq
class MedianFinder:
    def __init__(self):
        self.lo, self.hi = [], []  # lo is max-heap (negated), hi is min-heap
    def addNum(self, x):
        heapq.heappush(self.lo, -heapq.heappushpop(self.hi, x))
        if len(self.lo) > len(self.hi):
            heapq.heappush(self.hi, -heapq.heappop(self.lo))
    def findMedian(self):
        if len(self.hi) > len(self.lo): return self.hi[0]
        return (self.hi[0] - self.lo[0]) / 2
```

---

## Dynamic Programming

### 41. House Robber *(LeetCode #198 · Medium)*
<https://leetcode.com/problems/house-robber/>

You can't rob two adjacent houses; maximize total loot. At each house you choose: skip it (carry forward yesterday's best) or rob it (yesterday-but-one's best plus today's value). The recurrence `dp[i] = max(dp[i-1], dp[i-2] + nums[i])` reduces to two rolling variables, so O(1) space. This is the second "first DP problem" after Climbing Stairs and is the basis for "House Robber II" (circular street) and the tree variant. Complexity: O(n) time, O(1) space.

```python
def rob(nums):
    prev2 = prev1 = 0
    for n in nums:
        prev2, prev1 = prev1, max(prev1, prev2 + n)
    return prev1
```

### 42. Coin Change *(LeetCode #322 · Medium)*
<https://leetcode.com/problems/coin-change/>

Find the fewest coins needed to make a given amount, or -1 if impossible. Bottom-up DP: `dp[a]` is the minimum coins for amount `a`, with `dp[0] = 0` and the rest initialized to infinity. For each amount, try every coin: `dp[a] = min(dp[a], dp[a-c] + 1)` whenever `a-c >= 0`. The unbounded-knapsack flavor (each coin reusable) is what distinguishes this from the 0/1 variants. Greedy doesn't work in general (e.g., coins `[1, 3, 4]` and amount `6`). Complexity: O(amount × len(coins)).

```python
def coinChange(coins, amount):
    dp = [float('inf')] * (amount + 1); dp[0] = 0
    for a in range(1, amount + 1):
        for c in coins:
            if c <= a: dp[a] = min(dp[a], dp[a - c] + 1)
    return dp[amount] if dp[amount] != float('inf') else -1
```

### 43. Longest Increasing Subsequence *(LeetCode #300 · Medium)*
<https://leetcode.com/problems/longest-increasing-subsequence/>

Find the length of the longest strictly increasing subsequence (not necessarily contiguous). The simple DP is O(n²): `dp[i]` is the LIS ending at `i`, computed by scanning all earlier `j` with `nums[j] < nums[i]`. The O(n log n) solution maintains a "tails" array where `tails[k]` is the smallest possible tail of an increasing subsequence of length k+1; for each new value, binary-search the position where it should replace (or extend). The length of `tails` at the end is the answer. The array isn't a real subsequence, but its length is correct. Complexity: O(n log n).

```python
from bisect import bisect_left
def lengthOfLIS(nums):
    tails = []
    for n in nums:
        i = bisect_left(tails, n)
        if i == len(tails): tails.append(n)
        else: tails[i] = n
    return len(tails)
```

### 44. Word Break *(LeetCode #139 · Medium)*
<https://leetcode.com/problems/word-break/>

Given a string and a dictionary, decide whether the string can be segmented into space-separated dictionary words. DP over prefixes: `dp[i]` is True iff `s[:i]` is segmentable. Base case `dp[0] = True`. For each `i`, look back at every earlier `j` where `dp[j]` is True and check whether `s[j:i]` is a dictionary word. Convert the word list to a set for O(1) lookups. The string-slicing variant is O(n³) in the worst case but plenty fast for typical constraints. Complexity: O(n² · w) where w is the average word length.

```python
def wordBreak(s, wordDict):
    words = set(wordDict)
    dp = [False] * (len(s) + 1); dp[0] = True
    for i in range(1, len(s) + 1):
        for j in range(i):
            if dp[j] and s[j:i] in words:
                dp[i] = True
                break
    return dp[-1]
```

---

## HackerRank Classics

### 45. Diagonal Difference *(HackerRank · Easy)*
<https://www.hackerrank.com/challenges/diagonal-difference/problem>

Given an n×n square matrix, return the absolute difference between the sums of its primary and secondary diagonals. Single pass over `i` from 0 to n-1: add `arr[i][i]` to one running sum and `arr[i][n-1-i]` to the other. The point of this exercise is index arithmetic on 2-D arrays, not algorithmic depth — it's HackerRank's "do you understand row/column indexing" question and shows up in nearly every onboarding-style screening. Complexity: O(n) time, O(1) space.

```python
def diagonalDifference(arr):
    n = len(arr)
    return abs(sum(arr[i][i] - arr[i][n - 1 - i] for i in range(n)))
```

### 46. Plus Minus *(HackerRank · Easy)*
<https://www.hackerrank.com/challenges/plus-minus/problem>

Given an array of integers, print the fractions of positive, negative, and zero values, each on its own line with 6 decimal places. Single pass to count by sign; divide each count by the total length. Trivial, but it's the canonical HackerRank "can you read input, count things, and format output" warm-up — the formatting requirement is the actual test. Use Python f-string formatting `f'{x:.6f}'`. Complexity: O(n) time, O(1) space.

```python
def plusMinus(arr):
    n = len(arr)
    pos = sum(1 for x in arr if x > 0)
    neg = sum(1 for x in arr if x < 0)
    zer = n - pos - neg
    print(f'{pos/n:.6f}\n{neg/n:.6f}\n{zer/n:.6f}')
```

### 47. Mini-Max Sum *(HackerRank · Easy)*
<https://www.hackerrank.com/challenges/mini-max-sum/problem>

Given five positive integers, print the smallest and largest sums obtainable by adding exactly four of the five values. The clever observation: the smallest 4-sum is `total - max`, and the largest is `total - min` — no need to actually choose subsets. One pass to compute total, min, and max; then print the two derived sums. The point is to recognize the "leave one out" structure rather than brute-force the C(5,4) = 5 subsets. Complexity: O(n) time, O(1) space.

```python
def miniMaxSum(arr):
    total = sum(arr)
    print(total - max(arr), total - min(arr))
```

### 48. Time Conversion *(HackerRank · Easy)*
<https://www.hackerrank.com/challenges/time-conversion/problem>

Convert a 12-hour AM/PM time string (e.g. `"07:05:45PM"`) to 24-hour format (e.g. `"19:05:45"`). The tricky cases are exactly two: `12:xx:xxAM` becomes `00:xx:xx`, and `12:xx:xxPM` stays at `12`. Otherwise, PM adds 12 to a non-12 hour, and AM leaves a non-12 hour alone. Splitting on the AM/PM suffix and treating the hour as an integer makes the case analysis crisp. This problem catches a lot of candidates who forget to handle midnight (`12 AM` → `00`) correctly. Complexity: O(1).

```python
def timeConversion(s):
    suf, hh = s[-2:], int(s[:2])
    if suf == 'AM' and hh == 12: hh = 0
    elif suf == 'PM' and hh != 12: hh += 12
    return f'{hh:02d}{s[2:8]}'
```

### 49. Sales by Match (Sock Merchant) *(HackerRank · Easy)*
<https://www.hackerrank.com/challenges/sock-merchant/problem>

Given an array of sock colors, count how many matching pairs exist. Count the occurrences of each color, then sum `count // 2` across all colors. The minimal Python answer uses `collections.Counter` and a generator expression. This is the pattern-recognition exercise: every time the question is "how many groups of k can I form from a multiset", the answer is `sum(c // k for c in Counter(items).values())`. Complexity: O(n) time, O(n) space.

```python
from collections import Counter
def sockMerchant(n, ar):
    return sum(c // 2 for c in Counter(ar).values())
```

### 50. Sparse Arrays *(HackerRank · Medium)*
<https://www.hackerrank.com/challenges/sparse-arrays/problem>

Given a list of input strings and a list of query strings, return — for each query — how many times it appears in the input list. Naive nested loop is O(n × q × L). Better: count the input list once with `Counter`, then look up each query in O(1) amortized. The minimal version is a single-line list comprehension over the queries. This is HackerRank's gentle introduction to "preprocess once, query many times" — a pattern that scales to inverted indexes and search engines. Complexity: O(n + q).

```python
from collections import Counter
def matchingStrings(strings, queries):
    c = Counter(strings)
    return [c[q] for q in queries]
```
