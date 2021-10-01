import math, sys
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate
import logging

DIRECTIONS = Constants.DIRECTIONS
game_state = None

logging.basicConfig(filename='agent.log', filemode='w', level=logging.INFO)

def get_resource_tiles(game_state, width, height):
    resource_tiles: list[Cell] = []
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            if cell.has_resource():
                resource_tiles.append(cell)
    return resource_tiles

def get_close_resource(player, unit, resource_tiles):
    closest_dist = math.inf
    closest_resource_tile = None
    for resource_tile in resource_tiles:
        if resource_tile.resource.type == Constants.RESOURCE_TYPES.COAL and not player.researched_coal(): continue
        if resource_tile.resource.type == Constants.RESOURCE_TYPES.URANIUM and not player.researched_uranium(): continue
        dist = resource_tile.pos.distance_to(unit.pos)
        if dist < closest_dist:
            closest_dist = dist
            closest_resource_tile = resource_tile
    return closest_resource_tile

def get_close_city(player, unit):
    closest_dist = math.inf
    closest_city_tile = None
    for k, city in player.cities.items():
        for city_tile in city.citytiles:
            dist = city_tile.pos.distance_to(unit.pos)
            if dist < closest_dist:
                closest_dist = dist
                closest_city_tile = city_tile
    return closest_city_tile

def agent(observation, configuration):
    global game_state

    ### Do not edit ###
    if observation["step"] == 0:
        game_state = Game()
        game_state._initialize(observation["updates"])
        game_state._update(observation["updates"][2:])
        game_state.id = observation.player
    else:
        game_state._update(observation["updates"])
    
    actions = []

    ### AI Code goes down here! ### 
    player = game_state.players[observation.player]
    opponent = game_state.players[(observation.player + 1) % 2]
    width, height = game_state.map.width, game_state.map.height

    resource_tiles = get_resource_tiles(game_state, width, height)

    build_city = False
    dirs = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    # we iterate over all our units and do something with them
    for unit in player.units:
        if (len(player.units) >= len(player.cities)) and (not build_city):
            build_city = True
            logging.info(f'{observation["step"]}: Can build city. Setting Boolean Build_City to True')
        if unit.is_worker() and unit.can_act(): 
            if unit.get_cargo_space_left() > 0:
                # if the unit is a worker and we have space in cargo, lets find the nearest resource tile and try to mine it
                closest_resource_tile = get_close_resource(player, unit, resource_tiles)
                if closest_resource_tile is not None:
                    actions.append(unit.move(unit.pos.direction_to(closest_resource_tile.pos)))
            else:
                # if unit is a worker and there is no cargo space left, and we can build a city, lets build one
                if build_city:
                    if unit.can_build(game_state.map):
                        action = unit.build_city()
                        actions.append(action)
                        build_city = False
                        logging.info(f'{observation["step"]}: City Built. Setting Boolean Build_City to False')
                    else:
                        found = False
                        for d in dirs:
                            x = unit.pos.x + dirs[0][0]
                            y = unit.pos.y + dirs[0][1]

                            cell = game_state.map.get_cell(x, y)
                            if cell.resource == None and cell.citytile == None:
                                action = unit.pos.direction_to(cell.pos)
                                actions.append(action)
                                found = True
                                break
                        if not found:
                            if len(player.cities) > 0:
                                closest_city_tile = get_close_city(player, unit)
                                if closest_city_tile is not None:
                                    move_dir = unit.pos.direction_to(closest_city_tile.pos)
                                    action = unit.move(move_dir)
                                    actions.append(action)


                    
                # if nothing else, and have a city, go to city
                elif len(player.cities) > 0:
                    logging.info(f'{observation["step"]}: Resources Full, No other action available, going to city')
                    closest_city_tile = get_close_city(player, unit)
                    if closest_city_tile is not None:
                        move_dir = unit.pos.direction_to(closest_city_tile.pos)
                        if (unit.can_act()):
                            actions.append(unit.move(move_dir))

    for k, city in player.cities.items():
        for city_tile in city.citytiles:
            if len(city.citytiles) / len(player.units) < 1:
                if city_tile.can_act():
                    action = city_tile.build_worker()
                    actions.append(action)

    # you can add debug annotations using the functions in the annotate object
    # actions.append(annotate.circle(0, 0))
    
    return actions
