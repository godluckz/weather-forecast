import json, schedule, time, ipapi
from class_openweathermap import OpenWeatherApi
from os import environ
from class_notification_utils import NotificationUtility
import platform, re
# import argparse


w_device_location : json = None
w_device_details  : json = None


def load_device_details(): 
    global w_device_location, w_device_details
    try:       
        print("==>> Getting device location.")
        w_device_location = ipapi.location()
        # print(json.dumps(w_device_location,indent=4))
        # w_device_ip   = w_device_location["ip"]   
        # print(f"w_device_ip: {w_device_ip}")
        
        # w_response = requests.get('https://api64.ipify.org?format=json')
        # w_response.raise_for_status()
        # w_ip_response = w_response.json()
        # print(json.dumps(w_ip_response,indent=4))
        # w_device_ip   = w_ip_response["ip"]   
    except Exception as e:
        print(f"Error getting location: {e}")                    
        w_device_location = None
                
    # Get device details
    w_device_details = {
        "Machine": platform.machine(),
        "Version": platform.version(),
        "Platform": platform.platform(),
        "System": platform.system(),
        "Processor": platform.processor(),
        "Node": platform.node()
    }



def format_weather_data(p_weather_data, p_weather_date):                        
    w_icon_path    = p_weather_data["icon_path"] 
    w_image_source = f'<img src="{w_icon_path}" alt="loading problem" width=50 height=50>'
    
    w_format_str = f'''<p>                        
                    <b>Date:</b> {p_weather_date} <br>
                    {w_image_source} {p_weather_data["temperature"]}c - {p_weather_data["weather_description"]} <br>                
                    <b>Feels:</b> {p_weather_data["feels_like"]}c, <b>H:</b>{p_weather_data["temperature_max"]} <b>L:</b>{p_weather_data["temperature_min"]} <br>
                    <b>Humidity:</b> {p_weather_data["humidity"]}% <br>
                    <b>Wind:</b> {round(p_weather_data["wind_speed"]*3.6,2)} km/h  <br>
                    <b>Sunrise:</b> {p_weather_data["sunrise"]} <br>
                    <b>Sunset:</b> {p_weather_data["sunset"]} <br>                                            
                    </p>                    
                    '''     
    return w_format_str


def main(p_email_list : str) -> None:     
    load_device_details()
    w_device_lattitude = w_device_location["latitude"]
    W_device_longitude = w_device_location["longitude"]
    w_city             = w_device_location["city"]
    w_region           = w_device_location["region"]
    w_country_name     = w_device_location["country_name"]

    ## Print device details
    # for key, value in w_device_details.items():
    #     print(f"{key}: {value}")
    # print(f"w_device_lattitude: {w_device_lattitude}  - W_device_longitude: {W_device_longitude}")

    notification : NotificationUtility = NotificationUtility()    
    
    print("==>> Call OpenWeatherApi.")
    w_weather : OpenWeatherApi = OpenWeatherApi(p_latitude         = w_device_lattitude, 
                                                p_longitude        = W_device_longitude,
                                                p_forecast_records = 7)

    print("==>> Call to get weather summary.")
    w_weather_info: json= w_weather.get_weather_summary()  
    if w_weather_info:
        for w_weather_r in w_weather_info:        
            if w_weather_r == 'NOW':            
                w_weather      = w_weather_info[w_weather_r]   
                # print(w_weather)
                w_today_weather = f'''    
                                <p>                    
                                    <u><b>TODAY's WEATHER:</b></u> <br>                                                
                                '''                                        
                # w_today_weather = format_data_for_main(w_weather["data"], w_weather["weather_date"])
                w_today_weather = f'''                                
                                    {w_today_weather} {format_weather_data(w_weather["data"], w_weather["weather_date"])}                            
                                </p>
                                '''  
            elif w_weather_r == "FORECAST":            
                w_weather_focast = f'''    
                                <p>                    
                                    <u><b>WEATHER FORECAST:</b></u>                                                
                                '''  
                w_weather      = w_weather_info[w_weather_r]            
                # print(w_weather)
                for w_index in w_weather:
                    # print(w_weather[w_index]["data"])                                                  
                    w_weather_focast = f'''    
                                    {w_weather_focast} {format_weather_data(w_weather[w_index]["data"], w_weather[w_index]["weather_date"])}
                                    '''  
                w_weather_focast = f'''    
                                    {w_weather_focast}                            
                                    </p>                                                    
                                    '''  
        
        if w_weather_focast:
            w_email_body = f"""
                            <p>Good day,</p>
                            <p>Find below, weather information for {w_city}, {w_region} - {w_country_name}</p>
                            <p>========================</p>

                            {w_today_weather} 
                            =====================

                            {w_weather_focast}                            

                            <p>========================</p>
                            <p>Thank you,</p>
                            """                                                

            if p_email_list and len(p_email_list) > 0:    
                print("==>> Send forecast notification.")
                W_SUBJECT:  str = "🌦️Weather Forecast🌞"

                notification.send_email(p_email_to  = p_email_list,
                                        p_subject   = W_SUBJECT,                       
                                        p_message   = w_email_body)



def schedule_job(p_run_times : str, p_email_to: str):
    run_job    :bool = False
    w_job_name :str  = "weatherForecast"
    w_time_pattern = re.compile(r"^([01][0-9]|2[0-3]):([0-5][0-9])$")

    if not p_run_times:
        print("Not times give.")
        return
    
    w_run_imes : list = [i.strip() for i in p_run_times.split(",") if i]#remove empty data
    
    w_sleep_time_hours   = 1
    w_sleep_time_minutes = w_sleep_time_hours*60
    w_sleep_time_seconds = w_sleep_time_minutes*60

    schedule.cancel_job(w_job_name)
    for r_time in w_run_imes:    
        if w_time_pattern.match(r_time):
            try:
                schedule.every(1).day.at(r_time).do(lambda: main(p_email_list=p_email_to)).tag(w_job_name) 
                run_job = True
            except Exception as e:
                print(f"Fail to schedule for {r_time} - msg: {e}")
        else:
            print(f"{r_time} is skipped as it is not in a valid format e.g. 17:15")
    
       
    while run_job:        
        print("Check and run jobs.")
        schedule.run_pending()
        print(schedule.get_jobs())        
        print(f"Sleeping for {w_sleep_time_minutes} minute(s)")
        time.sleep(w_sleep_time_seconds)
        



if __name__ == "__main__":
    print("============++++++++++++============")    
    w_email_to      : str = input("Enter Email address to send weather report to (comma separated if more than one): ").strip().lower().replace(";",",")
    w_email_to_list : list = [i.strip() for i in w_email_to.split(",") if i]#remove empty data
    w_schedule_run  : str = input("Would you like to schedule the run?: ").strip().lower()    
    # w_parser = argparse.ArgumentParser()
    # w_parser.add_argument("--scheduleJob", type=str, required=True, help="schedule run")

    # args = w_parser.parse_args()
    # w_schedule_run = args.scheduleJob

    # print(f"schedule_run: {w_schedule_run}")
    if w_schedule_run in ("y","Y","Yes","YES"):
        w_run_times  : str = input("Run time in 24H format (e.g. 17:25), comma separated for multiple runs ?: ").strip().lower()    
        schedule_job(p_run_times = w_run_times,
                     p_email_to  = w_email_to_list)
    else:
        main(p_email_list = w_email_to_list)
    print("====================================")    
    print("=======Processing Completed!!=======")    
    print("====================================")    
    print("============++++++++++++============")    