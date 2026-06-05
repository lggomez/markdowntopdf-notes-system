# JavaScript / TypeScript — Design patterns and DDD-oriented building blocks

Audience: senior developers using TypeScript (or typed JS) for **maintainable** designs—workshop exercises, small services, front-end domains, kata. Complements `javascript-typescript-algorithms-reference.md`, which covers algorithms and built-ins in isolation.

This is **not** a substitute for Eric Evans or Vaughn Vernon — it is a **practical TS/JS** map: language features + patterns that show up in DDD-style codebases.

---

## 1. How this differs from algorithmic / stdlib-only TypeScript

| Concern | Isolated algorithms (single function, minimal deps) | Design / DDD style |
| ------- | --------------------------------------------------- | ------------------ |
| Primary goal | Correctness + complexity on a bounded problem | Boundaries, invariants, evolution |
| State | Often ephemeral, one-off | Long-lived aggregates, persistence |
| Types | Often loose or local | Interfaces, branded types, explicit errors |
| Dependencies | Built-ins only | Injection, ports, adapters, modules |

---

## 2. Language features that replace ceremony

- **`interface` / `type`** — ports as explicit contracts; **`satisfies`** checks literals without widening (TS 4.9+).
- **Discriminated unions** — `kind: 'success' | 'failure'` + payload; ideal for **results** and **domain events**.
- **`readonly`** — shallow immutability on properties and arrays; pair with **frozen** patterns for value objects.
- **Branded types** — `type Money = number & { readonly __brand: unique symbol }` (or `declare const`) to avoid accidental numeric mixing.
- **`class` with `#private`** — encapsulation without closure tricks; or **closures** for tiny modules.
- **`Error` subclasses** — `class DomainError extends Error` with stable `name` for handlers.

---

## 3. Design baseline for TypeScript newcomers

- TypeScript types vanish at runtime: validate external input at the boundary before constructing domain objects.
- Use a **composition root** (server bootstrap, page shell, CLI entrypoint, test fixture) to create adapters and pass them into use cases.
- Keep domain modules framework-free: no `Request`, ORM entity, React hook, or SDK types in entities and value objects.
- Prefer discriminated unions for expected outcomes; reserve exceptions for invariant violations and unexpected infrastructure failures.
- Map persistence rows / API DTOs to domain objects explicitly. Do not let transport shapes become the domain model.

```typescript
type Result<T, E extends string> =
  | { ok: true; value: T }
  | { ok: false; error: E };

type OrderId = string & { readonly __brand: "OrderId" };

class DomainError extends Error {}
```

---

## 4. Creational patterns (quick recall)

**Factory function** — branch on config or transport; return a **narrowed interface** type.

```typescript
export function createPricingEngine(kind: "stripe" | "flat"): PricingEngine {
  switch (kind) {
    case "stripe":
      return new StripePricingEngine(...);
    case "flat":
      return new FlatPricingEngine(...);
  }
}
```

**Builder** — fluent APIs or **`withX` copy** methods for immutable aggregates in tests.

```typescript
type OrderDraft = {
  readonly customerId: string;
  readonly couponCode?: string;
  readonly gift: boolean;
};

const base: OrderDraft = { customerId: "cust_123", gift: false };
const withCoupon = { ...base, couponCode: "WELCOME10" } satisfies OrderDraft;
```

**Singleton** — avoid as global mutable; prefer **explicit composition root** (create once, pass down).

---

## 5. Structural patterns

### Adapter

Implement the **port** interface; delegate to SDK.

```typescript
type ChargeResult = { ok: boolean; providerId: string };

export interface PaymentGateway {
  charge(amountCents: number, idempotencyKey: string): Promise<ChargeResult>;
}

export class StripeAdapter implements PaymentGateway {
  constructor(private readonly client: StripeClient) {}

  async charge(amountCents: number, idempotencyKey: string): Promise<ChargeResult> {
    const response = await this.client.charges.create(
      { amount: amountCents },
      { idempotencyKey },
    );
    return { ok: response.status === "succeeded", providerId: response.id };
  }
}
```

