# Python 3 — Design patterns and DDD-oriented building blocks

Audience: senior developers using Python for **maintainable** designs (workshop exercises, small services, kata). Complements `python3-algorithms-stdlib-reference.md`, which covers algorithms and the standard library in isolation.

This is **not** a substitute for Eric Evans or Vaughn Vernon — it is a **practical Python** map: language features + patterns that show up in DDD-style codebases.

---

## 1. How this differs from algorithmic / stdlib-only Python

| Concern | Isolated algorithms (single function, stdlib) | Design / DDD style |
| ------- | -------------------------------------------- | ------------------ |
| Primary goal | Correctness + complexity on a bounded problem | Boundaries, invariants, evolution |
| State | Often ephemeral, one-off | Long-lived aggregates, persistence |
| Types | Often minimal | Protocols, dataclasses, explicit errors |
| Dependencies | Standard library only | Injection, ports, adapters |

---

## 2. Python features that replace ceremony

- **`dataclasses`** — value-like objects with `frozen=True`, `slots=True` (3.10+) for immutability and memory.
- **`typing.Protocol`** — structural subtyping (duck typing with intent); ideal for **ports**.
- **`enum.Enum` / `IntEnum`** — finite domain states (order status, role).
- **`ABC` + `@abstractmethod`** — when you want **nominal** contracts (stricter than Protocol).
- **Exception types** — model domain failures (`InsufficientStock`, `CouponExpired`) instead of booleans.

---

## 3. Design baseline for Python newcomers

- Keep domain objects **framework-free**: no ORM models, HTTP requests, serializers, or task queue types inside entities and value objects.
- Put dependency creation in a **composition root** (CLI entrypoint, web app bootstrap, test fixture). Pass dependencies in; avoid global singletons.
- Use `Protocol` for ports when you want structural typing; use `ABC` only when inheritance identity matters.
- Prefer explicit domain exceptions for invariant failures; translate them to HTTP/UI/CLI errors at the boundary.
- Keep persistence mapping separate: ORM row → domain object → ORM row. Do not let lazy-loaded ORM behavior become domain behavior.

```python
class DomainException(Exception):
    pass


class CurrencyMismatchException(DomainException):
    pass
```

---

## 4. Creational patterns (quick recall)

**Factory function** — prefer a module-level function over a class when the constructor would branch on string types.

```python
class UnknownPricingEngineException(Exception):
    pass


def create_pricing_engine(kind: str) -> PricingEngine:
    if kind == "stripe":
        return StripePricingEngine(...)
    if kind == "flat":
        return FlatPricingEngine(...)
    raise UnknownPricingEngineException()
```

**Builder** — useful when construction has many optional steps (e.g. test fixtures, complex DTOs). In Python, often a **dataclass with defaults** + `replace()` suffices.

```python
from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class OrderDraft:
    customer_id: str
    coupon_code: str | None = None
    gift: bool = False


base = OrderDraft(customer_id="cust_123")
with_coupon = replace(base, coupon_code="WELCOME10")
```

**Singleton** — usually an antipattern; prefer **explicit app container** or module-level **factory** with clear lifecycle.

---

## 5. Structural patterns

### Adapter

Wrap foreign APIs to your port.

```python
from typing import Protocol


class PaymentGateway(Protocol):
    def charge(self, amount_cents: int, idempotency_key: str) -> ChargeResult:
        pass


class StripeAdapter:
    def __init__(self, client: StripeClient) -> None:
        self.__client = client

    def charge(self, amount_cents: int, idempotency_key: str) -> ChargeResult:
        response = self.__client.charges.create(..., idempotency_key=idempotency_key)
        return ChargeResult(ok=response.status == "succeeded", ...)
```

### Decorator

Wrap a port for metrics, logging, retries, authorization, or idempotency. In Python this is often a wrapper class or higher-order function over a `Protocol`.

