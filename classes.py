"""
classes.py
Defines functions and classes used in main.py

Author:
Nilusink
"""
from ursina import *
import typing as tp
import numpy as np
import requests
import json


PI: float = 3.14159265358979323846264338327950288419701

# API key for weatherapi.com
API_KEY: str = "5c5d3dcedeb54d45999185155222303"

# color defaults
# temperature
T_MIN_VAL: int = -60
T_OPT_VAL: int = 10
T_MAX_VAL: int = 40

T_MIN_COL: tp.Tuple[int, int, int] = (0, 0, 1)
T_OPT_COL: tp.Tuple[int, int, int] = (0, 1, 0)
T_MAX_COL: tp.Tuple[int, int, int] = (1, 0, 0)

# wind
W_MIN_VAL: int = 0
W_OPT_VAL: int = 50
W_MAX_VAL: int = 100

W_MIN_COL: tp.Tuple[int, int, int] = (0, 0, 1)
W_OPT_COL: tp.Tuple[int, int, int] = (1, 0, 1)
W_MAX_COL: tp.Tuple[int, int, int] = (1, 0, 0)

# models
ARROW_MODEL = "assets/arrow.obj"
SMOOTH_SPHERE = "assets/smooth_sphere.obj"
SPHERE = "sphere"


def float_map(x: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """
    like Arduino's map, but, well, in python
    """
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


class Vector3D:
    """
    Simple 3D vector class
    """
    x: float
    y: float
    z: float
    angle_xy: float
    angle_xz: float
    length_xy: float
    length: float

    def __init__(self):
        self.__x: float = 0
        self.__y: float = 0
        self.__z: float = 0
        self.__angle_xy: float = 0
        self.__angle_xz: float = 0
        self.__length_xy: float = 0
        self.__length: float = 0

    @property
    def x(self) -> float:
        return self.__x

    @x.setter
    def x(self, value: float) -> None:
        self.__x = value
        self.__update("c")

    @property
    def y(self) -> float:
        return self.__y

    @y.setter
    def y(self, value: float) -> None:
        self.__y = value
        self.__update("c")

    @property
    def z(self) -> float:
        return self.__z

    @z.setter
    def z(self, value: float) -> None:
        self.__z = value
        self.__update("c")

    @property
    def cartesian(self) -> tp.Tuple[float, float, float]:
        """
        :return: x, y, z
        """
        return self.x, self.y, self.z

    @cartesian.setter
    def cartesian(self, value: tp.Tuple[float, float, float]) -> None:
        """
        :param value: (x, y, z)
        """
        self.__x, self.__y, self.__z = value
        self.__update("c")

    @property
    def angle_xy(self) -> float:
        return self.__angle_xy

    @angle_xy.setter
    def angle_xy(self, value: float) -> None:
        self.__angle_xy = self.normalize_angle(value)
        self.__update("p")

    @property
    def angle_xz(self) -> float:
        return self.__angle_xz

    @angle_xz.setter
    def angle_xz(self, value: float) -> None:
        self.__angle_xz = self.normalize_angle(value)
        self.__update("p")

    @property
    def length_xy(self) -> float:
        """
        can't be set
        """
        return self.__length_xy

    @property
    def length(self) -> float:
        return self.__length

    @length.setter
    def length(self, value: float) -> None:
        self.__length = value
        self.__update("p")

    @property
    def polar(self) -> tp.Tuple[float, float, float]:
        """
        :return: angle_xy, angle_xz, length
        """
        return self.angle_xy, self.angle_xz, self.length

    @polar.setter
    def polar(self, value: tp.Tuple[float, float, float]) -> None:
        """
        :param value: (angle_xy, angle_xz, length)
        """
        self.__angle_xy = self.normalize_angle(value[0])
        self.__angle_xz = self.normalize_angle(value[1])
        self.__length = value[2]
        self.__update("p")

    @staticmethod
    def from_polar(angle_xy: float, angle_xz: float, length: float) -> "Vector3D":
        """
        create a Vector3D from polar form
        """
        v = Vector3D()
        v.polar = angle_xy, angle_xz, length
        return v

    @staticmethod
    def from_cartesian(x: float, y: float, z: float) -> "Vector3D":
        """
        create a Vector3D from cartesian form
        """
        v = Vector3D()
        v.cartesian = x, y, z
        return v

    @staticmethod
    def calculate_with_angles(length: float, angle1: float, angle2: float) -> tp.Tuple[float, float, float]:
        """
        calculate the x, y and z components of length facing (angle1, angle2)
        """
        tmp = np.cos(angle2) * length
        z = np.sin(angle2) * length
        x = np.cos(angle1) * tmp
        y = np.sin(angle1) * tmp

        return x, y, z

    @staticmethod
    def normalize_angle(angle: float) -> float:
        """
        removes "overflow" from an angle
        """
        while angle > 2 * PI:
            angle -= 2 * PI

        while angle < 0:
            angle += 2 * PI

        return angle

    # maths
    def __neg__(self) -> "Vector3D":
        self.cartesian = [-el for el in self.cartesian]
        return self

    def __add__(self, other) -> "Vector3D":
        if type(other) == Vector3D:
            return Vector3D.from_cartesian(x=self.x + other.x, y=self.y + other.y, z=self.z + other.z)

        return Vector3D.from_cartesian(x=self.x + other, y=self.y + other, z=self.z + other)

    def __sub__(self, other) -> "Vector3D":
        if type(other) == Vector3D:
            return Vector3D.from_cartesian(x=self.x - other.x, y=self.y - other.y, z=self.z - other.z)

        return Vector3D.from_cartesian(x=self.x - other, y=self.y - other, z=self.z - other)

    def __mul__(self, other) -> "Vector3D":
        if type(other) == Vector3D:
            return Vector3D.from_polar(angle_xy=self.angle_xy + other.angle_xy, angle_xz=self.angle_xz + other.angle_xz, length=self.length * other.length)

        return Vector3D.from_cartesian(x=self.x * other, y=self.y * other, z=self.z * other)

    def __truediv__(self, other) -> "Vector3D":
        return Vector3D.from_cartesian(x=self.x / other, y=self.y / other, z=self.z / other)

    # internal functions
    def __update(self, calc_from: str) -> None:
        match calc_from:
            case "p":
                self.__length_xy = np.cos(self.angle_xz) * self.length
                x, y, z = self.calculate_with_angles(self.length, self.angle_xy, self.angle_xz)
                self.__x = x
                self.__y = y
                self.__z = z

            case "c":
                self.__length_xy = np.sqrt(self.y**2 + self.x**2)
                self.__angle_xy = np.arctan2(self.y, self.x)
                self.__angle_xz = np.arctan2(self.z, self.x)
                self.__length = np.sqrt(self.x**2 + self.y**2 + self.z**2)

    def __repr__(self) -> str:
        return f"<\n" \
               f"\tVector3D:\n" \
               f"\tx:{self.x}\ty:{self.y}\tz:{self.z}\n" \
               f"\tangle_xy:{self.angle_xy}\tangle_xz:{self.__angle_xz}\tlength:{self.length}\n" \
               f">"


class PointCollector:
    instance: "PointCollector" = ...

    def __new__(cls, *args, **kwargs) -> "PointCollector":
        if cls.instance is not ...:
            return cls.instance

        cls.instance = super(PointCollector, cls).__new__(cls)
        return cls.instance

    def __init__(self) -> None:
        self.__points: tp.List["WeatherPoint"] = []

        self.__dp = "t"

    @property
    def points(self) -> tp.List["WeatherPoint"]:
        return self.__points.copy()

    @property
    def dp(self) -> str:
        """
        returns the currently used datapoint
        """
        return self.__dp

    def append(self, point: "WeatherPoint") -> None:
        """
        append a weather point to the array
        """
        self.__points.append(point)

    def update_data(self) -> None:
        """
        update the data of all weather stations
        """
        for point in self.__points:
            point.update_data()

    def show_temperature(self) -> None:
        """
        change all points to show temperature data
        """
        for point in self.__points:
            point.show_temperature()

        self.__dp = "t"

    def show_wind(self) -> None:
        """
        change all points to show wind data
        """
        for point in self.__points:
            point.show_wind()

        self.__dp = "w"


# point collector instance
POINT_COLLECTOR = PointCollector()


class WeatherPoint(Entity):
    """
    An Entity with weather data mapped to it
    """
    def __init__(self, station_data: dict, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.station_data = station_data

        match POINT_COLLECTOR.dp:
            case "t":
                self.show_temperature()

            case "w":
                self.show_wind()

        POINT_COLLECTOR.append(self)

    def update_data(self) -> None:
        """
        update the weather data for the current point
        """
        self.station_data = json.loads(requests.get(
            f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q="
            f"{self.station_data['location']['lat']},{self.station_data['location']['lon']}&aqi=no"
        ).content)

    def show_temperature(self) -> None:
        """
        show temperature data
        """
        self.color = list(three_color_mapper(
            T_MIN_VAL, T_MAX_VAL, T_OPT_VAL,
            self.station_data["current"]["temp_c"],
            T_MIN_COL, T_OPT_COL, T_MAX_COL
        )) + [1]
        self.model = SPHERE

    def show_wind(self) -> None:
        """
        show wind data
        """
        self.color = list(three_color_mapper(
            W_MIN_VAL, W_MAX_VAL, W_OPT_VAL,
            self.station_data["current"]["temp_c"],
            W_MIN_COL, W_OPT_COL, W_MAX_COL
        )) + [1]
        self.model = load_model(ARROW_MODEL, use_deepcopy=True)


class Selection:
    """
    Handles all selected objects
    """
    def __init__(self) -> None:
        self.__objs: tp.List[WeatherPoint] = []
        self.__colors: list = []

    def set(self, objects: tp.List[WeatherPoint]) -> None:
        """
        set the selection to a given array of Weahter Points
        """
        self.clear()
        for point in objects:
            self.add(point)

    def add(self, obj: WeatherPoint) -> None:
        """
        adds a Weather Point to the selection
        """
        if obj not in self.__objs:
            self.__objs.append(obj)
            self.__colors.append(obj.color)
            obj.color = (1, 1, 1, 1)

    def clear(self) -> None:
        """
        removes all Points from the selection and resets their color
        :return:
        """
        for point, c in zip(self.__objs, self.__colors):
            point.color = c

        self.__colors, self.__objs = [], []

    def __iter__(self) -> tp.Iterator[WeatherPoint]:
        for obj in self.__objs:
            yield obj

    def __bool__(self) -> bool:
        return not not self.__objs


def request_name(name: str) -> WeatherPoint | None:
    """
    request weather data at {name}
    and draw a sphere at the location
    with the color corresponding to
    the temperature
    """
    try:
        now_d = json.loads(requests.get(
            f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={name}&aqi=no"
        ).content)

    except json.decoder.JSONDecodeError:
        return

    return draw_lat_long(
        now_d,
        now_d["location"]["lat"],
        now_d["location"]["lon"],
        origin_radius=5,
        heading=now_d["current"]["wind_degree"]
    )


def request_lat_long(lat: float, long: float, use_original: bool = False) -> WeatherPoint | None:
    """
    request weather data at lat/long
    and draw a sphere at the location
    with the color corresponding to
    the temperature
    """
    try:
        now_d = json.loads(requests.get(
            f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={lat},{long}&aqi=no"
        ).content)

    except json.decoder.JSONDecodeError:
        return

    return draw_lat_long(
        now_d,
        lat if use_original else now_d["location"]["lat"],
        long if use_original else now_d["location"]["lon"],
        origin_radius=5,
        heading=now_d["current"]["wind_degree"]
    )


def draw_lat_long(data: dict, latitude: float, longitude: float, radius: float = 0.088,
                  origin_radius: float = 1, heading: float = 0) -> WeatherPoint:
    """
    draw a sphere at the given latitude and longitude
    """
    should = Vector3D.from_polar(angle_xy=longitude*(PI/180), angle_xz=latitude*(PI/180), length=origin_radius+.01)

    rot = (
        latitude,
        -90 - longitude,
        heading + 180
    )

    return WeatherPoint(
        station_data=data, model="sphere", collider="sphere", scale=radius,
        position=(should.x, should.z, should.y), rotation=rot, origin=(0, 0, 0)
    )


def three_color_mapper(min_value: float, max_value: float, optimal_value: float, now_value: float,
                       min_color: tuple, optimal_color: tuple, max_color: tuple) -> tp.Tuple[float, float, float]:
    """
    calculate color spectrum

    :return: (r, g, b)
    """
    # calculation for optimal value
    optimal_color = np.array(optimal_color) * float_map(abs(now_value - optimal_value), 0, (max_value - optimal_value), 1, 0)

    # calculation for maximal value
    max_color = np.array(max_color) * (0.0 if (now_value < optimal_value) else (1 if (now_value > max_value) else float_map(now_value, optimal_value, max_value, 0, 1)))

    # calculation for minimal value
    min_color = np.array(min_color) * (0.0 if (now_value > optimal_value) else (1 if (now_value < min_value) else float_map(now_value, min_value, optimal_value, 1, 0)))

    out = min_color + optimal_color + max_color

    return out[0], out[1], out[2]