### Decorator

Wrap `PaymentGateway` for retries, metrics, authorization, caching, or idempotency. Use a higher-order function or a class that implements the same interface.

```typescript
export class MeteredPaymentGateway implements PaymentGateway {
  constructor(
    private readonly wrapped: PaymentGateway,
    private readonly metrics: Metrics,
  ) {}

  async charge(amountCents: number, idempotencyKey: string): Promise<ChargeResult> {
    const result = await this.wrapped.charge(amountCents, idempotencyKey);
    this.metrics.increment("payment.charge", { ok: String(result.ok) });
    return result;
  }
}
```

### Facade

Expose a single entry to a subsystem; keep orchestration **thin** so domain rules stay in domain objects or domain services.

---

## 6. Behavioral patterns

### Strategy

Inject `PricingStrategy` **interface**; swap implementations per tenant, feature flag, or experiment.

```typescript
export interface PricingPolicy {
  apply(subtotal: Money): Money;
}

export class PercentageDiscount implements PricingPolicy {
  constructor(private readonly basisPoints: bigint) {}

  apply(subtotal: Money): Money {
    const discount = (subtotal.amount * this.basisPoints) / 10_000n;
    return Money.of(subtotal.amount - discount, subtotal.currency);
  }
}

export class NoDiscount implements PricingPolicy {
  apply(subtotal: Money): Money {
    return subtotal;
  }
}
```

### Observer / Pub-Sub

Use `EventTarget`, RxJS, simple callback lists, or an external event bus. **Domain event handlers** belong in **application** or **infrastructure**, not inside entities.

### Template Method

Abstract base classes are viable in TS; composition + strategy often stays flatter and easier to test.

### Command

Use `{ type: "PlaceOrder"; payload: ... }` plus a handler registry to model **CQRS** entrypoints.

---

## 7. DDD building blocks (TypeScript-flavored)

### 7.1 Value Object

- Equality by **value**; no surrogate id.
- Prefer **readonly** fields + methods that return **new** instances.
- JS object equality is by reference, so provide explicit `equals()` for value objects.

```typescript
class DomainError extends Error {}

export class Money {
  private constructor(
    readonly amount: bigint,
    readonly currency: string,
  ) {}

  static of(amount: bigint, currency: string): Money {
    return new Money(amount, currency);
  }

  add(other: Money): Money {
    if (other.currency !== this.currency) throw new DomainError("currency mismatch");
    return Money.of(this.amount + other.amount, this.currency);
  }

  equals(other: Money): boolean {
    return this.amount === other.amount && this.currency === other.currency;
  }
}
```

(`bigint` avoids float surprises for cents; **Decimal.js** etc. when rounding rules matter.)

### 7.2 Entity

- Stable **identity** (`id`); mutable **through methods** that enforce invariants.
- Expose read-only snapshots when callers need state; do not leak internal mutable arrays.

```typescript
type OrderLine = { sku: string; qty: number };

export class Order {
  constructor(readonly id: string, private lines: readonly OrderLine[]) {}

  addLine(line: OrderLine): void {
    if (line.qty <= 0) throw new DomainError("invalid qty");
    this.lines = [...this.lines, line];
  }

  getLines(): readonly OrderLine[] {
    return this.lines;
  }
}
```

### 7.3 Aggregate

- One **root** coordinates internal entities; external code holds references by **id**.
- One transactional change per aggregate **per use case** (rule of thumb).

### 7.4 Domain service

- Logic that involves **multiple** aggregates or no natural single owner (`TransferService`).

```typescript
export class InventoryReserver {
  reserve(inventory: Inventory, quantity: number): InventoryReservation {
    if (!this.canReserve(inventory, quantity)) {
      throw new DomainError("insufficient inventory");
    }
    return inventory.reserve(quantity);
  }

  private canReserve(inventory: Inventory, quantity: number): boolean {
    return inventory.availableUnits >= quantity;
  }
}
```

