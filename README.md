# 2D N-Body Simulation

Real-time 2D simulation of gravitational interactions between multiple celestial bodies using Pygame.


## How to Run

1. Make sure Pyhton is installed. Newer versions might not work with `pygame`. This was tested using Python 3.10.

2. **Install all dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Run the main script:**

    ```bash
    python main.py
    ```

The simulation window will open, showing the bodies in motion.


## Controls

### Time control keybinds

- **SPACE**: Pause/unpause simulation

While paused:
- **RIGHT (hold)**: Advance time forward
- **LEFT (hold)**: Rewind time backward
- **SHIFT + LEFT/RIGHT**: Faster rewind/fast-forward

While running:
- **R**: Reverse time direction


### Camera keybinds

- **0**: Follow origin coordinates (default)
- **C**: Follow center of mass
- **B**: Follow individual bodies

While following bodies:
- **UP**: Select next body to follow
- **DOWN**: Select previous body to follow


### Other keybinds

- **V**: Toggle display of velocity and acceleration vectors
- **H**: Show/hide control guide
- **ESC**: Exit the simulation


## Customizing the Simulation

In `main.py`, the `Simulation` constructor takes:

```python
Simulation(space, space_size, screen_size, seconds_per_second)
```

- `space`: Space object containing bodies
- `space_size`: Scaling of the physical simulation space
- `screen_size`: Tuple for simulation window dimensions
- `seconds_per_second`: Time scaling factor

Each body is added with:

```python
space.add_body(Body(mass, Vect2(x, y), Vect2(vx, vy)))
```

- `mass`: Mass of the body
- `Vect2(x, y)`: Initial position
- `Vect2(vx, vy)`: Initial velocity

Example bodies are already set up.


## File Structure

- `main.py`: Sets up bodies and starts simulation
- `physics.py`: Body and Space classes, gravitational calculations
- `simulation.py`: Pygame rendering and user interaction
- `utils.py`: Utility classes like Vect2, colors, and helper functions
