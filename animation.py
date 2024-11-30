import pygame
import random
import math

# Constants
WIDTH, HEIGHT = 800, 600
PARTICLE_COUNT = 5  # Number of particles to simulate
TIME_STEP = 5  # Time step for updates
MAX_FORCE = 1e9  # Reduced maximum allowable force for smoother movement
THETA = 0.8  # Multipole approximation threshold
K_COULOMB = 8.9875e9  # Coulomb's constant (in N·m²/C²)
PARTICLE_RADIUS = 18  # Fixed radius for all particles
DAMPING = 0.98  # Damping factor to reduce velocity over time

# Particle class
class Particle:
    def __init__(self, x, y, mass, radius=PARTICLE_RADIUS):
        self.x = x
        self.y = y
        self.mass = mass
        self.radius = radius
        self.fx = 0  # Force in x direction
        self.fy = 0  # Force in y direction
        self.vx = 0  # Velocity in x direction
        self.vy = 0  # Velocity in y direction

# QuadTree Node class
class QuadTreeNode:
    def __init__(self, x, y, size):
        self.x = x  # X position of the node
        self.y = y  # Y position of the node
        self.size = size  # Size of the node
        self.particles = []  # Particles in the node
        self.center_of_mass = [0, 0]  # Center of mass [x, y]
        self.mass = 0  # Total mass of particles in this node
        self.children = []  # Subnodes (4 children)

    def insert(self, p):
        if len(self.children) == 0 and len(self.particles) < 4:
            self.particles.append(p)
            self._update_mass_properties()
        else:
            if len(self.children) == 0:
                self.subdivide()
            for child in self.children:
                if child.contains(p):
                    child.insert(p)
                    break

    def contains(self, p):
        return self.x <= p.x < self.x + self.size and self.y <= p.y < self.y + self.size

    def subdivide(self):
        half_size = self.size / 2
        self.children.append(QuadTreeNode(self.x, self.y, half_size))
        self.children.append(QuadTreeNode(self.x + half_size, self.y, half_size))
        self.children.append(QuadTreeNode(self.x, self.y + half_size, half_size))
        self.children.append(QuadTreeNode(self.x + half_size, self.y + half_size, half_size))
        for p in self.particles:
            for child in self.children:
                if child.contains(p):
                    child.insert(p)
                    break
        self.particles = []
        self._update_mass_properties()

    def _update_mass_properties(self):
        if len(self.children) == 0:
            # Leaf node: compute mass and center of mass from particles
            self.mass = sum(p.mass for p in self.particles)
            if self.mass > 0:
                self.center_of_mass[0] = sum(p.x * p.mass for p in self.particles) / self.mass
                self.center_of_mass[1] = sum(p.y * p.mass for p in self.particles) / self.mass
        else:
            # Internal node: compute mass and center of mass from children
            self.mass = sum(child.mass for child in self.children)
            if self.mass > 0:
                self.center_of_mass[0] = sum(child.center_of_mass[0] * child.mass for child in self.children) / self.mass
                self.center_of_mass[1] = sum(child.center_of_mass[1] * child.mass for child in self.children) / self.mass

    def compute_force(self, particle, theta):
        if len(self.children) == 0:
            for p in self.particles:
                if p != particle:
                    self._compute_pairwise_force(p, particle)
        else:
            dx = self.center_of_mass[0] - particle.x
            dy = self.center_of_mass[1] - particle.y
            distance = math.sqrt(dx**2 + dy**2 + 1e-7)
            if distance < 1:
                return
            if self.size / distance < theta:
                force = K_COULOMB * self.mass * particle.mass / (distance**2 + 1e-7)
                force = min(force, MAX_FORCE)
                particle.fx += force * dx / distance
                particle.fy += force * dy / distance
            else:
                for child in self.children:
                    child.compute_force(particle, theta)

    def _compute_pairwise_force(self, p1, p2):
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        distance = math.sqrt(dx**2 + dy**2)
        if distance < p1.radius + p2.radius:
            return
        force = K_COULOMB * p1.mass * p2.mass / (distance**2 + 1e-7)
        force = min(force, MAX_FORCE)
        fx = force * dx / distance
        fy = force * dy / distance
        p1.fx += fx
        p1.fy += fy
        p2.fx -= fx
        p2.fy -= fy

