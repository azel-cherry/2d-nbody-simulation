from physics import Space, Body
from simulation import Simulation
from utils import Vect2


if __name__ == "__main__":

    space = Space()

    space.add_body(Body(3.0e28, Vect2(1.0e10, 0.0e00), Vect2(0.0e00, -1.4e04)))
    space.add_body(Body(3.0e28, Vect2(-3.5e10, 0.0e00), Vect2(0.0e00, 1.4e03)))
    space.add_body(Body(3.0e28, Vect2(-1.0e10, 0.0e00), Vect2(0.0e00, 1.4e04)))
    space.add_body(Body(3.0e28, Vect2(3.5e10, 0.0e00), Vect2(0.0e00, -1.4e03)))
    space.add_body(Body(3.0e20, Vect2(5.0e09, 0.0e00), Vect2(0.0e00, -1.0e02)))
    space.add_body(Body(3.0e20, Vect2(-5.0e09, 0.0e00), Vect2(0.0e00, 1.0e02)))

    sim = Simulation(space, 1.0e11, (1000, 700), 1e6)
    sim.start_sim()
