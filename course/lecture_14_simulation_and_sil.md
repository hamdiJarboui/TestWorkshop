# Simulation, closed-loop testing and acceptance criteria

## 14.1 Why a closed loop changes everything

An **open-loop** test calls the controller with a number and checks the number it returns: *"with error 10 km/h the throttle request is 0.51."* But a controller is only correct **in a loop**: the throttle matters because of what the *vehicle does with it*, which changes the next error, which changes the next throttle. Overshoot, oscillation and instability exist only in the loop.

```
 reference ──►(+)── error ──► CONTROLLER ── throttle ──► VEHICLE (plant) ──┐
              ▲−                (our code)                                  │ speed
              └───────────────────── sensor ◄───────────────────────────────┘
```

**Software-in-the-loop (SIL)** runs the *production controller code* against a **plant model** on a PC. It is the first place the behaviour of the whole loop can be tested — and, being fast and deterministic, it can run thousands of scenarios in CI.

## 14.2 The plant model

A longitudinal vehicle model comes straight from Newton's second law:

```
m · dv/dt  =  F_drive − F_drag − F_rolling − F_grade − F_brake
              F_drag = ½ρ·Cd·A·v²       F_rolling = Crr·m·g       F_grade = m·g·sin(θ)
```

To simulate it on a computer we **discretise time** with a fixed step `dt` (explicit Euler): `v ← v + a·dt`. Our `Vehicle.step` does exactly this. Four principles for the model itself:

1. **Keep it as simple as the question allows** — a point mass is enough to judge a cruise controller.
2. **Test the model first.** If coasting does not slow the car or the top speed is 400 km/h, every downstream result is meaningless. Plant sanity tests are real tests.
3. **State its validity range.** Drag/rolling/grade is not a model of hydroplaning.
4. **Pin the time step** so runs are deterministic and repeatable.

```python
# verified: python
from autotest.vehicle import Vehicle

coasting = Vehicle(speed_ms=30)
for _ in range(600):                      # 60 s without throttle
    coasting.step(0.0, 0.1)
assert 0 < coasting.speed_ms < 30         # sanity 1: it slows down but does not stop or reverse

full = Vehicle()
for _ in range(20000):
    full.step(1.0, 0.1)
assert 200 < full.speed_kmh < 300         # sanity 2: top speed set by drag balance, a believable number
print(f"top speed {full.speed_kmh:.0f} km/h")
```

## 14.3 Control performance: the vocabulary of a step response

When the set speed jumps from 80 to 100 km/h the speed *response* is judged by:

```
speed
 ▲            ┌─ overshoot ─┐
 │        ____╱‾‾‾╲___ ← peak
100├──────╱──────────╲‾‾‾‾‾‾‾‾‾  ← settles within a band (e.g. ±1 km/h)
 │    ╱                             steady-state error = target − final value
 │  ╱
80┼─┴───────────────────────────► time
   ↑ rise time           ↑ settling time
```

| Metric | Definition | Acceptance criterion used in Lab 11 |
|---|---|---|
| **Overshoot** | (peak − target) / step size | < 20 % (under 4 km/h on a 20 km/h step) |
| **Settling time** | last time outside the band | < 25 s to ±1 km/h |
| **Steady-state error** | target − final speed | < 0.1 km/h (integral action) |
| **Disturbance rejection** | dip when a 5 % hill starts, and recovery | dip < 4 km/h, recovers |

**Acceptance criteria are requirements written as numbers.** "Should feel smooth" cannot be tested; "overshoot < 4 km/h" can.

```python
# verified: python
from autotest.cruise import CruiseController
from autotest.vehicle import run_cruise

cc = CruiseController()
cc.power_on(); cc.set(100)
trace = run_cruise(cc, start_kmh=80, duration_s=120)          # list of (t, speed_kmh, throttle)

peak = max(v for _, v, _ in trace)
overshoot_pct = (peak - 100) / (100 - 80) * 100
settled_at = max(t for t, v, _ in trace if abs(v - 100) > 1.0)
final_error = abs(trace[-1][1] - 100)
print(f"overshoot {overshoot_pct:.0f} %   settles after {settled_at:.1f} s   final error {final_error:.3f} km/h")

assert overshoot_pct < 20 and settled_at < 25 and final_error < 0.1
assert all(0.0 <= u <= 1.0 for _, _, u in trace)               # the actuator command stays physical
```

## 14.4 Scenario testing and disturbances

A single step response is not enough. Build a **scenario catalogue**:

* different set speeds (40, 70, 100, 130, 160 km/h) — a *sweep*;
* disturbances: hills starting and ending, headwind;
* events inside the loop: **brake pressed** at t = 30 s; **cancel then resume**;
* degraded conditions: sensor bias, noise, delay.