# Initialize particles
def initialize_particles(count):
    particles = []
    for _ in range(count):
        x = random.uniform(PARTICLE_RADIUS, WIDTH - PARTICLE_RADIUS)
        y = random.uniform(PARTICLE_RADIUS, HEIGHT - PARTICLE_RADIUS)
        mass = random.uniform(1e11, 1e12)
        particles.append(Particle(x, y, mass))
    return particles

# Update particles with velocity and forces
def update_particles(particles):
    for p in particles:
        p.vx += (p.fx / p.mass) * TIME_STEP
        p.vy += (p.fy / p.mass) * TIME_STEP
        p.x += p.vx * TIME_STEP
        p.y += p.vy * TIME_STEP
        p.fx, p.fy = 0, 0

# Handle collisions between particles
def handle_collisions(particles):
    for i, p1 in enumerate(particles):
        for j, p2 in enumerate(particles[i + 1:], i + 1):
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            distance = math.sqrt(dx**2 + dy**2)

            relative_speed = math.sqrt((p2.vx - p1.vx)**2 + (p2.vy - p1.vy)**2)
            time_to_collision = (p1.radius + p2.radius - distance) / (relative_speed + 1e-7)
            if distance < p1.radius + p2.radius and time_to_collision < TIME_STEP:
                # Resolve overlap
                overlap = p1.radius + p2.radius - distance
                resolve_x = dx / distance * overlap / 2
                resolve_y = dy / distance * overlap / 2
                p1.x -= resolve_x
                p1.y -= resolve_y
                p2.x += resolve_x
                p2.y += resolve_y

                # Collision normal
                normal_x = dx / distance
                normal_y = dy / distance

                # Relative velocity
                relative_velocity_x = p2.vx - p1.vx
                relative_velocity_y = p2.vy - p1.vy

                # Velocity along the collision normal
                velocity_along_normal = (
                    relative_velocity_x * normal_x + relative_velocity_y * normal_y
                )

                if velocity_along_normal > 0:
                    continue

                # Impulse scalar
                impulse = (2 * velocity_along_normal) / (1 / p1.mass + 1 / p2.mass)

                # Apply impulse
                impulse_x = impulse * normal_x
                impulse_y = impulse * normal_y
                p1.vx += impulse_x / p1.mass
                p1.vy += impulse_y / p1.mass
                p2.vx -= impulse_x / p2.mass
                p2.vy -= impulse_y / p2.mass

# Handle collisions with walls
def handle_wall_collisions(particles):
    for p in particles:
        if p.x - p.radius < 0:
            p.vx = abs(p.vx)
            p.x = p.radius
        elif p.x + p.radius > WIDTH:
            p.vx = -abs(p.vx)
            p.x = WIDTH - p.radius
        if p.y - p.radius < 0:
            p.vy = abs(p.vy)
            p.y = p.radius
        elif p.y + p.radius > HEIGHT:
            p.vy = -abs(p.vy)
            p.y = HEIGHT - p.radius

# Main simulation loop
def run_simulation():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    particles = initialize_particles(PARTICLE_COUNT)

    running = True
    while running:
        screen.fill((0, 0, 0))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if 'quadtree' not in locals():  # Create the QuadTree only once
            quadtree = QuadTreeNode(0, 0, max(WIDTH, HEIGHT))
        else:
            quadtree = QuadTreeNode(0, 0, max(WIDTH, HEIGHT))  # Rebuild (Optional Optimization)
            for p in particles:
                quadtree.insert(p)

        for p in particles:
            quadtree.compute_force(p, THETA)

        update_particles(particles)
        handle_collisions(particles)
        handle_wall_collisions(particles)

        for p in particles:
            kinetic_energy = 0.5 * p.mass * (p.vx**2 + p.vy**2)
            scale_factor = math.sqrt(1e-9 * 1e-10)  # Equivalent to 1e-9.5
            color_intensity = min(255, int(kinetic_energy * scale_factor))  # Scale intensity
            color = (color_intensity, 0, 255 - color_intensity)  # Gradient from blue to red
            pygame.draw.circle(screen, color, (int(p.x), int(p.y)), p.radius)

            
        

        # Draw velocity vectors
        for p in particles:
            end_x = p.x + p.vx * 10  # Scale velocities for visualization
            end_y = p.y + p.vy * 10
            pygame.draw.line(screen, (255, 255, 0), (p.x, p.y), (end_x, end_y), 2)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    run_simulation()
