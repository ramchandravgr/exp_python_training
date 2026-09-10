import requests
import time
def main():
    retryCount = 0
    while(True):
        retryCount+=1
        response: requests.Response = requests.get(url="http://127.0.0.1:5002/api/libraries/90210")
        response.status_code
        print(f"Status code: {response.status_code}")
        if(response.status_code==200):
            break
        print("Initiating graceful recovery...")
        print(f"Attempt {retryCount}: Failed and going for Retry in 2s")
        time.sleep(2)



if __name__ == "__main__":
    main()