Events are injected *into the simulated loop* by time, exactly like a test engineer would at a HIL bench:

```python
# verified: python
from autotest.cruise import CruiseController, CruiseState
from autotest.vehicle import run_cruise

cc = CruiseController()
cc.power_on(); cc.set(100)
trace = run_cruise(cc, 100, 40, events={30.0: lambda controller, car: controller.brake()})
assert cc.state is CruiseState.STANDBY
assert all(u == 0.0 for t, _, u in trace if t > 30)            # after braking: no throttle at all
```

## 14.5 A tuning requirement can fail

Lab 11 asks for an 8 % hill with a dip of at most 4 km/h. With the default gains (Kp = 0.05, Ki = 0.01) the car dips **5.4 km/h** — the *requirement* exposes weak tuning. Raising the gains (e.g. Kp = 0.15, Ki = 0.02) gives a 2.5 km/h dip. Closed-loop tests make such trade-offs concrete: a higher gain rejects disturbances better but reacts more aggressively to sensor noise.

## 14.6 ABS: testing against a physical phenomenon

The ABS plant is a **quarter-car**: one wheel carrying a quarter of the vehicle mass, with tyre force given by a friction curve that **peaks at about 20 % slip**. The control group is crucial:

* *With* ABS, slip stays near the peak: no lock-up while the car is fast, and a shorter stopping distance.
* *Without* ABS, the wheel locks and the distance is longer.

A good test asserts **both** and keeps the baseline: if "no ABS" did not actually lock the wheel, then "ABS prevents locking" would prove nothing.

```python
# verified: python
from autotest.abs import simulate_braking

with_abs, without = simulate_braking(True), simulate_braking(False)
print(f"stopping distance: with ABS {with_abs['distance_m']:.1f} m, locked wheel {without['distance_m']:.1f} m")
assert without["locked_s"] > 1.0                               # baseline: braking without ABS locks the wheel
assert with_abs["locked_s"] == 0.0 and with_abs["peak_slip"] < 0.35
assert with_abs["distance_m"] < 0.9 * without["distance_m"]    # at least 10 % shorter
```

## 14.7 Numerical sensitivity: do not over-specify

Simulation results depend on the **time step**. Repeating the ABS stop with different `dt`:

```python
# verified: python
from autotest.abs import simulate_braking

for dt in (0.0005, 0.001, 0.005, 0.01):
    a = simulate_braking(True, dt=dt)["distance_m"]
    b = simulate_braking(False, dt=dt)["distance_m"]
    print(f"dt={dt:<7} ABS {a:5.1f} m   no ABS {b:5.1f} m   improvement {100 * (1 - a / b):4.1f} %")
    assert a < 0.9 * b                      # the REQUIREMENT holds at every step size...
```

The ABS distance varies by several metres between step sizes (the controller and plant interact with the sampling interval), while the **relative** criterion — "at least 10 % shorter" — holds throughout. Two lessons: **pin `dt` in tests** (determinism), and **prefer acceptance criteria that are robust to modelling details** over exact numbers that merely freeze one run.

## 14.8 Limits of simulation

Passing in SIL does not mean the real vehicle passes. Ask:

* Which **model assumptions** could be wrong (tyre curve, mass, sensor delay, actuator dynamics)?
* Which effects are **absent** (quantisation, CAN latency, ECU scheduling)?
* Which scenarios are **missing** (cut-in vehicle, sensor dropout mid-brake)?

That is why the pyramid continues upward (PIL, HIL, vehicle) and why the **same scenarios** are re-run on each stage. Real programmes also use **co-simulation** (the FMI standard lets tools exchange models), **back-to-back tests** (model vs. generated code must agree within tolerance), and **scenario databases** with parameter sweeps and randomised variation.

## Check your understanding

1. Why can't an open-loop unit test of the controller find integrator windup problems?
2. Your acceptance criterion is "overshoot < 5 %". Is it measurable? Rewrite it as one with explicit definitions.
3. Why must the *no-ABS* baseline stay in the test suite?
4. Why is `assert stopping_distance == 44.77` a poor ABS requirement?

<!--ANSWERS-->
1. Windup shows up as a consequence over *time* — after long saturation the speed overshoots badly. A single call returns just one number; only a loop with a plant reveals the accumulated effect.
2. Not as stated (overshoot of what?). For example: "after a 20 km/h set-speed step at constant speed on a flat road, the peak speed shall not exceed the new target by more than 20 % of the step (4 km/h)".
3. It proves the scenario is hazardous (the wheel really locks without ABS), so the ABS result is meaningful rather than vacuous.
4. The exact distance depends on the model, step size and tuning; it freezes one run. A relative criterion (≥ 10 % shorter than locked-wheel braking) captures the intent and survives modelling changes.
