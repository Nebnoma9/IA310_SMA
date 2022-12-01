import enum
import math
import random
import uuid
from enum import Enum

import mesa
import numpy as np
from collections import defaultdict

import mesa.space
from mesa import Agent, Model
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation
from mesa.visualization.ModularVisualization import VisualizationElement, ModularServer, UserSettableParameter
from mesa.visualization.modules import ChartModule

MAX_ITERATION = 100
PROBA_CHGT_ANGLE = 0.01


def move(x, y, speed, angle):
    return x + speed * math.cos(angle), y + speed * math.sin(angle)


def go_to(x, y, speed, dest_x, dest_y):
    if np.linalg.norm((x - dest_x, y - dest_y)) < speed:
        return (dest_x, dest_y), 2 * math.pi * random.random()
    else:
        angle = math.acos((dest_x - x)/np.linalg.norm((x - dest_x, y - dest_y)))
        if dest_y < y:
            angle = - angle
        return move(x, y, speed, angle), angle


class MarkerPurpose(Enum):
    DANGER = enum.auto(),
    INDICATION = enum.auto()


class ContinuousCanvas(VisualizationElement):
    local_includes = [
        "./js/simple_continuous_canvas.js",
        "./js/jquery.js"
    ]

    def __init__(self, canvas_height=500,
                 canvas_width=500, instantiate=True):
        VisualizationElement.__init__(self)
        self.canvas_height = canvas_height
        self.canvas_width = canvas_width
        self.identifier = "space-canvas"
        if (instantiate):
            new_element = ("new Simple_Continuous_Module({}, {},'{}')".
                           format(self.canvas_width, self.canvas_height, self.identifier))
            self.js_code = "elements.push(" + new_element + ");"

    def portrayal_method(self, obj):
        return obj.portrayal_method()

    def render(self, model):
        representation = defaultdict(list)
        for obj in model.schedule.agents:
            portrayal = self.portrayal_method(obj)
            if portrayal:
                portrayal["x"] = ((obj.x - model.space.x_min) /
                                  (model.space.x_max - model.space.x_min))
                portrayal["y"] = ((obj.y - model.space.y_min) /
                                  (model.space.y_max - model.space.y_min))
            representation[portrayal["Layer"]].append(portrayal)
        for obj in model.mines:
            portrayal = self.portrayal_method(obj)
            if portrayal:
                portrayal["x"] = ((obj.x - model.space.x_min) /
                                  (model.space.x_max - model.space.x_min))
                portrayal["y"] = ((obj.y - model.space.y_min) /
                                  (model.space.y_max - model.space.y_min))
            representation[portrayal["Layer"]].append(portrayal)
        for obj in model.markers:
            portrayal = self.portrayal_method(obj)
            if portrayal:
                portrayal["x"] = ((obj.x - model.space.x_min) /
                                  (model.space.x_max - model.space.x_min))
                portrayal["y"] = ((obj.y - model.space.y_min) /
                                  (model.space.y_max - model.space.y_min))
            representation[portrayal["Layer"]].append(portrayal)
        for obj in model.obstacles:
            portrayal = self.portrayal_method(obj)
            if portrayal:
                portrayal["x"] = ((obj.x - model.space.x_min) /
                                  (model.space.x_max - model.space.x_min))
                portrayal["y"] = ((obj.y - model.space.y_min) /
                                  (model.space.y_max - model.space.y_min))
            representation[portrayal["Layer"]].append(portrayal)
        for obj in model.quicksands:
            portrayal = self.portrayal_method(obj)
            if portrayal:
                portrayal["x"] = ((obj.x - model.space.x_min) /
                                  (model.space.x_max - model.space.x_min))
                portrayal["y"] = ((obj.y - model.space.y_min) /
                                  (model.space.y_max - model.space.y_min))
            representation[portrayal["Layer"]].append(portrayal)
        return representation


class Obstacle:  # Environnement: obstacle infranchissable
    def __init__(self, x, y, r):
        self.x = x
        self.y = y
        self.r = r

    def portrayal_method(self):
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": "black",
                     "r": self.r}
        return portrayal


class Quicksand:  # Environnement: ralentissement
    def __init__(self, x, y, r):
        self.x = x
        self.y = y
        self.r = r

    def portrayal_method(self):
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": "olive",
                     "r": self.r}
        return portrayal


class Mine:  # Environnement: élément à ramasser
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def portrayal_method(self):
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 2,
                     "Color": "blue",
                     "r": 2}
        return portrayal