### 7.5 Repository (port)

```typescript
export interface OrderRepository {
  get(orderId: string): Promise<Order | null>;
  save(order: Order): Promise<void>;
}
```

Implementations live next to DB/HTTP; **domain** depends only on the **interface**.

### 7.6 Application service / use case

- Async boundaries natural in JS: **load → domain → persist → emit events**.
- Owns transaction boundaries, idempotency checks, and calls to external ports.

```typescript
export class OrderPlacer {
  constructor(
    private readonly orders: OrderRepository,
    private readonly events: EventPublisher,
  ) {}

  async place(orderId: string, line: OrderLine): Promise<void> {
    const order = new Order(orderId, []);
    order.addLine(line);
    await this.orders.save(order);
    await this.events.publish({
      type: "OrderPlaced",
      orderId,
      at: new Date().toISOString(),
    });
  }
}
```

### 7.7 Domain events

- Typed payloads; include occurred-at and correlation ids for integration.
- Publish after commit when handlers cause external side effects.

```typescript
type DomainEvent =
  | { type: "OrderPlaced"; orderId: string; at: string }
  | { type: "InventoryReserved"; sku: string; qty: number; at: string };

export interface EventPublisher {
  publish(event: DomainEvent): Promise<void>;
}
```

---

## 8. Layering (hexagonal / clean)

**Domain** → **Application** → **Infrastructure**

**Rule:** domain never imports **framework** types (`Request`, ORM entities). Map at the edge (**anti-corruption layer**).

```typescript
function orderFromRow(row: OrderRow): Order {
  const order = new Order(row.id, []);
  for (const line of row.lines) {
    order.addLine({ sku: line.sku, qty: line.qty });
  }
  return order;
}
```

---

## 9. CQRS sketch (read vs write)

- **Commands** mutate aggregates; **queries** read optimized projections.
- **Read models** can be plain DTOs, SQL views, or denormalized documents.

---

## 10. Testing implications

| Layer | Focus |
| ----- | ----- |
| Domain | pure functions / entities: invariants, VO operations |
| Application | use-case tests with **in-memory** repository fakes |
| Infrastructure | adapter integration tests where ROI is clear |

Prefer **fakes** over over-specified mocks; assert **outcomes**, not every internal call.

```typescript
export class InMemoryOrderRepository implements OrderRepository {
  private readonly orders = new Map<string, Order>();

  async get(orderId: string): Promise<Order | null> {
    return this.orders.get(orderId) ?? null;
  }

  async save(order: Order): Promise<void> {
    this.orders.set(order.id, order);
  }
}
```

---

## 11. Anti-patterns to flag in review

- **God hook** — single React hook or Express router with all domain rules.
- **DTO as domain** — API shapes leak everywhere without translation.
- **Primitive obsession** — `amount: number` dollars across layers without currency context.
- **Event spam** — noisy events with no consumer contract.
- **Distributed aggregate** — two roots “updated together” without a consistency story.
- **Type-only safety at the boundary** — trusting JSON because it is typed as `Foo`; validate first.
- **Anemic aggregate** — entity has public fields only, while use cases own every invariant.
- **Promise leakage in domain** — pure domain methods become `async` because infrastructure slipped inward.

---

## 12. Micro-kata ideas (solo practice)

1. **Money + FX** — branded amounts, single rounding policy, explicit conversion errors.
2. **Cart** — lines with qty > 0 invariant; emit `LineAdded` from application layer only.
3. **Reservation** — choose aggregate boundaries (`Inventory` vs `Booking`) and document tradeoffs.

---

## 13. Further reading (external)

- Evans — *Domain-Driven Design*; Vernon — *Implementing Domain-Driven Design*.
- TypeScript: **Handbook** (interfaces, generics, narrowing), **eslint** rules for promise safety.

---

Pairing: use **`javascript-typescript-algorithms-reference.md`** for algorithms and API recall; use **this file** when the problem is **modeling, boundaries, and testable structure**.
