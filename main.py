"""
main.py
Main program, runs the 3d simulations

Author:
Nilusink
"""

###############################################################################################
#                                                                                             #
#     Controls                                                                                #
#       General                                                                               #
#           Search Location:    [enter]                                                       #
#                   Enter the name or coordinates (seperated with a ",") of your desired      #
#                   location. If any data for this location exists in the api's database,     #
#                   you will be taken to the newly created point.                             #
#                                                                                             #
#           Select:     [left mouse]                                                          #
#                   Select one weather station and display it's current weather data.         #
#                   Click somewhere with no existing station to deselect.                     #
#                                                                                             #
#           Bulk-Select: [shift + left mouse]                                                 #
#                   The same as above, but you can select multiple locations.                 #
#                                                                                             #
#           Update:     [u]                                                                   #
#                   Updates the weather data on all selected locations.                       #
#                                                                                             #
#       Movement                                                                              #
#           Rotate: [middle mouse + move mouse]                                               #
#           Zoom:   [middle mouse wheel]                                                      #
#                                                                                             #
###############################################################################################
from random import randint
from classes import *
from ursina import *
import string
import sys
import os

# ursina text init
Text.default_resolution = 1080 * Text.size

# defaults
TOTAL_POINTS: int = 0
MAX_POINTS: int = 1_000
RUNNING: bool = True


def request_structural() -> None:
    """
    requests station data every 10 degrees (lat & long)
    """
    global TOTAL_POINTS
    max_num = 36 * 18
    TOTAL_POINTS += max_num
    for x in range(-90, 90, 10):
        for y in range(-180, 180, 10):
            request_lat_long(x + randint(0, 1000) / 100, y + randint(0, 1000) / 100)

            if not RUNNING:
                return


def request_random() -> None:
    """
    randomly request weather data across the globe
    """
    global TOTAL_POINTS
    while RUNNING:
        request_lat_long(randint(-90000, 90000) / 1000, randint(-180000, 180000) / 1000)
        TOTAL_POINTS += 1
        if TOTAL_POINTS >= MAX_POINTS:
            return


