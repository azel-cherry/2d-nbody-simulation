import pygame.draw
import pygame.gfxdraw
import numpy as np
import colorsys
import time
from enum import Enum, auto

from utils import Vect2, Color, palette, lerp
from physics import Space, Body

p = palette


class FollowMode(Enum):
    CenterOfMass = auto()
    ZeroZero = auto()
    Body = auto()


class Simulation:
    def __init__(self,
                 space: Space,
                 space_size: float,
                 screen_size: tuple[int, int],
                 seconds_per_second: float = 1.0):
        self._space = space
        self._space_size = space_size
        self._screen_size = screen_size
        self._seconds_per_second = seconds_per_second

        self._colors: list[Color] = [  # type: ignore
            tuple(map(lambda x: int(x * 255), colorsys.hsv_to_rgb(x, 0.5, 0.8)))
            for x in np.linspace(0, 1, len(self._space.bodies), endpoint=False)
        ]

        self._t = 0.0
        self._time_dir = 1
        self._sub_steps: int = 50

        self._paused = False

        self._space_center = Vect2(0, 0)
        self._follow_mode = FollowMode.ZeroZero
        self._follow_body_index = 0

        self._show_vectors = False
        self._show_help = False

        self._traces: list[list[Vect2]] = []
        self._last_trace_update = 0
        self._trace_dt = 0.02
        self._max_trace_t = 1.5
        self._trace_len = int(self._max_trace_t / self._trace_dt)

        if not pygame.get_init():
            pygame.init()

        self._screen = pygame.display.set_mode(self._screen_size,
                                               flags=pygame.SCALED,
                                               vsync=0)
        self._font = pygame.font.SysFont(None, 24)

    @classmethod
    def from_file(cls, file_path: str, screen_size: tuple,
                  sps: float) -> "Simulation":
        space = Space()
        with open(file_path, "r") as f:
            num_bodies = int(f.readline())
            space_size = float(f.readline())
            for i in range(num_bodies):
                x, y, vx, vy, m = map(float, f.readline().strip().split())
                space.add_body(Body(m, Vect2(x, y), Vect2(vx, vy)))
            sim = Simulation(space, space_size, screen_size, sps)
        return sim

    @staticmethod
    def _mix_colors(c1: Color, c2: Color, t: float) -> Color:
        return (int(c1[0] + (c2[0] - c1[0]) * t), int(c1[1] + (c2[1] - c1[1]) * t),
                int(c1[2] + (c2[2] - c1[2]) * t))

    @staticmethod
    def _scale_vec(v: Vect2) -> Vect2:
        mag = v.mag()
        if mag == 0:
            return v
        else:
            return (v / mag) * (mag**0.6)

    @staticmethod
    def _draw_arrow(screen: pygame.Surface,
                    color: Color,
                    start: Vect2,
                    end: Vect2,
                    fill: bool = True,
                    extend: bool = False,
                    tip_size: float = 5.0):
        delta = end - start
        if delta.mag() < 1e-5:
            return

        dir = delta.normalized()
        s = tip_size
        if not extend:
            end -= dir * s
        pygame.draw.aaline(screen, color, start.to_tuple(), end.to_tuple())
        end += dir * s
        verts = [
            end.to_tuple(),
            (end - (dir * s) + (dir.perp() * s / 2)).to_tuple(),
            (end - (dir * s) - (dir.perp() * s / 2)).to_tuple(),
        ]
        pygame.gfxdraw.aapolygon(screen, verts, color)
        if fill:
            pygame.gfxdraw.filled_polygon(screen, verts, color)

    def _m_to_pix2D(self, v: Vect2) -> Vect2:
        v = v - self._space_center
        vx = v.x * self._screen_size[0] / self._space_size + self._screen_size[
            0] / 2
        vy = v.y * self._screen_size[1] / self._space_size + self._screen_size[
            1] / 2
        return Vect2(vx, vy)

    def _format_time(self, t: float) -> str:
        out = ""
        if t < 0:
            t = -t
            out += "-"

        n_years = int(t / 31536000)
        n_days = int(t / 86400) % 365
        n_hours = int(t / 3600) % 24
        n_minutes = int(t / 60) % 60
        n_seconds = int(t) % 60

        if n_years > 0:
            out += f"{n_years} "
            out += "year " if n_years == 1 else "years "
        if n_days > 0 or n_years > 0:
            out += f"{n_days} "
            out += "day " if n_days == 1 else "days "
        out += f"{n_hours:02}:{n_minutes:02}:{n_seconds:02}"

        return out

    def _update_traces(self):
        if pygame.time.get_ticks(
        ) - self._last_trace_update > self._trace_dt * 1000:
            for b, trace in zip(self._space.bodies, self._traces):
                trace.insert(0, self._m_to_pix2D(b.pos))
                if len(trace) > self._trace_len:
                    trace.pop(-1)

            self._last_trace_update = pygame.time.get_ticks()

    def _clear_traces(self):
        for trace in self._traces:
            trace.clear()
        self._last_trace_update = pygame.time.get_ticks()

    def _render_bodies(self):
        # display of bodies and acceleration vectors
        min_mass = min(b.mass for b in self._space.bodies)
        max_mass = max(b.mass for b in self._space.bodies)

        for b, color in zip(self._space.bodies, self._colors):
            b_in_screen = self._m_to_pix2D(b.pos)
            radius = 5
            if min_mass != max_mass:
                radius = lerp(b.mass, min_mass, max_mass, 4, 8)

            pygame.gfxdraw.aacircle(self._screen, int(b_in_screen.x),
                                    int(b_in_screen.y), int(radius), color)
            pygame.gfxdraw.filled_circle(self._screen, int(b_in_screen.x),
                                         int(b_in_screen.y), int(radius), color)

            if self._show_vectors:
                if b.acc.mag() != 0:
                    a_start = b.acc.normalized() * radius
                    a_in_screen = self._m_to_pix2D(b.pos + b.acc *
                                                  self._seconds_per_second**2 * 0.5)
                    a_in_screen = b_in_screen + self._scale_vec(a_in_screen -
                                                                b_in_screen)
                    self._draw_arrow(self._screen,
                                     p["white"],
                                     b_in_screen + a_start,
                                     a_in_screen + a_start,
                                     extend=True)

                if b.vel.mag() != 0:
                    v_start = b.vel.normalized() * radius
                    v_in_screen = self._m_to_pix2D(b.pos + b.vel *
                                                  self._seconds_per_second * 0.5)
                    v_in_screen = b_in_screen + self._scale_vec(v_in_screen -
                                                                b_in_screen)
                    self._draw_arrow(self._screen,
                                     p["white"],
                                     b_in_screen + v_start,
                                     v_in_screen + v_start,
                                     extend=True,
                                     fill=False)

        # display of center of masses
        mass_center = self._m_to_pix2D(self._space.mass_center()).to_tuple()
        pygame.draw.circle(self._screen, p["white"], mass_center, 1)

    def _render_traces(self):
        gradent_len = int(self._trace_len * 0.4)
        solid_len = self._trace_len - gradent_len

        for trace, color in zip(self._traces, self._colors):
            if 2 <= len(trace):
                n_grad = max(0, len(trace) - solid_len - 1)
                for i in range(n_grad):
                    mix = i / n_grad
                    i += max(solid_len - 1, 0)
                    pygame.draw.aaline(self._screen,
                                       self._mix_colors(color, p["bg"], mix),
                                       trace[i].to_tuple(), trace[i + 1].to_tuple())

                if solid_len > 1:
                    pygame.draw.aalines(
                        self._screen, color, False,
                        [p.to_tuple() for p in trace[:min(solid_len, len(trace))]])

    def _render_ui(self, dt: float, real_dt: float):
        # display of clock
        timer_img = self._font.render(self._format_time(self._t), True, p["white"])
        self._screen.blit(timer_img, (20, 20))

        # display of fps
        fps = self._font.render(f"{1/real_dt:.1f} fps", True, p["white"])
        self._screen.blit(fps, (self._screen_size[0] - fps.get_width() - 10, 10))
        fps = self._font.render(f"{dt/self._sub_steps:.2e} dt", True, p["white"])
        self._screen.blit(fps, (self._screen_size[0] - fps.get_width() - 10, 30))

        # display of legend
        legend = self._font.render("LEGEND", True, p["white"])
        self._screen.blit(legend, (20, 50))

        c_mass = self._font.render("center of masses", True, p["white"])
        self._screen.blit(c_mass, (40, 70))
        pygame.draw.circle(self._screen, p["white"], (25, 79), 1)

        if self._show_vectors:
            acc = self._font.render("acceleration", True, p["white"])
            self._screen.blit(acc, (40, 90))
            ofs = Vect2(0, 4)
            self._draw_arrow(self._screen,
                             p["white"],
                             Vect2(20, 100) + ofs,
                             Vect2(30, 90) + ofs,
                             tip_size=7)

            vel = self._font.render("velocity", True, p["white"])
            self._screen.blit(vel, (40, 110))
            self._draw_arrow(self._screen,
                             p["white"],
                             Vect2(20, 120) + ofs,
                             Vect2(30, 110) + ofs,
                             tip_size=7,
                             fill=False)

        # display of help
        if not self._show_help:
            help = self._font.render("Press H to show available actions", True,
                                     p["white"])
            self._screen.blit(help, (20, self._screen_size[1] - 40))

        if self._show_help:
            bar = self._font.render("SPACE - Pause/unpause", True, p["white"])
            self._screen.blit(bar, (20, self._screen_size[1] - 240))
            right = self._font.render("While paused: RIGHT (hold) - Go forward",
                                      True, p["white"])
            self._screen.blit(right, (20, self._screen_size[1] - 220))
            left = self._font.render("LEFT (hold) - Rewind", True, p["white"])
            self._screen.blit(left, (135, self._screen_size[1] - 200))
            r = self._font.render("R - Reverse time", True, p["white"])
            self._screen.blit(r, (20, self._screen_size[1] - 180))
            v = self._font.render("V - Show velocity and acceleration vectors", True,
                                  p["white"])
            self._screen.blit(v, (20, self._screen_size[1] - 160))
            z = self._font.render("0 - Follow (0,0) (default)", True, p["white"])
            self._screen.blit(z, (20, self._screen_size[1] - 140))
            c = self._font.render("C - Follow center of masses", True, p["white"])
            self._screen.blit(c, (20, self._screen_size[1] - 120))
            b = self._font.render("B - Follow bodies", True, p["white"])
            self._screen.blit(b, (20, self._screen_size[1] - 100))
            up = self._font.render("While following bodies: UP - Next body", True,
                                   p["white"])
            self._screen.blit(up, (20, self._screen_size[1] - 80))
            down = self._font.render("DOWN - Previous body", True, p["white"])
            self._screen.blit(down, (205, self._screen_size[1] - 60))
            esc = self._font.render("ESC - Exit simulation", True, p["white"])
            self._screen.blit(esc, (20, self._screen_size[1] - 40))
            h = self._font.render("H - hide guide", True, p["white"])
            self._screen.blit(h, (20, self._screen_size[1] - 20))

    def _handle_events(self, dt: float) -> bool:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_v:
                    self._show_vectors = not self._show_vectors

                if event.key == pygame.K_SPACE:
                    self._paused = not self._paused

                if event.key == pygame.K_h:
                    self._show_help = not self._show_help

                if event.key == pygame.K_r:
                    self._time_dir = -self._time_dir

                if event.key == pygame.K_ESCAPE:
                    return True

                if event.key == pygame.K_0:
                    self._follow_mode = FollowMode.ZeroZero
                    self._clear_traces()
                if event.key == pygame.K_c:
                    self._follow_mode = FollowMode.CenterOfMass
                    self._clear_traces()
                if event.key == pygame.K_b:
                    self._follow_mode = FollowMode.Body
                    self._clear_traces()

                if self._follow_mode == FollowMode.Body:
                    if event.key == pygame.K_DOWN:
                        self._follow_body_index -= 1
                        self._follow_body_index = self._follow_body_index % len(
                            self._space.bodies)
                        self._clear_traces()
                    if event.key == pygame.K_UP:
                        self._follow_body_index += 1
                        self._follow_body_index = self._follow_body_index % len(
                            self._space.bodies)
                        self._clear_traces()

        if self._paused:
            delta = 0.0
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                delta += -0.5 * dt
            if keys[pygame.K_RIGHT]:
                delta += 0.5 * dt

            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                delta *= 5.0

            if delta != 0.0:
                for _ in range(self._sub_steps):
                    self._space.step(delta / self._sub_steps)
                self._t += delta

        return False

    def _update_center(self):
        match self._follow_mode:
            case FollowMode.ZeroZero:
                self._space_center = Vect2(0, 0)
            case FollowMode.CenterOfMass:
                self._space_center = self._space.mass_center()
            case FollowMode.Body:
                self._space_center = self._space.bodies[self._follow_body_index].pos

    def _step(self, dt: float):
        for _ in range(self._sub_steps):
            self._space.step(dt / self._sub_steps * self._time_dir)
        self._t += dt * self._time_dir

    def start_sim(self):
        self._traces: list[list[Vect2]] = [[] for _ in self._space.bodies]
        self._last_trace_update = pygame.time.get_ticks()

        last_time: float = time.perf_counter()
        while True:
            real_dt = time.perf_counter() - last_time
            dt = real_dt * self._seconds_per_second
            last_time = time.perf_counter()

            quit = self._handle_events(dt)
            if quit:
                return

            self._update_center()

            self._screen.fill(p["bg"])

            self._render_traces()
            self._render_bodies()
            self._render_ui(dt, real_dt)

            pygame.display.flip()

            if not self._paused:
                self._update_traces()
                self._step(dt)
