import math, sys
from lux.game import Game
from lux.game_map import Cell, RESOURCE_TYPES
from lux.constants import Constants
from lux.game_constants import GAME_CONSTANTS
from lux import annotate

DIRECTIONS = Constants.DIRECTIONS
game_state = None
player = None

def check_if_city_tile(player, cell):
    found = False
    for k, city in player.cities.items():
        for city_tile in city.citytiles:
            if (cell.pos.equals(city_tile.pos)):
                found = True
                break
    return found

def get_resource_tiles(game_state, width, height):
    resource_tiles: list[Cell] = []
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            if cell.has_resource():
                resource_tiles.append(cell)
    return resource_tiles

def get_empty_tiles(game_state, width, height):
    empty_tiles: list[Cell] = []
    for y in range(height):
        for x in range(width):
            cell = game_state.map.get_cell(x, y)
            if not (cell.has_resource() or cell.citytile != None):
                empty_tiles.append(cell)
    return empty_tiles


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
    
    # we iterate over all our units and do something with them
    for unit in player.units:
        if unit.is_worker() and unit.can_act():
            closest_dist = math.inf
            closest_resource_tile = None
            if unit.get_cargo_space_left() > 0:
                # if the unit is a worker and we have space in cargo, lets find the nearest resource tile and try to mine it
                for resource_tile in resource_tiles:
                    if resource_tile.resource.type == Constants.RESOURCE_TYPES.COAL and not player.researched_coal(): continue
                    if resource_tile.resource.type == Constants.RESOURCE_TYPES.URANIUM and not player.researched_uranium(): continue
                    dist = resource_tile.pos.distance_to(unit.pos)
                    if dist < closest_dist:
                        closest_dist = dist
                        closest_resource_tile = resource_tile
                if closest_resource_tile is not None:
                    actions.append(unit.move(unit.pos.direction_to(closest_resource_tile.pos)))
            else:
                if (len(player.cities) <= len(player.units)):
                    cell = game_state.map.get_cell(unit.pos.x, unit.pos.y)
                    if not (cell.has_resource() or cell.citytile != None):
                        action = unit.build_city()
                        actions.append(action)
                    else:
                        empty_tiles = get_empty_tiles(game_state, width, height)
                        closest_dist = math.inf
                        closest_empty_tile = None
                        for empty_tile in empty_tiles:
                            dist = empty_tile.pos.distance_to(unit.pos)
                            if dist < closest_dist:
                                closest_dist = dist
                                closest_empty_tile = empty_tile
                        if closest_empty_tile is not None:
                            move_dir = unit.pos.direction_to(closest_empty_tile.pos)
                            actions.append(unit.move(move_dir))

                # if unit is a worker and there is no cargo space left, and we have cities, lets return to them
                elif len(player.cities) > 0:
                    closest_dist = math.inf
                    closest_city_tile = None
                    for k, city in player.cities.items():
                        for city_tile in city.citytiles:
                            dist = city_tile.pos.distance_to(unit.pos)
                            if dist < closest_dist:
                                closest_dist = dist
                                closest_city_tile = city_tile
                    if closest_city_tile is not None:
                        move_dir = unit.pos.direction_to(closest_city_tile.pos)
                        actions.append(unit.move(move_dir))
    citytile_count = 0

    dirs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    for k, city in player.cities.items():
        citytile_count += len(city.citytiles)

    for k, city in player.cities.items():
        fuel_burn = 0
        for city_tile in city.citytiles:
            count = 0
            for d in dirs:
                if not game_state.map.get_cell(city_tile.pos.x + d[0], city_tile.pos.y + d[1]).citytile == None:
                    count += 1
            burn = 23 - 5 * count
            fuel_burn += burn

        for city_tile in city.citytiles:
            if (citytile_count == len(player.units)):
                break
            fuel_burn = 0
            for k, city in player.cities.items():
                fuel_burn = fuel_burn + (23 - len(city.citytiles) * 5)
            if (city.fuel >= fuel_burn * 1):
                action = city_tile.build_worker()
                actions.append(action)
                citytile_count += 1
                # break
    # you can add debug annotations using the functions in the annotate object
    # actions.append(annotate.circle(0, 0))
    
    return actions
