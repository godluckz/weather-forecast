import requests, json, sys
from os import path, environ
from class_datetime_utils import DateTimeUtility


W_CURR_DIR   = path.dirname(__file__)
                
class OpenWeatherApi:
    def __init__(self, p_latitude: float, p_longitude: float, p_forecast_records = 4) -> None:
        self._ICONS_PATH = f"{W_CURR_DIR}/icons/"
        self._BASE_URL   = "https://api.openweathermap.org/data/2.5"

        self.date_time_utils = DateTimeUtility()        
        self.api_key = environ.get("OPW_API_KEY")
        self.latitude  : float = p_latitude
        self.longitude : float = p_longitude
        self.units     : str = "metric"
        self.forecast_records : int = p_forecast_records
        self.weather_summary : json = {}       
        self.weather_forecast: json = {}
        self.current_weather : json = {}
        if self.api_key:                                
            self.weather_forecast = self.get_weather_forecast()
            self.current_weather  = self.get_current_weather()         
        else:
            print("Missing API KEY")



    def get_sunrise_sunset(self, p_weather_data: json, p_data_name : str):
        w_sunrise_time  = None
        w_sunset_time   = None
        
        try:
            w_suntimes  = p_weather_data[p_data_name]      

            w_sunrise_unix_time = w_suntimes["sunrise"]
            w_sunset_unix_time  = w_suntimes["sunset"]

            w_sunrise_time = self.date_time_utils.get_datetime_from_unix_code(p_unix_code = w_sunrise_unix_time,
                                                                              p_format    = "%H:%M")
            w_sunset_time  = self.date_time_utils.get_datetime_from_unix_code(p_unix_code = w_sunset_unix_time,
                                                                              p_format    = "%H:%M")            
        except Exception as e:
            # print(f"No, Sunrise and Sunset detail: {e}")
            pass

        return w_sunrise_time, w_sunset_time


    
    def get_weather_details(self, p_data: json, p_sunrise_time: str, p_sunset_time: str) -> json:
        # print(json.dumps(p_data,indent=4))
        w_weather_data: json = p_data["weather"]            
        
        #--TOP DET--#
        try:
            w_weather_date   : json   = p_data["dt_txt"]
        except Exception as e: 
            w_weather_date_unix: int  = p_data["dt"]            
            w_weather_date     : str  = self.date_time_utils.get_datetime_from_unix_code(p_unix_code = w_weather_date_unix)            
        #--TOP DET--#
        
        w_weather_id          = w_weather_data[0]["id"]        
        w_weather_description = w_weather_data[0]["description"]
        w_weather_icon_code   = w_weather_data[0]["icon"]          
         
        #--MAIN--#
        w_weather_main        = p_data["main"]        
        w_weather_temp        = w_weather_main["temp"]
        w_weather_feels_like  = w_weather_main["feels_like"]        
        w_weather_temp_min    = w_weather_main["temp_min"]
        w_weather_temp_max    = w_weather_main["temp_max"]
        w_weather_humidity    = w_weather_main["humidity"]        
        #--MAIN--#
        
        #--WIND--#
        w_weather_wind        = p_data["wind"]        
        # print(w_weather_wind)
        w_weather_wind_speed  = w_weather_wind["speed"]
        w_weather_wind_deg    = w_weather_wind["deg"]  
        try:      
            w_weather_wind_gust   = w_weather_wind["gust"]  
        except Exception as e:
            # print("Gust details missing")
            w_weather_wind_gust = None                    
        #--WIND--#               
    
        
        #----------------#
        #Get weather icon
        #----------------#                
        W_ICON_URL = f"https://openweathermap.org/img/wn/{w_weather_icon_code}@2x.png"
        w_icon_response = requests.get(url=W_ICON_URL)
        w_icon_response.raise_for_status()

        with open(f"{self._ICONS_PATH}{w_weather_icon_code}.png", "wb") as file:
            file.write(w_icon_response.content)

        
        #------------------------#
        #Check sunrise and Sunset
        #------------------------#        
        if p_sunrise_time and p_sunset_time:        
            w_sunrise_time = p_sunrise_time    
            w_sunset_time  = p_sunset_time
        else:
            print(f"==>> Extract sunrise and sunset for {w_weather_date}.")
            w_sunrise_time,w_sunset_time = self.get_sunrise_sunset(p_weather_data = p_data, 
                                                                   p_data_name    = "sys")
            

        
        w_weather_summary: json = {            
            "weather_date" : w_weather_date,
            "weather_id"   : w_weather_id,                
            "data":{            
                "weather_description": w_weather_description,
                "temperature"        : w_weather_temp,        
                "temperature_min"    : w_weather_temp_min,
                "temperature_max"    : w_weather_temp_max,
                "feels_like"         : w_weather_feels_like,        
                "humidity"           : w_weather_humidity,                        
                "wind_speed"         : w_weather_wind_speed,
                "wind_deg"           : w_weather_wind_deg,
                "wind_gust"          : w_weather_wind_gust,                                
                "sunrise"            : w_sunrise_time, 
                "sunset"             : w_sunset_time,
                "icon_code"          : w_weather_icon_code,
                "icon_path"          : W_ICON_URL
                }
        }         
        
        return w_weather_summary
        
            

    def get_weather_data(self, p_url: str, p_params: json):

        w_response = requests.get(url=p_url,params=p_params)
        if w_response.status_code == 401:
            print(f"Unauthorized for url: {p_url}")
            return None
        w_response.raise_for_status()
        w_weather_data: json = w_response.json()        
        
        return w_weather_data
            
        
    def get_weather_forecast(self) -> json:            
        W_FORECAST_URL = f"{self._BASE_URL}/forecast" #5 Day / 3 Hour Forecast    
        # W_FORECAST_URL = f"{W_FORECAST_URL}/daily" #Paying service
        # f'http://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&appid={api_key}&exclude=current,minutely,hourly,daily'

        W_PARAMETERS = {
            "lat"  : self.latitude,
            "lon"  : self.longitude,
            "appid": self.api_key,
            "units": self.units,
            "cnt"  : self.forecast_records #To limit number of timestamps in the API response please setup cnt. Used for W_5_DAYS_FORECAST
        }

        w_weather_data: json = self.get_weather_data(p_url    = W_FORECAST_URL, 
                                                     p_params = W_PARAMETERS)
        return w_weather_data

        
    def get_current_weather(self) -> json:
        W_CURRENT_WEATHER_URL = f"{self._BASE_URL}/weather"
        W_PARAMETERS = {
            "lat"   :self.latitude,
            "lon"   :self.longitude,
            "appid" :self.api_key,
            "units" :self.units        
        }

        w_weather_data: json = self.get_weather_data(p_url    = W_CURRENT_WEATHER_URL, 
                                                     p_params = W_PARAMETERS)
                
        return w_weather_data    


    def get_weather_summary(self) -> json:        
        
        if not self.weather_forecast:
            return None
        

        w_forecast_list = self.weather_forecast["list"]         

        if not w_forecast_list:
            return None
        
        try:
            #------------------------#
            #Check sunrise and Sunset
            #------------------------# 
            print(f"==>> Extract sunrise and sunset.")
            w_sunrise_time, w_sunset_time = self.get_sunrise_sunset(p_weather_data = self.weather_forecast, 
                                                                    p_data_name    = "city")
        except Exception as e:
            pass


        #Current weather                
        w_weather_now = self.get_weather_details(p_data         = self.current_weather, 
                                                 p_sunrise_time = w_sunrise_time, 
                                                 p_sunset_time  = w_sunset_time)                 
        
        w_count: int = 0        
        w_weather_forecast: json = {}     
        for w_weather in w_forecast_list:
            w_count += 1
            w_weather_forecast[f"{str(w_count)}"] = self.get_weather_details(p_data         = w_weather, 
                                                                             p_sunrise_time = w_sunrise_time, 
                                                                             p_sunset_time  = w_sunset_time) 
                        
        self.weather_summary:json ={"NOW"     : w_weather_now,
                                    "FORECAST": w_weather_forecast}
                    
        
        return self.weather_summary
        
        
        
if __name__ == "__main__":
    print("Run main.py")