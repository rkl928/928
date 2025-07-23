import pygame
from pygame.locals import *
import random

pygame.init()

# Create the window
width = 500
height = 500
screen_size = (width, height)
screen = pygame.display.set_mode(screen_size)
pygame.display.set_caption('Car Game')

# Colors
gray = (100, 100, 100)
green = (76, 208, 56)
red = (200, 0, 0)
white = (255, 255, 255)
yellow = (255, 232, 0)

# Road and marker sizes
road_width = 300
marker_width = 10
marker_height = 50

# Lane coordinates
left_lane = 150
center_lane = 250
right_lane = 350
lanes = [left_lane, center_lane, right_lane]

# Road and edge markers
road = (100, 0, road_width, height)
left_edge_marker = (95, 0, marker_width, height)
right_edge_marker = (395, 0, marker_width, height)

# For animating movement of the lane markers
lane_marker_move_y = 0

# Player's starting coordinates
player_x = 250
player_y = 400

# Frame settings
clock = pygame.time.Clock()
fps = 120

# Game settings
gameover = False
speed = 2
score = 0
last_speed_increase_score = 0


# Behavior Tree Node Classes
class Node:
    def run(self):
        raise NotImplementedError("Run method must be implemented by subclasses.")


class Action(Node):
    def __init__(self, action):
        self.action = action

    def run(self):
        return self.action()


class Sequence(Node):
    def __init__(self, children):
        self.children = children

    def run(self):
        for child in self.children:
            if child.run() == "FAILURE":
                return "FAILURE"
        return "SUCCESS"


class Selector(Node):
    def __init__(self, children):
        self.children = children

    def run(self):
        for child in self.children:
            if child.run() == "SUCCESS":
                return "SUCCESS"
        return "FAILURE"


# Action Functions for Vehicle Behaviors
def increase_speed():
    global speed, last_speed_increase_score
    if score >= last_speed_increase_score + 10:
        speed += 1
        last_speed_increase_score += 10
        return "SUCCESS"
    return "RUNNING"


def move_forward(vehicle):
    vehicle.rect.y += speed
    if vehicle.rect.top >= height:
        vehicle.kill()
        global score
        score += 1
        return "SUCCESS"
    return "RUNNING"


def avoid_player():
    checked_lanes = [player.rect.centerx]
    for npc_vehicle in vehicle_group:
        if (player.rect.y - npc_vehicle.rect.y) < 300 and player.rect.centerx == npc_vehicle.rect.centerx:
            if player.rect.centerx > left_lane and left_lane not in checked_lanes:
                checked_lanes.append(left_lane)
                if not any(abs(npc.rect.x - left_lane) < 50 and abs(player.rect.y - npc.rect.y) < 200 for npc in
                           vehicle_group):
                    player.rect.x -= 100
                    return "SUCCESS"
            if player.rect.centerx < right_lane and right_lane not in checked_lanes:
                checked_lanes.append(right_lane)
                if not any(abs(npc.rect.x - right_lane) < 50 and abs(player.rect.y - npc.rect.y) < 200 for npc in
                           vehicle_group):
                    player.rect.x += 100
                    return "SUCCESS"
            return "FAILURE"
    return "FAILURE"


def check_collision(vehicle):
    for other_vehicle in vehicle_group:
        if vehicle != other_vehicle and vehicle.rect.colliderect(other_vehicle.rect):
            vehicle.kill()
            return "FAILURE"
    return "SUCCESS"


# Vehicle class with behavior tree integration
class Vehicle(pygame.sprite.Sprite):
    def __init__(self, image, x, y):  # Fixed to __init__ instead of _init_
        pygame.sprite.Sprite.__init__(self)
        image_scale = 45 / image.get_rect().width
        new_width = image.get_rect().width * image_scale
        new_height = image.get_rect().height * image_scale
        self.image = pygame.transform.scale(image, (new_width, new_height))
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.behavior_tree = Selector([
            Sequence([Action(lambda: move_forward(self)), Action(lambda: avoid_player())]),
            Action(lambda: check_collision(self))
        ])

    def update(self):
        self.behavior_tree.run()