```python
class MeteredPaymentGateway:
    def __init__(self, wrapped: PaymentGateway, metrics: Metrics) -> None:
        self.__wrapped = wrapped
        self.__metrics = metrics

    def charge(self, amount_cents: int, idempotency_key: str) -> ChargeResult:
        result = self.__wrapped.charge(
            amount_cents=amount_cents,
            idempotency_key=idempotency_key,
        )
        self.__metrics.increment("payment.charge", tags={"ok": result.ok})
        return result
```

### Facade

Expose a single entry to a subsystem; keep it thin so domain rules stay in the domain layer.

---

## 6. Behavioral patterns

### Strategy

Interchangeable algorithms behind one interface (`Protocol`). Classic for pricing, validation pipelines.

```python
from decimal import Decimal
from typing import Protocol


class PricingPolicy(Protocol):
    def apply(self, subtotal: Money) -> Money:
        pass


class PercentageDiscount:
    def __init__(self, percent: Decimal) -> None:
        self.__percent = percent

    def apply(self, subtotal: Money) -> Money:
        discount = subtotal.amount * self.__percent
        return Money(amount=subtotal.amount - discount, currency=subtotal.currency)


class NoDiscount:
    def apply(self, subtotal: Money) -> Money:
        return subtotal
```

### Observer / Pub-Sub

Use `asyncio` queues, simple in-process event lists, or an external bus. For **domain events**, keep handlers **application** or **infrastructure** — not inside entities.

### Template Method

A base class defines the skeleton and subclasses override hooks. In Python, composition + `Protocol` often stays flatter than inheritance.

### Command

Encapsulate an action as an object; pairs naturally with **CQRS**-style handlers (`handle(cmd) -> events`).

---

## 7. DDD building blocks (Python-flavored)

### 7.1 Value Object

- Defined by **attributes**, not identity.
- **Immutable** (`frozen=True`).
- Equality by value; safe to use as `dict` keys if hashable.

```python
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


class CurrencyMismatchException(Exception):
    pass


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str

    def add(self, other: Money) -> Money:
        if other.currency != self.currency:
            raise CurrencyMismatchException()
        return Money(amount=self.amount + other.amount, currency=self.currency)
```

### 7.2 Entity

- Has **identity** (id) even if attributes change.
- Mutations should preserve **invariants** inside methods (`raise` on violation).

```python
from dataclasses import dataclass


class InvalidOrderLineException(Exception):
    pass


@dataclass(slots=True)
class OrderLine:
    sku: str
    qty: int

class Order:
    def __init__(self, order_id: str) -> None:
        self.id = order_id
        self._lines: list[OrderLine] = []

    def add_line(self, line: OrderLine) -> None:
        if line.qty <= 0:
            raise InvalidOrderLineException()
        self._lines.append(line)

    def lines(self) -> tuple[OrderLine, ...]:
        return tuple(self._lines)
```

Expose read-only snapshots when callers need state; avoid returning internal mutable lists directly.

### 7.3 Aggregate

- **Cluster** of entities + value objects with one **aggregate root**.
- External references **by id** only; invariants enforced **within** the aggregate boundary.
- One transaction modifies **one** aggregate at a time (rule of thumb).

### 7.4 Domain service

- Stateless operation that doesn’t belong on a single entity (e.g. `TransferService` coordinating two accounts).

```python
class InventoryReserver:
    def reserve(self, inventory: Inventory, quantity: int) -> InventoryReservation:
        if self.can_reserve(inventory=inventory, quantity=quantity) is False:
            raise InsufficientInventoryException()
        return inventory.reserve(quantity=quantity)

    def can_reserve(self, inventory: Inventory, quantity: int) -> bool:
        return inventory.available_units >= quantity
```

### 7.5 Repository (port)

- **Interface** in domain/application; **implementation** in infrastructure.
- Returns domain objects; hides persistence details.

```python
from typing import Protocol


class OrderRepository(Protocol):
    def get(self, order_id: str) -> Order | None:
        pass

    def save(self, order: Order) -> None:
        pass
```

### 7.6 Application service / use case

