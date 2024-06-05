import os
from enum import Enum, auto
import pygame as pg
from pygame.math import Vector2
from vi import Agent, Simulation
from vi.config import Config, dataclass, deserialize


@deserialize
@dataclass
class FlockingConfig(Config):
    # You can change these for different starting weights
    alignment_weight: float = 0.5
    cohesion_weight: float = 0.5
    separation_weight: float = 0.5

    # These should be left as is.
    delta_time: float = 0.5                                   # To learn more https://gafferongames.com/post/integration_basics/ 
    mass: int = 20                                            

    def weights(self) -> tuple[float, float, float]:
        return (self.alignment_weight, self.cohesion_weight, self.separation_weight)


class Bird(Agent):
    config: FlockingConfig

    def change_position(self):
        
        # Pac-man-style teleport to the other end of the screen when trying to escape
        self.there_is_no_escape()
        
        #YOUR CODE HERE -----------
        alignment_vector = Vector2(0, 0)
        separation_vector = Vector2(0, 0)
        cohesion_vector = Vector2(0, 0)

        neighbors = list(self.in_proximity_accuracy())  # Convert to list to use len()
        if not neighbors:
            # If no neighbors, move randomly to ensure all birds are moving
            self.move = Vector2(self.config.movement_speed, 0).rotate(pg.time.get_ticks() % 360)
            self.pos += self.move * self.config.delta_time
            return

        for neighbor, _ in neighbors:
            if hasattr(neighbor, 'move'):
                alignment_vector += neighbor.move
            separation_vector += self.pos - neighbor.pos
            cohesion_vector += neighbor.pos

        alignment_vector /= len(neighbors)
        cohesion_vector /= len(neighbors)
        cohesion_vector -= self.pos

        # Normalize the vectors
        if alignment_vector.length() > 0:
            alignment_vector = alignment_vector.normalize()
        if separation_vector.length() > 0:
            separation_vector = separation_vector.normalize()
        if cohesion_vector.length() > 0:
            cohesion_vector = cohesion_vector.normalize()

        # Apply weights
        alignment_vector *= self.config.alignment_weight
        separation_vector *= self.config.separation_weight
        cohesion_vector *= self.config.cohesion_weight

        # Calculate the total force
        total_force = alignment_vector + separation_vector + cohesion_vector

        # Update move direction
        self.move += total_force

        # Normalize the velocity to maintain consistent speed
        if self.move.length() > 0:
            self.move = self.move.normalize() * self.config.movement_speed

        # Update position
        self.pos += self.move * self.config.delta_time

        # Change image based on separation distance
        min_distance = min([self.pos.distance_to(neighbor.pos) for neighbor, _ in neighbors])
        if min_distance < self.config.radius:  # Distance threshold for separation
            self.change_image(0)  # Turn white when they should move apart
        else:
            self.change_image(1)  # Turn red when they are close together
        #END CODE -----------------


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
            movement_speed=1,
            radius=50,
            seed=1,
        )
    )
    .batch_spawn_agents(50, Bird, images=["images/bird.png", "images/red.png"])
    .run()
)