class Window(Ursina):
    def __init__(self) -> None:
        super().__init__()
        self.cam = EditorCamera()

        self.__loaded = False
        self.typing_field_shown: bool = False
        self.selection = Selection()
        self.last_time: dict = deepcopy(held_keys)

        self.__fullscreen = True

        # configure window
        window.title = 'Weather'
        window.borderless = True
        window.fullscreen = self.fullscreen
        window.exit_button.visible = False
        window.fps_counter.enabled = True
        window.color = (0, 0, 0, 0)

        # info text
        self.info_text = Text(text="", origin=(0, 0), position=(-0.65, 0.29), background=True)
        self.clear_text()

        # typing box
        self.typing_text = Text(text="", origin=(0, 0), position=(0, 0), backgroud=False)

        # place objects
        # 3d world
        Entity(model=load_model("assets/smooth_sphere.obj"), texture="assets/globe_texture.jpg",
               scale=10, position=(0, 0, 0), rotation=(0, 180, 0))

        # set camera position
        camera.x = 0
        camera.y = 0
        camera.z = 0

        # "controls" label
        self.controls_label_shown: bool = True
        self.controls_label = Text(text="", origin=(0, 0), position=(0.65, 0.25), background=True)
        self.controls_label_text = dedent(f"""
        <scale:1.5><orange>Controls</><default><scale:1.0>
        (De)select Station: <orange>Mouse-Left</><default>
        Search Station: <orange>Enter</><default>

        <orange>View</><default>
        Move View: <orange>Mouse-Right</><default>
        Show Temperature: <orange>T</><default>
        Show Wind: <orange>W</><default>
        Toggle Airplanes: <orange>P</><default>
        Hide Weather Stations: <orange>E</><default>
        Hide All: <orange>A</><default>
        Hide this Window: <orange>H</><default>

        Exit: <orange>Escape</><default>
        """)
        self.controls_label.text = self.controls_label_text
        self.controls_label.create_background()

        self.flight_handler: FlightHandler = ...

    @property
    def fullscreen(self) -> bool:
        return self.__fullscreen

    @fullscreen.setter
    def fullscreen(self, value: bool) -> None:
        self.__fullscreen = value
        window.fullscreen = value

    def update(self):
        """
                Ursina update function
                """
        global RUNNING
        if not self.__loaded:
            # generate weather points
            Thread(target=request_structural).start()
            for _ in range(5):
                Thread(target=request_random).start()

            # generate airplanes
            self.flight_handler = FlightHandler()
            self.__loaded = True

        if not self.selection:
            self.clear_text()

        if issubclass(type(self.selection[0]), Airplane):
            self.update_airplane_text(self.selection[0])

        if mouse.left:
            now_point = mouse.hovered_entity
            if now_point:
                if issubclass(type(now_point), WeatherPoint):
                    self.update_text(now_point.station_data)
                    self.selection.add(now_point) if held_keys["shift"] else self.selection.set([now_point])

                elif issubclass(type(now_point), Airplane):
                    self.update_airplane_text(now_point)
                    self.selection.add(now_point) if held_keys["shift"] else self.selection.set([now_point])

            else:
                self.selection.clear()

        if not self.typing_field_shown:
            if held_keys["escape"]:
                RUNNING = False
                self.end()
                sys.exit(0)

            if held_keys["enter"] and not self.last_time["enter"]:
                self.open_typing()

            if held_keys["u"]:
                for point in self.selection:
                    Thread(target=point.update_data).start()

            if held_keys["t"] and not held_keys["w"]:
                POINT_COLLECTOR.show_temperature()

            elif held_keys["w"] and not held_keys["t"]:
                POINT_COLLECTOR.show_wind()

            if held_keys["f11"] and not self.last_time["f11"]:
                self.fullscreen = not self.fullscreen
                print(f"{self.fullscreen=}")

            if held_keys["h"] and not self.last_time["h"]:
                self.controls_label_shown = not self.controls_label_shown
                self.controls_label.background = self.controls_label_shown
                self.controls_label.text = self.controls_label_text if self.controls_label_shown else ""
                if self.controls_label_shown:
                    self.controls_label.create_background()

            if held_keys["p"] and not self.last_time["p"]:
                self.flight_handler.show = not self.flight_handler.show

            if held_keys["e"] and not self.last_time["e"]:
                POINT_COLLECTOR.hide()

            if held_keys["a"] and not self.last_time["a"]:
                self.flight_handler.show = False
                POINT_COLLECTOR.hide()

        else:
            if held_keys["enter"] and not self.last_time["enter"]:
                self.close_typing()

            else:
                self.handle_typing()

        self.last_time = deepcopy(held_keys)

    def open_typing(self) -> None:
        """
        show the "Entry" window
        """
        self.typing_field_shown = True
        self.typing_text.background = True

    def close_typing(self) -> None:
        """
        remove the "Entry" from the screen
        :return: the content of the typing field
        """
        self.typing_field_shown = False
        self.typing_text.background = False

        tmp, self.typing_text.text = self.typing_text.text, ""

        obj = request_name(tmp)
        if obj is None:
            return

        self.selection.set([obj])
        self.update_text(obj.station_data)

        w_data = obj.station_data

        lat, lon = w_data["location"]["lat"], w_data["location"]["lon"]
        self.set_camera(lat, lon, 1)

    def handle_typing(self) -> None:
        """
        periodically called by the update function if a typing window is opened
        used to "write"
        """
        if held_keys["shift"]:
            for character in string.printable+"öäü":
                if self.check_if_new(character):
                    self.typing_text.text += character.upper()

        else:
            for character in string.printable+"öäü":
                if self.check_if_new(character):
                    self.typing_text.text += character

        if self.check_if_new("space"):
            self.typing_text.text += " "

        if self.check_if_new("backspace"):
            self.typing_text.text = self.typing_text.text[:-1]

        self.typing_text.create_background()

    def check_if_new(self, character: str) -> bool:
        """
        check if a character is newly pressed
        """
        return held_keys[character] and not self.last_time[character]

    def update_text(self, station_data: dict) -> None:
        """"
        update the info box text (weather stations)
        """
        self.info_text.position = (-0.67, 0.29)
        wind_dir = station_data['current']['wind_degree']+180
        while wind_dir > 360:
            wind_dir -= 360
        while wind_dir < 0:
            wind_dir += 360

        cond = station_data['current']['condition']['text']

        if not os.path.exists(f"./icons/{cond}.png"):
            img = requests.get(f"http:{station_data['current']['condition']['icon']}")
            if img.status_code == 200:
                if not os.path.exists("./icons"):
                    os.mkdir("./icons")

                with open(f"./icons/{cond}.png", "wb") as out:
                    img.raw.decode_content = True
                    out.write(img.content)

        # decide which color to display the current temperature in
        temperature = station_data['current']['temp_c']
        temp_col: str = "green"
        if temperature < 0:
            temp_col = "blue"

        elif temperature > 20:
            temp_col = "red"

        t = dedent(f"""
        Station: <orange>{station_data['location']['name']}</><default>
        <scale:0.8>Country: <orange>{station_data['location']['country']}<default>

        <image:./icons/{cond}.png></>    {cond}        
        
        Temperature: <{temp_col}>{station_data['current']['temp_c']}<default>°C<default>
        Humidity: <gray>{station_data['current']['humidity']} %<default>
        Pressure: <gray>{station_data['current']['pressure_mb']} mb<default>
        Wind direction: <gray>{wind_dir}°<default>
        Wind speed: <gray>{station_data['current']['wind_kph']} km/h<default>
        Local Time: <gray>{station_data['location']['localtime']}<default>
        Last update: <gray>{round(time.time()-station_data['current']['last_updated_epoch'], 0)}s ago<default>
        """).strip()
        self.info_text.text = t
        self.info_text.create_background()

    def update_airplane_text(self, plane: Airplane) -> None:
        """"
        update the info box text (airplanes)
        """
        self.info_text.position = (-.60, .12)

        if plane.origin_airport is not ...:
            origin_airport_name = plane.origin_airport["name"]
            origin_airport_country = plane.origin_airport["position"]["country"]["name"]
            origin_airport_country = f"( {origin_airport_country} )"

        else:
            origin_airport_name = plane.flight.origin_airport_iata
            origin_airport_country = ""

        if plane.destination_airport is not ...:
            destination_airport_name = plane.destination_airport["name"]
            destination_airport_country = plane.destination_airport["position"]["country"]["name"]
            destination_airport_country = f"( {destination_airport_country} )"

        else:
            destination_airport_name = plane.flight.destination_airport_iata
            destination_airport_country = ""

        lat = f"{abs(plane.flight.latitude)}° {'E' if plane.flight.latitude >= 0 else 'W'}"
        lon = f"{abs(plane.flight.longitude)}° {'N' if plane.flight.longitude >= 0 else 'S'}"

        # to always get the same background
        t = dedent(f"""
        Flight: <orange><default>
        <scale:0.8>Airline: <orange><default>

        <scale:0.8>from:
        ……………………………………………………………………
        <scale:0.8>to:


        <orange>Speed<default>
        on ground:
        ground speed:
        vertical speed:

        <orange>Position<default>
        lat: <gray>{lat}<default>
        lon: <gray>{lon}<default>
        altitude:
        heading:

        <orange>Flight<default>
        callsign:
        SQUAWK code:

        <orange>Airplane<default>
        aircraft code:
        registration:
        """).strip()
        self.info_text.text = t
        self.info_text.create_background()

        # actual text editing
        t = dedent(f"""
        Flight: <orange>{plane.flight.icao_24bit}<default>
        <scale:0.8>Airline: <orange>{plane.airline['Name']}<default>

        <scale:0.8>from:
        <scale:0.6>{origin_airport_name} {origin_airport_country}
        <scale:0.8>to:
        <scale:0.6>{destination_airport_name} {destination_airport_country}<scale:1.0>

        <orange>Speed<default>
        on ground: {'<green>yes' if plane.flight.on_ground else '<red>no'}<default>
        ground speed: <gray>{plane.flight.get_ground_speed()}<default>
        vertical speed: <gray>{plane.flight.get_vertical_speed()}<default>

        <orange>Position<default>
        lat: <gray>{lat}<default>
        lon: <gray>{lon}<default>
        altitude: <gray>{plane.flight.get_altitude()}<default>
        heading: <gray>{plane.flight.get_heading()}<default>
        
        <orange>Flight<default>
        callsign: <gray>{plane.flight.callsign}<default>
        SQUAWK code: {'<gray>' if plane.flight.squawk == 'N/A' else '<red>'}{plane.flight.squawk}<default>
        
        <orange>Airplane<default>
        aircraft code: <gray>{plane.flight.aircraft_code}<default>
        registration: <gray>{plane.flight.registration}<default>
        """).strip()
        self.info_text.text = t

    def clear_text(self) -> None:
        """
        clear the info box text
        """
        self.info_text.position = (-0.8, 0.42)
        t = dedent("""
        Selected: <orange>nAn</><default>
        """).strip()
        self.info_text.text = t
        self.info_text.create_background()

    def set_camera(self, latitude: float, longitude: float, animation_time: float) -> None:
        """
        focus the camera on lat / lon
        """
        self.cam.position = (0, 0, 0)

        rot = (
            latitude,
            -90 - longitude,
            0
        )
        self.cam.animate_rotation(rot, duration=animation_time)

    def end(self) -> None:
        print(f"closing...")
        self.flight_handler.end()
        print(f"shutdown threads")
        sys.exit(0)


if __name__ == '__main__':
    def update() -> None:
        """
        ursina bound function
        """
        w.update()

    w = Window()
    w.run()

    RUNNING = False