- Orchestrates: load aggregates → domain calls → persist → publish events.
- **No** business rules that belong inside entities (watch for “anemic domain”).
- Owns transaction boundaries, idempotency checks, and calls to external ports.

```python
class OrderPlacer:
    def __init__(self, orders: OrderRepository, events: EventPublisher) -> None:
        self.__orders = orders
        self.__events = events

    def place(self, order_id: str, line: OrderLine) -> None:
        order = Order(order_id=order_id)
        order.add_line(line=line)
        self.__orders.save(order=order)
        self.__events.publish(OrderPlaced(order_id=order.id))
```

### 7.7 Domain events

- Past-tense facts (`OrderPlaced`, `InventoryReserved`).
- Carry minimal payload + identifiers; avoid giant graphs.
- Publish after commit when handlers cause external side effects.

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class OrderPlaced:
    order_id: str
    occurred_at: datetime


class EventPublisher(Protocol):
    def publish(self, event: OrderPlaced) -> None:
        pass
```

---

## 8. Layering (hexagonal / clean)

Typical dependency direction:

**Domain** (entities, VOs, domain services, domain events)  
← **Application** (use cases, transaction boundaries)  
← **Infrastructure** (DB, HTTP, message bus)

**Rule:** inner layers **never** import ORM models or framework types. Outer layers implement **ports** (`Protocol`).

```python
def order_from_row(row: OrderRow) -> Order:
    order = Order(order_id=row.id)
    for line in row.lines:
        order.add_line(line=OrderLine(sku=line.sku, qty=line.qty))
    return order
```

---

## 9. CQRS sketch (read vs write)

- **Write path**: aggregates + transactional consistency.
- **Read path**: denormalized **projections** / query models — optimized for UI or reports; updated by events or after commit.

In small Python services, “CQRS light” = separate **query functions** using SQL/views, not a second event store.

---

## 10. Testing implications

| Layer | Focus |
| ----- | ----- |
| Domain | pure unit tests: invariants, VO math, aggregate behavior |
| Application | use-case tests with **in-memory** fakes implementing ports |
| Infrastructure | adapter contract tests (optional), integration tests with real DB |

**Fake vs Mock**: prefer **fakes** (working in-memory repo) over brittle mock assertions on call order.

```python
class InMemoryOrderRepository:
    def __init__(self) -> None:
        self.__orders: dict[str, Order] = {}

    def get(self, order_id: str) -> Order | None:
        return self.__orders.get(order_id)

    def save(self, order: Order) -> None:
        self.__orders[order.id] = order
```

---

## 11. Anti-patterns to flag in review

- **God service** — 500-line “application service” with all rules.
- **ORM models as domain** — Active Record leaking everywhere.
- **Primitives obsession** — `str` money amounts across layers.
- **Event explosion** — one event per field change with no consumer story.
- **Distributed aggregate** — two roots updated in one “logical” operation without a clear consistency story.
- **Framework exception leakage** — domain raises HTTP/ORM/framework exceptions instead of domain-specific failures.
- **Anemic aggregate** — entity has fields only, while application service owns every invariant.

---

## 12. Micro-kata ideas (solo practice)

1. **Money + FX** — VOs, rounding policy in **one** place; invalid combinations raise domain errors.
2. **Cart** — add/remove lines; **invariant**: quantity > 0; publish `LineAdded` events from application layer.
3. **Reservation** — two aggregates (`Inventory`, `Booking`); enforce “no double book” via domain service or single aggregate boundary (discuss tradeoffs).

---

## 13. Further reading (external)

- Evans — *Domain-Driven Design* (strategic + tactical patterns).
- Vernon — *Implementing Domain-Driven Design* (aggregates, context maps).
- Python-specific: PEP 544 (`Protocol`), dataclasses docs, `collections.abc`.

---

Pairing: use **`python3-algorithms-stdlib-reference.md`** for algorithms and library recall; use **this file** when the problem is **modeling, boundaries, and testable structure**.
