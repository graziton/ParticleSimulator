import pygame
import random
import math

# Constants
WIDTH, HEIGHT = 1280, 720
TIME_STEP = 5  # Time step for updates
MAX_FORCE = 1e9  # Reduced maximum allowable force for smoother movement
K_COULOMB = 8.9875e9  # Coulomb's constant (in N·m²/C²)
DAMPING_WALL = 1
DAMPING_OBJECT = 1
EPSILON = 1e-7  # To avoid division by zero

# Particle class
class Particle:
    def __init__(self, x, y, mass, radius):
        self.x = x
        self.y = y
        self.mass = mass
        self.radius = radius
        self.fx = 0  # Force in x direction
        self.fy = 0  # Force in y direction
        self.vx = 0  # Velocity in x direction
        self.vy = 0  # Velocity in y direction

# Initialize particles
def initialize_particles(count, radius):
    particles = []
    mass = 1e12  # Assign a uniform mass to all particles
    for _ in range(count):
        x = random.uniform(radius, WIDTH - radius)
        y = random.uniform(radius, HEIGHT - radius)
        particles.append(Particle(x, y, mass, radius))
    return particles

# Compute pairwise forces
def compute_all_pairwise_forces(particles):
    for i in range(len(particles) - 1):
        for j in range(i + 1, len(particles)):
            p1, p2 = particles[i], particles[j]
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            distance_squared = dx**2 + dy**2 + EPSILON
            distance = math.sqrt(distance_squared)

            if distance < p1.radius + p2.radius:
                continue  # Skip overlapping particles

            force = K_COULOMB * p1.mass * p2.mass / distance_squared
            force = min(force, MAX_FORCE)

            fx = force * dx / distance
            fy = force * dy / distance

            p1.fx += fx
            p1.fy += fy
            p2.fx -= fx
            p2.fy -= fy

# Update particles with velocity and forces
def update_particles(particles):
    for p in particles:
        p.vx += (p.fx / p.mass) * TIME_STEP
        p.vy += (p.fy / p.mass) * TIME_STEP
        p.x += p.vx * TIME_STEP
        p.y += p.vy * TIME_STEP
        p.fx = p.fy = 0  # Reset forces inline

# Handle collisions between particles
def handle_collisions(particles):
    for i in range(len(particles) - 1):
        for j in range(i + 1, len(particles)):
            p1, p2 = particles[i], particles[j]
            dx = p2.x - p1.x
            dy = p2.y - p1.y
            distance_squared = dx**2 + dy**2
            distance = math.sqrt(distance_squared)

            if distance < p1.radius + p2.radius:  # Collision detected
                overlap = p1.radius + p2.radius - distance
                inv_distance = 1 / distance if distance > 0 else 0
                resolve_x = dx * inv_distance * overlap / 2
                resolve_y = dy * inv_distance * overlap / 2
                p1.x -= resolve_x
                p1.y -= resolve_y
                p2.x += resolve_x
                p2.y += resolve_y

                # Compute normal and tangential directions
                normal_x = dx * inv_distance
                normal_y = dy * inv_distance
                tangent_x = -normal_y
                tangent_y = normal_x

                # Project velocities onto normal and tangential directions
                v1n = p1.vx * normal_x + p1.vy * normal_y
                v2n = p2.vx * normal_x + p2.vy * normal_y
                v1t = p1.vx * tangent_x + p1.vy * tangent_y
                v2t = p2.vx * tangent_x + p2.vy * tangent_y

                # Apply conservation of momentum to normal components
                m1, m2 = p1.mass, p2.mass
                v1n_new = ((v1n * (m1 - m2) + 2 * m2 * v2n) / (m1 + m2)) * DAMPING_OBJECT
                v2n_new = ((v2n * (m2 - m1) + 2 * m1 * v1n) / (m1 + m2)) * DAMPING_OBJECT

                # Combine updated normal and unchanged tangential components
                p1.vx = v1t * tangent_x + v1n_new * normal_x
                p1.vy = v1t * tangent_y + v1n_new * normal_y
                p2.vx = v2t * tangent_x + v2n_new * normal_x
                p2.vy = v2t * tangent_y + v2n_new * normal_y

# Handle collisions with walls
def handle_wall_collisions(particles):
    for p in particles:
        if p.x - p.radius < 0:  # Left wall
            p.vx = -p.vx * DAMPING_WALL
            p.x = p.radius

        elif p.x + p.radius > WIDTH:  # Right wall
            p.vx = -p.vx * DAMPING_WALL
            p.x = WIDTH - p.radius

        if p.y - p.radius < 0:  # Top wall
            p.vy = -p.vy * DAMPING_WALL
            p.y = p.radius

        elif p.y + p.radius > HEIGHT:  # Bottom wall
            p.vy = -p.vy * DAMPING_WALL
            p.y = HEIGHT - p.radius