# Player class
class PlayerVehicle(Vehicle):
    def __init__(self, x, y):  # Fixed to __init__ instead of _init_
        image = pygame.image.load('./car.png')
        super().__init__(image, x, y)


# Sprite groups
player_group = pygame.sprite.Group()
vehicle_group = pygame.sprite.Group()

# Create the player's car
player = PlayerVehicle(player_x, player_y)
player_group.add(player)  # Add the player to the sprite group here

# Load vehicle images
image_filenames = ['pickup_truck.png', 'semi_trailer.png', 'taxi.png', 'van.png']
vehicle_images = []
for image_filename in image_filenames:
    image = pygame.image.load('./' + image_filename)
    vehicle_images.append(image)

# Load crash image
crash_image = pygame.image.load('./crash.png')
crash_image = pygame.transform.scale(crash_image, (player.rect.width, player.rect.height))

# Game loop
running = True
while running:
    clock.tick(fps)

    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        if event.type == KEYDOWN:
            if event.key == K_LEFT and player.rect.center[0] > left_lane:
                player.rect.x -= 100
            elif event.key == K_RIGHT and player.rect.center[0] < right_lane:
                player.rect.x += 100

    # Increase the speed
    increase_speed()

    # Draw the grass
    screen.fill(green)

    # Draw the road
    pygame.draw.rect(screen, gray, road)

    # Draw the edge markers
    pygame.draw.rect(screen, yellow, left_edge_marker)
    pygame.draw.rect(screen, yellow, right_edge_marker)

    # Draw the lane markers
    lane_marker_move_y += speed * 2
    if lane_marker_move_y >= marker_height * 2:
        lane_marker_move_y = 0
    for y in range(marker_height * -2, height, marker_height * 2):
        pygame.draw.rect(screen, white, (left_lane + 45, y + lane_marker_move_y, marker_width, marker_height))
        pygame.draw.rect(screen, white, (center_lane + 45, y + lane_marker_move_y, marker_width, marker_height))

    # Draw the player's car
    player_group.draw(screen)

    # Add new vehicles
    if len(vehicle_group) < 2:
        lane = random.choice(lanes)
        image = random.choice(vehicle_images)
        vehicle = Vehicle(image, lane, height / -2)
        vehicle_group.add(vehicle)

    # Update and draw vehicles
    vehicle_group.update()
    vehicle_group.draw(screen)

    # Display the score
    font = pygame.font.Font(pygame.font.get_default_font(), 16)
    text = font.render('Score: ' + str(score), True, white)
    text_rect = text.get_rect()
    text_rect.center = (50, 400)
    screen.blit(text, text_rect)

    # Display the speed
    font = pygame.font.Font(pygame.font.get_default_font(), 16)
    text = font.render('Speed: ' + str(speed), True, white)
    text_rect = text.get_rect()
    text_rect.center = (50, 450)
    screen.blit(text, text_rect)

    # Game over logic
    if pygame.sprite.spritecollide(player, vehicle_group, True):
        gameover = True
        screen.blit(crash_image, player.rect.topleft)

    # Display game over
    if gameover:
        pygame.draw.rect(screen, red, (0, 50, width, 100))
        text = font.render('Game Over! Press R to Restart', True, white)
        text_rect = text.get_rect()
        text_rect.center = (width / 2, 100)
        screen.blit(text, text_rect)

    pygame.display.update()

    # Handle restarting the game
    while gameover:
        for event in pygame.event.get():
            if event.type == QUIT:
                gameover = False
                running = False
            if event.type == KEYDOWN:
                if event.key == K_r:
                    gameover = False
                    score = 0
                    vehicle_group.empty()
                    player.rect.center = [player_x, player_y]
                    speed = 2

pygame.quit()