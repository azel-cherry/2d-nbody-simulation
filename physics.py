from utils import Vect2


class Body:
    def __init__(self, mass: float, p0: Vect2, v0: Vect2):
        self.mass = mass
        self.pos = p0
        self.vel = v0
        self._acc = Vect2(0, 0)
        self._stored_acc = Vect2(0, 0)

    @property
    def acc(self) -> Vect2:
        return self._stored_acc

    def apply_force(self, force: Vect2):
        self._acc += force / self.mass

    def step(self, dt: float):
        self._stored_acc = self._acc
        self.vel += self._acc * dt
        self.pos += self.vel * dt
        self._acc = Vect2(0, 0)

    def __str__(self) -> str:
        return f"m: {self.mass}\nv: {self.vel}\na: {self._acc}"


class Space:
    def __init__(self, G: float = 6.67e-11):
        self.bodies: list[Body] = []
        self._G = G

    def add_body(self, body: Body):
        self.bodies.append(body)

    def _body_dist(self, b1: Body, b2: Body) -> float:
        return abs((b1.pos - b2.pos).mag())

    def _get_force(self, b1: Body, b2: Body) -> Vect2:
        return self._G * b1.mass * b2.mass * (b2.pos - b1.pos) / self._body_dist(
            b1, b2)**3

    def step(self, dt: float):
        for i, b1 in enumerate(self.bodies):
            for j, b2 in enumerate(self.bodies):
                if i != j:
                    f = self._get_force(b1, b2)
                    b1.apply_force(f)

        for b in self.bodies:
            b.step(dt)

    def mass_center(self) -> Vect2:
        num = Vect2(0, 0)
        den = 0
        for b in self.bodies:
            num += b.mass * b.pos
            den += b.mass
        return num / den