# Optimized menu
def menu():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Particle Simulation - Menu")
    font = pygame.font.Font(None, 40)
    small_font = pygame.font.Font(None, 30)

    # Pre-rendering static UI elements onto a separate surface
    static_menu = pygame.Surface((WIDTH, HEIGHT))
    static_menu.fill((30, 30, 30))
    title_text = font.render("Particle Simulation", True, (255, 255, 255))
    particles_text = small_font.render("Number of Atoms (1-100):", True, (200, 200, 200))
    radius_text = small_font.render("Radius (1-10):", True, (200, 200, 200))

    static_menu.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 50))
    static_menu.blit(particles_text, (100, 150))
    static_menu.blit(radius_text, (100, 250))

    start_rect = pygame.Rect(WIDTH // 2 - 150, 400, 300, 60)
    quit_rect = pygame.Rect(WIDTH // 2 - 150, 500, 300, 60)
    pygame.draw.rect(static_menu, (50, 205, 50), start_rect)
    pygame.draw.rect(static_menu, (205, 50, 50), quit_rect)

    start_text = font.render("Start Simulation", True, (0, 0, 0))
    quit_text = font.render("Quit", True, (0, 0, 0))

    static_menu.blit(start_text, (start_rect.x + (start_rect.width - start_text.get_width()) // 2,
                                  start_rect.y + (start_rect.height - start_text.get_height()) // 2))
    static_menu.blit(quit_text, (quit_rect.x + (quit_rect.width - quit_text.get_width()) // 2,
                                 quit_rect.y + (quit_rect.height - quit_text.get_height()) // 2))

    input_boxes = {"particles": "", "radius": ""}
    active_box = None

    clock = pygame.time.Clock()  # Initializing clock for limiting FPS

    while True:
        screen.blit(static_menu, (0, 0))

        # Drawing dynamic elements (input boxes)
        for i, (key, value) in enumerate(input_boxes.items()):
            box_rect = pygame.Rect(400, 140 + i * 100, 200, 40)
            color = (255, 255, 255) if active_box == key else (200, 200, 200)
            pygame.draw.rect(screen, color, box_rect, 2)
            text_surface = small_font.render(value, True, (255, 255, 255))
            screen.blit(text_surface, (box_rect.x + 5, box_rect.y + 5))

        pygame.display.flip()
        clock.tick(30)  # Limited FPS to 30 to reduce CPU usage

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None, None
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if start_rect.collidepoint(event.pos):
                    try:
                        particle_count = int(input_boxes["particles"])
                        radius_value = int(input_boxes["radius"])
                        if 1 <= particle_count <= 100 and 1 <= radius_value <= 10:
                            return particle_count, 5 + 2 * (radius_value - 1)
                    except ValueError:
                        pass
                elif quit_rect.collidepoint(event.pos):
                    return None, None
                else:
                    for i, key in enumerate(input_boxes):
                        box_rect = pygame.Rect(400, 140 + i * 100, 200, 40)
                        if box_rect.collidepoint(event.pos):
                            active_box = key
                            break
                    else:
                        active_box = None
            elif event.type == pygame.KEYDOWN and active_box:
                if event.key == pygame.K_BACKSPACE:
                    input_boxes[active_box] = input_boxes[active_box][:-1]
                elif event.unicode.isdigit():
                    input_boxes[active_box] += event.unicode

# Main simulation loop
def run_simulation(particle_count, radius):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    particles = initialize_particles(particle_count, radius)

    # Trails dictionary for particle paths
    trails = {p: [] for p in particles}
    selected_particle = None  # For dragging a particle

    trail_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)  # Persistent surface for trails
    max_trail_length = 50  # Limit trail length

    running = True
    while running:
        screen.fill((0, 0, 0))  # Clear the main screen

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                for p in particles:
                    if math.sqrt((mouse_x - p.x) ** 2 + (mouse_y - p.y) ** 2) < p.radius:
                        selected_particle = p
                        break
            elif event.type == pygame.MOUSEBUTTONUP:
                selected_particle = None
            elif event.type == pygame.MOUSEMOTION and selected_particle:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                selected_particle.x, selected_particle.y = mouse_x, mouse_y

        # Compute forces and update particles
        compute_all_pairwise_forces(particles)
        max_speed = max(math.sqrt(p.vx ** 2 + p.vy ** 2) for p in particles)
        global TIME_STEP  # Update time step dynamically
        TIME_STEP = min(5, radius / (max_speed + EPSILON))
        update_particles(particles)
        handle_collisions(particles)
        handle_wall_collisions(particles)

        # Update trails
        for p in particles:
            trails[p].append((p.x, p.y, p.radius))
            if len(trails[p]) > max_trail_length:
                trails[p].pop(0)

        # Draw comet-like trails
        trail_surface.fill((0, 0, 0, 0))  # Clear trail surface
        for p in particles:
            if len(trails[p]) > 1:
                for i in range(len(trails[p]) - 1, 0, -1):
                    x1, y1, radius1 = trails[p][i]
                    x2, y2, radius2 = trails[p][i - 1]
                    alpha = int(255 * (i / len(trails[p])))

                    # Width for fade effect
                    width1 = radius1 * ((i / len(trails[p])) ** 0.5)
                    width2 = radius2 * (((i - 1) / len(trails[p])) ** 0.5)

                    # Trail color transition from red to blue
                    red = 255 - int(255 * (i / len(trails[p])))
                    blue = int(255 * (i / len(trails[p])))
                    trail_color = (red, 0, blue)

                    pygame.draw.polygon(
                        trail_surface,
                        trail_color + (alpha,),
                        [
                            (x1 - width1, y1), (x1 + width1, y1),
                            (x2 + width2, y2), (x2 - width2, y2),
                        ],
                    )
        screen.blit(trail_surface, (0, 0))  # Add trails to the main screen

        # Draw particles with color based on speed
        for p in particles:
            speed_squared = p.vx ** 2 + p.vy ** 2
            color_intensity = min(255, int(0.5 * p.mass * speed_squared * math.sqrt(1e-9 * 1e-10)))
            color = (color_intensity, 0, 255 - color_intensity)
            pygame.draw.circle(screen, color, (int(p.x), int(p.y)), p.radius)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    particle_count, radius = menu()
    if particle_count and radius:
        run_simulation(particle_count, radius)
