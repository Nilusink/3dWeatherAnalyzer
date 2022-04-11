# 3dWeatherAnalyzer
3d Visualization for weather stations using [weatherapi.com](https://www.weatherapi.com) and Ursina.
<br>
## Controls
### View
#### Temperature View: ``t``
Every weather station is represented as a sphere, colored
according to the temperature at its location. Blue means cold
and red means hot.

<br>

#### Wind View: ``w``
Every weather station is represented as an arrow, pointing
in the direction of the wind. The color of the arrow is
relative to the current wind speed, where Blue is 0 km/h
and red is 100 km/h

<br>

### General
#### Search Location: ``enter``
Enter the name or coordinates (seperated with a ",") of your desired      
location. If any data for this location exists in the api's database,     
you will be taken to the newly created point.                             

<br>

#### Select: ``left mouse``
Select one weather station and display it's current weather data.         
Click somewhere with no existing station to deselect.

<br>

#### Bulk-Select: ``shift + left mouse``
The same as above, but you can select multiple locations.                 

<br>

#### Update: ``u``
Updates the weather data on all selected locations.                       
<br>
### Movement
#### Rotate: ``middle mouse + move mouse``
#### Zoom: ``middle mouse wheel``