class Marker:  # La classe pour les balises
    def __init__(self, x, y, purpose, direction=None):
        self.x = x
        self.y = y
        self.purpose = purpose
        if purpose == MarkerPurpose.INDICATION:
            if direction is not None:
                self.direction = direction
            else:
                raise ValueError("Direction should not be none for indication marker")

    def portrayal_method(self):
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 2,
                     "Color": "red" if self.purpose == MarkerPurpose.DANGER else "green",
                     "r": 2}
        return portrayal


class Robot(Agent):  # La classe des agents
    def __init__(self, unique_id: int, model: Model, x, y, speed, sight_distance, angle=0.0):
        super().__init__(unique_id, model)
        self.x = x
        self.y = y
        self.speed = speed
        self.sight_distance = sight_distance
        self.angle = angle
        self.counter = 0
        self.midspeed = speed/2 

    def inborder(self,x,y):
        if ( x >= self.model.space.width or 
            y >= self.model.space.height or
            x <= 0 or
            y <= 0 ) :
            return False
        return True


    def step(self):
        
        futur_pos = move(self.x, self.y, self.speed, self.angle)
        pos_params=0

        
        #tourner à 90 indication
        if self.counter==0: 
            for indication in [x for x in self.model.markers if x.purpose==MarkerPurpose.INDICATION]:
                if  (self.x - indication.x)**2 + (self.y - indication.y)**2 <= (self.sight_distance)**2 :
                    for robot in self.model.schedule.agents:
                        if robot.unique_id != self.unique_id:
                            if not(robot.x==indication.x and robot.y==indication.y):
                                pos_params=go_to(self.x,self.y,self.speed,indication.x,indication.y)
                if self.x==indication.x and self.y==indication.y:
                    self.angle = random.choice([indication.direction + math.pi/2, indication.direction - math.pi/2])
                    self.model.markers.remove(indication)
        else:
            if self.counter > 0:
                self.counter -= 1 #gestion compte à rebours
        
        #faire demi tour Danger
        for danger in [x for x in self.model.markers if x.purpose==MarkerPurpose.DANGER]:
            if  (self.x - danger.x)**2 + (self.y - danger.y)**2 <= (self.sight_distance)**2 :
                self.angle = math.pi 
        
      

        #Eviter un autre robot
        near_robots = []
        posi = futur_pos
        for robot in self.model.schedule.agents:
            if robot.unique_id != self.unique_id:
                if (robot.x - self.x)**2 + (robot.y - self.y)**2 <= (self.sight_distance)**2 :
                    if math.sqrt((posi[0] - self.x)**2 + (posi[1] - self.y)**2) <= robot.midspeed*2:
                        self.angle = random.random() * 2 * math.pi
                        #posi = move(self.x, self.y, self.speed, self.angle)
                    near_robots.append(robot)
        

        #éviter un obstacle (bords)
        pos = futur_pos
        for obstacle in self.model.obstacles:
            while  (pos[0] - obstacle.x)**2 + (pos[1] - obstacle.y)**2 <= (obstacle.r)**2 :
                self.angle = random.random()*2*math.pi
                pos = move(self.x, self.y, self.speed, self.angle)

        pos = futur_pos
        while not self.inborder(pos[0],pos[1]) : 
            self.angle = random.random()*2*math.pi
            pos = move(self.x, self.y, self.speed, self.angle)

        #se diriger vers une mine et la détruire, ajouter une balise INDICATION
        for mine in self.model.mines:
            if (mine.x - self.x)**2 + (mine.y - self.y)**2 <= (self.sight_distance)**2 :
                for robot in self.model.schedule.agents:
                    if robot.unique_id != self.unique_id:
                        if not(robot.x==mine.x and robot.y==mine.y):
                            pos_params=go_to(self.x,self.y,self.speed,mine.x,mine.y)
            if self.x == mine.x and self.y == mine.y:
                self.model.mines.remove(mine)
                self.model.mines_desamorcees += 1 
                self.model.markers.append(Marker(self.x,self.y,MarkerPurpose.INDICATION,self.angle))
                self.counter = int(self.midspeed)

                
        #se déplacer sable mouvant ajouter une balise DANGER
        if random.random() < PROBA_CHGT_ANGLE:
            self.angle = random.random() * 2 * math.pi
        for quicksand in self.model.quicksands:
            if (self.x - quicksand.x)**2 + (self.y - quicksand.y)**2 <= (quicksand.r)**2 :
                self.speed = self.midspeed
                self.model.steps_in_quicksand +=1 
                if (futur_pos[0] - quicksand.x)**2 + (futur_pos[1] - quicksand.y)**2 > (quicksand.r)**2 :
                    self.model.markers.append(Marker(self.x,self.y,MarkerPurpose.DANGER))
            else:
                self.speed = self.midspeed*2
           

        (self.x,self.y) = move(self.x, self.y, self.speed, self.angle)
        
        if pos_params!=0:
            (self.x,self.y) = pos_params[0]
            pos_params=0
        
        
       

        


    def portrayal_method(self):
        portrayal = {"Shape": "arrowHead", "s": 1, "Filled": "true", "Color": "Red", "Layer": 3, 'x': self.x,
                     'y': self.y, "angle": self.angle}
        return portrayal


