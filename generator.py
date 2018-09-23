'''
Get appropriate metadata from apppliances.json
Create a "schedule" i.e. activation time for each room, when and where it is being used <<script>>
Assign a probability value of the room being "wasteful" i.e. devices on when they shouldn't
'''
import numpy as np
import json, re

class Room:

    def __init__(self, name, appliances, prob):
        self.name = name
        self.appliances = appliances
        self.probability = prob
        self.occupied = False
        self.appliances.sort(key=lambda x: x.rank, reverse = True)

    def occupy(self, timestamp):
        self.occupied = True
        for appliance in self.appliances:
            if int(timestamp) in appliance.usage:
                appliance.use()

    def chooseAppliancesToLeaveOn(self):
        onAppliances = [appliance for appliance in self.appliances if appliance.on]
        sumOfRanks = sum([appliance.rank for appliance in onAppliances])
        probabilitizedOnAppliances = []

        for app in onAppliances:
            for i in range(0, sumOfRanks - app.rank + 1):
                probabilitizedOnAppliances.append(app)
        numOfAppsToTurnOff = np.random.randint(0,len(onAppliances))

        while numOfAppsToTurnOff > 0:
            chosenIndex = np.random.randint(1, len(probabilitizedOnAppliances))
            appliance = probabilitizedOnAppliances[chosenIndex]
            appliance.turnOff()
            probabilitizedOnAppliances = [app for app in probabilitizedOnAppliances if app != appliance]
            numOfAppsToTurnOff -= 1


    def leave(self, timestamp):
        prob = self.probability
        var = np.random.rand()
        if var <= prob:
            self.chooseAppliancesToLeaveOn()
        else:
            for appliance in self.appliances:
                appliance.turnOff()
        self.occupied = False

    def __str__(self):
        applianceStrings = [str(app) for app in self.appliances]
        return ("Room name %s with appliances %s" %(self.name, applianceStrings))


class Appliance:

    def __init__(self, name, rank, present, value, usage, duration):
        self.name = name
        self.rank = rank
        self.present = present
        self.value = value
        self.usage = usage
        self.duration = duration
        self.on = False

    def use(self):
        self.on = True

    def turnOff(self):
        self.on = False

    def __str__(self):
        return ("%s with rank %s" %(self.name, self.rank))


def initializeVariables(jsonData):
    listOfRooms = jsonData.get("rooms", None)
    listOfRoomObjects = []
    if listOfRooms is None:
        return None
    for roomName in listOfRooms.keys():
        room = listOfRooms.get(roomName, None)
        probability = room.get("probability", None)
        appliances = room.get("appliances", None)
        listOfApplianceObjects = []
        for applianceName in appliances.keys():
            appliance = appliances.get(applianceName, None)
            rank = appliance.get("rank", 1)
            present = appliance.get("present", None)
            value = appliance.get("value", None)
            usage = appliance.get("usage", None)
            duration = appliance.get("duration", None)
            applianceObject = Appliance(applianceName, rank, present, value, usage, duration)
            listOfApplianceObjects.append(applianceObject)
        roomObject = Room(roomName, listOfApplianceObjects, probability)
        listOfRoomObjects.append(roomObject)
    return listOfRoomObjects

def populate(room, timestamp):
    roomData = [timestamp]
    for appliance in room.appliances:
        roomData.append(appliance.value if appliance.on else 0)
    roomData.append(room.occupied)
    return roomData



def interpret(chunks, room):
    timestamp = float(chunks[0])
    roomName = chunks[1]
    action = chunks[2]
    optionalChunkOffset = 0
    print ('time is ' + str(timestamp))
    print ('action is ' + action)
    if action == 'Occupy':
        room.occupy(timestamp)
        try:
            action = chunks[3]
            optionalChunkOffset = 1
        except IndexError as e:
            action = chunks[2]
    if action == 'Activate':
        applianceName = chunks[3 + optionalChunkOffset]
        appliances = room.appliances
        appliance = None
        for appliance2 in appliances:
            if appliance2.name == applianceName:
                appliance = appliance2
                break
        if appliance == None:
            print ("Undeclared appliance")
            return None
        appliance.use()
    elif action == 'Leave':
        room.leave(timestamp)
    elif action != "Occupy":
        print ("Invalid Operation")
        return None

    return populate(room, timestamp)



def process(code, rooms):
    lines = code.split("\n")[:-1]
    data = []
    for i in [j/2 for j in range(7, 48)]:
        triggeredRooms = []
        currentLines = [line for line in lines if int(float(line.split(' ')[0])) == i]
        for line in currentLines:
            chunks = line.split(' ')
            roomName = chunks[1]
            room = None
            for room2 in rooms:
                if room2.name == roomName:
                    room = room2
                    break
            if room == None:
                print ('Undeclared room')
                return None
            data.append(interpret(chunks, room))
            triggeredRooms.append(room)
        untriggeredRooms = [room for room in rooms if room not in triggeredRooms]
        for room in untriggeredRooms:
            data.append(populate(room, i))
    return data



with open ('appliances.json', 'r') as app:
    data = json.load(app)
    print (json.dumps(data, indent=4, sort_keys=True))
    rooms = initializeVariables(data)

with open ('script', 'r') as script:
    code = script.read()
    val = process(code, rooms)
    for v in val:
        print (v)
