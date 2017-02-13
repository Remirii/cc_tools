import test_data
import sys
import json

#Creates and returns a GameLibrary object(defined in test_data) from loaded json_data
def make_game_library_from_json(json_data):
    #Initialize a new GameLibrary
    game_library = test_data.GameLibrary()
    json_data = open("data/test_data.json").read()
    parsed_json = json.loads(json_data)
    for game in parsed_json:
        addedPlatform = test_data.Platform(parsed_json[game]["Platform"][1]['name'], 
                                           parsed_json[game]["Platform"][0]['launch year'])
        addedGame = test_data.Game(parsed_json[game]["title"], addedPlatform, parsed_json[game]["Year"])
        game_library.add_game(addedGame)

    #Loop through the json_data
        #Create a new Game object from the json_data by reading
        #  title
        #  year
        #  platform (which requires reading name and launch_year)
        #Add that Game object to the game_library
    #Return the completed game_library

    return game_library

# Handling command line arguments
#  Note: sys.argv is a list of strings that contains each command line argument
#        The first element in the list is always the name of the python file being run
# Command line format: <input json filename>

default_input_json_file = "data/test_data.json"

if len(sys.argv) == 2:
    input_json_file = sys.argv[1]
    print("Using command line args:", input_json_file)
else:
    print("Unknown command line options. Using default values:", default_input_json_file)
    input_json_file = default_input_json_file

library = make_game_library_from_json(default_input_json_file)

test_data.print_game_library(library)

#Load the json data from the input file
#Use make_game_library_from_json(json_data) to convert the data to GameLibrary data
#Print out the resulting GameLibrary data using print_game_library(game_library_data) in test_data.py
