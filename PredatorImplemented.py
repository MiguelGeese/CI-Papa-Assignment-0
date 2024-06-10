import os
from enum import Enum, auto
import pygame as pg
from pygame.math import Vector2
from vi import Agent, Simulation
from vi.config import Config, dataclass, deserialize

os.chdir("C:/Users/coolm/OneDrive - Vrije Universiteit Amsterdam/University documents/Second year/Collective intelligence/Assignment 0/Assignment_0/Assignment_0/CI-Papa-Assignment-0")

predator_instance = None
bird_instances = []

@deserialize
@dataclass
class FlockingConfig(Config):
    # You can change these for different starting weights
    alignment_weight: float = 0.5
    cohesion_weight: float = 0.6
    separation_weight: float = 0.6

    # These should be left as is.
    delta_time: float = 0.5                                   # To learn more https://gafferongames.com/post/integration_basics/ 
    mass: int = 20                                            

    def weights(self) -> tuple[float, float, float]:
        return (self.alignment_weight, self.cohesion_weight, self.separation_weight)


class Bird(Agent):
    config: FlockingConfig

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bird_instances.append(self)

    def change_position(self):
        global predator_instance

        self.there_is_no_escape()
        
        #YOUR CODE HERE -----------
        alignment_vector = Vector2(0, 0)
        separation_vector = Vector2(0, 0)
        cohesion_vector = Vector2(0, 0)
        predator_avoidance_vector = Vector2(0, 0)

        neighbors = list(self.in_proximity_accuracy())
        if not neighbors:
            self.move = Vector2(self.config.movement_speed, 0)
            self.pos += self.move * self.config.delta_time
            return

        if predator_instance:
            distance_to_predator = self.pos.distance_to(predator_instance.pos)
            if distance_to_predator < self.config.radius * 0.5:
                predator_avoidance_vector = self.pos - predator_instance.pos
                predator_avoidance_vector = predator_avoidance_vector.normalize() * self.config.movement_speed

        for neighbor, _ in neighbors:
            if hasattr(neighbor, 'move'):
                alignment_vector += neighbor.move
            separation_vector += self.pos - neighbor.pos
            cohesion_vector += neighbor.pos

        alignment_vector /= len(neighbors)
        cohesion_vector /= len(neighbors)
        cohesion_vector -= self.pos

        if alignment_vector.length() > 0:
            alignment_vector = alignment_vector.normalize()
        if separation_vector.length() > 0:
            separation_vector = separation_vector.normalize()
        if cohesion_vector.length() > 0:
            cohesion_vector = cohesion_vector.normalize()

        alignment_vector *= self.config.alignment_weight
        separation_vector *= self.config.separation_weight
        cohesion_vector *= self.config.cohesion_weight

        total_force = alignment_vector + separation_vector + cohesion_vector + predator_avoidance_vector

        self.move += total_force

        if self.move.length() > 0:
            self.move = self.move.normalize() * self.config.movement_speed

        self.pos += self.move * self.config.delta_time

        min_distance = min([self.pos.distance_to(neighbor.pos) for neighbor, _ in neighbors])
        if min_distance < self.config.radius:
            self.change_image(0)
        else:
            self.change_image(1)
        if min_distance < self.config.radius / 2:
            self.move += separation_vector * 2
        #END CODE -----------------


class Predator(Agent):
    config: FlockingConfig

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_update_time = 0  # Initialize last update time

    def change_position(self):
        global bird_instances

        self.there_is_no_escape()

        # Update direction every 1.5 seconds
        current_time = pg.time.get_ticks()
        if current_time - self.last_update_time > 1500:
            if bird_instances:
                closest_bird = min(bird_instances, key=lambda bird: self.pos.distance_to(bird.pos))
                direction_to_bird = closest_bird.pos - self.pos
                if direction_to_bird.length() > 0:
                    direction_to_bird = direction_to_bird.normalize()
                    self.move = direction_to_bird * self.config.movement_speed
            self.last_update_time = current_time

        self.pos += self.move * self.config.delta_time


class Selection(Enum):
    ALIGNMENT = auto()
    COHESION = auto()
    SEPARATION = auto()


class FlockingLive(Simulation):
    selection: Selection = Selection.ALIGNMENT
    config: FlockingConfig

    def handle_event(self, by: float):
        if self.selection == Selection.ALIGNMENT:
            self.config.alignment_weight += by
        elif self.selection == Selection.COHESION:
            self.config.cohesion_weight += by
        elif self.selection == Selection.SEPARATION:
            self.config.separation_weight += by

    def before_update(self):
        super().before_update()

        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_UP:
                    self.handle_event(by=0.1)
                elif event.key == pg.K_DOWN:
                    self.handle_event(by=-0.1)
                elif event.key == pg.K_1:
                    self.selection = Selection.ALIGNMENT
                elif event.key == pg.K_2:
                    self.selection = Selection.COHESION
                elif event.key == pg.K_3:
                    self.selection = Selection.SEPARATION

        a, c, s = self.config.weights()
        print(f"A: {a:.1f} - C: {c:.1f} - S: {s:.1f}")

(
    FlockingLive(
        FlockingConfig(
            image_rotation=True,
            movement_speed=5,
            radius=75,
            seed=1,
        )
    )
    .batch_spawn_agents(50, Bird, images=["images/bird.png", "images/red.png"])
    .batch_spawn_agents(1, Predator, images=["images/triangle@50px.png"])
    .run()
)