class MinedZone(Model):
    collector = DataCollector(
        model_reporters={"Mines": lambda model: len(model.mines),
                         "Danger markers": lambda model: len([m for m in model.markers if
                                                          m.purpose == MarkerPurpose.DANGER]),
                         "Indication markers": lambda model: len([m for m in model.markers if
                                                          m.purpose == MarkerPurpose.INDICATION]),
                         "Mines désamorcées": lambda model: model.mines_desamorcees,
                         "Tours passsés en sables mouvants": lambda model: model.steps_in_quicksand,
                         },
        agent_reporters={})

    def __init__(self, n_robots, n_obstacles, n_quicksand, n_mines, speed):
        Model.__init__(self)
        self.space = mesa.space.ContinuousSpace(600, 600, False)
        self.schedule = RandomActivation(self)
        self.mines = []  # Access list of mines from robot through self.model.mines
        self.markers = []  # Access list of markers from robot through self.model.markers (both read and write)
        self.obstacles = []  # Access list of obstacles from robot through self.model.obstacles
        self.quicksands = []  # Access list of quicksands from robot through self.model.quicksands
        self.mines_desamorcees = 0
        self.steps_in_quicksand = 0
        for _ in range(n_obstacles):
            self.obstacles.append(Obstacle(random.random() * 500, random.random() * 500, 10 + 20 * random.random()))
        for _ in range(n_quicksand):
            self.quicksands.append(Quicksand(random.random() * 500, random.random() * 500, 10 + 20 * random.random()))
        for _ in range(n_robots):
            x, y = random.random() * 500, random.random() * 500
            while [o for o in self.obstacles if np.linalg.norm((o.x - x, o.y - y)) < o.r] or \
                    [o for o in self.quicksands if np.linalg.norm((o.x - x, o.y - y)) < o.r]:
                x, y = random.random() * 500, random.random() * 500
            self.schedule.add(
                Robot(int(uuid.uuid1()), self, x, y, speed,
                      2 * speed, random.random() * 2 * math.pi))
        for _ in range(n_mines):
            x, y = random.random() * 500, random.random() * 500
            while [o for o in self.obstacles if np.linalg.norm((o.x - x, o.y - y)) < o.r] or \
                    [o for o in self.quicksands if np.linalg.norm((o.x - x, o.y - y)) < o.r]:
                x, y = random.random() * 500, random.random() * 500
            self.mines.append(Mine(x, y))
        self.datacollector = self.collector

    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()
        if not self.mines:
            self.running = False


def run_single_server():
    chart = ChartModule([{"Label": "Mines",
                          "Color": "Orange"},
                         {"Label": "Danger markers",
                          "Color": "Red"},
                         {"Label": "Indication markers",
                          "Color": "Green"},
                         {"Label": "Mines désamorcées",
                          "Color": "Blue"},
                         {"Label": "Tours passsés en sables mouvants",
                          "Color": "Black"},
                         ],
                        data_collector_name='datacollector')
    server = ModularServer(MinedZone,
                           [ContinuousCanvas(),
                            chart],
                           "Deminer robots",
                           {"n_robots": UserSettableParameter('slider', "Number of robots", 7, 3,
                                                             15, 1),
                            "n_obstacles": UserSettableParameter('slider', "Number of obstacles", 5, 2, 10, 1),
                            "n_quicksand": UserSettableParameter('slider', "Number of quicksand", 5, 2, 10, 1),
                            "speed": UserSettableParameter('slider', "Robot speed", 15, 5, 40, 5),
                            "n_mines": UserSettableParameter('slider', "Number of mines", 15, 5, 30, 1)})
    server.port = 8521
    server.launch()


if __name__ == "__main__":
    run_single_server()
