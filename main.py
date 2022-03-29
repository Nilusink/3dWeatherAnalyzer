"""
main.py
Main program, runs the 3d simulations

Author:
Nilusink
"""
from threading import Thread
from random import randint
from classes import *
from ursina import *
import string


# ursina text init
Text.default_resolution = 1080 * Text.size

TOTAL_POINTS: int = 0
MAX_POINTS: int = 5000
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

        # configure window
        window.title = 'Weather'
        window.borderless = True
        window.fullscreen = True
        window.exit_button.visible = False
        window.fps_counter.enabled = True
        window.color = (0, 0, 0, 0)

        # info text
        self.info_text = Text(text="", origin=(0, 0), position=(-0.65, 0.37), background=True)
        self.clear_text()

        # typing box
        self.typing_text = Text(text="", origin=(0, 0), position=(0, 0), backgroud=False)

        # place objects
        # lighting
        # pivot = Entity()
        # DirectionalLight(parent=pivot, y=2, z=3, shadows=True, rotation=(45, -45, 45))

        # 3d world
        Entity(model=load_model("assets/smooth_sphere.obj"), texture="assets/globe_texture.jpg",
               scale=10, position=(0, 0, 0), rotation=(0, 180, 0))

        # set camera position
        camera.x = 0
        camera.y = 0
        camera.z = 0

    def update(self):
        """
                Ursina update function
                """
        if not self.__loaded:
            Thread(target=request_structural).start()
            for _ in range(5):
                Thread(target=request_random).start()
            # for i in range(-90, 90, 10):
            #     draw_at(i, 0, use_original=True)
            #     draw_at(i, 90, use_original=True)
            self.__loaded = True

        if not self.selection:
            self.clear_text()

        if mouse.left:
            now_point = mouse.hovered_entity
            if now_point:
                now_point: WeatherPoint
                self.update_text(now_point.station_data)
                self.selection.add(now_point) if held_keys["shift"] else self.selection.set([now_point])

            else:
                self.selection.clear()

        if not self.typing_field_shown:
            if held_keys["enter"] and not self.last_time["enter"]:
                self.open_typing()

            if held_keys["u"]:
                for point in self.selection:
                    Thread(target=point.update_data).start()

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
            for character in string.ascii_lowercase:
                if self.check_if_new(character):
                    self.typing_text.text += character.upper()

        else:
            for character in string.printable:
                if self.check_if_new(character):
                    self.typing_text.text += character

        if self.check_if_new("space"):
            self.typing_text.text += " "

        if self.check_if_new("backspace"):
            self.typing_text.text = self.typing_text.text[:-1]

        self.typing_text.create_background()

    def check_if_new(self, character: str) -> bool:
        return held_keys[character] and not self.last_time[character]

    def update_text(self, station_data: dict) -> None:
        """"
        update the info box text
        """
        t = dedent(f"""
Station: <orange>{station_data['location']['name']}</><default>
Country: {station_data['location']['country']}
Temperature: {station_data['current']['temp_c']}°C
Humidity: {station_data['current']['humidity']} %
Pressure: {station_data['current']['pressure_mb']} mb
Local Time: {station_data['location']['localtime']}
    """).strip()
        self.info_text.text = t
        self.info_text.create_background()

    def clear_text(self) -> None:
        """
        clear the info box text
        """
        t = dedent("""
Station: <orange>nAn</><default>
        """).strip()
        self.info_text.text = t
        self.info_text.create_background()

    def set_camera(self, latitude: float, longitude: float, animation_time: float) -> None:
        """
        focus the camera on lat / lon at a given distance
        """
        self.cam.position = (0, 0, 0)

        rot = (
            latitude,
            -90 - longitude,
            0
        )
        # self.cam.animate_position(pos, duration=animation_time)
        self.cam.animate_rotation(rot, duration=animation_time)


if __name__ == '__main__':
    def update() -> None:
        w.update()

    w = Window()
    w.run()

    RUNNING = False
